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
    Melody interval and rhythm pattern extraction from MIDI.
"""

import pretty_midi
from typing import Tuple, List


def midi_to_note_sequence(midi_path: str) -> Tuple[List[int], List[float], List[float]]:
    """
    Extract a note sequence from a MIDI file.

    Returns:
        tuple: (pitches, start_times, durations)
    """
    try:
        midi_data = pretty_midi.PrettyMIDI(midi_path)
    except Exception as e:
        raise ValueError(f"Error loading MIDI {midi_path}: {e}")

    # Combine notes across all non-drum instruments
    notes = []
    for instrument in midi_data.instruments:
        if not instrument.is_drum:
            notes.extend(instrument.notes)

    if not notes:
        return [], [], []

    # Sort by onset time
    notes.sort(key=lambda x: x.start)

    pitches = [n.pitch for n in notes]
    start_times = [n.start for n in notes]
    durations = [n.end - n.start for n in notes]

    return pitches, start_times, durations


def pitches_to_intervals(pitches: List[int]) -> List[int]:
    """
    Convert pitch sequence to chromatic melodic intervals.

    Args:
        pitches: List of MIDI note numbers.

    Returns:
        List of semitone intervals.
    """
    if len(pitches) < 2:
        return []

    return [pitches[i] - pitches[i - 1] for i in range(1, len(pitches))]


def compute_duration_ratios(durations: List[float]) -> List[int]:
    """
    Convert absolute durations to quantized ratio categories.

    Returns:
        Category list: -1 (shorter), 0 (similar), 1 (longer).
    """
    if len(durations) < 2:
        return []

    ratios = []
    for i in range(len(durations) - 1):
        if durations[i] > 0:
            ratio = durations[i + 1] / durations[i]
            if ratio < 0.7:
                ratios.append(-1)
            elif ratio < 1.3:
                ratios.append(0)
            else:
                ratios.append(1)
        else:
            ratios.append(0)

    return ratios


def compute_ioi_ratios(start_times: List[float]) -> List[int]:
    """
    Compute inter-onset-interval (IOI) ratio categories.

    Returns:
        List of IOI ratio categories.
    """
    if len(start_times) < 3:
        return []

    iois = [start_times[i] - start_times[i - 1] for i in range(1, len(start_times))]

    ratios = []
    for i in range(len(iois) - 1):
        if iois[i] > 0:
            ratio = iois[i + 1] / iois[i]
            if ratio < 0.7:
                ratios.append(-1)
            elif ratio < 1.3:
                ratios.append(0)
            else:
                ratios.append(1)
        else:
            ratios.append(0)

    return ratios
