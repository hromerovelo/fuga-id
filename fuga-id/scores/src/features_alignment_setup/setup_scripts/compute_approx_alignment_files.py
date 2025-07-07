"""
BSD 2-Clause License

Copyright (c) 2024, Hilda Romero-Velo
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice, this
  list of conditions and the following disclaimer in the documentation
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
  Created by Hilda Romero-Velo on October 2024.
"""

"""
  This script processes JSON files containing feature values for individual musical scores. 
  It combines these values (each represented as a single character) into unified text files 
  (one per feature) where each score feature is separated by a newline character. Additionally,
  it generates and saves cost maps for the global and local approximate alignment based on the 
  difference of values. The cost maps are saved as binary files.

  Input: JSON files with feature values for each score.
  Output: Text files and cost matrix files for each feature.
"""

import os
import sys
import json
from fractions import Fraction
import sqlite3

# Calculate base directories
script_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.abspath(os.path.join(script_dir, "../../../data"))
indexes_dir = os.path.abspath(os.path.join(script_dir, "../../../indexes"))

# Setup import paths
common_directory = os.path.abspath(os.path.join(script_dir, "../../../../common"))
dicts_directory = os.path.join(common_directory, "dicts")
utils_directory = os.path.join(script_dir, "../../../utils")

# Add paths to sys.path for module imports
sys.path.append(common_directory)
sys.path.append(dicts_directory)
sys.path.append(utils_directory)

# Import required modules
import approx_dictionary
from utility_functions import to_single_notation, save_cost_map, write_text_to_file

# Define source and target directories
jsons_dir = os.path.join(data_dir, "computed", "features", "corpus_jsons")
approx_alignment_files_dir = os.path.join(indexes_dir, "approximate_alignment")
global_alignment_files_dir = os.path.join(indexes_dir, "global_alignment")

# Create approximate alignment directory
try:
    os.makedirs(approx_alignment_files_dir, exist_ok=True)
except Exception as e:
    print(
        f"An error occurred while creating directory '{approx_alignment_files_dir}': {e}"
    )

# Create global alignment directory
try:
    os.makedirs(global_alignment_files_dir, exist_ok=True)
except Exception as e:
    print(
        f"An error occurred while creating directory '{global_alignment_files_dir}': {e}"
    )

# Define feature text file paths
chromatic_text_file = os.path.join(approx_alignment_files_dir, "chromatic_text.txt")
diatonic_text_file = os.path.join(approx_alignment_files_dir, "diatonic_text.txt")
rhythm_text_file = os.path.join(approx_alignment_files_dir, "rhythm_text.txt")
ids_file = os.path.join(approx_alignment_files_dir, "melodic_line_ids.txt")

# Map files to store the cost matrix
chromatic_cost_map = os.path.join(approx_alignment_files_dir, "chromatic_cost_map.bin")
diatonic_cost_map = os.path.join(approx_alignment_files_dir, "diatonic_cost_map.bin")
rhythm_cost_map = os.path.join(approx_alignment_files_dir, "rhythmic_cost_map.bin")
global_chromatic_cost_map = os.path.join(
    global_alignment_files_dir, "chromatic_cost_map.bin"
)
global_diatonic_cost_map = os.path.join(
    global_alignment_files_dir, "diatonic_cost_map.bin"
)
global_rhythm_cost_map = os.path.join(
    global_alignment_files_dir, "rhythmic_cost_map.bin"
)

# Define database file and error log file
db_file = os.path.join(script_dir, "../../../../database/folkoteca.db")
error_log = os.path.join(
    script_dir, "../../../../database/folkoteca_scores_db_error_log.txt"
)
folkoteca_musicxml_dir = os.path.join(
    script_dir, "../../../data/origin/scores_musicxml/"
)
folkoteca_kern_dir = os.path.join(
    script_dir, "../../../data/computed/scores/scores_kern/kern_prepared/"
)


def check_database_and_tables():
    """
    Checks if the database file and required tables exist.

    Raises:
        SystemExit: If the database file or required tables do not exist.
    """
    if not os.path.isfile(db_file):
        raise SystemExit(f"ERROR: Database file '{db_file}' does not exist.")
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Check if the required tables exist in the database
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='Score';"
    )
    score_table_exists = cursor.fetchone()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='Melodic_Line';"
    )
    melodic_line_table_exists = cursor.fetchone()

    if not score_table_exists or not melodic_line_table_exists:
        conn.close()
        raise SystemExit(
            f"ERROR: Tables 'Score' or 'Melodic_Line' do not exist in {db_file}."
        )

    conn.close()


def save_data_to_db(melodic_line_id, chromatic, diatonic, rhythm):
    """
    Saves scores and melodic lines data to the database.

    Args:
        melodic_line_id (str): The identifier of the melodic line.
        chromatic (str): The chromatic feature values.
        diatonic (str): The diatonic feature values.
        rhythm (str): The rhythm feature values.
    """
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    musical_form = melodic_line_id.split("_")[1]
    score_id = "_".join(melodic_line_id.split("_")[:-3])
    line_number = int(melodic_line_id.split("_")[-3])

    musicxml_file = os.path.join(folkoteca_musicxml_dir, f"{score_id}.musicxml")
    kern_file = os.path.join(folkoteca_kern_dir, f"{melodic_line_id}.krn")
    if os.path.isfile(musicxml_file) and os.path.isfile(kern_file):
        try:
            cursor.execute(
                "INSERT OR IGNORE INTO Score (score_id, musical_form, file_extension) VALUES (?, ?, ?)",
                (score_id, musical_form, ".musicxml"),
            )
            cursor.execute(
                "INSERT INTO Melodic_Line (melodic_line_id, line_number, score_id, chromatic_feature, diatonic_feature, rhythmic_feature) VALUES (?, ?, ?, ?, ?, ?)",
                (melodic_line_id, line_number, score_id, chromatic, diatonic, rhythm),
            )
            conn.commit()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
    else:
        with open(error_log, "a") as log_file:
            if not os.path.isfile(musicxml_file):
                log_file.write(f"File not found: {musicxml_file}\n")
            if not os.path.isfile(kern_file):
                log_file.write(f"File not found: {kern_file}\n")

    conn.close()


def features_to_single_notation():
    """
    Translates the features using their corresponding dictionary so that each value occupies only
    one character. For each feature, combines all calculated values from the scores into a single
    text. Additionally, for each feature, a separate file is generated for each feature to store
    the starting position of each score within the unified text.

    Returns:
        dict: A dictionary containing combined text for chromatic, diatonic, and rhythm features,
              along with their corresponding score ranges.
    """
    with os.scandir(jsons_dir) as files:
        chromatic_text = ""
        diatonic_text = ""
        rhythm_text = ""
        ids = ""

        for file in files:
            with open(file.path) as f:
                try:
                    data = json.load(f)

                    # Translate each feature into single-character notation
                    chromatic = to_single_notation(
                        data["chromatic"], approx_dictionary.CHROMATIC_DIC
                    )
                    chromatic_text += chromatic.strip() + "\n"

                    diatonic = to_single_notation(
                        data["diatonic"], approx_dictionary.DIATONIC_DIC
                    )
                    diatonic_text += diatonic.strip() + "\n"

                    rhythm = to_single_notation(
                        data["rhythm"], approx_dictionary.RHYTHM_DIC
                    )
                    rhythm_text += rhythm.strip() + "\n"

                    ids += data["id"] + "\n"
                    save_data_to_db(data["id"], chromatic, diatonic, rhythm)

                except json.JSONDecodeError as e:
                    print(f"Error reading JSON from file {file.path}: {e}")

        return {
            "chromatic_text": chromatic_text,
            "diatonic_text": diatonic_text,
            "rhythm_text": rhythm_text,
            "melodic_lines_ids": ids,
        }


def build_cost_map(dic, match_value, mismatch_sign):
    """
    Builds a cost matrix for alignment based on the difference of dictionary keys.

    Args:
        dic (dict): A dictionary where the keys are numeric values and the values are characters.

    Returns:
        dict: A dictionary of dictionaries representing the alignment cost matrix.
              The diagonal elements have a value of 1 (matches), and the off-diagonal
              elements have negative values based on the absolute difference between the keys.
    """
    cost_map = {}
    keys = list(dic.keys())
    values = list(dic.values())

    for i in range(len(values)):
        cost_map[values[i]] = {}
        for j in range(len(values)):
            if i == j:
                # Assign 1 for matches (diagonal)
                cost_map[values[i]][values[j]] = match_value
            else:
                # Convert keys to floats, handling fractions if necessary
                val_i = float(Fraction(keys[i]))
                val_j = float(Fraction(keys[j]))
                # Compute penalty as the negative absolute difference
                cost_map[values[i]][values[j]] = mismatch_sign * abs(val_i - val_j)

    return cost_map


if __name__ == "__main__":
    # Check database and tables
    check_database_and_tables()

    # Get features from all scores
    features = features_to_single_notation()

    # Write feature texts to files
    write_text_to_file(chromatic_text_file, features["chromatic_text"])
    write_text_to_file(diatonic_text_file, features["diatonic_text"])
    write_text_to_file(rhythm_text_file, features["rhythm_text"])
    write_text_to_file(ids_file, features["melodic_lines_ids"])

    # Generate and save local approximate alignment cost maps
    local_aa_match = 1.0
    local_aa_mismatch_sign = -1.0
    save_cost_map(
        build_cost_map(
            approx_dictionary.CHROMATIC_DIC, local_aa_match, local_aa_mismatch_sign
        ),
        chromatic_cost_map,
    )
    save_cost_map(
        build_cost_map(
            approx_dictionary.DIATONIC_DIC, local_aa_match, local_aa_mismatch_sign
        ),
        diatonic_cost_map,
    )
    save_cost_map(
        build_cost_map(
            approx_dictionary.RHYTHM_DIC, local_aa_match, local_aa_mismatch_sign
        ),
        rhythm_cost_map,
    )

    # Generate and save global alignment cost maps
    global_aa_match = 0.0
    global_aa_mismatch_sign = 1.0
    save_cost_map(
        build_cost_map(
            approx_dictionary.CHROMATIC_DIC, global_aa_match, global_aa_mismatch_sign
        ),
        global_chromatic_cost_map,
    )
    save_cost_map(
        build_cost_map(
            approx_dictionary.DIATONIC_DIC, global_aa_match, global_aa_mismatch_sign
        ),
        global_diatonic_cost_map,
    )
    save_cost_map(
        build_cost_map(
            approx_dictionary.RHYTHM_DIC, global_aa_match, global_aa_mismatch_sign
        ),
        global_rhythm_cost_map,
    )
