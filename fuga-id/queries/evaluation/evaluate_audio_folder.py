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
Script Name: evaluate_audio_folder.py

Description:
This script processes all files in a specified directory, checking if they are WAV files. 
For each valid WAV file, it runs the "generate_queries_from_recording.py" command using the 
file as input. If a file is not a WAV file, it logs the error to an "error_log.txt" file. 
Additionally, the script verifies that the provided database to store the results of executing
the command exists.

Usage:
    python3 evaluate_audio_folder.py <directory_path> -db <database_path>

Parameters:
    <directory_path>: The path to the directory containing the WAV files to be processed.
    -db, --db_path: The path to the SQLite database required for "generate_queries_from_recording.py".

Dependencies:
    - Python 3.x
    - Ensure the script `generate_queries_from_recording.py` is available.

Output:
    - Executes the command `python3 generate_queries_from_recording.py <recording> -db <database_path>` 
      for each valid WAV file.
    - Logs invalid files in an "error_log.txt" file located in the script's directory.
"""

import argparse
import os
import sys
import subprocess


def log_error(message):
    """
    Logs an error message to error_log.txt.

    Parameters:
        message (str): The error message to log.
    """
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    error_log_path = os.path.join(current_script_dir, "error_log.txt")
    with open(error_log_path, "a") as log_file:
        log_file.write(f"{message}\n")


def print_progress(processed, total):
    """
    Prints the progress as a percentage.

    Parameters:
        processed (int): The number of processed files.
        total (int): The total number of files.
    """
    percentage = (processed / total) * 100 if total > 0 else 100
    print(
        f"Progress: {processed}/{total} files processed ({percentage:.2f}%)", end="\r"
    )


def process_files(directory_path, database_path):
    """
    Processes files in the given directory and executes the "generate_queries_from_recording.py"
    command for each one. Displays the progress as percentage.

    Parameters:
        directory_path (str): The path to the directory containing files to process.
        database_path (str): The path to the database.
    """
    files = os.listdir(directory_path)
    total_files = len(files)
    processed_files = 0

    print_progress(processed_files, total_files)
    for filename in files:
        file_path = os.path.join(directory_path, filename)

        # Skip if not a file
        if not os.path.isfile(file_path):
            processed_files += 1
            print_progress(processed_files, total_files)
            continue

        # Check if the file is a WAV or MIDI file
        if file_path.lower().endswith(".wav") or file_path.lower().endswith(".mid"):
            # Construct the command to run
            command = [
                "python3",
                os.path.join(
                    os.path.dirname(__file__), "generate_queries_from_recording.py"
                ),
                file_path,
                "-db",
                database_path,
            ]
            try:
                subprocess.run(command, check=True)
            except subprocess.CalledProcessError as e:
                log_error(f"Failed to process '{filename}': {e}")
        else:
            log_error(f"Invalid file (not WAV): {filename}")

        processed_files += 1
        print_progress(processed_files, total_files)

    print(f"Finished processing {processed_files}/{total_files} files.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Process WAV or MIDI files in a directory and launch 'generate_queries_from_recording.py' command.",
        usage="python3 evaluate_audio_folder.py <directory_path> -db <database_path>",
    )
    parser.add_argument(
        "directory_path",
        help="Path to the directory containing the WAV or MIDI files from which the queries will be generated.",
    )
    parser.add_argument(
        "-db", "--db_path", required=True, help="Path to the SQLite database."
    )
    args = parser.parse_args()

    # Parse arguments
    directory_path = args.directory_path
    database_path = args.db_path

    # Check arguments
    if not os.path.isdir(directory_path):
        print(f"Error: The directory '{directory_path}' does not exist.")
        sys.exit(1)

    if not os.path.isfile(database_path):
        print(
            f"Error: The database path '{database_path}' does not exist or is not a file."
        )
        sys.exit(1)

    # Process files in the directory
    process_files(directory_path, database_path)
