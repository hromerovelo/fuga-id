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
    Unified metrics for AMT evaluation.
"""

import sys
import os
from difflib import SequenceMatcher
from typing import Dict, Optional

# Add parent directories
sys.path.append(os.path.join(os.path.dirname(__file__), "../common"))
sys.path.append(os.path.join(os.path.dirname(__file__), "core"))

from midi_comparison import compare_midi_with_mir_eval
from interval_extraction import (
    midi_to_note_sequence,
    pitches_to_intervals,
    compute_duration_ratios,
)


def compute_note_metrics(
    ground_truth_midi: str,
    transcribed_midi: str,
    onset_tolerance: float = 0.05,
    pitch_tolerance: float = 50.0,
) -> Optional[Dict]:
    """
    Compute note-level metrics using mir_eval.

    Args:
        ground_truth_midi: Path to ground-truth MIDI.
        transcribed_midi: Path to transcribed MIDI.
        onset_tolerance: Onset tolerance in seconds (default: 50 ms).
        pitch_tolerance: Pitch tolerance in cents (default: 50 cents).

    Returns:
        Dictionary with metrics or None on failure.
    """
    try:
        metrics = compare_midi_with_mir_eval(
            ground_truth_midi,
            transcribed_midi,
            onset_tolerance=onset_tolerance,
            pitch_tolerance=pitch_tolerance,
        )
        return metrics
    except Exception as e:
        print(f"Error computing note metrics: {e}")
        return None


def sequence_similarity(seq1: list, seq2: list) -> float:
    """Compute sequence similarity in the [0, 1] range."""
    if not seq1 or not seq2:
        return 0.0

    str1 = ",".join(map(str, seq1))
    str2 = ",".join(map(str, seq2))

    return SequenceMatcher(None, str1, str2).ratio()


def edit_distance(seq1: list, seq2: list) -> int:
    """Compute Levenshtein edit distance between two sequences."""
    if not seq1:
        return len(seq2)
    if not seq2:
        return len(seq1)

    m, n = len(seq1), len(seq2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if seq1[i - 1] == seq2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])

    return dp[m][n]


def compute_interval_metrics(
    ground_truth_midi: str, transcribed_midi: str
) -> Optional[Dict]:
    """
    Compute interval-based melodic and rhythmic metrics.

    These metrics are invariant to key and octave shifts, and focus on
    relative melodic/rhythmic patterns.

    Returns:
        Dictionary with metrics or None on failure.
    """
    try:
        # Extract note sequences
        gt_pitches, _, gt_durs = midi_to_note_sequence(ground_truth_midi)
        tr_pitches, _, tr_durs = midi_to_note_sequence(transcribed_midi)

        if not gt_pitches or not tr_pitches:
            return None

        # Melodic intervals
        gt_intervals = pitches_to_intervals(gt_pitches)
        tr_intervals = pitches_to_intervals(tr_pitches)

        interval_similarity = sequence_similarity(gt_intervals, tr_intervals)
        interval_edit_dist = edit_distance(gt_intervals, tr_intervals)
        max_len = max(len(gt_intervals), len(tr_intervals))
        interval_accuracy = 1 - (interval_edit_dist / max_len) if max_len > 0 else 0

        # Rhythmic ratios
        gt_ratios = compute_duration_ratios(gt_durs)
        tr_ratios = compute_duration_ratios(tr_durs)

        rhythm_similarity = sequence_similarity(gt_ratios, tr_ratios)
        rhythm_edit_dist = edit_distance(gt_ratios, tr_ratios)
        max_rhythm_len = max(len(gt_ratios), len(tr_ratios))
        rhythm_accuracy = (
            1 - (rhythm_edit_dist / max_rhythm_len) if max_rhythm_len > 0 else 0
        )

        # Sequence-length ratio
        length_ratio = (
            len(tr_intervals) / len(gt_intervals) if len(gt_intervals) > 0 else 0
        )

        return {
            "interval_similarity": interval_similarity,
            "interval_accuracy": interval_accuracy,
            "interval_edit_distance": interval_edit_dist,
            "rhythm_similarity": rhythm_similarity,
            "rhythm_accuracy": rhythm_accuracy,
            "rhythm_edit_distance": rhythm_edit_dist,
            "length_ratio": length_ratio,
            "gt_note_count": len(gt_pitches),
            "transcribed_note_count": len(tr_pitches),
        }

    except Exception as e:
        print(f"Error computing interval metrics: {e}")
        return None


def compute_all_metrics(
    ground_truth_midi: str,
    transcribed_midi: str,
    onset_tolerance: float = 0.05,
    pitch_tolerance: float = 50.0,
) -> Dict:
    """
    Compute all available metrics (note-level + interval-level).

    Returns:
        Combined metrics dictionary.
    """
    all_metrics = {}

    # Note-level metrics
    note_metrics = compute_note_metrics(
        ground_truth_midi, transcribed_midi, onset_tolerance, pitch_tolerance
    )

    if note_metrics:
        all_metrics.update(note_metrics)

    # Interval-level metrics
    interval_metrics = compute_interval_metrics(ground_truth_midi, transcribed_midi)

    if interval_metrics:
        all_metrics.update(interval_metrics)

    return all_metrics
