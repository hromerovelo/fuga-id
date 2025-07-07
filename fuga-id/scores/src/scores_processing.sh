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
 # This script executes the necessary processes to compute the score features, 
 # sets up the corresponding files for computing an Approximate Alignment, 
 # and generates the related BLAST databases for future alignments.
 '

#!/bin/bash
set -e # Exit immediately if any command fails

# Current script directory
script_dir=$(dirname "$(realpath "$0")")

# Directory for the database
database_directory="$script_dir/../../database"

# Generate the SQLite database/
echo -e "Generating database..."
sqlite3 "$database_directory/folkoteca.db" <"$database_directory/generate_database.sql"
echo -e "Database generated successfully.\n\n"

# Directory containing the scripts and Python files for computing features
features_computing_directory="$script_dir/features_computing"

# Execute features computation script
echo "Computing features..."
bash "$features_computing_directory/compute_features.sh"
echo -e "Features computed successfully.\n\n"

# Directory containing the scripts and Python files for setting up feature alignment
features_alignment_setup_directory="$script_dir/features_alignment_setup"

# Execute compute_setup.sh file to prepare for feature alignment
echo "Setting up files for Approximate Alignment and BLAST configuration..."
bash "$features_alignment_setup_directory/compute_setup.sh"
echo -e "Setup computed successfully.\n\n\n"

# Generating BLAST databases for each feature
echo "Generating BLAST databases for each feature..."

# Change to the blast indexes directory
cd "$script_dir/../indexes/blast/"

# Create a BLAST database for the Diatonic feature
echo "...Generating Diatonic database..."
# The makeblastdb command creates a BLAST database from the specified FASTA file.
# -in: Input file containing the sequences (diatonic.fsa).
# -dbtype: Type of database to create (prot indicates a protein database).
# -out: Name of the output database (diatonic_db).
makeblastdb -in diatonic.fsa -dbtype prot -out diatonic_db
echo -e "Diatonic database generated.\n\n"

# Create a BLAST database for the Chromatic feature
echo "...Generating Chromatic database..."
makeblastdb -in chromatic.fsa -dbtype prot -out chromatic_db
echo -e "Chromatic database generated.\n\n"

# Create a BLAST database for the Rhythm feature
echo "...Generating Rhythm database..."
makeblastdb -in rhythm.fsa -dbtype prot -out rhythm_db
echo -e "Rhythm database generated.\n\n"

# Final message indicating all databases have been generated
echo "All BLAST databases generated successfully."
