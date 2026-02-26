#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

DEFAULT_ENERGY_COLUMNS = ["PACKAGE_ENERGY (J)"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create violin and box plots for per-file package energy deltas "
            "from EnergiBridge CSV measurements."
        )
    )
    parser.add_argument(
        "-i",
        "--input",
        default="analysis",
        help="CSV file or directory containing CSV files (default: analysis)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="analysis/total_energy_violin_box.png",
        help="Output image path (default: analysis/total_energy_violin_box.png)",
    )
    parser.add_argument(
        "--columns",
        nargs="+",
        default=DEFAULT_ENERGY_COLUMNS,
        help="Energy columns to include (default: PACKAGE_ENERGY (J))",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Display the plot window in addition to saving the image",
    )
    return parser.parse_args()


def collect_csv_files(path_str: str) -> list[Path]:
    path = Path(path_str)
    if path.is_file():
        return [path]
    if path.is_dir():
        avg_files = sorted(path.glob("*_avg.csv"))
        if avg_files:
            return avg_files
        return sorted(path.glob("*.csv"))
    return []


def build_long_dataframe(csv_files: list[Path], columns: list[str]) -> pd.DataFrame:
    records: list[dict[str, object]] = []

    for csv_path in csv_files:
        if csv_path.stem.endswith("_001"):
            continue
        df = pd.read_csv(csv_path)
        column = next((col for col in columns if col in df.columns), None)
        if not column:
            continue
        series = pd.to_numeric(df[column], errors="coerce").dropna()
        if series.size < 2:
            continue
        value = float(series.iloc[-1] - series.iloc[0])
        records.append(
            {
                "file": csv_path.stem,
                "energy_delta_j": value,
            }
        )

    return pd.DataFrame.from_records(records)


def make_plots(long_df: pd.DataFrame, output_path: Path) -> None:
    categories = sorted(long_df["file"].unique().tolist())
    grouped_data = [
        long_df.loc[long_df["file"] == name, "energy_delta_j"].values
        for name in categories
    ]

    fig, axes = plt.subplots(1, 2, figsize=(14, 5), constrained_layout=True)

    axes[0].violinplot(grouped_data, showmeans=True, showmedians=True, showextrema=True)
    axes[0].set_title("Violin Plot: Package Energy Delta per File")
    axes[0].set_xlabel("Measurement File")
    axes[0].set_ylabel("Package Energy Delta (J)")
    axes[0].set_xticks(range(1, len(categories) + 1))
    axes[0].set_xticklabels(categories, rotation=20, ha="right")

    axes[1].boxplot(grouped_data, labels=categories, showfliers=True)
    axes[1].set_title("Box Plot: Package Energy Delta per File")
    axes[1].set_xlabel("Measurement File")
    axes[1].set_ylabel("Package Energy Delta (J)")
    axes[1].tick_params(axis="x", rotation=20)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def _summarize_totals(
    csv_files: list[Path], columns: list[str]
) -> dict[str, list[float]]:
    grouped: dict[str, list[float]] = {}
    for csv_path in csv_files:
        stem = csv_path.stem
        if stem.endswith("_001"):
            continue
        if stem.startswith("chrome_tiktok"):
            label = "chrome_tiktok"
        elif stem.startswith("chrome_youtube"):
            label = "chrome_youtube"
        else:
            continue
        df = pd.read_csv(csv_path)
        column = next((col for col in columns if col in df.columns), None)
        if not column:
            continue
        series = pd.to_numeric(df[column], errors="coerce").dropna()
        if series.size < 2:
            continue
        total = float(series.iloc[-1] - series.iloc[0])
        grouped.setdefault(label, []).append(total)
    return grouped


def _plot_group_summary(
    grouped_totals: dict[str, list[float]],
    output_path: Path,
    title: str,
) -> None:
    labels = sorted(grouped_totals.keys())
    means = [sum(grouped_totals[label]) / len(grouped_totals[label]) for label in labels]
    counts = [len(grouped_totals[label]) for label in labels]

    fig, axes = plt.subplots(1, 2, figsize=(12, 4), constrained_layout=True)
    bars = axes[0].bar(labels, means, color=["#2f6f8f", "#b4572a"])
    axes[0].set_title("Average Package Energy Delta")
    axes[0].set_ylabel("Average Package Energy Delta (J)")
    axes[0].set_xlabel("Scenario")
    axes[0].bar_label(bars, labels=[f"n={n}" for n in counts], padding=3)

    violin_data = [grouped_totals.get(label, []) for label in labels]
    axes[1].violinplot(violin_data, showmeans=True, showmedians=True, showextrema=True)
    axes[1].set_title("Per-File Package Energy Delta")
    axes[1].set_xlabel("Scenario")
    axes[1].set_ylabel("Package Energy Delta (J)")
    axes[1].set_xticks(range(1, len(labels) + 1))
    axes[1].set_xticklabels(labels, rotation=20, ha="right")

    fig.suptitle(title)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def _group_csvs_by_subfolder(input_dir: Path) -> dict[str, list[Path]]:
    groups: dict[str, list[Path]] = {}
    for subdir in sorted(p for p in input_dir.iterdir() if p.is_dir()):
        csvs = sorted(subdir.glob("*.csv"))
        if csvs:
            groups[subdir.name] = csvs
    return groups


def _resolve_output_path(output_arg: str, group_name: str) -> Path:
    output_path = Path(output_arg)
    if output_path.suffix.lower() == ".png":
        base_dir = output_path.parent
        base_name = output_path.stem
        return base_dir / f"{base_name}_{group_name}.png"
    return output_path / f"{group_name}_total_energy_violin_box.png"


def _group_avg_files(input_dir: Path) -> dict[str, list[Path]]:
    groups: dict[str, list[Path]] = {}
    for csv_path in sorted(input_dir.glob("*_avg.csv")):
        stem = csv_path.stem
        if stem.endswith("_chrome_tiktok_avg"):
            group = stem[: -len("_chrome_tiktok_avg")]
        elif stem.endswith("_chrome_youtube_avg"):
            group = stem[: -len("_chrome_youtube_avg")]
        else:
            group = stem[: -len("_avg")]
        groups.setdefault(group, []).append(csv_path)
    return groups


def _normalize_avg_labels(long_df: pd.DataFrame, group_name: str) -> pd.DataFrame:
    if long_df.empty:
        return long_df
    label = long_df["file"].copy()
    prefix = f"{group_name}_"
    label = label.str.removeprefix(prefix)
    label = label.str.replace("_avg", "", regex=False)
    return long_df.assign(file=label)


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    if input_path.is_dir():
        avg_groups = _group_avg_files(input_path)
        if avg_groups:
            output_dir = Path(args.output)
            if output_dir.suffix.lower() != ".png":
                output_dir.mkdir(parents=True, exist_ok=True)
            for group_name, csv_files in avg_groups.items():
                long_df = build_long_dataframe(csv_files, args.columns)
                long_df = _normalize_avg_labels(long_df, group_name)
                if long_df.empty:
                    print(f"Skipping {group_name}: no usable energy data")
                    continue
                output_path = _resolve_output_path(args.output, group_name)
                make_plots(long_df, output_path)
                print(f"{group_name}: processed {len(csv_files)} file(s)")
                print(f"{group_name}: saved violin + box plots to: {output_path}")
            if args.show:
                print("--show is ignored when generating per-subfolder plots.")
            return 0

        groups = _group_csvs_by_subfolder(input_path)
        root_csvs = sorted(input_path.glob("*.csv"))
        if root_csvs:
            groups[input_path.name] = root_csvs
        if not groups:
            print(f"No CSV files found at: {args.input}")
            return 1

        output_dir = Path(args.output)
        if output_dir.suffix.lower() != ".png":
            output_dir.mkdir(parents=True, exist_ok=True)

        for group_name, csv_files in groups.items():
            grouped_totals = _summarize_totals(csv_files, args.columns)
            if not grouped_totals:
                print(f"Skipping {group_name}: no chrome_tiktok/chrome_youtube data")
                continue
            output_path = _resolve_output_path(args.output, group_name)
            title = f"Average Package Energy Delta - {group_name}"
            _plot_group_summary(grouped_totals, output_path, title)
            total_files = sum(len(v) for v in grouped_totals.values())
            print(f"{group_name}: processed {total_files} file(s)")
            print(f"{group_name}: saved plot to: {output_path}")
        if args.show:
            print("--show is ignored when generating per-subfolder plots.")
        return 0

    csv_files = collect_csv_files(args.input)
    if not csv_files:
        print(f"No CSV files found at: {args.input}")
        return 1

    long_df = build_long_dataframe(csv_files, args.columns)
    if long_df.empty:
        print("No usable energy data found in the selected files/columns.")
        return 1

    output_path = Path(args.output)
    make_plots(long_df, output_path)

    print(f"Processed {len(csv_files)} file(s)")
    print(f"Saved violin + box plots to: {output_path}")

    if args.show:
        plot_df = long_df.copy()
        categories = sorted(plot_df["file"].unique().tolist())
        grouped_data = [
            plot_df.loc[plot_df["file"] == name, "energy_delta_j"].values
            for name in categories
        ]
        fig, axes = plt.subplots(1, 2, figsize=(14, 5), constrained_layout=True)
        axes[0].violinplot(
            grouped_data, showmeans=True, showmedians=True, showextrema=True
        )
    axes[0].set_title("Violin Plot: Package Energy Delta per File")
        axes[0].set_xlabel("Measurement File")
    axes[0].set_ylabel("Package Energy Delta (J)")
        axes[0].set_xticks(range(1, len(categories) + 1))
        axes[0].set_xticklabels(categories, rotation=20, ha="right")
        axes[1].boxplot(grouped_data, labels=categories, showfliers=True)
    axes[1].set_title("Box Plot: Package Energy Delta per File")
        axes[1].set_xlabel("Measurement File")
    axes[1].set_ylabel("Package Energy Delta (J)")
        axes[1].tick_params(axis="x", rotation=20)
        plt.show()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
