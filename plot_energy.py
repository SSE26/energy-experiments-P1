#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

DEFAULT_ENERGY_COLUMNS = [
    "PACKAGE_ENERGY (J)",
    "DRAM_ENERGY (J)",
    "PP0_ENERGY (J)",
    "PP1_ENERGY (J)",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create violin and box plots for per-sample energy consumption "
            "from EnergiBridge CSV measurements."
        )
    )
    parser.add_argument(
        "-i",
        "--input",
        default="measurements",
        help="CSV file or directory containing CSV files (default: measurements)",
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
        help=(
            "Energy columns to include (default: PACKAGE_ENERGY (J), "
            "DRAM_ENERGY (J), PP0_ENERGY (J), PP1_ENERGY (J))"
        ),
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
        return sorted(path.glob("*.csv"))
    return []


def build_long_dataframe(csv_files: list[Path], columns: list[str]) -> pd.DataFrame:
    records: list[dict[str, object]] = []

    for csv_path in csv_files:
        df = pd.read_csv(csv_path)
        present_columns = [col for col in columns if col in df.columns]
        if not present_columns:
            continue

        numeric_df = df[present_columns].apply(pd.to_numeric, errors="coerce")
        deltas = numeric_df.diff()
        deltas = deltas.where(deltas >= 0)
        total_deltas = deltas.sum(axis=1, min_count=1).dropna()

        for value in total_deltas:
            records.append(
                {
                    "file": csv_path.stem,
                    "energy_delta_j": float(value),
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
    axes[0].set_title("Violin Plot: Total Energy per Sample")
    axes[0].set_xlabel("Measurement File")
    axes[0].set_ylabel("Energy Delta (J)")
    axes[0].set_xticks(range(1, len(categories) + 1))
    axes[0].set_xticklabels(categories, rotation=20, ha="right")

    axes[1].boxplot(grouped_data, labels=categories, showfliers=True)
    axes[1].set_title("Box Plot: Total Energy per Sample")
    axes[1].set_xlabel("Measurement File")
    axes[1].set_ylabel("Energy Delta (J)")
    axes[1].tick_params(axis="x", rotation=20)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def main() -> int:
    args = parse_args()
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
        axes[0].set_title("Violin Plot: Total Energy per Sample")
        axes[0].set_xlabel("Measurement File")
        axes[0].set_ylabel("Energy Delta (J)")
        axes[0].set_xticks(range(1, len(categories) + 1))
        axes[0].set_xticklabels(categories, rotation=20, ha="right")
        axes[1].boxplot(grouped_data, labels=categories, showfliers=True)
        axes[1].set_title("Box Plot: Total Energy per Sample")
        axes[1].set_xlabel("Measurement File")
        axes[1].set_ylabel("Energy Delta (J)")
        axes[1].tick_params(axis="x", rotation=20)
        plt.show()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
