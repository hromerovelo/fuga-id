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
MIDI Comparison Module
"""

"""
Compares MIDI transcriptions against ground truth using mir_eval metrics
(standard for MIREX Music Information Retrieval competitions).

Provides note-level and frame-level evaluation metrics:
- Note-level: precision, recall, F1 (with onset tolerance)
- Frame-level: pitch accuracy, chroma accuracy, voicing metrics

Usage:
    from midi_comparison import compare_midi_with_mir_eval
    
    metrics = compare_midi_with_mir_eval('ground_truth.mid', 'transcription.mid')
    print(f"Note F1: {metrics['note_f1']:.3f}")
"""

import numpy as np
import pretty_midi
import warnings

warnings.filterwarnings("ignore")

try:
    import mir_eval
except ImportError:
    print("Error: mir_eval not installed. Install with: pip install mir_eval")
    raise


def midi_to_note_data(midi_path):
    """
    Extract note data from MIDI file.

    Args:
        midi_path: Path to MIDI file

    Returns:
        tuple: (intervals, pitches) where
            intervals: Nx2 array of [onset, offset] times
            pitches: N array of MIDI note numbers
    """
    try:
        midi_data = pretty_midi.PrettyMIDI(midi_path)
    except Exception as e:
        print(f"Error loading MIDI file {midi_path}: {e}")
        return np.array([]).reshape(0, 2), np.array([])

    # Combine all instruments
    notes = []
    for instrument in midi_data.instruments:
        if not instrument.is_drum:
            notes.extend(instrument.notes)

    if not notes:
        return np.array([]).reshape(0, 2), np.array([])

    # Sort by onset time
    notes.sort(key=lambda x: x.start)

    # Extract intervals and pitches
    intervals = np.array([[note.start, note.end] for note in notes])
    pitches = np.array([note.pitch for note in notes])

    return intervals, pitches


def midi_to_melody_contour(midi_path, frame_rate=100):
    """
    Extract melody contour from MIDI file for frame-level evaluation.

    Args:
        midi_path: Path to MIDI file
        frame_rate: Frames per second (default: 100Hz = 10ms frames)

    Returns:
        tuple: (times, frequencies) where
            times: Time stamps array
            frequencies: F0 values in Hz (or 0 for unvoiced)
    """
    try:
        midi_data = pretty_midi.PrettyMIDI(midi_path)
    except Exception as e:
        print(f"Error loading MIDI file {midi_path}: {e}")
        return np.array([]), np.array([])

    # Get total duration
    if not midi_data.instruments:
        return np.array([]), np.array([])

    duration = midi_data.get_end_time()
    if duration == 0:
        return np.array([]), np.array([])

    # Generate time grid
    hop_length = 1.0 / frame_rate  # seconds per frame
    times = np.arange(0, duration, hop_length)
    frequencies = np.zeros(len(times))

    # For each frame, find the highest pitch note that is active
    for instrument in midi_data.instruments:
        if instrument.is_drum:
            continue

        for note in instrument.notes:
            # Find frames where this note is active
            start_frame = int(note.start * frame_rate)
            end_frame = int(note.end * frame_rate)

            # Convert MIDI note to frequency
            freq = pretty_midi.note_number_to_hz(note.pitch)

            # Take highest frequency in case of overlapping notes
            for i in range(start_frame, min(end_frame, len(frequencies))):
                frequencies[i] = max(frequencies[i], freq)

    return times, frequencies


def compare_midi_with_mir_eval(
    ground_truth_path,
    transcription_path,
    onset_tolerance=0.05,
    offset_ratio=0.2,
    pitch_tolerance=50.0,
    frame_rate=100,
):
    """
    Compare two MIDI files using mir_eval metrics.

    Args:
        ground_truth_path: Path to ground truth MIDI
        transcription_path: Path to transcribed MIDI
        onset_tolerance: Onset tolerance in seconds (default: 50ms)
        offset_ratio: Offset tolerance as ratio of note duration (default: 0.2)
        pitch_tolerance: Pitch tolerance in cents (default: 50 cents)
        frame_rate: Frames per second for melody evaluation (default: 100Hz)

    Returns:
        dict: Dictionary with all mir_eval metrics
    """
    metrics = {}

    # ========== Note-level evaluation ==========
    try:
        ref_intervals, ref_pitches = midi_to_note_data(ground_truth_path)
        est_intervals, est_pitches = midi_to_note_data(transcription_path)

        if len(ref_intervals) == 0 or len(est_intervals) == 0:
            print(
                f"Warning: Empty note data (ref: {len(ref_intervals)}, est: {len(est_intervals)})"
            )
            metrics["note_precision"] = 0.0
            metrics["note_recall"] = 0.0
            metrics["note_f1"] = 0.0
        else:
            # mir_eval transcription metrics
            precision, recall, f1, _ = (
                mir_eval.transcription.precision_recall_f1_overlap(
                    ref_intervals,
                    ref_pitches,
                    est_intervals,
                    est_pitches,
                    offset_ratio=offset_ratio,
                    onset_tolerance=onset_tolerance,
                )
            )

            metrics["note_precision"] = float(precision)
            metrics["note_recall"] = float(recall)
            metrics["note_f1"] = float(f1)

    except Exception as e:
        print(f"Error in note-level evaluation: {e}")
        metrics["note_precision"] = None
        metrics["note_recall"] = None
        metrics["note_f1"] = None

    # ========== Frame-level melody evaluation ==========
    try:
        ref_times, ref_frequencies = midi_to_melody_contour(
            ground_truth_path, frame_rate
        )
        est_times, est_frequencies = midi_to_melody_contour(
            transcription_path, frame_rate
        )

        if len(ref_frequencies) == 0 or len(est_frequencies) == 0:
            print(
                f"Warning: Empty melody contour (ref: {len(ref_frequencies)}, est: {len(est_frequencies)})"
            )
            metrics["voicing_recall"] = 0.0
            metrics["voicing_false_alarm"] = 0.0
            metrics["raw_pitch_accuracy"] = 0.0
            metrics["raw_chroma_accuracy"] = 0.0
            metrics["overall_accuracy"] = 0.0
        else:
            # Align time grids (use shorter duration)
            min_length = min(len(ref_frequencies), len(est_frequencies))
            ref_freq_aligned = ref_frequencies[:min_length]
            est_freq_aligned = est_frequencies[:min_length]

            # Convert to mir_eval format (0 = unvoiced, >0 = frequency)
            ref_voicing = ref_freq_aligned > 0
            est_voicing = est_freq_aligned > 0

            # Voicing metrics
            voicing_recall, voicing_false_alarm = mir_eval.melody.voicing_measures(
                ref_voicing, est_voicing
            )

            metrics["voicing_recall"] = float(voicing_recall)
            metrics["voicing_false_alarm"] = float(voicing_false_alarm)

            # Pitch accuracy metrics
            raw_pitch_accuracy = mir_eval.melody.raw_pitch_accuracy(
                ref_voicing,
                ref_freq_aligned,
                est_voicing,
                est_freq_aligned,
                cent_tolerance=pitch_tolerance,
            )

            raw_chroma_accuracy = mir_eval.melody.raw_chroma_accuracy(
                ref_voicing,
                ref_freq_aligned,
                est_voicing,
                est_freq_aligned,
                cent_tolerance=pitch_tolerance,
            )

            overall_accuracy = mir_eval.melody.overall_accuracy(
                ref_voicing,
                ref_freq_aligned,
                est_voicing,
                est_freq_aligned,
                cent_tolerance=pitch_tolerance,
            )

            metrics["raw_pitch_accuracy"] = float(raw_pitch_accuracy)
            metrics["raw_chroma_accuracy"] = float(raw_chroma_accuracy)
            metrics["overall_accuracy"] = float(overall_accuracy)

    except Exception as e:
        print(f"Error in frame-level evaluation: {e}")
        metrics["voicing_recall"] = None
        metrics["voicing_false_alarm"] = None
        metrics["raw_pitch_accuracy"] = None
        metrics["raw_chroma_accuracy"] = None
        metrics["overall_accuracy"] = None

    return metrics


def print_metrics(metrics):
    """
    Pretty print metrics dictionary.

    Args:
        metrics: Dictionary of metrics returned by compare_midi_with_mir_eval
    """
    print("\n" + "=" * 50)
    print("MIDI Transcription Evaluation (mir_eval)")
    print("=" * 50)

    print("\n--- Note-level Metrics ---")
    print(f"  Note Precision:  {metrics.get('note_precision', 0.0)*100:.2f}%")
    print(f"  Note Recall:     {metrics.get('note_recall', 0.0)*100:.2f}%")
    print(f"  Note F1 Score:   {metrics.get('note_f1', 0.0)*100:.2f}%")

    print("\n--- Frame-level Melody Metrics ---")
    print(f"  Voicing Recall:         {metrics.get('voicing_recall', 0.0)*100:.2f}%")
    print(
        f"  Voicing False Alarm:    {metrics.get('voicing_false_alarm', 0.0)*100:.2f}%"
    )
    print(
        f"  Raw Pitch Accuracy:     {metrics.get('raw_pitch_accuracy', 0.0)*100:.2f}%"
    )
    print(
        f"  Raw Chroma Accuracy:    {metrics.get('raw_chroma_accuracy', 0.0)*100:.2f}%"
    )
    print(f"  Overall Accuracy:       {metrics.get('overall_accuracy', 0.0)*100:.2f}%")
    print("=" * 50 + "\n")


def main():
    """Command-line interface for MIDI comparison."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Compare MIDI transcriptions using mir_eval metrics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("ground_truth", help="Ground truth MIDI file")
    parser.add_argument("transcription", help="Transcribed MIDI file")
    parser.add_argument(
        "--onset-tolerance",
        type=float,
        default=0.05,
        help="Onset tolerance in seconds (default: 0.05)",
    )
    parser.add_argument(
        "--offset-ratio",
        type=float,
        default=0.2,
        help="Offset tolerance ratio (default: 0.2)",
    )
    parser.add_argument(
        "--pitch-tolerance",
        type=float,
        default=50.0,
        help="Pitch tolerance in cents (default: 50)",
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    metrics = compare_midi_with_mir_eval(
        args.ground_truth,
        args.transcription,
        onset_tolerance=args.onset_tolerance,
        offset_ratio=args.offset_ratio,
        pitch_tolerance=args.pitch_tolerance,
    )

    if args.json:
        import json

        print(json.dumps(metrics, indent=2))
    else:
        print_metrics(metrics)


if __name__ == "__main__":
    main()
