#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt


DEFAULT_ENERGY_COLUMNS = ["PACKAGE_ENERGY (J)"]


def _collect_groups(input_dir: Path) -> dict[str, dict[str, list[Path]]]:
    groups: dict[str, dict[str, list[Path]]] = {}
    root_group: dict[str, list[Path]] = {"chrome_tiktok": [], "chrome_youtube": []}
    for csv_path in sorted(input_dir.glob("*.csv")):
        stem = csv_path.stem
        if stem.endswith("_001"):
            continue
        if stem.startswith("chrome_tiktok"):
            root_group["chrome_tiktok"].append(csv_path)
        elif stem.startswith("chrome_youtube"):
            root_group["chrome_youtube"].append(csv_path)
    if root_group["chrome_tiktok"] or root_group["chrome_youtube"]:
        groups[input_dir.name] = root_group
    for subdir in sorted(p for p in input_dir.iterdir() if p.is_dir()):
        by_label: dict[str, list[Path]] = {"chrome_tiktok": [], "chrome_youtube": []}
        for csv_path in sorted(subdir.glob("*.csv")):
            stem = csv_path.stem
            if stem.endswith("_001"):
                continue
            if stem.startswith("chrome_tiktok"):
                by_label["chrome_tiktok"].append(csv_path)
            elif stem.startswith("chrome_youtube"):
                by_label["chrome_youtube"].append(csv_path)
        if by_label["chrome_tiktok"] or by_label["chrome_youtube"]:
            groups[subdir.name] = by_label
    return groups


def _total_energy_from_csv(path: Path, columns: list[str]) -> float | None:
    df = pd.read_csv(path)
    column = next((col for col in columns if col in df.columns), None)
    if not column:
        return None
    series = pd.to_numeric(df[column], errors="coerce").dropna()
    if series.size < 2:
        return None
    return float(series.iloc[-1] - series.iloc[0])


def _collect_totals(paths: list[Path], columns: list[str]) -> np.ndarray:
    values: list[float] = []
    for path in paths:
        total = _total_energy_from_csv(path, columns)
        if total is not None:
            values.append(total)
    return np.asarray(values, dtype=float)


def _shapiro(series: np.ndarray, alpha: float) -> tuple[float, float, bool]:
    if series.size < 3:
        return float("nan"), float("nan"), False
    stat, p = stats.shapiro(series)
    return float(stat), float(p), bool(p >= alpha)


def _remove_outliers(series: np.ndarray) -> np.ndarray:
    if series.size == 0:
        return series
    mean = float(np.mean(series))
    std = float(np.std(series, ddof=0))
    if std == 0:
        return series
    lower = mean - 3 * std
    upper = mean + 3 * std
    return series[(series >= lower) & (series <= upper)]


def _cohens_d(a: np.ndarray, b: np.ndarray) -> float:
    if a.size < 2 or b.size < 2:
        return float("nan")
    var_a = np.var(a, ddof=1)
    var_b = np.var(b, ddof=1)
    pooled = ((a.size - 1) * var_a + (b.size - 1) * var_b) / (a.size + b.size - 2)
    if pooled <= 0:
        return float("nan")
    return float((np.mean(a) - np.mean(b)) / np.sqrt(pooled))


def _plot_violin_box(a: np.ndarray, b: np.ndarray, output_path: Path, title: str) -> None:
    labels = ["chrome_tiktok", "chrome_youtube"]
    grouped_data = [a, b]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4), constrained_layout=True)
    axes[0].violinplot(grouped_data, showmeans=True, showmedians=True, showextrema=True)
    axes[0].set_title("Violin Plot: Package Energy Delta per File")
    axes[0].set_xlabel("Scenario")
    axes[0].set_ylabel("Package Energy Delta (J)")
    axes[0].set_xticks(range(1, len(labels) + 1))
    axes[0].set_xticklabels(labels, rotation=20, ha="right")

    axes[1].boxplot(grouped_data, labels=labels, showfliers=True)
    axes[1].set_title("Box Plot: Package Energy Delta per File")
    axes[1].set_xlabel("Scenario")
    axes[1].set_ylabel("Package Energy Delta (J)")
    axes[1].tick_params(axis="x", rotation=20)

    fig.suptitle(title)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Full analysis pipeline: plots, normality, outliers, Welch test, effect size."
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
        help="Output directory for plots/reports (default: analysis)",
    )
    parser.add_argument(
        "--columns",
        nargs="+",
        default=DEFAULT_ENERGY_COLUMNS,
        help="Energy columns to include (default: PACKAGE_ENERGY (J))",
    )
    parser.add_argument("--alpha", type=float, default=0.05, help="Significance level")
    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    groups = _collect_groups(input_dir)
    if not groups:
        print(f"No matching subfolders found in {input_dir}")
        return 1

    for subfolder, by_label in groups.items():
        a_raw = _collect_totals(by_label["chrome_tiktok"], args.columns)
        b_raw = _collect_totals(by_label["chrome_youtube"], args.columns)

        report_lines: list[str] = []
        report_lines.append(f"Subfolder: {subfolder}")
        report_lines.append(f"Samples: tiktok={a_raw.size} youtube={b_raw.size}")

        if a_raw.size < 2 or b_raw.size < 2:
            report_lines.append("Not enough samples for statistics.")
            (output_dir / f"{subfolder}_report.txt").write_text("\n".join(report_lines))
            continue

        stat_a, p_a, normal_a = _shapiro(a_raw, args.alpha)
        stat_b, p_b, normal_b = _shapiro(b_raw, args.alpha)
        report_lines.append("Normality (Shapiro-Wilk, raw):")
        report_lines.append(f"tiktok: W={stat_a:.6g} p={p_a:.6g} normal={normal_a}")
        report_lines.append(f"youtube: W={stat_b:.6g} p={p_b:.6g} normal={normal_b}")

        a_clean = a_raw
        b_clean = b_raw
        removed_a = 0
        removed_b = 0
        if not (normal_a and normal_b):
            a_clean = _remove_outliers(a_raw)
            b_clean = _remove_outliers(b_raw)
            removed_a = int(a_raw.size - a_clean.size)
            removed_b = int(b_raw.size - b_clean.size)
            stat_a2, p_a2, normal_a2 = _shapiro(a_clean, args.alpha)
            stat_b2, p_b2, normal_b2 = _shapiro(b_clean, args.alpha)
            report_lines.append("Normality (after 3-sigma outlier removal):")
            report_lines.append(f"tiktok: W={stat_a2:.6g} p={p_a2:.6g} normal={normal_a2}")
            report_lines.append(f"youtube: W={stat_b2:.6g} p={p_b2:.6g} normal={normal_b2}")
            report_lines.append(f"Outliers removed: tiktok={removed_a} youtube={removed_b}")
            if not (normal_a2 and normal_b2):
                report_lines.append("Normality still failed: experiment should be repeated.")
                u_stat, p_u = stats.mannwhitneyu(a_clean, b_clean, alternative="two-sided")
                report_lines.append("Mann-Whitney U (two-sided):")
                report_lines.append(f"U={u_stat:.6g} p={p_u:.6g} alpha={args.alpha}")

        if a_clean.size < 2 or b_clean.size < 2:
            report_lines.append("Not enough samples after cleaning.")
            (output_dir / f"{subfolder}_report.txt").write_text("\n".join(report_lines))
            continue

        t_stat, p = stats.ttest_ind(a_clean, b_clean, equal_var=False)
        mean_a = float(np.mean(a_clean))
        mean_b = float(np.mean(b_clean))
        mean_diff = mean_a - mean_b
        pct_diff = (mean_diff / mean_b) * 100 if mean_b != 0 else float("nan")
        d = _cohens_d(a_clean, b_clean)

        report_lines.append("Welch's t-test (two-sided):")
        report_lines.append(f"t={t_stat:.6g} p={p:.6g} alpha={args.alpha}")
        report_lines.append(f"mean_tiktok={mean_a:.6g} mean_youtube={mean_b:.6g}")
        report_lines.append(f"mean_diff (A-B)={mean_diff:.6g}")
        report_lines.append(f"percent_diff (A-B)/B={pct_diff:.6g}%")
        report_lines.append(f"Cohen's d={d:.6g}")

        report_path = output_dir / f"{subfolder}_report.txt"
        report_path.write_text("\n".join(report_lines))

        plot_path = output_dir / f"{subfolder}_violin_box.png"
        _plot_violin_box(a_clean, b_clean, plot_path, f"{subfolder} Package Energy Delta")

        print(f"{subfolder}: wrote {report_path} and {plot_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
