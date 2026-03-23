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
  Created by Hilda Romero-Velo on October 2024.
"""

"""
  This script processes JSON files located in the specified directory,
  extracting feature values for chromatic, diatonic, and rhythm
  characteristics. It consolidates these values into separate FSA files
  for each feature type.

  Input: JSON files containing feature values.
  Output: FSA files for chromatic, diatonic, and rhythm features.
"""

import os
import sys
import json

# Get the path of 'common' directory
common_directory = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../../common")
)
# Get the path of 'common/dicts' directory
dicts_directory = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../../common/dicts")
)

# Add those paths to sys.path to allow importing the modules
sys.path.append(common_directory)
sys.path.append(dicts_directory)

# Import the blast_dictionary module and utility_functions.py
import blast_dictionary
from utility_functions import to_single_notation

# Compute base directory
script_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.abspath(os.path.join(script_dir, "../../../data"))

# Directory containing JSON files with feature analysis
jsons_dir = os.path.join(data_dir, "computed", "features", "corpus_jsons")

# Target directory for storing FSA files
indexes_dir = os.path.abspath(os.path.join(script_dir, "../../../indexes"))
blast_db_dir = os.path.join(indexes_dir, "blast")

# Create the target directory if it doesn't exist
try:
    os.makedirs(blast_db_dir, exist_ok=True)
except Exception as e:
    print(f"An error occurred while creating directory '{blast_db_dir}': {e}")

# Destination files for feature sequences in FSA format
chromatic_fsa_file = os.path.join(blast_db_dir, "chromatic.fsa")
diatonic_fsa_file = os.path.join(blast_db_dir, "diatonic.fsa")
rhythm_fsa_file = os.path.join(blast_db_dir, "rhythm.fsa")


def write_fsa_file(ids, sequences, fsa_file_path, translation_dict):
    """
    Writes feature sequences and their identifiers to an FSA file in FASTA format.

    Args:
        ids (list): List of sequence identifiers.
        sequences (list): List of sequences to be written.
        fsa_file_path (str): Path to the output FSA file.
        translation_dict (dict): Dictionary for translating feature strings to protein sequences.
    """
    with open(fsa_file_path, "w") as fsa_file:  # Open the file in write mode
        for i in range(len(ids)):  # Iterate through all sequences
            fsa_file.write(f">{ids[i]}\n")  # Write the identifier in FASTA format
            line = to_single_notation(
                sequences[i], translation_dict
            )  # Translate the sequence
            fsa_file.write(f"{line}\n")  # Write the translated sequence


def features_to_fsa():
    """
    Loads features from JSON files and saves them into separate FSA files for each feature type.

    This function reads the JSON files, extracts the chromatic, diatonic, and rhythm features,
    and writes them to their corresponding FSA files.
    """
    chromatic = []  # List to store chromatic feature sequences
    diatonic = []  # List to store diatonic feature sequences
    rhythm = []  # List to store rhythm feature sequences
    ids = []  # List to store sequence identifiers

    # Iterate through each file in the specified directory
    with os.scandir(jsons_dir) as files:
        for file in files:
            with open(file.path) as f:  # Open each JSON file
                data = json.load(f)  # Load the JSON data into a dictionary
                # Check if required keys exist in the JSON data
                if (
                    "chromatic" in data
                    and "diatonic" in data
                    and "rhythm" in data
                    and "id" in data
                ):
                    chromatic.append(
                        data["chromatic"]
                    )  # Append chromatic data to the list
                    diatonic.append(
                        data["diatonic"]
                    )  # Append diatonic data to the list
                    rhythm.append(data["rhythm"])  # Append rhythm data to the list
                    ids.append(data["id"])  # Append IDs to the list
                else:
                    print(
                        f"Warning: Missing keys in {file.path}"
                    )  # Warning if keys are missing

    # Write the sequences to corresponding FSA files using their respective dictionaries
    write_fsa_file(ids, chromatic, chromatic_fsa_file, blast_dictionary.CHROMATIC_DIC)
    write_fsa_file(ids, diatonic, diatonic_fsa_file, blast_dictionary.DIATONIC_DIC)
    write_fsa_file(ids, rhythm, rhythm_fsa_file, blast_dictionary.RHYTHM_DIC)


if __name__ == "__main__":
    features_to_fsa()
