#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def _collect_groups(input_dir: Path) -> dict[str, dict[str, list[Path]]]:
    groups: dict[str, dict[str, list[Path]]] = {}
    for subdir in sorted(p for p in input_dir.iterdir() if p.is_dir()):
        by_label: dict[str, list[Path]] = {"chrome_tiktok": [], "chrome_youtube": []}
        for csv_path in sorted(subdir.glob("*.csv")):
            stem = csv_path.stem
            if stem.startswith("chrome_tiktok"):
                by_label["chrome_tiktok"].append(csv_path)
            elif stem.startswith("chrome_youtube"):
                by_label["chrome_youtube"].append(csv_path)
        if by_label["chrome_tiktok"] or by_label["chrome_youtube"]:
            groups[subdir.name] = by_label
    return groups


def _round_time(series: pd.Series, resolution: int) -> pd.Series:
    if resolution <= 0:
        return series
    return (series / resolution).round().astype("Int64") * resolution


def _average_group(
    csv_files: list[Path],
    columns: list[str],
    time_round_ns: int,
    reset_threshold: float,
) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    present_sets: list[set[str]] = []
    for csv_path in csv_files:
        df = pd.read_csv(csv_path)
        if "Time" not in df.columns:
            continue
        present = [col for col in columns if col in df.columns]
        if not present:
            continue
        present_sets.append(set(present))

        frame = df[["Time", *present]].copy()
        frame["Time"] = pd.to_numeric(frame["Time"], errors="coerce")
        for col in present:
            frame[col] = pd.to_numeric(frame[col], errors="coerce")
        frame = frame.dropna(subset=["Time"])
        frame = frame.sort_values("Time")

        numeric_df = frame[present]
        deltas = numeric_df.diff()
        deltas = deltas.where(deltas >= reset_threshold)
        deltas = deltas.mask(deltas < 0, 0)

        deltas.insert(0, "Time", frame["Time"].values)
        if time_round_ns > 0:
            deltas["Time"] = _round_time(deltas["Time"], time_round_ns)
        deltas = deltas.dropna(subset=["Time"])
        if deltas.empty:
            continue

        # Within-file duplicate times: average them before cross-file averaging.
        deltas = deltas.groupby("Time", as_index=False).mean(numeric_only=True)
        frames.append(deltas)

    if not frames:
        return pd.DataFrame()

    common_cols = set(columns)
    if present_sets:
        common_cols = set.intersection(*present_sets)
    missing_cols = set(columns) - common_cols
    if missing_cols:
        print(f"Warning: dropping columns not present in all files: {sorted(missing_cols)}")

    keep_cols = ["Time", *sorted(common_cols)]
    trimmed = [frame[keep_cols] for frame in frames]
    combined = pd.concat(trimmed, ignore_index=True)
    averaged = combined.groupby("Time", as_index=False).mean(numeric_only=True)

    if common_cols:
        averaged["TOTAL_ENERGY_DELTA (J)"] = averaged[list(common_cols)].sum(
            axis=1, min_count=1
        )
    return averaged


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Average CSV samples per subfolder and platform, grouped by Time."
    )
    parser.add_argument(
        "-i",
        "--input",
        default="measurements",
        help="Measurements directory with subfolders (default: measurements)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="analysis",
        help="Output directory for averaged CSVs (default: analysis)",
    )
    parser.add_argument(
        "--columns",
        nargs="+",
        default=["PACKAGE_ENERGY (J)", "DRAM_ENERGY (J)", "PP0_ENERGY (J)", "PP1_ENERGY (J)"],
        help="Energy columns to include in averaging",
    )
    parser.add_argument(
        "--time-round",
        type=int,
        default=1_000_000,
        help="Round Time to this resolution in ns before averaging (default: 1_000_000)",
    )
    parser.add_argument(
        "--reset-threshold",
        type=float,
        default=-1e-3,
        help="Treat deltas below this as counter resets (default: -1e-3)",
    )
    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    groups = _collect_groups(input_dir)
    if not groups:
        print(f"No matching subfolders found in {input_dir}")
        return 1

    for subfolder, by_label in groups.items():
        for label, csv_files in by_label.items():
            if not csv_files:
                continue
            averaged = _average_group(
                csv_files,
                args.columns,
                args.time_round,
                args.reset_threshold,
            )
            if averaged.empty:
                print(f"Skipping {subfolder}/{label}: no usable data")
                continue
            out_path = output_dir / f"{subfolder}_{label}_avg.csv"
            averaged.to_csv(out_path, index=False)
            print(f"Wrote {out_path} ({len(csv_files)} files)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
