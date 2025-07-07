"""
BSD 2-Clause License

Copyright (c) 2024, Hilda Romero-Velo
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
  Created by Hilda Romero-Velo on November 2024.
"""

"""
Script: extract_audio_fragment.py
Purpose: Extract a specific fragment from an audio or MIDI file provided a starting and an ending 
    timestamp.

Usage:
    python3 extract_audio_fragment.py <file> -s <start_time> -e <end_time> [-f <folder>]

Arguments:
    <file>: Mandatory. Path to the original audio or MIDI file.
    -s, --start: Mandatory. Start time of the fragment in milliseconds (e.g., 1000 for 1 second).
    -e, --end: Mandatory. End time of the fragment in milliseconds.
    -f, --folder: Optional. Folder to save the extracted fragment. Defaults to the current folder.

Output:
    The script saves the audio or MIDI fragment as a new file named:
    <original_file_name>_<start_time>_<end_time>.<extension>
    Example: input_1000_5000.wav
             input_1000_5000.mid
"""

import argparse
import mido
import os
from pydub import AudioSegment


def prepare_output_path(input_file, start_time, end_time, output_folder):
    """
    Prepare output path and create folders.

    Args:
        input_file (str): Path to the original audio or MIDI file.
        start_time (int): Start time of the fragment in milliseconds.
        end_time (int): End time of the fragment in milliseconds.
        output_folder (str): Folder to save the extracted fragment.

    Returns:
        str: Path to save the extracted fragment.
    """
    base_name = os.path.basename(input_file)
    file_name, file_extension = os.path.splitext(base_name)
    output_file = os.path.join(
        output_folder, f"{file_name}_{start_time}_{end_time}{file_extension}"
    )
    os.makedirs(output_folder, exist_ok=True)
    return output_file


def extract_midi_fragment(input_midi, start_time, end_time, output_file):
    """
    Extract a fragment from a MIDI file.

    Args:
        input_midi (str): Path to the original MIDI file.
        start_time (int): Start time of the fragment in milliseconds.
        end_time (int): End time of the fragment in milliseconds.
        output_file (str): Path to save the extracted fragment.
    """
    midi_file = mido.MidiFile(input_midi)
    output_midi = mido.MidiFile()
    output_midi.ticks_per_beat = midi_file.ticks_per_beat

    # Convert milliseconds to ticks
    tempo = 500000  # Default tempo (microseconds per beat)
    for track in midi_file.tracks:
        for msg in track:
            if msg.type == "set_tempo":
                tempo = msg.tempo
                break
    ticks_per_ms = (midi_file.ticks_per_beat * 1000) / tempo
    start_ticks = int(start_time * ticks_per_ms)
    end_ticks = int(end_time * ticks_per_ms)

    # Copy tempo and time signature events
    output_midi.tracks.append(mido.MidiTrack())
    for msg in midi_file.tracks[0]:
        if msg.type in ["set_tempo", "time_signature"]:
            output_midi.tracks[0].append(msg.copy())

    # Process each track
    for track in midi_file.tracks:
        output_track = mido.MidiTrack()
        output_midi.tracks.append(output_track)

        current_ticks = 0
        notes_on = {}  # Keep track of active notes

        for msg in track:
            current_ticks += msg.time

            if start_ticks <= current_ticks <= end_ticks:
                # Include note_on events just before start_ticks
                if msg.type == "note_on" and msg.velocity > 0:
                    notes_on[msg.note] = msg
                    new_msg = msg.copy()
                    new_msg.time = 0 if len(output_track) == 0 else msg.time
                    output_track.append(new_msg)

                # Include note_off events
                elif msg.type == "note_off" or (
                    msg.type == "note_on" and msg.velocity == 0
                ):
                    if msg.note in notes_on:
                        new_msg = msg.copy()
                        new_msg.time = msg.time
                        output_track.append(new_msg)
                        del notes_on[msg.note]

                # Include other message types
                else:
                    new_msg = msg.copy()
                    new_msg.time = msg.time
                    output_track.append(new_msg)

        # Close any pending notes at end_ticks
        for note, msg in notes_on.items():
            output_track.append(mido.Message("note_off", note=note, velocity=0, time=0))

    output_midi.save(output_file)


def extract_audio_fragment(input_audio, start_time, end_time, output_file):
    """
    Extract a fragment of an audio file and save it to the specified folder.

    Args:
        input_audio (str): Path to the original audio file.
        start_time (int): Start time of the fragment in milliseconds.
        end_time (int): End time of the fragment in milliseconds.
        output_file (str): Path to save the extracted fragment.
    """
    audio = AudioSegment.from_file(input_audio)
    fragment = audio[start_time:end_time]
    fragment.export(output_file, format=os.path.splitext(output_file)[1][1:])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract a fragment from an audio or MIDI file.",
        usage=(
            "python3 extract_audio_fragment.py <file> -s <start_time> -e <end_time> [-f <folder>]\n\n"
            "Example:\n"
            "  python3 extract_audio_fragment.py input.wav -s 1000 -e 5000 -f ./output\n"
            "  python3 extract_audio_fragment.py input.mid -s 1000 -e 5000 -f ./output"
        ),
    )

    parser.add_argument("file", help="Path to the original audio or MIDI file.")
    parser.add_argument(
        "-s", "--start", type=int, required=True, help="Start time in milliseconds."
    )
    parser.add_argument(
        "-e", "--end", type=int, required=True, help="End time in milliseconds."
    )
    parser.add_argument(
        "-f",
        "--folder",
        default=".",
        help="Folder to save the extracted fragment. Default is the current folder.",
    )

    args = parser.parse_args()

    try:
        output_file = prepare_output_path(args.file, args.start, args.end, args.folder)

        # Choose extraction function based on file extension
        _, extension = os.path.splitext(args.file)
        if extension.lower() == ".mid":
            extract_midi_fragment(args.file, args.start, args.end, output_file)
        else:
            extract_audio_fragment(args.file, args.start, args.end, output_file)
    except Exception as e:
        print(f"Error extracting fragment: {e}")
