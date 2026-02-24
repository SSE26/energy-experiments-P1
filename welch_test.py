#!/usr/bin/env python3
"""Perform Welch's t-test on a numeric column between two CSV files."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from scipy import stats


def _load_series(path: Path, column: str) -> np.ndarray:
    df = pd.read_csv(path)
    if column not in df.columns:
        raise KeyError(f"Column '{column}' not found in {path}")
    return pd.to_numeric(df[column], errors="coerce").dropna().to_numpy()


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Welch's t-test on a CSV column between two files.")
    parser.add_argument("--file-a", required=True, help="First CSV file path")
    parser.add_argument("--file-b", required=True, help="Second CSV file path")
    parser.add_argument(
        "--column",
        default="PACKAGE_ENERGY (J)",
        help="Column name to compare (default: PACKAGE_ENERGY (J))",
    )
    parser.add_argument("--alpha", type=float, default=0.05, help="Significance level (default: 0.05)")
    args = parser.parse_args(argv)

    file_a = Path(args.file_a)
    file_b = Path(args.file_b)
    if not file_a.exists() or not file_b.exists():
        raise SystemExit("Both --file-a and --file-b must exist")

    a = _load_series(file_a, args.column)
    b = _load_series(file_b, args.column)

    if a.size < 2 or b.size < 2:
        raise SystemExit(f"Not enough data (n_a={a.size}, n_b={b.size})")

    t_stat, p = stats.ttest_ind(a, b, equal_var=False)
    mean_a = float(np.mean(a))
    mean_b = float(np.mean(b))
    mean_diff = mean_a - mean_b
    pct_diff = (mean_diff / mean_b) * 100 if mean_b != 0 else float("nan")

    decision = "REJECT" if p < args.alpha else "FAIL TO REJECT"

    print("Welch's t-test (two-sided)")
    print(f"column='{args.column}' alpha={args.alpha}")
    print(f"A: {file_a} n={a.size} mean={mean_a:.6g}")
    print(f"B: {file_b} n={b.size} mean={mean_b:.6g}")
    print(f"t={t_stat:.6g} p={p:.6g} decision={decision} H0")
    print(f"mean_diff (A-B) = {mean_diff:.6g}")
    print(f"percent_diff (A-B)/B = {pct_diff:.6g}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
