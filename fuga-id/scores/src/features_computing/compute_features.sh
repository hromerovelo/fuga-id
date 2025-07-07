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
 # Created by Hilda Romero-Velo on May 2024.
 '

: ' 
 # This script runs the necessary scripts to compute the features (diatonic, 
 # chromatic, and rhythmic) of the scores and to save them in JSON files. 
 '

#!/bin/bash

# Directory where the current script is located
script_dir=$(dirname "$(realpath "$0")")

# Directory where scripts and Python files to compute features are located
base_dir="$script_dir/features_scripts"

# Function to run scripts and check for success
run_script() {
    local script_path="$1"
    local script_name=$(basename "$script_path")
    echo "Running $script_name script..."
    bash "$script_path"

    # Check if the previous script executed successfully
    if [ $? -ne 0 ]; then
        echo "Error running $script_name script."
        exit 1
    fi

    echo -e "$script_name execution completed.\n"
}

# Execute the scripts in sequence
run_script "$base_dir/corpus_to_kern.sh"
run_script "$base_dir/extend_corpus.sh"
run_script "$base_dir/extract_features.sh"

# Execute process_features.py file
echo "Running process_features.py script..."
python3 "$base_dir/process_features.py"

# Check if the previous script executed successfully
if [ $? -ne 0 ]; then
    echo "Error running process_features.py script."
    exit 1
fi

echo -e "process_features.py execution completed.\n"
