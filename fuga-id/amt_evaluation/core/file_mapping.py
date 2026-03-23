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
    Mapping utilities across audio files, piano MIDIs, and original score MIDIs.
"""

from pathlib import Path
from typing import Optional, List, Tuple


def extract_melody_base_name(filename: str) -> str:
    """
    Extract melody base name from a file name.

    Examples:
        muineiras_muineira-de-froxan_flauta_M7.wav -> muineiras_muineira-de-froxan
        muineiras_muineira-de-froxan_piano_M7_mid.mid -> muineiras_muineira-de-froxan
    """
    stem = Path(filename).stem

    # Remove common suffixes
    stem = stem.replace("_mid", "").replace("_wav", "")

    # Known instruments
    instruments = [
        "flauta",
        "gaita",
        "violin",
        "saxo",
        "whistle",
        "clarinete",
        "trompeta",
        "voz",
        "piano",
    ]

    # Keep tokens until instrument or mode token is found
    parts = stem.split("_")
    melody_parts = []

    for part in parts:
        if (
            any(inst in part.lower() for inst in instruments)
            or part.startswith("M")
            or part.startswith("v")
        ):
            break
        melody_parts.append(part)

    return "_".join(melody_parts)


def find_midi_for_melody(melody_base: str, midi_dir: str) -> Optional[str]:
    """
    Find the piano MIDI corresponding to a melody base name.

    Args:
        melody_base: Melody base name (example: muineiras_muineira-de-froxan).
        midi_dir: Directory containing MIDI files.

    Returns:
        Path to the matched MIDI file, or None.
    """
    for midi_file in Path(midi_dir).glob("*_mid.mid"):
        if extract_melody_base_name(midi_file.name) == melody_base:
            return str(midi_file)

    return None


def find_wav_midi_pairs(
    directory: str, pattern: str = "*_mid.mid"
) -> List[Tuple[str, str, str]]:
    """
    Find MIDI/WAV pairs in a directory.

    Args:
        directory: Directory to scan.
        pattern: Glob pattern for MIDI files.

    Returns:
        List of tuples: (midi_path, wav_path, recording_id).
    """
    pairs = []

    for midi_file in Path(directory).glob(pattern):
        base_name = midi_file.stem.replace("_mid", "")
        wav_file = midi_file.parent / f"{base_name}_wav.wav"

        if wav_file.exists():
            pairs.append((str(midi_file), str(wav_file), base_name))

    return pairs


def map_instrument_wavs_to_piano_midis(
    audio_dir: str, midi_dir: str, instrument_filter: Optional[str] = None
) -> List[Tuple[str, str, str, str]]:
    """
    Map instrument WAV files to corresponding piano MIDIs.

    Returns:
        List of tuples: (wav_path, midi_path, melody_base, instrument).
    """
    mappings = []

    for wav_file in Path(audio_dir).glob("*.wav"):
        # Apply optional instrument filter
        if instrument_filter and instrument_filter.lower() not in wav_file.name.lower():
            continue

        melody_base = extract_melody_base_name(wav_file.name)
        midi_path = find_midi_for_melody(melody_base, midi_dir)

        if midi_path:
            # Extract instrument token
            parts = wav_file.stem.split("_")
            instrument = "unknown"
            instruments = [
                "flauta",
                "gaita",
                "violin",
                "saxo",
                "whistle",
                "clarinete",
                "trompeta",
                "voz",
                "piano",
            ]
            for part in parts:
                if any(inst in part.lower() for inst in instruments):
                    instrument = part
                    break

            mappings.append((str(wav_file), midi_path, melody_base, instrument))

    return mappings


def map_instrument_wavs_to_original_scores(
    audio_dir: str, scores_midi_dir: str, instrument_filter: Optional[str] = None
) -> List[Tuple[str, str, str, str]]:
    """
    Map instrument WAV files to Folkoteca original score MIDIs.

    Uses database/recordings.py for exact WAV-to-score mapping.

    Args:
        audio_dir: Directory with instrument WAVs (queries/data/folkoteca_audios/).
        scores_midi_dir: Directory with original score MIDIs.
        instrument_filter: Optional instrument filter.

    Returns:
        List of tuples: (wav_path, original_midi_path, melody_base, instrument).

    Example:
        WAV:  danzas_danza-das-patelas_flauta_M7_v1.wav
        MIDI: pezas_danzas_danza-das-patelas_danza-das-patelas-partitura.mid
    """
    mappings = []

    # Import recordings.py to get exact mapping records
    try:
        import sys
        import re

        database_path = Path(__file__).parent.parent.parent / "database"
        if str(database_path) not in sys.path:
            sys.path.insert(0, str(database_path))
        import recordings
    except ImportError as e:
        print(f"Warning: could not import database/recordings.py: {e}")
        return []

    # Build mapping: recording_id -> (base_score_name, instrument)
    wav_to_score_map = {}
    for record in recordings.recording_insert_statements:
        if len(record) >= 5:
            recording_id = record[0]  # example: danzas_danza-das-patelas_flauta_M7_v1
            instrument = record[2]
            format_type = record[3]
            melodic_line_id = record[4]

            # Keep only instrument WAV recordings (exclude piano)
            if format_type == "WAV" and instrument != "Piano":
                # Remove _X_e_Y suffix from melodic_line_id to get base score name
                base_score_name = re.sub(r"_\d+_e_\d+$", "", melodic_line_id)
                wav_to_score_map[recording_id] = (base_score_name, instrument)

    # Match WAV files with score MIDI files
    for wav_file in Path(audio_dir).glob("*.wav"):
        recording_id = wav_file.stem

        # Apply optional instrument filter
        if instrument_filter and instrument_filter.lower() not in recording_id.lower():
            continue

        # Look up in precomputed mapping
        if recording_id in wav_to_score_map:
            base_score_name, instrument = wav_to_score_map[recording_id]

            # Try direct MIDI candidates first
            midi_candidates = [
                Path(scores_midi_dir) / f"{base_score_name}.mid",
                Path(scores_midi_dir) / f"{base_score_name}.midi",
            ]

            midi_path = None
            for candidate in midi_candidates:
                if candidate.exists():
                    midi_path = candidate
                    break

            # Fallback to glob search
            if not midi_path:
                matches = list(Path(scores_midi_dir).glob(f"{base_score_name}*"))
                if matches:
                    midi_path = matches[0]

            if midi_path and midi_path.exists():
                # Extract melody base name
                melody_base = extract_melody_base_name(wav_file.name)
                mappings.append(
                    (str(wav_file), str(midi_path), melody_base, instrument)
                )

    return mappings
