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
    Runs a full AMT evaluation matrix (systems x scenarios) and generates
    consolidated CSV, text report, and comparative Excel output.
"""

import argparse
import subprocess
import sys
import os
import pandas as pd
from pandas.errors import EmptyDataError
from datetime import datetime


def run_evaluation(mode: str, amt_system: str, output: str, limit: int = None) -> bool:
    """Run one AMT evaluation job."""
    cmd = [
        sys.executable,
        "evaluate_amt.py",
        "--mode",
        mode,
        "--amt-system",
        amt_system,
        "--output",
        output,
    ]

    if limit:
        cmd.extend(["--limit", str(limit)])

    print(f"\n{'='*80}")
    print(f"Running: {amt_system} - {mode}")
    print(f"{'='*80}")

    log_path = os.path.splitext(output)[0] + ".log"

    try:
        # Keep stdout in terminal, redirect stderr (warnings/noise) to log.
        with open(log_path, "w") as log_file:
            subprocess.run(cmd, check=True, stderr=log_file)
        print(f"Warnings log: {log_path}")
        print(f"Completed: {amt_system} - {mode}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error in {amt_system} - {mode}: {e}")
        print(f"Check warnings/errors log: {log_path}")
        return False


def consolidate_results(csv_files: list, output: str):
    """Consolidate multiple CSV files into one."""
    all_dfs = []
    skipped_files = []

    for csv_file in csv_files:
        if os.path.exists(csv_file):
            try:
                if os.path.getsize(csv_file) == 0:
                    skipped_files.append((csv_file, "empty file"))
                    continue

                df = pd.read_csv(csv_file)
                if df.empty:
                    skipped_files.append((csv_file, "no rows"))
                    continue

                all_dfs.append(df)
            except EmptyDataError:
                skipped_files.append((csv_file, "no columns"))
            except Exception as e:
                skipped_files.append((csv_file, f"read error: {e}"))

    if skipped_files:
        print("\nSkipped CSV files during consolidation:")
        for path, reason in skipped_files:
            print(f"   - {path} ({reason})")

    if all_dfs:
        consolidated = pd.concat(all_dfs, ignore_index=True)
        consolidated.to_csv(output, index=False)
        print(f"\nConsolidated results saved to: {output}")
        print(f"   Total evaluations: {len(consolidated)}")
        return True
    else:
        print("\nNo CSV files were found to consolidate")
        return False


def validate_csv_output(csv_file: str):
    """Validate that a CSV exists and contains at least one data row."""
    if not os.path.exists(csv_file):
        return False, "file not found"

    try:
        if os.path.getsize(csv_file) == 0:
            return False, "empty file"

        df = pd.read_csv(csv_file)
        if df.empty:
            return False, "no rows"

        return True, "ok"
    except EmptyDataError:
        return False, "no columns"
    except Exception as e:
        return False, f"read error: {e}"


def generate_comparison_report(consolidated_csv: str, output_txt: str):
    """Generate a comparative report across AMT systems."""
    df = pd.read_csv(consolidated_csv)

    lines = []
    lines.append("=" * 80)
    lines.append("AMT COMPARATIVE REPORT - FULL EVALUATION")
    lines.append("=" * 80)
    lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Total evaluations: {len(df)}")
    lines.append("")

    # Summary by AMT system
    lines.append("=" * 80)
    lines.append("COMPARISON BY AMT SYSTEM")
    lines.append("=" * 80)
    lines.append("")

    for amt_system in sorted(df["amt_system"].unique()):
        subset = df[df["amt_system"] == amt_system]
        lines.append(f"{'─'*80}")
        lines.append(f"{amt_system.upper()}")
        lines.append(f"{'─'*80}")
        lines.append(f"Evaluations: {len(subset)}")

        if "note_f1" in subset.columns:
            lines.append(
                f"Note F1:           {subset['note_f1'].mean():.3f} (±{subset['note_f1'].std():.3f})"
            )
        if "interval_accuracy" in subset.columns:
            lines.append(
                f"Interval Accuracy: {subset['interval_accuracy'].mean():.3f} (±{subset['interval_accuracy'].std():.3f})"
            )
        if "rhythm_accuracy" in subset.columns:
            lines.append(
                f"Rhythm Accuracy:   {subset['rhythm_accuracy'].mean():.3f} (±{subset['rhythm_accuracy'].std():.3f})"
            )
        if "transcription_time_ms" in subset.columns:
            lines.append(
                f"Average time:      {subset['transcription_time_ms'].mean():.0f} ms"
            )
        lines.append("")

    # Comparison by scenario
    lines.append("=" * 80)
    lines.append("COMPARISON BY SCENARIO")
    lines.append("=" * 80)
    lines.append("")

    for audio_type in sorted(df["audio_type"].unique()):
        subset = df[df["audio_type"] == audio_type]
        lines.append(f"{'─'*80}")
        lines.append(f"{audio_type.upper()}")
        lines.append(f"{'─'*80}")

        # For each system in this scenario
        for amt_system in sorted(subset["amt_system"].unique()):
            sys_subset = subset[subset["amt_system"] == amt_system]

            lines.append(f"\n  {amt_system}:")
            lines.append(f"    n = {len(sys_subset)}")
            if "note_f1" in sys_subset.columns:
                lines.append(f"    Note F1: {sys_subset['note_f1'].mean():.3f}")
            if "interval_accuracy" in sys_subset.columns:
                lines.append(
                    f"    Interval Acc: {sys_subset['interval_accuracy'].mean():.3f}"
                )

        lines.append("")

    # Comparison by ground-truth type (if present)
    if "ground_truth_type" in df.columns:
        lines.append("=" * 80)
        lines.append("COMPARISON BY GROUND-TRUTH TYPE")
        lines.append("=" * 80)
        lines.append("")
        lines.append("piano_midi:      Human performance (includes folk variability)")
        lines.append("original_score:  Quantized score (fixed reference)")
        lines.append("")

        for gt_type in sorted(df["ground_truth_type"].dropna().unique()):
            subset = df[df["ground_truth_type"] == gt_type]
            lines.append(f"{'─'*80}")
            lines.append(f"{gt_type.upper()}")
            lines.append(f"{'─'*80}")

            # For each system
            for amt_system in sorted(subset["amt_system"].unique()):
                sys_subset = subset[subset["amt_system"] == amt_system]

                lines.append(f"\n  {amt_system}:")
                lines.append(f"    n = {len(sys_subset)}")
                if "note_f1" in sys_subset.columns:
                    lines.append(
                        f"    Note F1: {sys_subset['note_f1'].mean():.3f} (±{sys_subset['note_f1'].std():.3f})"
                    )
                if "interval_accuracy" in sys_subset.columns:
                    lines.append(
                        f"    Interval Acc: {sys_subset['interval_accuracy'].mean():.3f} (±{sys_subset['interval_accuracy'].std():.3f})"
                    )
                if "rhythm_accuracy" in sys_subset.columns:
                    lines.append(
                        f"    Rhythm Acc: {sys_subset['rhythm_accuracy'].mean():.3f} (±{sys_subset['rhythm_accuracy'].std():.3f})"
                    )

            lines.append("")

    # Summary table
    lines.append("=" * 80)
    lines.append("SUMMARY TABLE")
    lines.append("=" * 80)
    lines.append("")

    header = f"{'System':<15} {'Scenario':<25} {'n':<6} {'F1':<8} {'Interval':<10} {'Time(ms)':<12}"
    lines.append(header)
    lines.append("─" * 80)

    for amt_system in sorted(df["amt_system"].unique()):
        for audio_type in sorted(df["audio_type"].unique()):
            subset = df[
                (df["amt_system"] == amt_system) & (df["audio_type"] == audio_type)
            ]

            if len(subset) > 0:
                n = len(subset)
                f1 = subset["note_f1"].mean() if "note_f1" in subset.columns else 0
                interval = (
                    subset["interval_accuracy"].mean()
                    if "interval_accuracy" in subset.columns
                    else 0
                )
                time = (
                    subset["transcription_time_ms"].mean()
                    if "transcription_time_ms" in subset.columns
                    else 0
                )

                # Truncate long names
                sys_short = amt_system[:13]
                type_short = audio_type[:23]

                row = f"{sys_short:<15} {type_short:<25} {n:<6} {f1:<8.3f} {interval:<10.3f} {time:<12.0f}"
                lines.append(row)

    lines.append("")
    lines.append("=" * 80)
    lines.append("RECOMMENDATIONS")
    lines.append("=" * 80)
    lines.append("")

    # Best system by metric
    lines.append("BEST SYSTEM BY METRIC:")
    lines.append("")

    if "interval_accuracy" in df.columns:
        best_interval = df.groupby("amt_system")["interval_accuracy"].mean().idxmax()
        best_interval_score = df.groupby("amt_system")["interval_accuracy"].mean().max()
        lines.append(
            f"  Interval Accuracy: {best_interval} ({best_interval_score:.3f})"
        )

    if "note_f1" in df.columns:
        best_f1 = df.groupby("amt_system")["note_f1"].mean().idxmax()
        best_f1_score = df.groupby("amt_system")["note_f1"].mean().max()
        lines.append(f"  Note F1:           {best_f1} ({best_f1_score:.3f})")

    if "transcription_time_ms" in df.columns:
        fastest = df.groupby("amt_system")["transcription_time_ms"].mean().idxmin()
        fastest_time = df.groupby("amt_system")["transcription_time_ms"].mean().min()
        lines.append(f"  Fastest:           {fastest} ({fastest_time:.0f} ms)")

    lines.append("")
    lines.append("FOR N-GRAM SEARCH:")
    lines.append("   Prioritize Interval Accuracy over Note F1")
    lines.append("")

    report = "\n".join(lines)

    # Save report
    with open(output_txt, "w") as f:
        f.write(report)

    print(f"Comparative report saved to: {output_txt}")

    # Also print to console
    print("\n" + report)


def main():
    parser = argparse.ArgumentParser(
        description="Run a complete AMT evaluation for all systems",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
    Examples:

    # Full evaluation (4 systems x 3 scenarios)
python run_full_evaluation.py

    # Synthesized only for all systems
python run_full_evaluation.py --modes synthesized

    # Quick test (10 files per scenario)
python run_full_evaluation.py --limit 10

    # Only basic-pitch and crepe-notes
python run_full_evaluation.py --systems basic-pitch crepe-notes
        """,
    )

    parser.add_argument(
        "--systems",
        nargs="+",
        default=["basic-pitch", "crepe-notes", "pyin", "swiftf0"],
        choices=["basic-pitch", "crepe-notes", "pyin", "swiftf0"],
        help="AMT systems to evaluate (default: all)",
    )

    parser.add_argument(
        "--modes",
        nargs="+",
        default=["synthesized", "piano_wav", "instruments"],
        choices=["synthesized", "piano_wav", "instruments"],
        help="Scenarios to evaluate (default: all)",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit files per scenario (useful for testing)",
    )

    parser.add_argument(
        "--output-dir",
        default="./results",
        help="Output directory (default: ./results)",
    )

    args = parser.parse_args()

    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print("=" * 80)
    print("FULL AMT EVALUATION")
    print("=" * 80)
    print(f"Systems: {', '.join(args.systems)}")
    print(f"Scenarios: {', '.join(args.modes)}")
    if args.limit:
        print(f"Per-scenario limit: {args.limit} files")
    print("=" * 80)

    csv_files = []
    failed_combinations = []
    total_combinations = len(args.systems) * len(args.modes)
    current = 0

    # Run all combinations
    for amt_system in args.systems:
        for mode in args.modes:
            current += 1
            print(f"\n[{current}/{total_combinations}] Processing...")

            output_csv = os.path.join(
                args.output_dir, f"{mode}_{amt_system}_{timestamp}.csv"
            )

            success = run_evaluation(mode, amt_system, output_csv, args.limit)

            if not success:
                failed_combinations.append(
                    (amt_system, mode, "evaluation command failed")
                )
                continue

            csv_ok, reason = validate_csv_output(output_csv)
            if csv_ok:
                csv_files.append(output_csv)
            else:
                failed_combinations.append((amt_system, mode, reason))

    if failed_combinations:
        print("\n" + "=" * 80)
        print("FAILED COMBINATIONS")
        print("=" * 80)
        for amt_system, mode, reason in failed_combinations:
            print(f"- {amt_system} / {mode}: {reason}")
        print("\nContinuing with valid combinations only.")

    if not csv_files:
        print("\nNo valid result files were produced by any combination.")
        print("Fix the reported issues and rerun.")
        sys.exit(2)

    # Consolidate results
    print("\n" + "=" * 80)
    print("CONSOLIDATING RESULTS")
    print("=" * 80)

    consolidated_csv = os.path.join(
        args.output_dir, f"evaluation_complete_{timestamp}.csv"
    )

    if consolidate_results(csv_files, consolidated_csv):
        # Generate comparative report
        report_txt = os.path.join(args.output_dir, f"comparison_report_{timestamp}.txt")

        generate_comparison_report(consolidated_csv, report_txt)

        # Generate comparative Excel
        print("\n" + "=" * 80)
        print("GENERATING COMPARATIVE EXCEL")
        print("=" * 80)

        excel_report = os.path.join(args.output_dir, f"amt_comparison_{timestamp}.xlsx")

        try:
            subprocess.run(
                [
                    sys.executable,
                    "generate_comparison_excel.py",
                    "--input",
                    consolidated_csv,
                    "--output",
                    excel_report,
                ],
                check=True,
            )
            print(f"Excel generated: {excel_report}")
        except subprocess.CalledProcessError as e:
            print(f"Could not generate Excel (openpyxl required): {e}")
            print("   Install with: pip install openpyxl")
        except Exception as e:
            print(f"Error generating Excel: {e}")

        print("\n" + "=" * 80)
        print("FULL EVALUATION FINISHED")
        print("=" * 80)
        print(f"Consolidated CSV: {consolidated_csv}")
        print(f"TXT report:      {report_txt}")
        if os.path.exists(excel_report):
            print(f"Comparative Excel: {excel_report}")
        print("")
        print("To inspect the report:")
        print(f"   cat {report_txt}")
        print(f"   less {report_txt}")
        if os.path.exists(excel_report):
            print(f"\nTo open the Excel file:")
            print(f"   libreoffice {excel_report}")
    else:
        print("\nError while consolidating results")
        sys.exit(1)


if __name__ == "__main__":
    main()
