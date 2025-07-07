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
Script: generate_queries_from_recording.py
Purpose: Extract random fragments from a recording, save them in the database, 
         launch queries for each fragment, and clean up temporary files.

Usage:
    python3 generate_queries_from_recording.py <recording> -db <path_to_database>

Steps:
1. Verifies if the recording exists in the "Recording" table of "folkoteca.db".
2. Extracts 4 random fragments of random durations (3-20 seconds).
3. Saves fragment metadata in the "Query" table, using milliseconds for timestamps.
4. Launches `launch_query.py` for each fragment using its query ID.
5. Deletes temporary fragment files.

Required Arguments:
    <recording>: Path to the audio file for the recording.
    -db, --db_path: Path to the SQLite database.

Dependencies:
    - SQLite3 for database access.
    - The `extract_audio_fragment.py` script must be available.
    - The `launch_query.py` script must be available.
"""

import argparse
import os
from pydub import AudioSegment
import random
import sqlite3
import subprocess
import mido
import sys

MIN_FRAGMENT_DURATION = 3000  # Minimum fragment duration in milliseconds
MAX_FRAGMENT_DURATION = 20000  # Maximum fragment duration in milliseconds
DEFAULT_NUM_FRAGMENTS = 4  # Default number of fragments to generate

script_dir = os.path.dirname(os.path.abspath(__file__))
audio_fragments_dir = os.path.join(script_dir, "audio_fragments")


def get_file_duration(file_path):
    """
    Get duration in milliseconds for either WAV or MIDI file.
    Args:
        file_path (str): Path to the recording file.
    Returns:
        int: Duration in milliseconds.
    """
    extension = os.path.splitext(file_path)[1].lower()

    if extension == ".wav":
        audio = AudioSegment.from_file(file_path)
        return len(audio)
    elif extension == ".mid":
        midi_file = mido.MidiFile(file_path)
        # Calculate total time in ticks
        total_ticks = 0
        for track in midi_file.tracks:
            track_ticks = 0
            for msg in track:
                track_ticks += msg.time
            total_ticks = max(total_ticks, track_ticks)
        # Convert ticks to milliseconds using tempo
        tempo = 500000  # Default tempo (microseconds per beat)
        for track in midi_file.tracks:
            for msg in track:
                if msg.type == "set_tempo":
                    tempo = msg.tempo
                    break
        microseconds_per_tick = tempo / midi_file.ticks_per_beat
        return int((total_ticks * microseconds_per_tick) / 1000)
    else:
        raise ValueError(f"Unsupported file format: {extension}")


def check_recording_in_db(recording_id, db_path="folkoteca.db"):
    """
    Checks if a recording exists in the 'Recording' table.
    Args:
        recording_id (str): Name of the recording (without extension).
        db_path (str): Path to the SQLite database.
    Returns:
        bool: True if the recording exists, False otherwise.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT recording_id FROM Recording WHERE recording_id = ?", (recording_id,)
        )
        result = cursor.fetchone()
        return result is not None
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    finally:
        conn.close()


def fragment_exists(recording_id, start_ms, end_ms, db_path="folkoteca.db"):
    """
    Checks if a fragment with the given timestamps already exists in the database.
    Args:
        recording_id (str): The recording ID.
        start_ms (int): Start time in milliseconds.
        end_ms (int): End time in milliseconds.
        db_path (str): Path to the SQLite database.
    Returns:
        bool: True if the fragment exists, False otherwise.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 1 FROM Query 
            WHERE recording_id = ? AND start_timestamp = ? AND end_timestamp = ?
            """,
            (recording_id, start_ms, end_ms),
        )
        result = cursor.fetchone()
        return result is not None
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    finally:
        conn.close()


def generate_adaptive_fragments(duration_ms, num_fragments=DEFAULT_NUM_FRAGMENTS):
    """
    Generates adaptive random fragments based on recording duration.
    Args:
        duration_ms (int): Total duration of the recording in milliseconds.
        num_fragments (int): Desired number of fragments (dinamically adjusted for short recordings).
    Returns:
        list of tuples: Each tuple contains (start_time, end_time) in milliseconds.
    """
    if duration_ms < MIN_FRAGMENT_DURATION * 2:
        raise ValueError("Recording is too short to extract meaningful fragments.")

    # Adjust number of fragments for short recordings
    if duration_ms < MAX_FRAGMENT_DURATION * num_fragments:
        num_fragments = max(2, duration_ms // (2 * MIN_FRAGMENT_DURATION))

    fragments = []

    # First fragment: near the start (0%-10%)
    start = random.randint(0, duration_ms // 10)
    end = min(
        duration_ms,
        start + random.randint(MIN_FRAGMENT_DURATION, MAX_FRAGMENT_DURATION),
    )
    fragments.append((start, end))

    # Last fragment: near the end (90%-100%)
    end = duration_ms
    start = max(0, end - random.randint(MIN_FRAGMENT_DURATION, MAX_FRAGMENT_DURATION))
    fragments.append((start, end))

    # Intermediate fragments: within the middle 80% (10%-90%)
    for _ in range(num_fragments - 2):
        start = random.randint(duration_ms // 10, (duration_ms * 9) // 10)
        end = min(
            duration_ms,
            start + random.randint(MIN_FRAGMENT_DURATION, MAX_FRAGMENT_DURATION),
        )
        fragments.append((start, end))

    return fragments


def store_query_in_db(recording_id, start_ms, end_ms, db_path="folkoteca.db"):
    """
    Stores a query fragment in the 'Query' table.
    Args:
        recording_id (str): The recording ID.
        start_ms (int): Start time in milliseconds.
        end_ms (int): End time in milliseconds.
        db_path (str): Path to the SQLite database.
    Returns:
        int: The query ID of the inserted record.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO Query (start_timestamp, end_timestamp, recording_id)
            VALUES (?, ?, ?)
            """,
            (start_ms, end_ms, recording_id),
        )
        query_id = cursor.lastrowid
        conn.commit()
        return query_id
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        conn.close()


def process_fragment(recording, start_ms, end_ms, query_id, db_path):
    """
    Processes a fragment: extracts it, launches the query, and deletes the temporary file.
    Args:
        recording (str): Path to the original recording.
        start_ms (int): Start time of the fragment in milliseconds.
        end_ms (int): End time of the fragment in milliseconds.
        query_id (int): Query ID.
        db_path(str): Path to the SQLite database
    """
    os.makedirs(audio_fragments_dir, exist_ok=True)
    recording_base_name = os.path.basename(recording)
    recording_file_name, recording_file_extension = os.path.splitext(
        recording_base_name
    )
    fragment_path = os.path.join(
        audio_fragments_dir,
        f"{recording_file_name}_{start_ms}_{end_ms}{recording_file_extension}",
    )
    extract_audio_fragment_script = os.path.join(
        script_dir, "../utils/extract_audio_fragment.py"
    )
    launch_command_script = os.path.join(script_dir, "launch_query.py")

    # Extract fragment
    extract_command = [
        "python3",
        extract_audio_fragment_script,
        recording,
        "-s",
        str(start_ms),
        "-e",
        str(end_ms),
        "-f",
        audio_fragments_dir,
    ]
    subprocess.run(extract_command, check=True)

    # Launch query
    launch_command = [
        "python3",
        launch_command_script,
        fragment_path,
        "-qid",
        str(query_id),
        "-db",
        db_path,
    ]
    subprocess.run(launch_command, check=True)

    # Delete fragment
    if os.path.exists(fragment_path):
        os.remove(fragment_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate queries from a recording.")
    parser.add_argument(
        "recording", help="Path to the recording (e.g., recording.wav, recording.mid)."
    )
    parser.add_argument(
        "-db", "--db_path", required=True, help="Path to the SQLite database."
    )
    args = parser.parse_args()

    if not os.path.isfile(args.recording):
        print(f"Error: File {args.recording} does not exist.")
        sys.exit(1)

    recording_id = os.path.splitext(os.path.basename(args.recording))[0]

    # Check if the recording exists in the database
    if not check_recording_in_db(recording_id, args.db_path):
        print(f"Error: Recording {recording_id} does not exist in the database.")
        sys.exit(1)

    # Get the file duration
    try:
        duration_ms = get_file_duration(args.recording)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    try:
        # Generate adaptive fragments
        fragments = generate_adaptive_fragments(duration_ms)

        # Process each fragment
        for start_ms, end_ms in fragments:
            if fragment_exists(recording_id, start_ms, end_ms, args.db_path):
                print(
                    f"{recording_id} fragment {start_ms}-{end_ms} already exists in the database. Skipping..."
                )
                continue

            query_id = store_query_in_db(recording_id, start_ms, end_ms, args.db_path)
            if query_id is None:
                print(
                    f"Error: Failed to store {recording_id} fragment {start_ms}-{end_ms} in the database."
                )
                continue
            process_fragment(args.recording, start_ms, end_ms, query_id, args.db_path)

        # Clean up: remove the audio_fragments_dir if empty
        if not os.listdir(audio_fragments_dir):
            os.rmdir(audio_fragments_dir)

    except Exception as e:
        print(f"Error during processing: {e}")
