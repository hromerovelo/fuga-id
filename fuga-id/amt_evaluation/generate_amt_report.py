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
    AMT report generator.

    Produces a full report with:
    - Summary
    - Scenario comparisons
    - Pitch-vs-rhythm error analysis
"""

import argparse
import pandas as pd
import sys


def load_results(csv_path: str) -> pd.DataFrame:
    """Load evaluation results from a CSV file."""
    try:
        df = pd.read_csv(csv_path)
        return df
    except Exception as e:
        print(f"Error loading {csv_path}: {e}")
        sys.exit(1)


def generate_summary(df: pd.DataFrame) -> str:
    """Generate summary section."""
    lines = []
    lines.append("=" * 80)
    lines.append("SUMMARY - AMT EVALUATION")
    lines.append("=" * 80)
    lines.append("")

    # Totals
    lines.append(f"Total evaluated files: {len(df)}")
    lines.append(f"AMT system(s): {', '.join(df['amt_system'].unique())}")
    lines.append(f"Audio types: {', '.join(df['audio_type'].unique())}")
    lines.append("")

    # Global metrics
    if "note_f1" in df.columns:
        lines.append(
            f"Average Note F1:         {df['note_f1'].mean():.3f} (±{df['note_f1'].std():.3f})"
        )
    if "interval_accuracy" in df.columns:
        lines.append(
            f"Interval Accuracy:       {df['interval_accuracy'].mean():.3f} (±{df['interval_accuracy'].std():.3f})"
        )
    if "rhythm_accuracy" in df.columns:
        lines.append(
            f"Rhythm Accuracy:         {df['rhythm_accuracy'].mean():.3f} (±{df['rhythm_accuracy'].std():.3f})"
        )
    if "transcription_time_ms" in df.columns:
        lines.append(
            f"Transcription time:      {df['transcription_time_ms'].mean():.0f} ms on average"
        )

    return "\n".join(lines)


def compare_by_audio_type(df: pd.DataFrame) -> str:
    """Compare results by audio type."""
    lines = []
    lines.append("")
    lines.append("=" * 80)
    lines.append("COMPARISON BY AUDIO TYPE")
    lines.append("=" * 80)
    lines.append("")

    for audio_type in sorted(df["audio_type"].unique()):
        subset = df[df["audio_type"] == audio_type]

        lines.append(f"{'─' * 80}")
        lines.append(f"{audio_type.upper()}")
        lines.append(f"{'─' * 80}")
        lines.append(f"Files: {len(subset)}")
        lines.append("")

        # Note-level metrics
        if "note_f1" in subset.columns:
            lines.append("  Note-level metrics (mir_eval):")
            lines.append(
                f"     Note F1:         {subset['note_f1'].mean():.3f} (±{subset['note_f1'].std():.3f})"
            )
            lines.append(f"     Precision:       {subset['note_precision'].mean():.3f}")
            lines.append(f"     Recall:          {subset['note_recall'].mean():.3f}")
            if "voicing_recall" in subset.columns:
                lines.append(
                    f"     Voicing Recall:  {subset['voicing_recall'].mean():.3f}"
                )
            if "raw_pitch_accuracy" in subset.columns:
                lines.append(
                    f"     Pitch Accuracy:  {subset['raw_pitch_accuracy'].mean():.3f}"
                )
            lines.append("")

        # Interval-level metrics
        if "interval_accuracy" in subset.columns:
            lines.append("  Interval-level metrics (melodic patterns):")
            lines.append(
                f"     Interval Accuracy:  {subset['interval_accuracy'].mean():.3f} (±{subset['interval_accuracy'].std():.3f})"
            )
            lines.append(
                f"     Interval Similarity: {subset['interval_similarity'].mean():.3f}"
            )
            if "rhythm_accuracy" in subset.columns:
                lines.append(
                    f"     Rhythm Accuracy:    {subset['rhythm_accuracy'].mean():.3f} (±{subset['rhythm_accuracy'].std():.3f})"
                )
            if "length_ratio" in subset.columns:
                lines.append(
                    f"     Length Ratio:       {subset['length_ratio'].mean():.2f}"
                )
            lines.append("")

        # Timing
        if "transcription_time_ms" in subset.columns:
            lines.append(
                f"  Time: {subset['transcription_time_ms'].mean():.0f} ms (±{subset['transcription_time_ms'].std():.0f})"
            )
            lines.append("")

    return "\n".join(lines)


def analyze_pitch_vs_rhythm_errors(df: pd.DataFrame) -> str:
    """Analyze pitch vs rhythm errors."""
    lines = []
    lines.append("")
    lines.append("=" * 80)
    lines.append("ANALYSIS: PITCH vs RHYTHM ERRORS")
    lines.append("=" * 80)
    lines.append("")

    # For each audio type
    for audio_type in sorted(df["audio_type"].unique()):
        subset = df[df["audio_type"] == audio_type]

        if (
            "note_f1" not in subset.columns
            or "raw_pitch_accuracy" not in subset.columns
        ):
            continue

        avg_f1 = subset["note_f1"].mean()
        avg_pitch_acc = subset["raw_pitch_accuracy"].mean()
        avg_interval_acc = (
            subset["interval_accuracy"].mean()
            if "interval_accuracy" in subset.columns
            else 0
        )

        lines.append(f"{audio_type}:")
        lines.append(
            f"   Note F1:            {avg_f1:.3f} (requires exact pitch + timing ±50 ms)"
        )
        lines.append(
            f"   Pitch Accuracy:     {avg_pitch_acc:.3f} (% of frames with correct pitch)"
        )
        if avg_interval_acc > 0:
            lines.append(
                f"   Interval Accuracy:  {avg_interval_acc:.3f} (relative melodic patterns)"
            )
        lines.append("")

        # Gap between metrics
        gap = avg_pitch_acc - avg_f1

        if gap > 0.3:
            lines.append(
                f"   Large gap ({gap:.1%}): errors are mainly timing/segmentation"
            )
            lines.append(
                f"     The system detects pitch well ({avg_pitch_acc:.0%}) but fails on onset/offset"
            )
            timing_err_pct = min(gap * 100, (1 - avg_f1) * 70)
            pitch_err_pct = (1 - avg_f1) * 100 - timing_err_pct
            lines.append(
                f"     Estimate: ~{timing_err_pct:.0f}% timing error, ~{pitch_err_pct:.0f}% pitch error"
            )
        elif gap > 0.1:
            lines.append(f"   Moderate gap ({gap:.1%}): mixed errors")
            lines.append("     Issues affect both pitch and segmentation")
        else:
            lines.append(f"   Small gap ({gap:.1%}): errors are mainly pitch-related")
            lines.append("     The system has core pitch-detection limitations")

        lines.append("")

    return "\n".join(lines)


def generate_comparison_table(df: pd.DataFrame) -> str:
    """Generate comparison table."""
    lines = []
    lines.append("")
    lines.append("=" * 80)
    lines.append("COMPARISON TABLE")
    lines.append("=" * 80)
    lines.append("")

    # Header
    header = f"{'Scenario':<30} {'n':<8} {'Note F1':<10} {'Interval':<10} {'Rhythm':<10} {'Time(ms)':<12}"
    lines.append(header)
    lines.append("─" * 80)

    # Rows
    for audio_type in sorted(df["audio_type"].unique()):
        subset = df[df["audio_type"] == audio_type]

        n = len(subset)
        f1 = subset["note_f1"].mean() if "note_f1" in subset.columns else 0
        interval = (
            subset["interval_accuracy"].mean()
            if "interval_accuracy" in subset.columns
            else 0
        )
        rhythm = (
            subset["rhythm_accuracy"].mean()
            if "rhythm_accuracy" in subset.columns
            else 0
        )
        time = (
            subset["transcription_time_ms"].mean()
            if "transcription_time_ms" in subset.columns
            else 0
        )

        # Truncate long scenario names
        name = audio_type[:28]

        row = f"{name:<30} {n:<8} {f1:<10.3f} {interval:<10.3f} {rhythm:<10.3f} {time:<12.0f}"
        lines.append(row)

    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Generate a full AMT evaluation report"
    )

    parser.add_argument(
        "--input", required=True, help="CSV file with evaluation results"
    )

    parser.add_argument(
        "--output", default=None, help="Output file path (default: stdout)"
    )

    args = parser.parse_args()

    # Load data
    df = load_results(args.input)

    # Build report sections
    sections = []
    sections.append(generate_summary(df))
    sections.append(generate_comparison_table(df))
    sections.append(compare_by_audio_type(df))
    sections.append(analyze_pitch_vs_rhythm_errors(df))

    # Join report
    report = "\n".join(sections)

    # Output
    if args.output:
        with open(args.output, "w") as f:
            f.write(report)
        print(f"Report saved to: {args.output}")
    else:
        print(report)


if __name__ == "__main__":
    main()
