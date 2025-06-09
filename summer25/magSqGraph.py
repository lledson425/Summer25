import subprocess
import sys

# AUTO-INSTALL REQUIRED PACKAGES 
def install_if_missing(package):
    try:
        __import__(package)
    except ImportError:
        print(f"Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

for pkg in ['pandas', 'matplotlib', 'numpy']:
    install_if_missing(pkg)

# IMPORT AFTER INSTALL 
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

#  CONFIG 
data_file = 'bins_test1.txt'

# LOAD AND CLEAN DATA 
try:
    # Load file, ignore lines starting with "#"
    df = pd.read_csv(data_file, delim_whitespace=True, comment='#', header=None)

    # Manually assign column names based on file format
    df.columns = ['L', 'T', 'binNum', 'E', 'ESq', 'AccRate_local', 'AccRate_clust',
                  'mag', 'magSq', 'sigma1', 'helicityMod_x', 'helicityMod_y']
    
    # Drop rows that are all NaN (can occur if blank lines or broken lines exist)
    df.dropna(how='all', inplace=True)

except FileNotFoundError:
    print(f" Error: '{data_file}' not found.")
    sys.exit(1)

# GROUP BY TEMPERATURE AND CALCULATE STATS 
grouped = df.groupby('T')
mean_magSq = grouped['magSq'].mean()
std_magSq = grouped['magSq'].std()
counts = grouped['magSq'].count()
stderr_magSq = std_magSq / np.sqrt(counts)

# PLOT 
plt.figure(figsize=(8, 6))
plt.errorbar(mean_magSq.index, mean_magSq.values, yerr=stderr_magSq.values,
             fmt='o-', capsize=5, label='magSq ± stderr')
plt.xlabel('Temperature (T)')
plt.ylabel('Average magSq')
plt.title('Average magSq vs Temperature with Standard Error Bars')
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()
