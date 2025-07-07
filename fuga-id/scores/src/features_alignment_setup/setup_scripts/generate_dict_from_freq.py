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
  Created by Hilda Romero-Velo on May 2024.
"""

usage_message = """
Usage: generate_dict_from_freq.py -f <feature> -o <origin> [-tf <target_file>] [-fa <True|False>] [-al <blast|approximate>] [-s <True|False>] [-top <number>]

Description:
This script generates a features dictionary for either BLAST or Approximate Alignment from JSON files containing feature analyses of individual scores.

Arguments:
  -f, --feature <feature>           Specify the feature to generate the dictionary from or to compute frequency analysis.
                                    Possible values: diatonic, chromatic, rhythm, or all. (Required)

  -o, --origin <origin>             Source folder with a JSON file for each score containing the diatonic, chromatic,
                                    and rhythmic features analysis. (Required)

  -tf, --target_file <target_file>  Filename of the dictionary destination file (extension must be .py).
                                    Defaults to 'dictionary.py' if not specified. (Optional)

  -fa, --frequency_analysis <True|False>
                                    Set to True to perform frequency analysis instead of generating a dictionary.
                                    Defaults to False. (Optional)

  -al, --alignment <blast|approximate>
                                    Specifies whether the dictionary should be computed for blast or approximate alignment.
                                    Defaults to 'blast'. (Optional)

  -s, --silences <True|False>       Set to True to consider silences when generating a dictionary or performing
                                    frequency analysis. Defaults to False. (Optional)

  -top, --top <number>              Number of top frequencies to consider. Optional parameter. 
                                    Defaults to 20 for BLAST (the number of available protein characters)
                                    and 222 for Approximate Alignment (the number of single-byte ASCII printable characters). 
                                    (Optional)
"""


import os
import re
import sys
import csv
import json
import argparse
from collections import Counter
import matplotlib.pyplot as plt

# Available protein characters to use BLAST as alignment solution.
protein_chars = [
    "A",
    "C",
    "D",
    "E",
    "F",
    "G",
    "H",
    "I",
    "K",
    "L",
    "M",
    "N",
    "P",
    "Q",
    "R",
    "S",
    "T",
    "V",
    "W",
    "Y",
]


# Retrieves the specified feature from each JSON document in the given directory to merge
# the whole corpus into a single text to be scanned.
def iterate_jsons_directory(folder, feature):
    text = ""
    # Traverse the directory
    for filename in os.listdir(folder):
        if filename.endswith(".json"):
            filepath = os.path.join(folder, filename)

            # Open and read the JSON file
            with open(filepath, "r", encoding="utf-8") as file:
                try:
                    data = json.load(file)

                    # Extract the value associated with the key "feature"
                    if feature in data:
                        text += data[feature]
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON from file {filename}: {e}")

    return text


# Analyses the frequency of the different values inside the text divided by ;
# Returns top frequent value keys and the frequency analysis list sorted by frequency.
def extract_value_frequency(text, top, silences):
    # Split each feature value separated by ;
    values = text.split(";")

    # Remove empty strings from values and unmark silences if specified
    if silences:
        values = [value for value in values if value]
    else:
        values = [value.replace("r", "") for value in values if value]

    # Calculate frequency of each value
    frequency = Counter(values)

    # Order elements by frequency
    sorted_items = sorted(frequency.items(), key=lambda item: item[1], reverse=True)

    # Extract keys from the 'top' elements
    top_keys = [item[0] for item in sorted_items[:top]]

    return top_keys, sorted_items


# Updates the given constant (constant_name) in the dictionary file (file_path)
# with the dictionary provided in new_value or adds it in if it does not already exist.
def update_constant(file_path, constant_name, new_value):
    # Try to read the content of the file if it exists, otherwise initialize an empty string
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            content = file.read()
    else:
        content = ""

    # Regular expression to find the constant assignment
    pattern = re.compile(rf"({constant_name}\s*=\s*{{[^}}]*}})")

    # Check if the constant exists and replace its value or add it if it does not exist
    if pattern.search(content):
        # Substitute the existing constant with the new value
        content = pattern.sub(f"{constant_name} = {new_value}", content)
        ## print(f"{constant_name} has been updated successfully.")
    else:
        # Add the new constant at the end of the file
        content += f"\n{constant_name} = {new_value}"
        ## print(f"{constant_name} was not found and has been added successfully.")

    # Write the modified or new content back to the file
    with open(file_path, "w") as file:
        file.write(content)

    ## print(f"Changes have been written to {file_path}.")


# Assigns each value retrieved for a feature to the characters provided in new_values.
# It saves the resulting dictionary into a constant inside the given file (dict_file).
def create_dictionary(feature_values, new_values, dict_file, feature):
    dictionary = str(dict(zip(feature_values, new_values)))
    constant = ""
    if feature == "diatonic":
        constant = "DIATONIC_DIC"
    elif feature == "chromatic":
        constant = "CHROMATIC_DIC"
    else:
        constant = "RHYTHM_DIC"

    update_constant(dict_file, constant, dictionary)


# Plots the frequency of values for a given feature.
# Saves a CSV file with the provided frequencies.
def plot_values_frequency(frequency, feature, target_dir, silences):
    prefix = feature
    if feature == "rhythm":
        prefix = feature + "_r" if silences else feature + "_wor"

    # Plot
    if not isinstance(frequency, dict):
        frequency = dict(frequency)

    keys = list(frequency.keys())
    values = list(frequency.values())

    plt.figure(figsize=(14, 8))
    plt.bar(keys, values)
    plt.xlabel("Categories")
    plt.ylabel("Frequency")
    plt.title(f"Frequency of values for {feature}")
    plt.savefig(
        os.path.abspath(os.path.join(target_dir, prefix + "_frequency_graph.png"))
    )

    # Save character frequency data to a CSV file
    with open(
        os.path.abspath(os.path.join(target_dir, prefix + "_char_frequency.csv")),
        "w",
        newline="",
        encoding="utf-8",
    ) as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Value", "Frequency"])
        for char, freq in frequency.items():
            writer.writerow([char, freq])


# Auxiliar function to retrieve all single-byte printable ASCII characters
def get_single_byte_printable_characters():
    # List to store single-byte printable characters (ASCII)
    single_byte_printable_chars = []

    # Add uppercase letters (A-Z)
    for codepoint in range(ord("A"), ord("Z") + 1):  # A-Z
        char = chr(codepoint)
        single_byte_printable_chars.append(char)

    # Add lowercase letters (a-z)
    for codepoint in range(ord("a"), ord("z") + 1):  # a-z
        char = chr(codepoint)
        single_byte_printable_chars.append(char)

    # Add digits (0-9)
    for codepoint in range(ord("0"), ord("9") + 1):  # 0-9
        char = chr(codepoint)
        single_byte_printable_chars.append(char)

    # Add other single-byte printable characters
    for codepoint in range(256):  # Unicode range
        char = chr(codepoint)
        if (
            char.isprintable()
            and char not in ('"', "'", "`", "\n")
            and not ("A" <= char <= "Z" or "a" <= char <= "9" or "0" <= char <= "9")
        ):
            single_byte_printable_chars.append(char)

    return single_byte_printable_chars


# Auxiliar function to ensure dictionary.py extension
def ensure_py_extension(filename):
    # Split the filename into name and extension
    base, ext = os.path.splitext(filename)

    # Check if the extension is .py
    if ext != ".py":
        # If no extension or a different extension, add or change to .py
        new_filename = base + ".py"
        print(f"Filename changed to: {new_filename}")
        return new_filename

    return filename


if __name__ == "__main__":
    # Initialize the argument parser
    parser = argparse.ArgumentParser(
        description="Features dictionary generation for BLAST and Approximate Alignment.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Argument for specifying the feature to generate dictionary from or to compute frequency analysis
    parser.add_argument(
        "-f",
        "--feature",
        action="store",
        required=True,
        help="Specify the feature to generate a dictionary from or to compute frequency analysis. "
        "Possible values: diatonic, chromatic, rhythm, or all.",
    )

    # Argument for the source folder containing JSON files with feature analysis
    parser.add_argument(
        "-o",
        "--origin",
        action="store",
        required=True,
        help="Source folder containing a JSON file for each score, which includes diatonic, chromatic, "
        "and rhythmic feature analysis.",
    )

    # Argument for the destination filename of the generated dictionary
    parser.add_argument(
        "-tf",
        "--target_file",
        type=str,
        action="store",
        required=False,
        help="Filename for the dictionary destination file (extension must be .py). "
        "Defaults to 'dictionary.py' if not specified.",
    )

    # Argument for performing frequency analysis instead of generating a dictionary
    parser.add_argument(
        "-fa",
        "--frequency_analysis",
        action="store",
        required=False,
        help="Set to True to perform frequency analysis instead of generating a dictionary. "
        "Defaults to False.",
    )

    # Argument for selecting the type of alignment for dictionary computation
    parser.add_argument(
        "-al",
        "--alignment",
        action="store",
        required=False,
        help="Specifies the type of alignment for dictionary computation. "
        "Possible values: blast or approximate. Defaults to 'blast'.",
    )

    # Argument for considering silences during dictionary generation or frequency analysis
    parser.add_argument(
        "-s",
        "--silences",
        action="store",
        required=False,
        help="Set to True to include silences when generating a dictionary or performing "
        "frequency analysis. Defaults to False.",
    )

    # Argument for specifying the number of top frequencies to consider
    parser.add_argument(
        "-top",
        "--top",
        type=int,
        action="store",
        required=False,
        help="Number of top frequencies to consider. Optional parameter. "
        "Defaults to 20 for BLAST (number of available protein characters) and 222 "
        "for Approximate Alignment (number of single-byte ASCII printable characters).",
    )

    args = parser.parse_args()
    available_features = ["diatonic", "chromatic", "rhythm"]

    # Print usage message if no arguments are provided or -h is requested
    if not vars(args) or args.feature is None:
        print(usage_message)
        parser.exit()

    # Retrieve source folder with the scores analysis in JSON format
    folder = args.origin

    # Feature to be considered (or all of them)
    feature = args.feature.lower()
    if feature not in available_features + ["all"]:
        print(
            "Error: feature not recognized. Available features: diatonic, chromatic, rhythm or all."
        )
        sys.exit(1)

    # Check whether a frequency analysis should be performed instead of generating the dictionary
    frequency_analysis = (
        args.frequency_analysis and args.frequency_analysis.lower() == "true"
    )

    # Retrieve type of alignment or defult it to blast
    alignment = "blast"

    if args.alignment:
        alignment_lower = args.alignment.lower()
        if alignment_lower in ["blast", "approximate"]:
            alignment = alignment_lower
        else:
            print(
                "Error: alignment not recognized. Available alignments: blast or approximate."
            )
            sys.exit(1)

    # Specifies the characters to be associated with each value in the corpus
    chars = (
        protein_chars
        if alignment == "blast"
        else get_single_byte_printable_characters()
    )

    # Check whether silences should be taken into account
    silences = args.silences and args.silences.lower() == "true"

    # Retrieve top if it is specified, otherwise the maximum value is considered
    top = args.top if args.top else len(chars)

    # File to store dictionaries
    dict_file = args.target_file if args.target_file else "dictionaries.py"

    # Check whether JSON folder exists and is not empty
    if os.path.isdir(folder):
        if not os.listdir(folder):
            print("Directory is empty")
        else:
            # Iterate over all features if it is specified
            features = available_features if feature == "all" else [feature]

            for feature in features:
                # Retrieve all values in corpus for the provided feature
                text = iterate_jsons_directory(folder, feature)
                # Compute frequency of each value
                top_keys, frequency = extract_value_frequency(text, top, silences)

                if frequency_analysis:
                    # Create analysis directory
                    script_dir = os.path.dirname(__file__)
                    target_dir = os.path.join(
                        script_dir, "../../../", "extra", "features_frequency_analysis"
                    )

                    try:
                        os.makedirs(target_dir, exist_ok=True)
                        plot_values_frequency(frequency, feature, target_dir, silences)
                    except Exception as e:
                        print(
                            f"An error occurred while creating directory '{target_dir}': {e}"
                        )
                else:
                    create_dictionary(top_keys, chars, dict_file, feature)

    else:
        print("Given directory does not exist")
