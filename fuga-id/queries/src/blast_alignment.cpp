/***
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
**/

//
// Created by Hilda Romero-Velo on November 2024.
//

/**
 * @file blast_alignment.cpp
 * @brief This program performs feature extraction and BLAST alignment for a given query file.
 *
 * The program processes a query file (WAV or MIDI) and searches for the best alignments in a
 * pre-defined database using a BLAST-like algorithm. It measures and records execution timing
 * for the feature extraction and alignment steps, and saves the results and timing statistics
 * to a JSON file.
 *
 * Usage:
 *   - Compile the program using a C++ compiler with the required libraries (e.g., g++).
 *   - Run the executable with the following arguments:
 *     `./blast_alignment [-c|-d|-r] query_file`
 *
 * Command-line arguments:
 *   - `-c`, `-d`, `-r`: Specify the search type (chromatic, diatonic, or rhythm).
 *   - `query_file`: Path to the query file (WAV for chromatic/diatonic, MIDI for rhythm).
 *
 * Functionality:
 *   1. Validates and parses command-line arguments.
 *   2. Extracts features from the query file based on the selected search type.
 *   3. Performs a BLAST alignment using the extracted features.
 *   4. Measures real, user, and system CPU times for both feature extraction and alignment.
 *   5. Generates a JSON file containing the scores retrieved from the alignment and the timing data.
 *   6. Handles error scenarios and cleans up temporary files.
 *
 * Dependencies:
 *   - Requires BLAST tools and bash scripts for feature extraction.
 *   - Outputs the results in JSON format.
 *
 * Notes:
 *   - Ensure the required files and directories are in place before execution.
 *   - Make sure the necessary permissions are granted for executing shell scripts.
 *
 * Outputs:
 * - Results and timing data are saved in JSON format.
 *
 * @author Hilda Romero-Velo
 * @date 2024-11-19
 * @version 1.0
 */

#include <algorithm>
#include <fstream>
#include <iostream>
#include <string>
#include <sstream>
#include <sys/stat.h>
#include <unordered_map>
#include <vector>
#include "shared/cli_utils.hpp"
#include "shared/data_structures.hpp"
#include "shared/file_operations.hpp"
#include "shared/json_operations.hpp"
#include "shared/system_utils.hpp"

using namespace std;

/**
 * @brief Reads the scores from the specified file and returns the top N unique sseqid
 *        ordered by bitscore in descending order. Duplicates are removed.
 *
 * @param score_results_file File containing the alignment results (sseqid and bitscore).
 * @return A vector of unique sseqid ordered by bitscore in descending order.
 */
vector<AlignmentResult> read_scores_from_file(const string &score_results_file)
{
    unordered_map<string, AlignmentResult> best_alignments; // Map to track the best alignment for each sseqid
    ifstream score_file(score_results_file);
    if (!score_file)
    {
        cerr << "Error: Could not open score file " << score_results_file << endl;
        return {};
    }

    string line;
    while (getline(score_file, line))
    {
        istringstream iss(line);
        string sseqid;
        double bitscore;
        int qstart, qend, sstart, send;

        // Parse the sseqid, bitscore, qstart, qend, sstart, send
        if (!(iss >> sseqid >> bitscore >> qstart >> qend >> sstart >> send))
        {
            cerr << "Warning: Skipping malformed line: " << line << endl;
            continue;
        }

        // Check if this sseqid already has an entry, and keep the one with the highest bitscore
        if (best_alignments.find(sseqid) == best_alignments.end() ||
            best_alignments[sseqid].alignment_score < bitscore)
        {
            best_alignments[sseqid] = AlignmentResult{
                static_cast<float>(bitscore),
                {sstart, qstart}, // Origin positions (text, query)
                {send, qend},     // Ending positions (text, query)
                sseqid            // Sequence ID
            };
        }
    }
    score_file.close();

    // Create a vector from the map to sort the results by bitscore
    vector<AlignmentResult> sorted_alignments;
    for (const auto &entry : best_alignments)
    {
        sorted_alignments.push_back(entry.second);
    }

    // Sort alignments by bitscore in descending order
    sort(sorted_alignments.begin(), sorted_alignments.end(),
         [](const AlignmentResult &a, const AlignmentResult &b)
         {
             return a.alignment_score > b.alignment_score;
         });

    // Keep only the top 5 alignments
    if (sorted_alignments.size() > 5)
    {
        sorted_alignments.resize(5);
    }

    return sorted_alignments;
}

/**
 * @brief Main entry point of the program.
 *
 * This program handles the processing of command-line arguments, manages the execution of
 * shell commands for feature extraction and BLAST alignment, and collects timing statistics
 * for each of these operations. It also generates a JSON report with scores retrieved during
 * the alignment and with timing information.
 *
 * The program expects two command-line arguments:
 * 1. A search type flag (`-c`, `-d`, or `-r`) indicating the type of search to perform
 *    (chromatic, diatonic, or rhythm).
 * 2. The path to the query file, which can be either a WAV file (for chromatic and diatonic)
 *    or a MIDI file (for rhythm).
 *
 * The main steps in the program include:
 * - Validating and parsing the command-line arguments.
 * - Extracting features from the query file based on the selected search type.
 * - Running a BLAST search on the extracted features against a pre-defined database.
 * - Collecting timing statistics for feature extraction and alignment processes.
 * - Generating a JSON file with the top N scores and timing results.
 *
 * If any step fails, the program cleans up temporary files and exits with an error code.
 *
 * @param argc The number of command-line arguments passed to the program.
 * @param argv An array of command-line argument strings.
 *             argv[1] should specify the search type (`-c`, `-d`, or `-r`), and argv[2]
 *             should specify the query file.
 *
 * @return int 0 if the program executed successfully, non-zero if an error occurred.
 */
int main(int argc, char **argv)
{
    string search_feature, query_file;
    if (!validate_args(argc, argv, search_feature, query_file, "blast"))
    {
        return 1;
    }

    // Prepare the paths for query features and the appropriate database based on the search type
    string base_dir = get_executable_directory();
    string query_sf_file;
    string db = get_search_files(base_dir, search_feature, query_sf_file, "blast");

    // Define the shell commands for extracting query features and cleaning temporary files.
    string extract_query_features = base_dir + "/../src/extract_query_feature.sh";
    string clean_tmp = base_dir + "/../utils/clean_tmp.sh";
    string features_command = "bash " + extract_query_features + " " + search_feature + " " +
                              query_file + " -m blast";
    string clean_command = "bash " + clean_tmp;

    // Measure the time taken to extract features from the query.
    double extract_feature_user_time, extract_feature_system_time;
    long extract_feature_clock_time;
    string file_content;
    measure_time_and_cpu([&]()
                         { file_content = launch_command(features_command, query_sf_file); },
                         false, extract_feature_user_time, extract_feature_system_time,
                         extract_feature_clock_time, true);
    if (file_content == "ERROR") // If feature extraction fails, clean up and exit with failure.
    {
        system(clean_command.c_str());
        return EXIT_FAILURE;
    }

    // Split the file content by lines and get the second line (the query in FASTA format)
    istringstream file_stream(file_content);
    string query;
    getline(file_stream, query);      // Skip the first line (sseqid)
    if (!getline(file_stream, query)) // Get the second line (query)
    {
        system(clean_command.c_str());
        return EXIT_SUCCESS;
    }

    // Check if query is empty
    if (query.empty())
    {
        system(clean_command.c_str());
        return EXIT_SUCCESS;
    }

    // Prepare BLAST command and results directory.
    string results_dir = base_dir + "/../data/results";
    mkdir(results_dir.c_str(), 0755);
    string score_results_file = results_dir + "/score_results.txt";

    string blast_command = "blastp -query " + query_sf_file +
                           " -db " + db +
                           " -word_size 2 " +
                           " -matrix IDENTITY " +
                           " -max_target_seqs 5 " +
                           " -comp_based_stats 0 " +
                           " -evalue 1e5 " +
                           " -outfmt \"6 sseqid bitscore qstart qend sstart send\" " +
                           " -out " + score_results_file;

    // Measure the time taken to compute the BLAST alignment.
    double blast_user_time, blast_system_time;
    long blast_clock_time;
    string success;
    measure_time_and_cpu([&]()
                         { success = launch_command(blast_command); },
                         true, blast_user_time, blast_system_time,
                         blast_clock_time, true);

    // If BLAST fails or results file is not generated, clean up and exit
    if (success == "ERROR" || !file_exists(score_results_file))
    {
        system(clean_command.c_str());
        return EXIT_FAILURE;
    }

    vector<AlignmentResult> top_sseqids = read_scores_from_file(score_results_file);

    // Save the timing results and retrieved scores into a JSON file.
    save_result_and_timing_to_json(
        top_sseqids, query, extract_feature_user_time, extract_feature_system_time,
        extract_feature_clock_time, blast_user_time, blast_system_time,
        blast_clock_time, results_dir + "/score_and_timing_results.json");

    delete_file(score_results_file);

    // Clean up temporary files after the program finishes.
    system(clean_command.c_str());
    return EXIT_SUCCESS;
}