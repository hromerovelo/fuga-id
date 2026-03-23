#!/usr/bin/env python3
"""
BSD 2-Clause License

Copyright (c) 2026, Hilda Romero-Velo
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

"""
    Created by Hilda Romero-Velo on February 2026.
"""

"""
    Generate a comparative AMT evaluation Excel report.
"""

import pandas as pd
import argparse
import sys
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.formatting.rule import ColorScaleRule


def load_results(csv_path: str) -> pd.DataFrame:
    """Load consolidated results CSV."""
    df = pd.read_csv(csv_path)

    # Validate required columns
    required = [
        "amt_system",
        "audio_type",
        "note_f1",
        "interval_accuracy",
        "rhythm_accuracy",
        "transcription_time_ms",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in CSV: {missing}")

    return df


def create_executive_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Creates executive summary table with key metrics by system and scenario.
    """
    summary_data = []

    for system in sorted(df["amt_system"].unique()):
        system_df = df[df["amt_system"] == system]

        # By scenario
        for audio_type in sorted(system_df["audio_type"].unique()):
            subset = system_df[system_df["audio_type"] == audio_type]

            # Check if ground_truth_type exists for this subset
            if (
                "ground_truth_type" in subset.columns
                and subset["ground_truth_type"].notna().any()
            ):
                # Split by ground truth type
                for gt_type in sorted(subset["ground_truth_type"].dropna().unique()):
                    gt_subset = subset[subset["ground_truth_type"] == gt_type]

                    summary_data.append(
                        {
                            "AMT System": system,
                            "Scenario": audio_type,
                            "Ground Truth": gt_type,
                            "N files": len(gt_subset),
                            "Note F1 (↑)": round(gt_subset["note_f1"].mean(), 3),
                            "Interval Acc (↑)": round(
                                gt_subset["interval_accuracy"].mean(), 3
                            ),
                            "Rhythm Acc (↑)": round(
                                gt_subset["rhythm_accuracy"].mean(), 3
                            ),
                            "Time/file (ms) (↓)": int(
                                gt_subset["transcription_time_ms"].mean()
                            ),
                            "Pitch Acc Raw (↑)": (
                                round(gt_subset["raw_pitch_accuracy"].mean(), 3)
                                if "raw_pitch_accuracy" in gt_subset.columns
                                else None
                            ),
                        }
                    )
            else:
                # No ground truth type, add as before
                summary_data.append(
                    {
                        "AMT System": system,
                        "Scenario": audio_type,
                        "Ground Truth": "-",
                        "N files": len(subset),
                        "Note F1 (↑)": round(subset["note_f1"].mean(), 3),
                        "Interval Acc (↑)": round(
                            subset["interval_accuracy"].mean(), 3
                        ),
                        "Rhythm Acc (↑)": round(subset["rhythm_accuracy"].mean(), 3),
                        "Time/file (ms) (↓)": int(
                            subset["transcription_time_ms"].mean()
                        ),
                        "Pitch Acc Raw (↑)": (
                            round(subset["raw_pitch_accuracy"].mean(), 3)
                            if "raw_pitch_accuracy" in subset.columns
                            else None
                        ),
                    }
                )

        # System overall average
        summary_data.append(
            {
                "AMT System": system,
                "Scenario": "⭐ OVERALL AVERAGE",
                "Ground Truth": "all",
                "N files": len(system_df),
                "Note F1 (↑)": round(system_df["note_f1"].mean(), 3),
                "Interval Acc (↑)": round(system_df["interval_accuracy"].mean(), 3),
                "Rhythm Acc (↑)": round(system_df["rhythm_accuracy"].mean(), 3),
                "Time/file (ms) (↓)": int(system_df["transcription_time_ms"].mean()),
                "Pitch Acc Raw (↑)": (
                    round(system_df["raw_pitch_accuracy"].mean(), 3)
                    if "raw_pitch_accuracy" in system_df.columns
                    else None
                ),
            }
        )

    return pd.DataFrame(summary_data)


def create_scenario_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """
    Detailed breakdown by scenario.
    """
    breakdown = []

    for audio_type in sorted(df["audio_type"].unique()):
        subset = df[df["audio_type"] == audio_type]

        # Add separator
        breakdown.append(
            {
                "Scenario": f"═══ {audio_type} ═══",
                "System": "",
                "Ground Truth": "",
                "N": "",
                "Note Precision": "",
                "Note Recall": "",
                "Note F1": "",
                "Interval Similarity": "",
                "Interval Accuracy": "",
                "Rhythm Accuracy": "",
                "Time (ms)": "",
            }
        )

        for system in sorted(subset["amt_system"].unique()):
            sys_subset = subset[subset["amt_system"] == system]

            # Check if ground_truth_type exists
            if (
                "ground_truth_type" in sys_subset.columns
                and sys_subset["ground_truth_type"].notna().any()
            ):
                # Split by ground truth type
                for gt_type in sorted(
                    sys_subset["ground_truth_type"].dropna().unique()
                ):
                    gt_subset = sys_subset[sys_subset["ground_truth_type"] == gt_type]

                    breakdown.append(
                        {
                            "Scenario": audio_type,
                            "System": system,
                            "Ground Truth": gt_type,
                            "N": len(gt_subset),
                            "Note Precision": round(
                                gt_subset["note_precision"].mean(), 3
                            ),
                            "Note Recall": round(gt_subset["note_recall"].mean(), 3),
                            "Note F1": round(gt_subset["note_f1"].mean(), 3),
                            "Interval Similarity": round(
                                gt_subset["interval_similarity"].mean(), 3
                            ),
                            "Interval Accuracy": round(
                                gt_subset["interval_accuracy"].mean(), 3
                            ),
                            "Rhythm Accuracy": round(
                                gt_subset["rhythm_accuracy"].mean(), 3
                            ),
                            "Time (ms)": int(gt_subset["transcription_time_ms"].mean()),
                        }
                    )
            else:
                # No ground truth type
                breakdown.append(
                    {
                        "Scenario": audio_type,
                        "System": system,
                        "Ground Truth": "-",
                        "N": len(sys_subset),
                        "Note Precision": round(sys_subset["note_precision"].mean(), 3),
                        "Note Recall": round(sys_subset["note_recall"].mean(), 3),
                        "Note F1": round(sys_subset["note_f1"].mean(), 3),
                        "Interval Similarity": round(
                            sys_subset["interval_similarity"].mean(), 3
                        ),
                        "Interval Accuracy": round(
                            sys_subset["interval_accuracy"].mean(), 3
                        ),
                        "Rhythm Accuracy": round(
                            sys_subset["rhythm_accuracy"].mean(), 3
                        ),
                        "Time (ms)": int(sys_subset["transcription_time_ms"].mean()),
                    }
                )

    return pd.DataFrame(breakdown)


def create_performance_comparison(df: pd.DataFrame) -> pd.DataFrame:
    """
    Performance table (speed vs accuracy).
    """
    perf_data = []

    for system in sorted(df["amt_system"].unique()):
        subset = df[df["amt_system"] == system]

        # Calculate aggregate metrics
        avg_time = subset["transcription_time_ms"].mean()
        avg_f1 = subset["note_f1"].mean()
        avg_interval = subset["interval_accuracy"].mean()

        # Classify speed
        if avg_time < 2000:
            speed_class = "⚡ Ultra-fast"
        elif avg_time < 5000:
            speed_class = "🏃 Fast"
        elif avg_time < 15000:
            speed_class = "🚶 Moderate"
        else:
            speed_class = "🐢 Slow"

        # Classify interval quality (most important for search)
        if avg_interval > 0.85:
            quality_class = "🥇 Excellent"
        elif avg_interval > 0.75:
            quality_class = "🥈 Good"
        elif avg_interval > 0.65:
            quality_class = "🥉 Acceptable"
        else:
            quality_class = "⚠️ Insufficient"

        perf_data.append(
            {
                "System": system,
                "Speed": speed_class,
                "Interval Quality": quality_class,
                "Avg Time (ms)": int(avg_time),
                "Note F1": round(avg_f1, 3),
                "Interval Accuracy": round(avg_interval, 3),
                "Rhythm Accuracy": round(subset["rhythm_accuracy"].mean(), 3),
                "Total Files": len(subset),
            }
        )

    return pd.DataFrame(perf_data)


def style_worksheet(ws, df, title):
    """Apply worksheet styling."""
    # Title
    ws.merge_cells(f"A1:{chr(64 + len(df.columns))}1")
    title_cell = ws["A1"]
    title_cell.value = title
    title_cell.font = Font(size=14, bold=True, color="FFFFFF")
    title_cell.fill = PatternFill(
        start_color="1F4E78", end_color="1F4E78", fill_type="solid"
    )
    title_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 30

    # Headers (row 2)
    for col_idx, col_name in enumerate(df.columns, 1):
        cell = ws.cell(row=2, column=col_idx)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(
            start_color="4472C4", end_color="4472C4", fill_type="solid"
        )
        cell.alignment = Alignment(horizontal="center")
        cell.border = Border(bottom=Side(style="thin", color="000000"))

    # Adjust widths
    for col_idx, col_name in enumerate(df.columns, 1):
        max_length = max(len(str(col_name)), 12)
        ws.column_dimensions[chr(64 + col_idx)].width = max_length + 2

    # Apply color scale to numeric metrics
    for col_idx, col_name in enumerate(df.columns, 1):
        if any(
            keyword in col_name.lower()
            for keyword in ["acc", "f1", "precision", "recall", "similarity"]
        ):
            col_letter = chr(64 + col_idx)
            ws.conditional_formatting.add(
                f"{col_letter}3:{col_letter}{len(df)+2}",
                ColorScaleRule(
                    start_type="min",
                    start_color="F8696B",
                    mid_type="percentile",
                    mid_value=50,
                    mid_color="FFEB84",
                    end_type="max",
                    end_color="63BE7B",
                ),
            )


def create_ground_truth_comparison(df: pd.DataFrame) -> pd.DataFrame:
    """
    Creates comparison of metrics by ground truth type (piano_midi vs original_score).
    Only applies when ground_truth_type column exists.
    """
    if "ground_truth_type" not in df.columns:
        return None

    # Filter only real instruments that have both ground truths
    instruments_df = df[df["audio_type"].str.startswith("real_instrument")]

    if instruments_df.empty:
        return None

    comparison_data = []

    for system in sorted(instruments_df["amt_system"].unique()):
        system_df = instruments_df[instruments_df["amt_system"] == system]

        # Data for piano_midi
        piano_df = system_df[system_df["ground_truth_type"] == "piano_midi"]
        # Data for original_score
        score_df = system_df[system_df["ground_truth_type"] == "original_score"]

        if not piano_df.empty and not score_df.empty:
            comparison_data.append(
                {
                    "AMT System": system,
                    "Ground Truth": "piano_midi",
                    "N files": len(piano_df),
                    "Note F1": round(piano_df["note_f1"].mean(), 3),
                    "Interval Acc": round(piano_df["interval_accuracy"].mean(), 3),
                    "Rhythm Acc": round(piano_df["rhythm_accuracy"].mean(), 3),
                    "Description": "Human interpretation (with folk variability)",
                }
            )

            comparison_data.append(
                {
                    "AMT System": system,
                    "Ground Truth": "original_score",
                    "N files": len(score_df),
                    "Note F1": round(score_df["note_f1"].mean(), 3),
                    "Interval Acc": round(score_df["interval_accuracy"].mean(), 3),
                    "Rhythm Acc": round(score_df["rhythm_accuracy"].mean(), 3),
                    "Description": "Quantized score (fixed reference)",
                }
            )

            # Calculate difference (interpretative variance contribution)
            comparison_data.append(
                {
                    "AMT System": system,
                    "Ground Truth": "Δ (piano - score)",
                    "N files": "",
                    "Note F1": round(
                        piano_df["note_f1"].mean() - score_df["note_f1"].mean(), 3
                    ),
                    "Interval Acc": round(
                        piano_df["interval_accuracy"].mean()
                        - score_df["interval_accuracy"].mean(),
                        3,
                    ),
                    "Rhythm Acc": round(
                        piano_df["rhythm_accuracy"].mean()
                        - score_df["rhythm_accuracy"].mean(),
                        3,
                    ),
                    "Description": "Interpretative variability contribution",
                }
            )

            # Separator row
            comparison_data.append(
                {
                    "AMT System": "",
                    "Ground Truth": "",
                    "N files": "",
                    "Note F1": "",
                    "Interval Acc": "",
                    "Rhythm Acc": "",
                    "Description": "",
                }
            )

    return pd.DataFrame(comparison_data) if comparison_data else None


def generate_excel_report(csv_path: str, output_path: str):
    """Generates comprehensive comparative Excel report."""
    print(f"Loading results from: {csv_path}")
    df = load_results(csv_path)

    print(f"Loaded {len(df)} results")
    print(f"   Systems: {', '.join(sorted(df['amt_system'].unique()))}")
    print(f"   Scenarios: {', '.join(sorted(df['audio_type'].unique()))}")

    wb = Workbook()
    wb.remove(wb.active)  # Remove default sheet

    # 1. Executive Summary
    print("\nGenerating sheet: Executive Summary...")
    summary_df = create_executive_summary(df)
    ws_summary = wb.create_sheet("Executive Summary")

    for r_idx, row in enumerate(
        dataframe_to_rows(summary_df, index=False, header=True), 2
    ):
        for c_idx, value in enumerate(row, 1):
            ws_summary.cell(row=r_idx, column=c_idx, value=value)

    style_worksheet(ws_summary, summary_df, "🎯 EXECUTIVE SUMMARY - AMT COMPARISON")

    # 2. Scenario breakdown
    print("Generating sheet: Scenario Breakdown...")
    breakdown_df = create_scenario_breakdown(df)
    ws_breakdown = wb.create_sheet("Scenario Breakdown")

    for r_idx, row in enumerate(
        dataframe_to_rows(breakdown_df, index=False, header=True), 2
    ):
        for c_idx, value in enumerate(row, 1):
            cell = ws_breakdown.cell(row=r_idx, column=c_idx, value=value)
            # Highlight separators
            if isinstance(value, str) and "═══" in value:
                cell.font = Font(bold=True)
                cell.fill = PatternFill(
                    start_color="E7E6E6", end_color="E7E6E6", fill_type="solid"
                )

    style_worksheet(ws_breakdown, breakdown_df, "📊 DETAILED BREAKDOWN BY SCENARIO")

    # 3. Performance
    print("Generating sheet: Performance...")
    perf_df = create_performance_comparison(df)
    ws_perf = wb.create_sheet("Performance")

    for r_idx, row in enumerate(
        dataframe_to_rows(perf_df, index=False, header=True), 2
    ):
        for c_idx, value in enumerate(row, 1):
            ws_perf.cell(row=r_idx, column=c_idx, value=value)

    style_worksheet(ws_perf, perf_df, "⚡ SPEED vs ACCURACY")

    # 4. Ground Truth Comparison (if exists)
    gt_comparison_df = create_ground_truth_comparison(df)
    if gt_comparison_df is not None:
        print("📋 Generating sheet: Ground Truth Comparison...")
        ws_gt = wb.create_sheet("Ground Truth Comparison")

        for r_idx, row in enumerate(
            dataframe_to_rows(gt_comparison_df, index=False, header=True), 2
        ):
            for c_idx, value in enumerate(row, 1):
                cell = ws_gt.cell(row=r_idx, column=c_idx, value=value)
                # Highlight differences (Δ)
                if isinstance(value, str) and "Δ" in value:
                    cell.font = Font(bold=True, color="FF6B35")
                    cell.fill = PatternFill(
                        start_color="FFF3CD", end_color="FFF3CD", fill_type="solid"
                    )

        style_worksheet(
            ws_gt,
            gt_comparison_df,
            "🎯 COMPARISON: Piano MIDI vs Original Scores",
        )

    # Save
    wb.save(output_path)
    print(f"\nExcel generated: {output_path}")
    print(f"\nSheets included:")
    print(f"   1. Executive Summary - Overall comparative view")
    print(f"   2. Scenario Breakdown - Complete metrics by scenario")
    print(f"   3. Performance - Speed vs accuracy")
    if gt_comparison_df is not None:
        print(f"   4. Ground Truth Comparison - Piano MIDI vs Original Scores")


def main():
    parser = argparse.ArgumentParser(
        description="Generate comparative Excel from AMT evaluation results",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_comparison_excel.py \\
    --input results/evaluation_complete_20260209.csv \\
    --output results/amt_comparison_report.xlsx
        """,
    )

    parser.add_argument(
        "--input", required=True, help="Consolidated CSV with evaluation results"
    )

    parser.add_argument(
        "--output",
        default="results/amt_comparison_report.xlsx",
        help="Output Excel path",
    )

    args = parser.parse_args()

    if not Path(args.input).exists():
        print(f"Error: file not found: {args.input}")
        sys.exit(1)

    # Create output directory if needed
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)

    generate_excel_report(args.input, args.output)


if __name__ == "__main__":
    main()
