#!/usr/bin/env python3
"""Run Shapiro-Wilk normality test on a numeric column for CSV files."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from scipy import stats


def _list_csvs(measurements_dir: Path, files: list[str] | None) -> list[Path]:
    if files:
        return [Path(f) if Path(f).suffix == ".csv" else measurements_dir / f for f in files]
    return sorted(measurements_dir.glob("*.csv"))


def _get_series(path: Path, column: str) -> np.ndarray:
    df = pd.read_csv(path)
    if column not in df.columns:
        raise KeyError(f"Column '{column}' not found in {path}")
    series = pd.to_numeric(df[column], errors="coerce").dropna()
    return series.to_numpy()


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Shapiro-Wilk normality test for CSV column(s).")
    parser.add_argument(
        "--column",
        default="PACKAGE_ENERGY (J)",
        help="Column name to test (default: PACKAGE_ENERGY (J))",
    )
    parser.add_argument(
        "--measurements-dir",
        default="measurements",
        help="Directory with CSV files (default: measurements)",
    )
    parser.add_argument(
        "--files",
        nargs="*",
        help="Optional list of CSV files to include (default: all CSVs in measurements dir)",
    )
    parser.add_argument("--alpha", type=float, default=0.05, help="Significance level (default: 0.05)")
    args = parser.parse_args(argv)

    measurements_dir = Path(args.measurements_dir)
    csvs = _list_csvs(measurements_dir, args.files)
    if not csvs:
        raise SystemExit(f"No CSV files found in {measurements_dir}")

    print(f"Shapiro-Wilk test | column='{args.column}' | alpha={args.alpha}")
    for path in csvs:
        data = _get_series(path, args.column)
        if data.size < 3:
            print(f"{path}: not enough data (n={data.size})")
            continue
        stat, p = stats.shapiro(data)
        normal = "PASS" if p >= args.alpha else "FAIL"
        print(f"{path}: n={data.size} W={stat:.6f} p={p:.6g} normality={normal}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
