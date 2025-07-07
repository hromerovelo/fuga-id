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
 # Created by Hilda Romero-Velo on December 2024.
 '
: '
 # This script executes the necessary processes to compute the score features,
 # prepare the scores data for alignment algorithms, and evaluate the performance
 # of the alignment algorithms with the provided audio recordings. It returns the
 # results in a database and a corresponding analysis report in Excel format.
 '

#!/bin/bash
set -e # Exit immediately if any command fails

# Current script directory
script_dir=$(dirname "$(realpath "$0")")

show_usage() {
  echo "Usage: ./run_folkoteca.sh [-h] [-p]"
  echo "Options:"
  echo "  -h    Show this help message"
  echo "  -p    Use piano dataset"
}

# Parse command line arguments
use_piano=false
while getopts "hp" opt; do
  case $opt in
  h)
    show_usage
    exit 0
    ;;
  p)
    use_piano=true
    ;;
  \?)
    echo "Invalid option: -$OPTARG" >&2
    show_usage
    exit 1
    ;;
  esac
done

# Compile the C++ programs
echo -e "Compiling C++ programs...\n"
mkdir "$script_dir/queries/bin"
g++ -o "$script_dir/queries/bin/approximate_alignment" \
  "$script_dir/queries/src/approximate_alignment.cpp" \
  "$script_dir/queries/src/shared/alignment_utils.cpp" \
  "$script_dir/queries/src/shared/cli_utils.cpp" \
  "$script_dir/queries/src/shared/file_operations.cpp" \
  "$script_dir/queries/src/shared/json_operations.cpp" \
  "$script_dir/queries/src/shared/system_utils.cpp" \
  -std=c++17

g++ -o "$script_dir/queries/bin/blast_alignment" \
  "$script_dir/queries/src/blast_alignment.cpp" \
  "$script_dir/queries/src/shared/cli_utils.cpp" \
  "$script_dir/queries/src/shared/file_operations.cpp" \
  "$script_dir/queries/src/shared/json_operations.cpp" \
  "$script_dir/queries/src/shared/system_utils.cpp" \
  -std=c++17
echo -e "C++ programs compiled successfully.\n\n"

# Process scores to extract features and prepare data for alignment algorithms
echo -e "Processing scores...\n\n"
bash "$script_dir/scores/src/scores_processing.sh"
echo -e "Setup computed successfully.\n\n"

# Store recordings in the database
echo -e "Storing recordings in the database...\n"
if [ "$use_piano" = true ]; then
  python3 "$script_dir/database/insert_recordings.py" --use_piano_set
  AUDIO_FOLDER="$script_dir/queries/data/folkoteca_piano_recordings/"
else
  python3 "$script_dir/database/insert_recordings.py"
  AUDIO_FOLDER="$script_dir/queries/data/folkoteca_audios/"
fi
echo -e "Recordings stored successfully.\n\n"

# Launch evaluation of audio recordings
echo -e "Launching evaluation of audio recordings...\n\n"
python3 "$script_dir/queries/evaluation/evaluate_audio_folder.py" "$AUDIO_FOLDER" -db "$script_dir/database/folkoteca.db"
echo -e "\n\nEvaluation completed successfully.\n\n"

# Analyze the results of the evaluation
echo -e "Analyzing evaluation results...\n"
python3 "$script_dir/database/analyze_results.py"
echo -e "\nResults analyzed successfully.\n\n"

echo -e "Check the results at $script_dir/database/folkoteca_report.xlsx\n"
echo -e "You can access the database at $script_dir/database/folkoteca.db by running 'sqlite3 folkoteca.db'\n"
