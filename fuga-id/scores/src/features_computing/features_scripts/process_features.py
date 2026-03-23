"""
BSD 2-Clause License

Copyright (c) 2023, Hilda Romero-Velo
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
  Created by Hilda Romero-Velo on July 2023.
"""

""" 
  This script compiles **kern feature analyses (chromatic, diatonic, rhythmic) into JSON files
  for each score, discarding unnecessary data and separating values with semicolons (;). 
"""

import os
import sys
import json
import shutil
from fractions import Fraction

# Get the path of 'common' directory
common_directory = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../../common")
)

# Add the path to sys.path to allow importing the modules
sys.path.append(common_directory)

# Import utility_functions.py module
from utility_functions import extract_feature

script_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.abspath(os.path.join(script_dir, "../../../data"))

# Directories containing **kern feature analysis
chromatic_dir = os.path.join(
    data_dir, "computed", "features", "corpus_analysis", "chromatic_analysis"
)
diatonic_dir = os.path.join(
    data_dir, "computed", "features", "corpus_analysis", "diatonic_analysis"
)
rhythmic_dir = os.path.join(
    data_dir, "computed", "features", "corpus_analysis", "rhythmic_analysis"
)

# File suffixes for each analyzed score feature
chromatic_end = "_chromatic.txt"
diatonic_end = "_diatonic.txt"
rhythmic_end = "_rhythmic.txt"

# Target directory
jsons_dir = os.path.join(data_dir, "computed", "features", "corpus_jsons")
try:
    os.makedirs(jsons_dir)
except FileExistsError:
    shutil.rmtree(jsons_dir)
except Exception as e:
    print(f"An error occurred while creating directory '{jsons_dir}': {e}")


def save_json_file(filename, data):
    with open(os.path.join(jsons_dir, filename + ".json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


# Processing chromatic feature. + sign and step 0 (no change in frequency) are removed.
def extract_chromatic(filepath):
    return extract_feature(filepath, ignore_value=0)


# Processing diatonic feature. + sign and step 1 (no change in frequency) are removed.
def extract_diatonic(filepath):
    return extract_feature(filepath, ignore_value=1)


# Processing rhythmic feature. Ties values are joined, rests are mantained and rhythm
# ratio is computed.
def extract_rhythm(filepath):
    rhythm_feature = ""
    old_r = None  # Tracks initial note duration for ratio computation
    sum_r = 0  # Tracks cumulative duration of tied notes
    with open(filepath, "r", encoding="utf8") as f:
        for line in f:
            larray = line.split()
            try:
                r1 = Fraction(larray[0])  # Converts note duration to Fraction
                if r1 != 0:
                    # Initialize first note duration as baseline
                    if old_r == None:
                        old_r = r1
                    else:
                        # Accumulate duration for tied notes
                        if larray[1].strip().startswith("["):
                            sum_r += r1
                        elif larray[1].strip().endswith("]"):
                            sum_r += r1
                            rhythm_feature += str(sum_r / old_r) + ";"
                            old_r = sum_r  # Update baseline to tied notes duration
                            sum_r = 0
                        elif sum_r != 0:
                            sum_r += r1
                        else:
                            # Identify rests and compute rhythm ratio
                            rest = "r" if "r" in larray[1] else ""
                            rhythm_feature += str(r1 / old_r) + rest + ";"
                            old_r = r1  # Update baseline to new note duration
            except ValueError:
                continue
    return rhythm_feature


if __name__ == "__main__":
    with os.scandir(chromatic_dir) as files:
        for f in files:
            score = {}
            id = f.name.removesuffix(chromatic_end)
            score["id"] = id
            # Extract chromatic, diatonic, and rhythmic features for each score
            score["chromatic"] = extract_chromatic(f.path)
            score["diatonic"] = extract_diatonic(
                os.path.join(diatonic_dir, id + diatonic_end)
            )
            score["rhythm"] = extract_rhythm(
                os.path.join(rhythmic_dir, id + rhythmic_end)
            )
            save_json_file(id, score)
