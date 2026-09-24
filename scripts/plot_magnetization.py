#!/usr/bin/env python3
"""Plot mean squared magnetization as a function of temperature."""


import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

COLUMNS = [
    "L", "T", "bin_num", "E", "E_sq", "acceptance_local",
    "acceptance_cluster", "magnetization", "magnetization_sq", "sigma1",
    "helicity_modulus_x", "helicity_modulus_y",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Simulator bins_*.txt file")
    parser.add_argument("--output", type=Path, help="Save the plot instead of displaying it")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    frame = pd.read_csv(args.input, sep=r"\s+", comment="#", header=None, names=COLUMNS)
    grouped = frame.groupby("T")["magnetization_sq"]
    mean = grouped.mean()
    stderr = grouped.std() / np.sqrt(grouped.count())

    _, axis = plt.subplots(figsize=(8, 6))
    axis.errorbar(mean.index, mean.values, yerr=stderr.values, fmt="o-", capsize=5)
    axis.set(xlabel="Temperature", ylabel="Mean squared magnetization")
    axis.grid(True)
    plt.tight_layout()

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(args.output, dpi=200)
    else:
        plt.show()


if __name__ == "__main__":
    main()
