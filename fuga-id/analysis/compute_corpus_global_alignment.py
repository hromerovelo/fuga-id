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
  This script computes the global alignment of the corpus by comparing the 
  features of each pair of melodic lines.
"""

import os
import shutil
import subprocess
import sqlite3
import multiprocessing as mp
import time
import sys

script_dir = os.path.dirname(__file__)


def launch_alignment_command(score_1_feature, score_2_feature, feature_type):
    """
    Function to launch the global approximate alignment command and capture the output.

    Parameters:
        score_1_feature (str): Feature string of the first score.
        score_2_feature (str): Feature string of the second score.
        feature_type (str): The type of feature to be aligned.

    Returns:
        str: The computed distance between the two features.
    """
    command = (
        './global-align "'
        + score_1_feature
        + '" "'
        + score_2_feature
        + '"'
        + " -f "
        + feature_type
    )

    result = subprocess.run(command, shell=True, capture_output=True, text=True)

    # Check if the command was successful
    if result.returncode == 0:
        # Return computed distance
        return result.stdout
    else:
        print(f"\nError executing command: {command}")
        print(f"Error message: {result.stderr}")
        return None


def process_pair(pair_data):
    """
    Function to process a single pair of melodic lines.

    Parameters:
        pair_data (tuple): Contains (id1, chromatic1, diatonic1, rhythmic1, id2, chromatic2, diatonic2, rhythmic2)

    Returns:
        tuple: (id1, id2, chromatic_rate, diatonic_rate, rhythmic_rate)
    """
    id1, chromatic1, diatonic1, rhythmic1, id2, chromatic2, diatonic2, rhythmic2 = (
        pair_data
    )

    # Compute the alignment rates for each feature type
    chromatic_rate = launch_alignment_command(chromatic1, chromatic2, "chromatic")
    diatonic_rate = launch_alignment_command(diatonic1, diatonic2, "diatonic")
    rhythmic_rate = launch_alignment_command(rhythmic1, rhythmic2, "rhythmic")

    chromatic_rate = float(chromatic_rate) if chromatic_rate is not None else -1
    diatonic_rate = float(diatonic_rate) if diatonic_rate is not None else -1
    rhythmic_rate = float(rhythmic_rate) if rhythmic_rate is not None else -1

    return (id1, id2, chromatic_rate, diatonic_rate, rhythmic_rate)


def compute_melodic_lines_alignment(global_db_file, num_processes=None):
    """
    Function to compute the global alignment for each pair of melodic lines in the database.
    The results are stored in the Global_Alignment table using parallel processing.

    Parameters:
        global_db_file (str): The path to the global database file.
        num_processes (int): Number of processes to use. If None, uses all available cores.
    """
    if num_processes is None:
        num_processes = mp.cpu_count()

    print(f"Using {num_processes} processes for parallel computation.")

    conn = sqlite3.connect(global_db_file)
    cursor = conn.cursor()

    # Retrieve all melodic lines from the database
    cursor.execute(
        "SELECT melodic_line_id, chromatic_feature, diatonic_feature, rhythmic_feature FROM Melodic_Line"
    )
    melodic_lines = cursor.fetchall()

    total_pairs = len(melodic_lines) * (len(melodic_lines) - 1) // 2
    print(f"Total pairs to process: {total_pairs}")

    # Generate all pairs to be processed
    pairs_to_process = []
    for i, (id1, chromatic1, diatonic1, rhythmic1) in enumerate(melodic_lines):
        for j in range(i + 1, len(melodic_lines)):
            id2, chromatic2, diatonic2, rhythmic2 = melodic_lines[j]
            pairs_to_process.append(
                (
                    id1,
                    chromatic1,
                    diatonic1,
                    rhythmic1,
                    id2,
                    chromatic2,
                    diatonic2,
                    rhythmic2,
                )
            )

    # Close the database connection before starting multiprocessing
    conn.close()

    # Process pairs in parallel
    processed_pairs = 0
    batch_size = 100  # Process results in batches to avoid memory issues

    with mp.Pool(processes=num_processes) as pool:
        # Process all pairs
        results = []

        print(f"Starting parallel processing...")
        start_time = time.time()

        # Use imap_unordered for better memory efficiency and progress tracking
        for i, result in enumerate(
            pool.imap_unordered(process_pair, pairs_to_process, chunksize=10)
        ):
            results.append(result)
            processed_pairs += 1

            # Show progress every 100 pairs or at the end
            if processed_pairs % 100 == 0 or processed_pairs == total_pairs:
                elapsed_time = time.time() - start_time
                pairs_per_second = (
                    processed_pairs / elapsed_time if elapsed_time > 0 else 0
                )
                eta = (
                    (total_pairs - processed_pairs) / pairs_per_second
                    if pairs_per_second > 0
                    else 0
                )
                print(
                    f"\rProgress: {processed_pairs}/{total_pairs} pairs processed "
                    f"({processed_pairs/total_pairs*100:.1f}%) - "
                    f"{pairs_per_second:.1f} pairs/sec - "
                    f"Time left: {eta/60:.1f} min",
                    end="",
                )

            # Insert results in batches to avoid memory buildup
            if len(results) >= batch_size or processed_pairs == total_pairs:
                insert_results_batch(global_db_file, results)
                results = []

    print(f"\nProcessing complete in {(time.time() - start_time)/60:.1f} minutes.")


def insert_results_batch(global_db_file, results_batch):
    """
    Insert a batch of results into the database.

    Parameters:
        global_db_file (str): Path to the database file.
        results_batch (list): List of result tuples to insert.
    """
    conn = sqlite3.connect(global_db_file)
    cursor = conn.cursor()

    insert_statement = """
    INSERT INTO Global_Alignment (melodic_line_id_1, melodic_line_id_2, chromatic_rate, diatonic_rate, rhythmic_rate)
    VALUES (?, ?, ?, ?, ?)
    """

    cursor.executemany(insert_statement, results_batch)
    conn.commit()
    conn.close()


def check_and_prepare_environment(original_db_file, global_db_file):
    """
    Function to check if folkoteca.db exists. If it fails, it executes the necessary cleanup
    and processing commands to obtain the data it needs.

    Parameters:
        original_db_file (str): The path to the original database file (folkoteca.db).
    """
    if not os.path.isfile(original_db_file):
        cleanup_command = f"bash {os.path.join(script_dir, '../scores/utils/cleanup_scores_processing.sh')}"
        processing_command = (
            f"bash {os.path.join(script_dir, '../scores/src/scores_processing.sh')}"
        )

        # Execute cleanup command
        cleanup_result = subprocess.run(cleanup_command, shell=True)
        if cleanup_result.returncode != 0:
            print("Error: Cleanup command failed.")
            exit(1)

        # Execute processing command
        processing_result = subprocess.run(processing_command, shell=True)
        if processing_result.returncode != 0:
            print("Error: Processing command failed.")
            exit(1)

    # Compile global_approximate_alignment.cpp
    compile_command = (
        "g++ -o global-align "
        + os.path.join(script_dir, "global_approximate_alignment.cpp ")
        + os.path.join(script_dir, "../queries/src/shared/alignment_utils.cpp ")
        + os.path.join(script_dir, "../queries/src/shared/system_utils.cpp ")
        + os.path.join(script_dir, "../queries/src/shared/file_operations.cpp ")
        + "-std=c++11"
    )

    compile_result = subprocess.run(compile_command, shell=True)
    if compile_result.returncode != 0:
        print("Error: Compilation of global_approximate_alignment.cpp failed.")
        exit(1)

    if not os.path.exists(global_db_file):
        open(global_db_file, "w").close()
    shutil.copy2(original_db_file, global_db_file)


if __name__ == "__main__":
    global_db_file = os.path.join(script_dir, "global_folkoteca.db")
    original_db_file = os.path.join(script_dir, "../database/folkoteca.db")

    # Parse command line arguments for number of processes
    num_processes = None
    if len(sys.argv) > 1:
        try:
            num_processes = int(sys.argv[1])
            if num_processes <= 0:
                print(
                    "Number of processes must be positive. Using all available cores."
                )
                num_processes = None
        except ValueError:
            print("Invalid number of processes. Using all available cores.")
            num_processes = None

    # Check if the global_folkoteca.db file already exists
    if os.path.exists(global_db_file):
        user_input = input(
            "The 'global_folkoteca.db' file already exists. Do you want to continue computing the global alignment of the corpus? (yes/no): "
        )
        if user_input.lower() == "yes":
            os.remove(global_db_file)
        else:
            print("Operation cancelled by the user.")
            exit(0)

    # Check and prepare the environment
    check_and_prepare_environment(original_db_file, global_db_file)

    # Display system information
    total_cores = mp.cpu_count()
    processes_to_use = num_processes if num_processes else total_cores
    print(f"System has {total_cores} CPU cores available.")
    print(f"Will use {processes_to_use} processes for computation.")

    compute_melodic_lines_alignment(global_db_file, num_processes)
