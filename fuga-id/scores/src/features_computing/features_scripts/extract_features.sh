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
 # This script conducts diatonic, chromatic, and rhythmic analysis of scores in  
 # **kern format, taking advantage of the Humdrum toolkit.
 '

#!/bin/bash

# Directory where the current script is located
script_dir=$(dirname "$(realpath "$0")")

# Data directory and directory of the **kern prepared corpus
data_dir=$(realpath "$script_dir/../../../data")
corpus_kern_dir="$data_dir/computed/scores/scores_kern"
kern_prepared="$corpus_kern_dir/kern_prepared"

# Create a directory for corpus analysis results
mkdir -p "$data_dir/computed/features/corpus_analysis"
corpus_analysis="$data_dir/computed/features/corpus_analysis"

# Diatonic and rhythmic analysis folders
mkdir -p "$corpus_analysis/diatonic_analysis"
diatonic_analysis="$corpus_analysis/diatonic_analysis"

mkdir -p "$corpus_analysis/rhythmic_analysis"
rhythmic_analysis="$corpus_analysis/rhythmic_analysis"

# Corpus in semits (semitones) format to compute chromatic analysis
mkdir -p "$data_dir/computed/scores/scores_kern/corpus_semits"
corpus_semits="$data_dir/computed/scores/scores_kern/corpus_semits"

echo "Diatonic and rhythmic analysis ongoing..."

# Iterate over each prepared kern file for analysis
for FILE in "$kern_prepared"/*; do
  filename=$(basename "$FILE" .krn)

  # Diatonic analysis: Analyze the diatonic features of the score
  mint -d "$FILE" >"$diatonic_analysis/${filename}_diatonic.txt"

  # Rhythmic analysis: Analyze the rhythmic features of the score
  beat -d -f -p -A 0 "$FILE" >"$rhythmic_analysis/${filename}_rhythmic.txt"

  # Conversion to semits for chromatic analysis: Convert kern to semitone representation
  semits -x "$FILE" >"$corpus_semits/${filename}.sem"
done

echo "Diatonic and rhythmic analysis completed."

# Chromatic analysis
echo "Chromatic analysis ongoing..."

# Create a directory for prepared semit files
mkdir "$data_dir/computed/scores/scores_kern/corpus_semits_prepared"
corpus_semits_prepared="$data_dir/computed/scores/scores_kern/corpus_semits_prepared"

# Remove rests from semit files to prepare for chromatic analysis
for FILE in "$corpus_semits"/*; do
  filename=$(basename "$FILE")
  # Removing rests to compute chromatic distance
  humsed '/r/d' "$FILE" >"$corpus_semits_prepared/$filename"
done

# Create a directory for chromatic analysis results
mkdir "$corpus_analysis/chromatic_analysis"
chromatic_analysis="$corpus_analysis/chromatic_analysis"

# Perform chromatic analysis
for FILE in "$corpus_semits_prepared"/*; do
  filename=$(basename "$FILE" .sem)
  # Compute chromatic distance and output to text file
  xdelta -s ^= "$FILE" >"$chromatic_analysis/${filename}_chromatic.txt"
done

echo "Chromatic analysis completed."
