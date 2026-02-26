#!/usr/bin/env python3
"""Perform Welch's t-test on a numeric column between two CSV files or groups."""
from __future__ import annotations

import argparse
import glob
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


def _expand_targets(targets: list[str]) -> list[Path]:
    paths: list[Path] = []
    for target in targets:
        candidate = Path(target)
        if candidate.exists():
            if candidate.is_file():
                paths.append(candidate)
                continue
            if candidate.is_dir():
                paths.extend(sorted(candidate.rglob("*.csv")))
                continue
        for match in glob.glob(target, recursive=True):
            match_path = Path(match)
            if match_path.is_file():
                paths.append(match_path)
    return sorted(set(paths))


def _aggregate(series: np.ndarray, method: str) -> float | None:
    if series.size == 0:
        return None
    if method == "total":
        if series.size < 2:
            return None
        return float(series[-1] - series[0])
    if method == "mean":
        return float(np.mean(series))
    if method == "sum":
        return float(np.sum(series))
    if method == "median":
        return float(np.median(series))
    raise ValueError(f"Unknown aggregate method: {method}")


def _load_group(paths: list[Path], column: str, aggregate: str) -> tuple[np.ndarray, int]:
    values: list[float] = []
    skipped = 0
    for path in paths:
        series = _load_series(path, column)
        value = _aggregate(series, aggregate)
        if value is None:
            skipped += 1
            continue
        values.append(value)
    return np.asarray(values, dtype=float), skipped


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Welch's t-test on a CSV column between two files or groups."
    )
    parser.add_argument("--file-a", help="First CSV file path")
    parser.add_argument("--file-b", help="Second CSV file path")
    parser.add_argument(
        "--group-a",
        nargs="+",
        help=(
            "Group A targets (files, directories, or glob patterns). "
            "Example: measurements/**/chrome_tiktok_*.csv"
        ),
    )
    parser.add_argument(
        "--group-b",
        nargs="+",
        help=(
            "Group B targets (files, directories, or glob patterns). "
            "Example: measurements/**/chrome_youtube_*.csv"
        ),
    )
    parser.add_argument(
        "--column",
        default="PACKAGE_ENERGY (J)",
        help="Column name to compare (default: PACKAGE_ENERGY (J))",
    )
    parser.add_argument(
        "--aggregate",
        choices=["total", "mean", "sum", "median"],
        default="total",
        help="How to reduce each file to a single value (default: total)",
    )
    parser.add_argument("--alpha", type=float, default=0.05, help="Significance level (default: 0.05)")
    args = parser.parse_args(argv)

    if args.group_a or args.group_b:
        if not (args.group_a and args.group_b):
            raise SystemExit("Both --group-a and --group-b are required when using group mode")
        paths_a = _expand_targets(args.group_a)
        paths_b = _expand_targets(args.group_b)
        if not paths_a or not paths_b:
            raise SystemExit("Both --group-a and --group-b must resolve to at least one CSV")
        a, skipped_a = _load_group(paths_a, args.column, args.aggregate)
        b, skipped_b = _load_group(paths_b, args.column, args.aggregate)
        label_a = f"group-a ({len(paths_a)} files)"
        label_b = f"group-b ({len(paths_b)} files)"
    else:
        if not args.file_a or not args.file_b:
            raise SystemExit("Provide --file-a and --file-b, or use --group-a and --group-b")
        file_a = Path(args.file_a)
        file_b = Path(args.file_b)
        if not file_a.exists() or not file_b.exists():
            raise SystemExit("Both --file-a and --file-b must exist")
        a = _load_series(file_a, args.column)
        b = _load_series(file_b, args.column)
        skipped_a = 0
        skipped_b = 0
        label_a = str(file_a)
        label_b = str(file_b)

    if a.size < 2 or b.size < 2:
        raise SystemExit(f"Not enough data (n_a={a.size}, n_b={b.size})")

    t_stat, p = stats.ttest_ind(a, b, equal_var=False)
    mean_a = float(np.mean(a))
    mean_b = float(np.mean(b))
    mean_diff = mean_a - mean_b
    pct_diff = (mean_diff / mean_b) * 100 if mean_b != 0 else float("nan")

    decision = "REJECT" if p < args.alpha else "FAIL TO REJECT"

    print("Welch's t-test (two-sided)")
    print(f"column='{args.column}' aggregate={args.aggregate} alpha={args.alpha}")
    print(f"A: {label_a} n={a.size} mean={mean_a:.6g}")
    print(f"B: {label_b} n={b.size} mean={mean_b:.6g}")
    print(f"t={t_stat:.6g} p={p:.6g} decision={decision} H0")
    print(f"mean_diff (A-B) = {mean_diff:.6g}")
    print(f"percent_diff (A-B)/B = {pct_diff:.6g}%")
    if skipped_a or skipped_b:
        print(f"Skipped files: A={skipped_a} B={skipped_b}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
