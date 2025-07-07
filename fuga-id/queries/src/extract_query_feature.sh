: '
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
 '

: '
 # Created by Hilda Romero-Velo on October 2024.
 '

: '
# Script to extract musical features from audio files (WAV or MIDI).
# This script supports extracting chromatic, diatonic, and rhythm features.
# 
# Usage:
#   Run the script with one of the following feature flags:
#     - -c <wav_or_midi_file_path>    Extracts chromatic feature from a WAV or MIDI file.
#     - -d <wav_or_midi_file_path>    Extracts diatonic feature from a WAV or MIDI file.
#     - -r <wav_or_midi_file_path>   Extracts rhythm feature from a WAV or MIDI file.
#   The script requires the additional argument:
#     - -m <method>           Specifies the alignment method: 'approximate' or 'blast'.
# 
# Example usage:
#   ./extract_query_feature.sh -c path/to/file.wav -m approximate
#
# Dependencies:
#   The script assumes the availability of several utilities:
#   - basic-pitch
#   - mid2hum
#   - humsed
#   - mint (for diatonic analysis)
#   - semits and xdelta (for chromatic analysis)
#   - Python script 'feature_format_transformation.py' for final data formatting
#
# Output:
#   The script generates a final output file with the selected feature in single format
#   (where each value is represented with a single byte) as follows:
#     - For the 'approximate' method: a TXT file (e.g., chromatic_sf_query.txt).
#     - For the 'blast' method: a FASTA file (e.g., chromatic_sf_query.fasta).
#
# All generated files are stored in a 'tmp' directory at the script's root.

#!/bin/bash

# Usage message
usage="Usage: $0 -c <file_path> | -d <file_path> | -r <file_path> [-m approximate | blast]\n\
    Extract features from audio files:\n\
    -c <wav_or_midi_file_path>    Extract chromatic features from a WAV or MIDI file\n\
    -d <wav_or_midi_file_path>    Extract diatonic features from a WAV or MIDI file\n\
    -r <wav_or_midi_file_path>    Extract rhythm features from a WAV or MIDI file\n\
    -m <method>       Specify alignment method: 'approximate' or 'blast' (required)\n\
    \nExample:\n\
  $0 -c path/to/file.wav -m approximate"

# Default variables
feature=""
input_file=""
method=""

# Function to show usage and exit
show_usage_and_exit() {
    echo -e "$usage"
    exit 1
}

# Function to validate if a file exists
validate_file_exists() {
    if [ ! -f "$1" ]; then
        echo "Error: File '$1' does not exist." >&2
        exit 1
    fi
}

# Function to validate file extension
validate_file_extension() {
    local file_ext="$1"
    if [ "$file_ext" != "wav" ] && [ "$file_ext" != "mid" ]; then
        echo "Error: File '$input_file' must be a .wav or .mid file for $feature feature." >&2
        exit 1
    fi
}

# Process command-line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
    -c | --chromatic)
        feature="chromatic"
        ;;
    -d | --diatonic)
        feature="diatonic"
        ;;
    -r | --rhythm)
        feature="rhythm"
        ;;
    -m | --method)
        if [[ "$2" == "approximate" || "$2" == "blast" ]]; then
            method="$2"
            shift
        else
            echo "Error: Invalid method. Choose 'approximate' or 'blast'." >&2
            show_usage_and_exit
        fi
        ;;
    -h | --help)
        show_usage_and_exit
        ;;
    *)
        if [ -z "$input_file" ]; then
            input_file="$1"
        else
            echo "Error: Invalid argument: $1" >&2
            show_usage_and_exit
        fi
        ;;
    esac
    shift
done

# Validate required arguments
if [ -z "$feature" ]; then
    echo "Error: Specify one feature option: -c, -d, or -r." >&2
    show_usage_and_exit
fi
if [ -z "$method" ]; then
    echo "Error: Specify method using -m (approximate or blast)" >&2
    show_usage_and_exit
fi
if [ -z "$input_file" ]; then
    echo "Error: Specify a file path after the feature option" >&2
    show_usage_and_exit
fi

# Validate file existence and extension
validate_file_exists "$input_file"
extension="${input_file##*.}"
case "$feature" in
chromatic | diatonic | rhythm)
    validate_file_extension "$extension"
    ;;
esac
filename=$(basename "$input_file" .${extension})

# Define temporary directories and check existence
script_dir=$(dirname "$(realpath "$0")")
temp_dir="$script_dir/../tmp"
mkdir -p "$temp_dir"
if [ ! -d "$temp_dir" ]; then
    echo "Error: Failed to create temporary directory."
    exit 1
fi

# Define error log directory and files
mkdir -p $(realpath "$script_dir/../logs")
logs_dir=$(realpath "$script_dir/../logs")
error_log="$logs_dir/error_log.txt"

# Function to analyze rhythm
process_rhythm() {
    local ext="$1"

    if [ "$ext" = "wav" ]; then
        basic-pitch "$temp_dir/" "$input_file" >/dev/null 2>>"$error_log"
        midi_file="$temp_dir/${filename}_basic_pitch.mid"
    else
        midi_file="$input_file"
    fi

    if [ "$method" = "approximate" ]; then
        python3 "$script_dir/feature_format_transformation.py" -r "$midi_file" -m "$method" \
            >"$temp_dir/rhythm_sf_query.txt"
    else
        echo ">${filename}" >"$temp_dir/rhythm_sf_query.fasta"
        python3 "$script_dir/feature_format_transformation.py" -r "$midi_file" -m "$method" \
            >>"$temp_dir/rhythm_sf_query.fasta"
    fi
}

# Function to analyze chromatic or diatonic
process_chromatic_diatonic() {
    local ext="$1"

    if [ "$ext" = "wav" ]; then
        basic-pitch "$temp_dir/" "$input_file" >/dev/null 2>>"$error_log"
        midi_file="$temp_dir/${filename}_basic_pitch.mid"
    else
        midi_file="$input_file"
    fi

    # Convert MIDI to **kern format
    mid2hum "$midi_file" >"$temp_dir/query_kern.krn" 2>>"$error_log"
    validate_file_exists "$temp_dir/query_kern.krn"

    # Clean **kern file
    humsed '/r/d' "$temp_dir/query_kern.krn" >"$temp_dir/query_kern_wor.krn"
    humsed '/-/d' "$temp_dir/query_kern_wor.krn" >"$temp_dir/query_kern_cleaned.krn"
    validate_file_exists "$temp_dir/query_kern_cleaned.krn"

    # Compute diatonic or chromatic analysis
    if [ "$feature" = "diatonic" ]; then
        mint -d "$temp_dir/query_kern_cleaned.krn" >"$temp_dir/query_diatonic_analysis.txt"
        validate_file_exists "$temp_dir/query_diatonic_analysis.txt"
        if [ "$method" = "approximate" ]; then
            python3 "$script_dir/feature_format_transformation.py" \
                -d "$temp_dir/query_diatonic_analysis.txt" \
                -m "$method" >"$temp_dir/diatonic_sf_query.txt"
        else
            echo ">${filename}" >"$temp_dir/diatonic_sf_query.fasta"
            python3 "$script_dir/feature_format_transformation.py" \
                -d "$temp_dir/query_diatonic_analysis.txt" \
                -m "$method" >>"$temp_dir/diatonic_sf_query.fasta"
        fi
    else
        semits -x "$temp_dir/query_kern_cleaned.krn" >"$temp_dir/query_semits.sem"
        validate_file_exists "$temp_dir/query_semits.sem"
        xdelta -s ^= "$temp_dir/query_semits.sem" >"$temp_dir/query_chromatic_analysis.txt"
        validate_file_exists "$temp_dir/query_chromatic_analysis.txt"
        if [ "$method" = "approximate" ]; then
            python3 "$script_dir/feature_format_transformation.py" \
                -c "$temp_dir/query_chromatic_analysis.txt" \
                -m "$method" >"$temp_dir/chromatic_sf_query.txt"
        else
            echo ">${filename}" >"$temp_dir/chromatic_sf_query.fasta"
            python3 "$script_dir/feature_format_transformation.py" \
                -c "$temp_dir/query_chromatic_analysis.txt" \
                -m "$method" >>"$temp_dir/chromatic_sf_query.fasta"
        fi
    fi
}

# Call the appropriate function based on the feature
case "$feature" in
chromatic | diatonic)
    process_chromatic_diatonic "$extension"
    ;;
rhythm)
    process_rhythm "$extension"
    ;;
esac
