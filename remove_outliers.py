#!/usr/bin/env python3
"""Remove 3-sigma outliers from a numeric column in a CSV file."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Remove outliers (mean ± 3*std) from a CSV column.")
    parser.add_argument("--file", required=True, help="CSV file path")
    parser.add_argument(
        "--column",
        default="PACKAGE_ENERGY (J)",
        help="Column name to filter (default: PACKAGE_ENERGY (J))",
    )
    parser.add_argument(
        "--out",
        help="Output CSV path (default: measurements/cleaned_<name>.csv)",
    )
    args = parser.parse_args(argv)

    src = Path(args.file)
    if not src.exists():
        raise SystemExit(f"File not found: {src}")

    df = pd.read_csv(src)
    if args.column not in df.columns:
        raise SystemExit(f"Column '{args.column}' not found in {src}")

    series = pd.to_numeric(df[args.column], errors="coerce")
    mean = series.mean()
    std = series.std(ddof=0)
    lower = mean - 3 * std
    upper = mean + 3 * std

    mask = series.between(lower, upper, inclusive="both")
    filtered = df[mask].copy()

    out = Path(args.out) if args.out else src.parent / f"cleaned_{src.name}"
    filtered.to_csv(out, index=False)

    removed = len(df) - len(filtered)
    print(
        f"Removed {removed} rows out of {len(df)} (kept {len(filtered)}). "
        f"Bounds: [{lower:.6g}, {upper:.6g}] -> {out}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
