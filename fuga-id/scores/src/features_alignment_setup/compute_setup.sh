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
 # This script generates dictionaries related to the features of the scores for both 
 # approximate alignment and BLAST algorithms by calling 'generate_dict_from_freq.py'. 
 # It also executes 'compute_approx_alignment_files.py' and 'compute_blast_files.py' 
 # to prepare the necessary files for future alignment processes based on these features.
 '

#!/bin/bash

# Directory where the current script is located
script_dir=$(dirname "$(realpath "$0")")

# Data directory, common directory and dicts directory
data_dir=$(realpath "$script_dir/../../data")
common_dir=$(realpath "$script_dir/../../../common")
mkdir -p "$common_dir/dicts"
dicts_dir="$common_dir/dicts"

# Directory where scripts and Python files to setup features are located
setup_scripts_dir="$script_dir/setup_scripts"

# Function to run a Python script and check for errors
run_python_script() {
  local script_name="$1"
  shift
  python3 "$setup_scripts_dir/$script_name" "$@"
  if [ $? -ne 0 ]; then
    echo "Error running $script_name."
    exit 1
  fi
}

# Generate the feature values frequency analysis
echo "Computing feature values frequency analysis..."
run_python_script "generate_dict_from_freq.py" \
  -f all \
  -fa True \
  -o "$data_dir/computed/features/corpus_jsons/"
echo "Feature values frequency analysis computed."

# Generate dictionaries for Approximate Alignment
echo "Generating Approximate Alignment dictionary..."
run_python_script "generate_dict_from_freq.py" \
  -f all \
  -o "$data_dir/computed/features/corpus_jsons/" \
  -tf "$dicts_dir/approx_dictionary.py" \
  -al approximate
echo "Approximate Alignment dictionary generated."

# Generate dictionaries for BLAST
echo "Generating BLAST dictionary..."
run_python_script "generate_dict_from_freq.py" \
  -f all \
  -o "$data_dir/computed/features/corpus_jsons/" \
  -tf "$dicts_dir/blast_dictionary.py"
echo "BLAST dictionary generated."

# Compute Approximate Alignment text files and cost maps binary files
echo "Computing Approximate Alignment files..."
run_python_script "compute_approx_alignment_files.py"
echo "Approximate Alignment files computed successfully."

# Compute BLAST FSA files
echo "Computing BLAST FSA files..."
run_python_script "compute_blast_files.py"
echo "BLAST FSA files computed successfully."
