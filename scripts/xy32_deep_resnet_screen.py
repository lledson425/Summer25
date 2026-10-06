from pathlib import Path
import json, time, traceback
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import torch
import torch.nn.functional as F
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from torchvision.models import (
    ResNet34_Weights, ResNet50_Weights, ResNet101_Weights,
    resnet34, resnet50, resnet101,
)

L=32; N_RUNS=10_000; N_T=41; BINS=10; TBKT=.89294
RATIOS=np.array([.60,.70,.78,.84,.87,.89,.90,.91,.92,.93,.94,.95,.96,.97,.98,.99,1.,1.01,1.02,1.03,1.04,1.05,1.06,1.07,1.08,1.09,1.10,1.11,1.12,1.13,1.14,1.15,1.16,1.17,1.18,1.19,1.20,1.30,1.45,1.60,1.80])
ROOT=Path('/home/lledson/senior-thesis/data/processed/xy32_broad/matched_all_bins')
STATE=Path('/home/lledson/senior-thesis/run_state'); STATE.mkdir(parents=True,exist_ok=True)
ANGLES=np.load(ROOT/'all_angles_float16.npy',mmap_mode='r')
temp_ids=np.tile(np.repeat(np.arange(N_T,dtype=np.int8),BINS),N_RUNS)
fit_bins=(np.arange(N_RUNS)[:,None]+np.arange(N_T)[None,:])%BINS
FIT=((np.arange(N_RUNS)[:,None]*N_T+np.arange(N_T)[None,:])*BINS+fit_bins).reshape(-1)
FIT_TEMP=temp_ids[FIT]
physics=np.load(ROOT/'resnet_pc_physical_observables_fit.npz')
energy=np.asarray(physics['energy_per_site'],np.float32)
device=torch.device('cuda')
specs={
 'resnet34':(resnet34,ResNet34_Weights.DEFAULT,512,384),
 'resnet50':(resnet50,ResNet50_Weights.DEFAULT,2048,224),
 'resnet101':(resnet101,ResNet101_Weights.DEFAULT,2048,160),
}

def embed(name,ctor,weights,dim,batch):
    path=ROOT/f'{name}_threephase_fit_embeddings_float16.npy'; prog=ROOT/f'{name}_threephase_fit_progress.txt'
    if path.exists(): out=np.lib.format.open_memmap(path,mode='r+'); start=int(prog.read_text()) if prog.exists() else len(FIT)
    else: out=np.lib.format.open_memmap(path,mode='w+',dtype=np.float16,shape=(len(FIT),dim)); start=0
    model=ctor(weights=weights); model.fc=torch.nn.Identity(); model.eval().to(device)
    mean=torch.tensor(weights.transforms().mean,device=device).view(1,3,1,1); std=torch.tensor(weights.transforms().std,device=device).view(1,3,1,1)
    phases=torch.tensor([0,-2*np.pi/3,2*np.pi/3],device=device).view(1,3,1,1)
    with torch.inference_mode():
      for s in range(start,len(FIT),batch):
        e=min(s+batch,len(FIT)); a=torch.tensor(np.asarray(ANGLES[FIT[s:e]],np.float32),device=device).unsqueeze(1)
        image=.5+.5*torch.cos(a+phases); image=F.interpolate(image,(224,224),mode='nearest'); image=(image-mean)/std
        with torch.autocast('cuda',dtype=torch.float16): z=model(image)
        out[s:e]=z.float().cpu().numpy().astype(np.float16)
        if e%10_000<batch or e==len(FIT): out.flush(); prog.write_text(str(e)); print(name,'embedded',e,'/',len(FIT),flush=True)
    del model; torch.cuda.empty_cache(); out.flush(); del out
    return np.load(path,mmap_mode='r')

def pca40(name,x,dim,batch=2048):
    path=ROOT/f'{name}_threephase_fit_pca.npz'; scores_path=ROOT/f'{name}_threephase_fit_pc1-40.npy'
    if path.exists():
      q=np.load(path); mean=q['mean']; vals=q['eigenvalues']; comps=q['components']
    else:
      total=torch.zeros(dim,device=device,dtype=torch.float64)
      for s in range(0,len(x),batch): total+=torch.tensor(np.asarray(x[s:s+batch],np.float32),device=device,dtype=torch.float64).sum(0)
      mu=total/len(x); cov=torch.zeros((dim,dim),device=device,dtype=torch.float32)
      muf=mu.float()
      for s in range(0,len(x),batch):
        z=torch.tensor(np.asarray(x[s:s+batch],np.float32),device=device)-muf; cov+=z.T@z
        if s%50_000<batch: print(name,'covariance',s,'/',len(x),flush=True)
      cov/=(len(x)-1); vals_t,vecs=torch.linalg.eigh(cov); order=torch.argsort(vals_t,descending=True)
      mean=mu.cpu().numpy(); vals=vals_t[order].double().cpu().numpy(); comps=vecs[:,order].T.cpu().numpy()
      np.savez(path,mean=mean,eigenvalues=vals,components=comps)
      del cov,vals_t,vecs; torch.cuda.empty_cache()
    if scores_path.exists(): scores=np.load(scores_path,mmap_mode='r')
    else:
      scores=np.lib.format.open_memmap(scores_path,mode='w+',dtype=np.float32,shape=(len(x),40)); ct=torch.tensor(comps[:40],device=device); mt=torch.tensor(mean,device=device,dtype=torch.float32)
      for s in range(0,len(x),4096):
        z=torch.tensor(np.asarray(x[s:s+4096],np.float32),device=device); scores[s:s+len(z)]=((z-mt)@ct.T).cpu().numpy()
      scores.flush(); del scores; scores=np.load(scores_path,mmap_mode='r')
    return vals,comps,scores

def corr(a,b):
    a=(a-a.mean())/a.std(); b=(b-b.mean())/b.std(); return float(np.mean(a*b))

rng=np.random.default_rng(901)
eval_pos=np.concatenate([rng.choice(np.flatnonzero(FIT_TEMP==ti),125,replace=False) for ti in range(N_T)])
rows=[]; curves={}

# Existing ResNet-18 three-phase scores establish the exact same baseline.
existing=np.load(ROOT/'resnet18_pc1-40_scores.npy',mmap_mode='r')
scores18=np.asarray(existing[FIT,:40],np.float32)
q=np.load(ROOT/'resnet18_pca.npz'); models={'resnet18':(q['eigenvalues'],scores18)}

for name,(ctor,weights,dim,batch) in specs.items():
    print('\nSTART',name,time.ctime(),flush=True)
    x=embed(name,ctor,weights,dim,batch); vals,comps,scores=pca40(name,x,dim); models[name]=(vals,np.asarray(scores,np.float32))
    print('DONE',name,time.ctime(),flush=True)

for name,(vals,scores) in models.items():
    evr=vals/vals.sum(); n90=int(np.searchsorted(np.cumsum(evr),.9)+1)
    candidates=[]
    for j in range(10):
      candidates += [(abs(corr(scores[:,j],energy)),j,'signed',scores[:,j]),(abs(corr(np.abs(scores[:,j]),energy)),j,'magnitude',np.abs(scores[:,j]))]
    best=max(candidates,key=lambda z:z[0]); energy_r,pc,form,feature=best; feature=np.asarray(feature,np.float32)[:,None]
    km=KMeans(2,random_state=42,n_init=10,max_iter=300,algorithm='lloyd').fit(feature)
    labels=km.labels_; high=int(np.argmax([RATIOS[FIT_TEMP[labels==k]].mean() for k in range(2)]))
    curve=np.array([(labels[FIT_TEMP==ti]==high).mean() for ti in range(N_T)]); curves[name]=curve
    sil=float(silhouette_score(feature[eval_pos],labels[eval_pos]))
    # Blind 40-PC benchmark with identical settings.
    km40=KMeans(2,random_state=42,n_init=10,max_iter=300,algorithm='lloyd').fit(scores[:,:40]); lab40=km40.labels_
    sil40=float(silhouette_score(scores[eval_pos,:40],lab40[eval_pos]))
    rows.append({'model':name,'embedding_dimensions':512 if name=='resnet18' else specs[name][2], 'PCs_for_90pct':n90,'best_energy_PC':pc+1,'score_form':form,'energy_abs_correlation':energy_r,'single_coordinate_silhouette':sil,'blind_PC1_40_silhouette':sil40,'low_T_high_cluster_fraction':curve[0],'at_TBKT_high_cluster_fraction':curve[16],'high_T_high_cluster_fraction':curve[-1]})

table=pd.DataFrame(rows).sort_values('model'); table.to_csv(ROOT/'xy32_deep_resnet_screen.csv',index=False)
(ROOT/'xy32_deep_resnet_screen.json').write_text(json.dumps(table.to_dict('records'),indent=2))
fig,ax=plt.subplots(figsize=(10,6))
for name in sorted(curves):
    row=table[table.model==name].iloc[0]; ax.plot(RATIOS,curves[name],'o-',ms=2.5,label=f"{name}: PC{row.best_energy_PC} {row.score_form}, sil={row.single_coordinate_silhouette:.3f}")
ax.axvline(1,color='black',ls='--',label=r'$T_{BKT}$'); ax.set(xlabel=r'$T/T_{BKT}$',ylabel='Higher-temperature cluster fraction',title='Deeper frozen ImageNet ResNets: identical three-phase XY screen'); ax.grid(alpha=.25); ax.legend(); fig.tight_layout(); fig.savefig(ROOT/'xy32_deep_resnet_screen.png',dpi=220)
print(table.to_string(index=False),flush=True)
(STATE/'xy32_deep_resnet_screen.complete').write_text(time.ctime())
