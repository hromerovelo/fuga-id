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
 # This script converts the selected set of scores from MusicXML to **kern format.
 # It cleans the **kern files by removing unnecessary information, retaining only the notes.
 '

#!/bin/bash

# Directory where the current script is located
script_dir=$(dirname "$(realpath "$0")")

# Data directory, directory of the original MusicXML corpus and
# directory of the original MEI corpus.
data_dir=$(realpath "$script_dir/../../../data")
musicxml_corpus_dir="$data_dir/origin/scores_musicxml"
mei_corpus_dir="$data_dir/origin/scores_mei"

# Directory for all **kern format computations
mkdir -p "$data_dir/computed/scores/scores_kern"
corpus_kern_dir="$data_dir/computed/scores/scores_kern"

# Directory with raw translation of the corpus from MusicXML/MEI format to **kern
mkdir -p "$corpus_kern_dir/raw_kern"
raw_kern="$corpus_kern_dir/raw_kern"

# **kern corpus without *clefX, **dynam and **text column. Just notes are kept.
mkdir -p "$corpus_kern_dir/notes_kern"
notes_kern="$corpus_kern_dir/notes_kern"

# Error log directory and files
mkdir -p $(realpath "$script_dir/../logs")
logs_dir=$(realpath "$script_dir/../logs")
error_log="$logs_dir/error_log.txt"
musicxml_error_log="$logs_dir/musicxml2hum_error_log.txt"

# Clean error log files
>"$error_log"
>"$musicxml_error_log"

echo "Performing MusicXML corpus conversion..."
# MusicXML to **kern transformation
for FILE in "$musicxml_corpus_dir"/*; do
  filename=$(basename "$FILE" .musicxml)
  musicxml2hum "$FILE" >"$raw_kern"/"$filename".krn 2>>"$musicxml_error_log"

  # Check if the conversion was successful
  if [ $? -ne 0 ]; then
    echo "corpus_to_kern.sh: Error converting $FILE to **kern format." >>"$error_log"
  fi
done
echo "MusicXML corpus converted to kern."

# Cleaning **kern file
echo "Removing unnecessary information from kern files..."
for FILE in "$raw_kern"/*; do
  filename=$(basename "$FILE")
  extractx -I "*clefX, **dynam, **text, **mxhm" "$FILE" >"$notes_kern"/"$filename"

  # Check if the cleaning was successful
  if [ $? -ne 0 ]; then
    echo "corpus_to_kern.sh: Error cleaning $FILE." >>"$error_log"
  fi
done
echo "Kern files cleared."
