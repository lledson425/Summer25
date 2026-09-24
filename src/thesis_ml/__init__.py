"""Machine-learning models for Ising and XY spin configurations."""

from .ising_vae import VAE as IsingVAE
from .xy_vae import VAE as XYVAE

__all__ = ["IsingVAE", "XYVAE"]
