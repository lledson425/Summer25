# Senior Thesis: Spin Models and Representation Learning

This repository combines Monte Carlo simulation of two-dimensional spin models with
variational-autoencoder (VAE) and clustering analyses. It supports both the Ising
model and higher-dimensional O(N) models, including the XY model.

## Repository layout

```text
configs/             Example simulation parameter files
data/raw/            Generated simulation output (ignored by Git)
data/processed/      Derived arrays and tables (ignored by Git)
models/              Trained model artifacts (ignored by Git)
notebooks/ising/     Ising analysis notebooks
notebooks/xy/        XY analysis notebooks
scripts/             Simulation and plotting entry points
src/simulation/      C++ Monte Carlo simulator
src/thesis_ml/       Python VAE implementations
tests/                Lightweight project checks
```

Only source code, notebooks, configuration examples, and placeholder files are
versioned. Generated data and trained models belong in their respective ignored
directories.

## Python setup

Python 3.10 or newer is recommended.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev,resnet]"
```

The `resnet` extra supports the pretrained ResNet-18 embedding analysis in the Ising notebook. On GPU systems, install the PyTorch build appropriate for the local CUDA driver if needed.

Launch Jupyter from the repository root so the installed `thesis_ml` package is
available to every notebook:

```bash
jupyter lab
```

## Build the simulator

```bash
make -C src/simulation
```

The executable is written to `src/simulation/on`. The simulator expects a parameter
file named `params_<run-name>.txt` in its current working directory and writes
`bins_<run-name>.txt` and `spinConfigs_<run-name>.txt`.

## Generate data

The runner creates isolated run directories under `data/raw`, copies the example
configuration into each one, assigns a unique seed, and limits concurrency:

```bash
scripts/run_simulations.sh --runs 10 --jobs 4 --base-name ising
```

Run `scripts/run_simulations.sh --help` for all options. Edit a copy of
`configs/params_example.txt` for production runs and pass it with `--params`.

## Plot simulation output

```bash
python scripts/plot_magnetization.py data/raw/<run>/bins_<run>.txt \
  --output data/processed/magnetization.png
```

## Tests

```bash
pytest
```

The basic test suite does not require TensorFlow. Model import tests run automatically
when the optional ML dependencies are installed.
