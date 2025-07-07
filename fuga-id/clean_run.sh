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
 # This script removes all files generated during the execution of the 
 # run_fuga-id.sh script. It includes those generated during the evaluation
 # process as well as the compiled C++ programs and error logs.
 '

#!/bin/bash

# Directory where the current script is located
script_dir=$(dirname "$(realpath "$0")")

# Remove evaluation files
echo -e "Removing files generated during the evaluation process...\n\n"
bash "$script_dir/queries/utils/cleanup_queries.sh"
echo -e "Evaluation files removed successfully.\n\n"

# Remove scores files
echo -e "Removing files generated during the scores processing...\n\n"
bash "$script_dir/scores/utils/cleanup_scores_processing.sh"
echo -e "Scores files removed successfully.\n\n"

# List of directories and files to be deleted, using absolute paths
paths_to_delete=(
    "$(realpath "$script_dir/queries/bin")"                    # Directory containing compiled C++ programs
    "$(realpath "$script_dir/database/folkoteca_report.xlsx")" # Excel report file
    "$(realpath "$script_dir/database/failed_inserts.log")"    # Log file for failed inserts
)

echo -e "Removing compiled C++ programs and error logs...\n\n"

# Loop through each path and delete if it exists
for path in "${paths_to_delete[@]}"; do
    # Check if the path exists (can be either a file or directory)
    if [ -e "$path" ]; then
        rm -rf "$path"                 # Delete directory or file recursively and forcefully
        echo "$path has been deleted." # Confirmation message
    fi
done

# Remove any error_log.txt files in the current directory and its subdirectories
find "$script_dir" -type f -name "error_log.txt" -exec rm -f {} +

echo -e "Compilation files and error logs removed successfully.\n\n"

# Notify the user that cleanup is complete
echo -e "Cleanup completed.\n\n"
