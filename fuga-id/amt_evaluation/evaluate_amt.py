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
    Main AMT evaluation runner.

    Evaluates AMT systems in three scenarios:
    1. Synthesized MIDI baseline
    2. Piano WAV audio
    3. Real instrument recordings

    Produces note-level, interval-level, and rhythm-level metrics.
"""

import argparse
import os
import sys
from pathlib import Path
from tqdm import tqdm
import pandas as pd

# Add paths
script_dir = os.path.dirname(os.path.abspath(__file__))  # amt_evaluation/
fugaid_dir = os.path.dirname(script_dir)  # fuga-id/
queries_dir = os.path.join(fugaid_dir, "queries")  # queries/

sys.path.insert(0, fugaid_dir)
sys.path.insert(0, queries_dir)
sys.path.insert(0, os.path.join(queries_dir, "utils"))

from core.audio_synthesis import synthesize_midi_to_wav
from core.file_mapping import (
    find_wav_midi_pairs,
    map_instrument_wavs_to_piano_midis,
    map_instrument_wavs_to_original_scores,
)
from metrics import compute_all_metrics

sys.path.insert(0, os.path.join(queries_dir, "utils"))
from amt_wrapper import transcribe


def evaluate_synthesized_piano(
    midi_dir: str, amt_system: str, limit: int = None
) -> pd.DataFrame:
    """
    Evaluate synthesized MIDI baseline.

    Workflow: MIDI -> FluidSynth -> WAV -> AMT -> compare with original MIDI.
    """
    print("\n" + "=" * 80)
    print("AMT EVALUATION 1: SYNTHESIZED PIANO (Baseline)")
    print("=" * 80)
    print(f"AMT system: {amt_system.upper()}")
    print(f"Directory: {midi_dir}")

    # Find MIDI files
    midi_files = list(Path(midi_dir).glob("*_mid.mid"))

    if limit:
        midi_files = midi_files[:limit]

    print(f"Files to process: {len(midi_files)}")

    results = []

    for midi_file in tqdm(midi_files, desc="Processing"):
        recording_id = midi_file.stem.replace("_mid", "")

        try:
            # Synthesize audio
            wav_file = synthesize_midi_to_wav(str(midi_file))

            # Transcribe
            transcribed_midi = f"/tmp/{recording_id}_{amt_system}_transcription.mid"
            result = transcribe(wav_file, transcribed_midi, method=amt_system)

            # Clean temporary WAV
            os.remove(wav_file)

            if not result or not result.get("success"):
                continue

            # Compute metrics
            metrics = compute_all_metrics(str(midi_file), transcribed_midi)
            metrics["recording_id"] = recording_id
            metrics["amt_system"] = amt_system
            metrics["audio_type"] = "synthesized_piano"
            metrics["transcription_time_ms"] = result.get("transcription_time_ms", 0)

            results.append(metrics)

            # Clean transcribed MIDI
            os.remove(transcribed_midi)

        except Exception as e:
            print(f"\nError in {recording_id}: {e}")
            continue

    return pd.DataFrame(results)


def evaluate_real_piano_wav(
    piano_dir: str, amt_system: str, limit: int = None
) -> pd.DataFrame:
    """
    Evaluate "real" piano WAV files.

    Workflow: piano WAV -> AMT -> compare with corresponding MIDI.
    """
    print("\n" + "=" * 80)
    print("AMT EVALUATION 2: PIANO WAV (Real Audio)")
    print("=" * 80)
    print(f"AMT system: {amt_system.upper()}")
    print(f"Directory: {piano_dir}")

    # Find MIDI/WAV pairs
    pairs = find_wav_midi_pairs(piano_dir)

    if limit:
        pairs = pairs[:limit]

    print(f"MIDI/WAV pairs found: {len(pairs)}")

    results = []

    for midi_path, wav_path, recording_id in tqdm(pairs, desc="Processing"):
        try:
            # Transcribe WAV
            transcribed_midi = f"/tmp/{recording_id}_{amt_system}_transcription.mid"
            result = transcribe(wav_path, transcribed_midi, method=amt_system)

            if not result or not result.get("success"):
                continue

            # Compute metrics
            metrics = compute_all_metrics(midi_path, transcribed_midi)
            metrics["recording_id"] = recording_id
            metrics["amt_system"] = amt_system
            metrics["audio_type"] = "real_piano_wav"
            metrics["transcription_time_ms"] = result.get("transcription_time_ms", 0)

            results.append(metrics)

            os.remove(transcribed_midi)

        except Exception as e:
            print(f"\nError in {recording_id}: {e}")
            continue

    return pd.DataFrame(results)


def evaluate_real_instruments(
    audio_dir: str,
    midi_dir: str,
    amt_system: str,
    instrument_filter: str = None,
    limit: int = None,
) -> pd.DataFrame:
    """
    Evaluate real instruments against piano MIDI.

    Workflow: instrument WAV -> AMT -> compare with piano MIDI.

    Uses relaxed tolerances due to inherent folk-performance variability.
    """
    print("\n" + "=" * 80)
    print("AMT EVALUATION 3A: INSTRUMENTS vs PIANO MIDI")
    print("=" * 80)
    print(f"AMT system: {amt_system.upper()}")
    print(f"Audio dir: {audio_dir}")
    print(f"MIDI dir (piano): {midi_dir}")
    if instrument_filter:
        print(f"Instrument filter: {instrument_filter}")

    # Map instrument WAVs to piano MIDIs
    mappings = map_instrument_wavs_to_piano_midis(
        audio_dir, midi_dir, instrument_filter
    )

    if limit:
        mappings = mappings[:limit]

    print(f"Mappings found: {len(mappings)}")

    results = []

    for wav_path, midi_path, melody_base, instrument in tqdm(
        mappings, desc="Processing"
    ):
        try:
            # Transcribe
            transcribed_midi = f"/tmp/{melody_base}_{instrument}_{amt_system}.mid"
            result = transcribe(wav_path, transcribed_midi, method=amt_system)

            if not result or not result.get("success"):
                continue

            # Metrics with relaxed tolerances
            metrics = compute_all_metrics(
                midi_path,
                transcribed_midi,
                onset_tolerance=0.1,  # ±100ms
                pitch_tolerance=100.0,  # ±100 cents
            )

            metrics["recording_id"] = melody_base
            metrics["amt_system"] = amt_system
            metrics["audio_type"] = f"real_instrument_{instrument}"
            metrics["instrument"] = instrument
            metrics["ground_truth_type"] = "piano_midi"
            metrics["transcription_time_ms"] = result.get("transcription_time_ms", 0)

            results.append(metrics)

            os.remove(transcribed_midi)

        except Exception as e:
            print(f"\nError in {melody_base}: {e}")
            continue

    return pd.DataFrame(results)


def evaluate_real_instruments_vs_original_scores(
    audio_dir: str,
    scores_midi_dir: str,
    amt_system: str,
    instrument_filter: str = None,
    limit: int = None,
) -> pd.DataFrame:
    """
    Evaluate real instruments against original score MIDI.

    Workflow: instrument WAV -> AMT -> compare with original score MIDI.
    """
    print("\n" + "=" * 80)
    print("AMT EVALUATION 3B: INSTRUMENTS vs ORIGINAL SCORE")
    print("=" * 80)
    print(f"AMT system: {amt_system.upper()}")
    print(f"Audio dir: {audio_dir}")
    print(f"Scores MIDI dir: {scores_midi_dir}")
    if instrument_filter:
        print(f"Instrument filter: {instrument_filter}")

    # Map instrument WAVs to original score MIDIs
    mappings = map_instrument_wavs_to_original_scores(
        audio_dir, scores_midi_dir, instrument_filter
    )

    if limit:
        mappings = mappings[:limit]

    print(f"Mappings found: {len(mappings)}")

    results = []

    for wav_path, midi_path, melody_base, instrument in tqdm(
        mappings, desc="Processing"
    ):
        try:
            # Transcribe
            transcribed_midi = (
                f"/tmp/{melody_base}_{instrument}_{amt_system}_vs_score.mid"
            )
            result = transcribe(wav_path, transcribed_midi, method=amt_system)

            if not result or not result.get("success"):
                continue

            # Metrics with relaxed tolerances
            metrics = compute_all_metrics(
                midi_path,
                transcribed_midi,
                onset_tolerance=0.1,  # ±100ms
                pitch_tolerance=100.0,  # ±100 cents
            )

            metrics["recording_id"] = melody_base
            metrics["amt_system"] = amt_system
            metrics["audio_type"] = f"real_instrument_{instrument}"
            metrics["instrument"] = instrument
            metrics["ground_truth_type"] = "original_score"
            metrics["transcription_time_ms"] = result.get("transcription_time_ms", 0)

            results.append(metrics)

            os.remove(transcribed_midi)

        except Exception as e:
            print(f"\nError in {melody_base}: {e}")
            continue

    return pd.DataFrame(results)


def main():
    parser = argparse.ArgumentParser(
        description="Unified AMT systems evaluation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples (run from amt_evaluation/):

# Evaluate all 3 scenarios with basic-pitch (10 files each)
python3 evaluate_amt.py \\
  --mode all \\
  --amt-system basic-pitch \\
  --output ./results/amt_complete_evaluation.csv \
  --limit 10

# Baseline only (synthesized MIDI)
python3 evaluate_amt.py \
  --mode synthesized \
  --amt-system basic-pitch \
  --output ./results/amt_baseline.csv

# Real instruments only (flutes)
python3 evaluate_amt.py \
  --mode instruments \
  --amt-system basic-pitch \
    --instrument-filter flute \
  --output ./results/amt_flautas.csv \\
  --limit 20
        """,
    )

    parser.add_argument(
        "--mode",
        choices=["synthesized", "piano_wav", "instruments", "all"],
        default="all",
        help="Evaluation mode",
    )

    parser.add_argument(
        "--amt-system",
        default="basic-pitch",
        choices=["basic-pitch", "swiftf0", "crepe-notes", "pyin"],
        help="AMT system to evaluate",
    )

    parser.add_argument(
        "--midi-dir",
        default="../queries/data/folkoteca_piano_recordings/",
        help="Directory with piano MIDIs (and WAVs for piano_wav mode)",
    )

    parser.add_argument(
        "--audio-dir",
        default="../queries/data/folkoteca_audios/",
        help="Directory with instrument WAV files (for instruments mode)",
    )

    parser.add_argument(
        "--scores-midi-dir",
        default="../scores/data/origin/scores_midi/",
        help="Directory with original score MIDIs (for score-based comparison)",
    )

    parser.add_argument(
        "--instrument-filter",
        default=None,
        help="Filter by instrument (flute, bagpipe, violin, etc.)",
    )

    parser.add_argument(
        "--output",
        default="./results/amt_evaluation_results.csv",
        help="Output CSV path (directory is created automatically)",
    )

    parser.add_argument(
        "--limit", type=int, default=None, help="Limit number of files per mode"
    )

    args = parser.parse_args()

    all_results = []

    # Run evaluations according to selected mode
    if args.mode in ["synthesized", "all"]:
        df = evaluate_synthesized_piano(args.midi_dir, args.amt_system, args.limit)
        all_results.append(df)

    if args.mode in ["piano_wav", "all"]:
        df = evaluate_real_piano_wav(args.midi_dir, args.amt_system, args.limit)
        all_results.append(df)

    if args.mode in ["instruments", "all"]:
        # Comparison against piano MIDI (human interpretation)
        df_piano = evaluate_real_instruments(
            args.audio_dir,
            args.midi_dir,
            args.amt_system,
            args.instrument_filter,
            args.limit,
        )
        all_results.append(df_piano)

        # Comparison against original score MIDIs
        df_scores = evaluate_real_instruments_vs_original_scores(
            args.audio_dir,
            args.scores_midi_dir,
            args.amt_system,
            args.instrument_filter,
            args.limit,
        )
        all_results.append(df_scores)

    # Combine results
    if all_results:
        final_df = pd.concat(all_results, ignore_index=True)

        # If no rows/columns were produced, avoid writing empty CSV
        if final_df.empty or len(final_df.columns) == 0:
            print("\nNo files were processed (check input paths, filters, and limits)")
            sys.exit(2)

        # Create output directory if it does not exist
        output_dir = os.path.dirname(args.output)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        final_df.to_csv(args.output, index=False)

        print("\n" + "=" * 80)
        print("EVALUATION COMPLETED")
        print("=" * 80)
        print(f"Results saved to: {args.output}")
        print(f"Total processed files: {len(final_df)}")

        # Quick summary (only if there are results)
        if len(final_df) > 0 and "audio_type" in final_df.columns:
            print("\nSummary by audio type:")
            for audio_type in final_df["audio_type"].unique():
                subset = final_df[final_df["audio_type"] == audio_type]
                print(f"\n  {audio_type}:")
                print(f"    n = {len(subset)}")
                if "note_f1" in subset.columns:
                    print(f"    Note F1: {subset['note_f1'].mean():.3f}")
                if "interval_accuracy" in subset.columns:
                    print(
                        f"    Interval Accuracy: {subset['interval_accuracy'].mean():.3f}"
                    )

            print(f"\nTo generate a full report:")
            print(f"   python generate_amt_report.py --input {args.output}")
        else:
            print("\nNo files were processed (check paths or use --limit > 0)")

    else:
        print("\nNo results were generated")


if __name__ == "__main__":
    main()
