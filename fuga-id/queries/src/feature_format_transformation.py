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
This script processes chromatic and diatonic features from **kern files and the 
rhythmic feature from MIDI files. The extracted data is converted into a single 
notation format and printed to the console. Users can specify which features to 
compile using command-line arguments, and must specify an alignment method 
(`approximate` or `blast`) for the conversion process. Note that chromatic and 
diatonic **kern analyses are stored in TXT files.

Example usage:
    python feature_format_transformation.py -c path/to/chromatic_kern_analysis_file.txt -m blast
    python feature_format_transformation.py -d path/to/diatonic_kern_analysis_file.txt -m blast
    python feature_format_transformation.py -r path/to/midi_file.mid -m approximate
"""

import os
import sys
import argparse
import pretty_midi

# Define directories to allow importing shared modules and dictionaries
common_directory = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../common")
)

dicts_directory = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../common/dicts")
)

utils_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), "../utils/"))

sys.path.append(common_directory)
sys.path.append(dicts_directory)
sys.path.append(utils_directory)

# Import dictionaries for alignment methods and utilities for feature extraction
# and notation conversion.
import approx_dictionary
import blast_dictionary
from utility_functions import extract_feature, to_single_notation
from constants import RATIOS_NUMS


# Extract chromatic feature from the **kern analysis file, ignoring changes with a step value of 0
# (meaning no change in frequency)
def extract_chromatic(filepath):
    return extract_feature(filepath, ignore_value=0)


# Extract diatonic feature from the **kern analysis file, ignoring changes with a step value of 1
# (meaning no change in frequency)
def extract_diatonic(filepath):
    return extract_feature(filepath, ignore_value=1)


# Extract rhythm feature from a MIDI file by computing duration ratios between consecutive notes
def extract_rhythm(midifilepath):
    data = pretty_midi.PrettyMIDI(midifilepath)
    ratios = []

    # Process each instrument track in the MIDI file
    for instrument in data.instruments:
        num_notes = len(instrument.notes)

        # Skip tracks with fewer than 2 notes, as we cannot compute a ratio with just one note
        if num_notes < 2:
            continue

        # Precompute tick durations of each note to avoid repeated time-to-tick conversions
        tick_durations = [
            data.time_to_tick(note.get_duration()) for note in instrument.notes
        ]

        # Calculate the duration ratio between consecutive notes
        for i in range(num_notes - 1):
            current_duration_ticks = tick_durations[i]
            next_duration_ticks = tick_durations[i + 1]
            if current_duration_ticks == 0:
                continue  # Avoid division by zero

            # Find closest predefined ratio to computed ratio
            ratio = next_duration_ticks / current_duration_ticks
            closest_ratio = min(RATIOS_NUMS, key=lambda x: abs(x - ratio))
            ratios.append(str(closest_ratio))

    # Return computed ratios as a string separated by ';', or an empty string if no ratios found
    return ";".join(ratios) + ";" if ratios else ""


# Process chromatic feature from a **kern analysis file, convert values
# to a single notation format, and print the result.
def process_chromatic(filepath, dictionary):
    chromatic_feature = extract_chromatic(filepath)
    chromatic_query = to_single_notation(chromatic_feature, dictionary.CHROMATIC_DIC)
    print(chromatic_query)


# Process diatonic feature from a **kern analysis file, convert values
# to a single notation format, and print the result.
def process_diatonic(filepath, dictionary):
    diatonic_feature = extract_diatonic(filepath)
    diatonic_query = to_single_notation(diatonic_feature, dictionary.DIATONIC_DIC)
    print(diatonic_query)


# Process rhythm feature from a MIDI file, convert values
# to a single notation format, and print the result.
def process_rhythm(midifilepath, dictionary):
    rhythm_feature = extract_rhythm(midifilepath)
    rhythm_query = to_single_notation(rhythm_feature, dictionary.RHYTHM_DIC)
    print(rhythm_query)


# Set up command-line argument parsing for specifying feature type and alignment method
parser = argparse.ArgumentParser(
    description="Query processing. Humdrum Kern features to single format notation.",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)

# Arguments to process the chromatic/diatonic feature from a specified **kern analysis file
parser.add_argument(
    "-c",
    "--chromatic",
    action="store",
    help="Convert query chromatic features to single format. Kern analysis needed.",
)

parser.add_argument(
    "-d",
    "--diatonic",
    action="store",
    help="Convert query diatonic features to single format. Kern analysis needed.",
)

# Argument to process rhythm feature from a specified MIDI file
parser.add_argument(
    "-r",
    "--rhythm",
    action="store",
    help="Convert query rhythm to single format. MIDI file needed.",
)

# Argument to specify the alignment method (mandatory)
parser.add_argument(
    "-m",
    "--method",
    required=True,
    choices=["approximate", "blast"],
    help="Specify alignment method: 'approximate' or 'blast'. This argument is required.",
)

args = parser.parse_args()

# Check if at least one feature flag is specified
if not (args.chromatic or args.diatonic or args.rhythm):
    parser.error("You must specify at least one feature option: -c, -d, or -r.")

# Select dictionary based on the specified alignment method
dictionary = approx_dictionary if args.method == "approximate" else blast_dictionary

# Process each feature if specified
if args.chromatic:
    process_chromatic(args.chromatic, dictionary)

if args.diatonic:
    process_diatonic(args.diatonic, dictionary)

if args.rhythm:
    process_rhythm(args.rhythm, dictionary)
