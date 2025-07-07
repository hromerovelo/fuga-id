: '
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
 '

: '
 # Created by Hilda Romero-Velo on August 2023.
 '

: ' 
 # This script separates the different spines and voices of each score in **kern format
 # into individual files. It extracts staves from the notes **kern corpus, expands the voices,
 # adjusts them, and removes grace notes to create a final prepared **kern corpus. 
 '

#!/bin/bash

# Directory where the current script is located
script_dir=$(dirname "$(realpath "$0")")

# Data directory and directory of the just notes **kern corpus
data_dir=$(realpath "$script_dir/../../../data")
corpus_kern_dir="$data_dir/computed/scores/scores_kern"
notes_kern="$corpus_kern_dir/notes_kern"

# Error log file
logs_dir=$(realpath "$script_dir/../logs")
error_log="$logs_dir/error_log.txt"

# Extracting each spine to a single file
mkdir -p "$corpus_kern_dir/staves_kern"
staves_kern="$corpus_kern_dir/staves_kern"

echo "Extracting staves..."
for FILE in "$notes_kern"/*; do
  filename=$(basename "$FILE" .krn)
  staves=$(extractx -C "$FILE")

  # Check if any staves were found
  if test -n "$staves"; then
    for ((i = 1; i <= $staves; i++)); do
      extractx -s "$i" "$FILE" >"$staves_kern/${filename}_$i.krn"
    done
  else
    echo "extend_courpus.sh: No staves found in $filename." >>"$error_log"
  fi
done
echo "Staves extracted."

# Extend voices so that each one is stored in one spine
mkdir -p "$corpus_kern_dir/extended_kern"
extended_kern="$corpus_kern_dir/extended_kern"

echo "Expanding staves..."
for FILE in "$staves_kern"/*; do
  filename=$(basename "$FILE" .krn)
  extractx -e "$FILE" >"$extended_kern/${filename}_e.krn"

  # Check if the expansion was successful
  if [ $? -ne 0 ]; then
    echo "extend_courpus.sh: Error expanding $FILE." >>"$error_log"
  fi
done
echo "Staves expanded."

# Extracting each new spine to a single file again
mkdir -p "$corpus_kern_dir/staves_prepared"
staves_prepared="$corpus_kern_dir/staves_prepared"

echo "Adjusting staves..."
for FILE in "$extended_kern"/*; do
  filename=$(basename "$FILE" .krn)
  staves=$(extractx -C "$FILE")

  # Check if any staves were found
  if test -n "$staves"; then
    for ((i = 1; i <= $staves; i++)); do
      extractx -s "$i" "$FILE" >"$staves_prepared/${filename}_$i.krn"
    done
  else
    echo "extend_courpus.sh: No staves found in $filename during adjustment." >>"$error_log"
  fi
done
echo "Staves adjusted."

# Removing grace notes to achieve the final **kern prepared corpus
mkdir -p "$corpus_kern_dir/kern_prepared"
kern_prepared="$corpus_kern_dir/kern_prepared"

echo "Removing grace notes..."
for FILE in "$staves_prepared"/*; do
  filename=$(basename "$FILE")
  humsed '/qq/d' "$FILE" >"$kern_prepared/$filename"

  # Check if the removal of grace notes was successful
  if [ $? -ne 0 ]; then
    echo "extend_courpus.sh: Error removing grace notes from $FILE." >>"$error_log"
  fi
done
echo "Grace notes removed."
