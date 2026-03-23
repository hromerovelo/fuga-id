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
  Created by Hilda Romero-Velo on December 2024.
"""

""" 
  This script inserts the recordings into the database from the recording_insert_statements 
  list. If the melodic line does not exist in the database, the recording is not inserted, the 
  recording_id is logged in the failed_inserts.log file, and the audio file is deleted from the 
  folkoteca_audios directory.
"""

import argparse
import sqlite3
import os

script_dir = os.path.dirname(__file__)
db_path = os.path.join(script_dir, "folkoteca.db")
log_file_path = os.path.join(script_dir, "failed_inserts.log")
audio_files_dir = os.path.join(script_dir, "../queries/data/folkoteca_audios")


def log_failed_insert(recording_id):
    with open(log_file_path, "a") as log_file:
        log_file.write(f"Failed to insert recording_id: {recording_id}\n")


def delete_recording_file(recording_id, format):
    recording_file_path = os.path.join(
        audio_files_dir,
        f"{recording_id}.wav" if format == "WAV" else f"{recording_id}.mid",
    )
    if os.path.exists(recording_file_path):
        os.remove(recording_file_path)


def melodic_line_exists(cursor, melodic_line_id):
    cursor.execute(
        "SELECT 1 FROM Melodic_Line WHERE melodic_line_id = ?", (melodic_line_id,)
    )
    return cursor.fetchone() is not None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Insert recordings into the database.")
    parser.add_argument(
        "--use_piano_set",
        action="store_true",
        help="Use piano recordings instead of default recordings",
    )
    args = parser.parse_args()

    # Import appropriate recording set
    if args.use_piano_set:
        from piano_recordings import recording_insert_statements
    else:
        from recordings import recording_insert_statements

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        for recording in recording_insert_statements:
            recording_id, musician_code, instrument, format, melodic_line_id = recording

            if melodic_line_exists(cursor, melodic_line_id):
                try:
                    cursor.execute(
                        """
                        INSERT INTO Recording (recording_id, musician_code, instrument, format, melodic_line_id)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        recording,
                    )
                except sqlite3.Error:
                    log_failed_insert(recording_id)
                    delete_recording_file(recording_id, format)
            else:
                log_failed_insert(recording_id)
                delete_recording_file(recording_id, format)

        conn.commit()

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()
