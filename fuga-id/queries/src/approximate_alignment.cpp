/**
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
 * @file approximate_alignment.cpp
 * @brief Program to compute approximate alignments between a query and a reference text.
 *
 * This program implements a sequence alignment algorithm using dynamic programming
 * to approximate the best match between a query and a reference text. It supports different
 * search types (-c for chromatic, -d for diatonic, and -r for rhythmic), extracts features
 * from the query, performs alignment, and calculates the alignment score. The program also
 * tracks and records execution and CPU times for feature extraction, alignment, and scoring.
 *
 * Usage:
 *   - Compile the program using a C++ compiler supporting C++11 or later (e.g., g++).
 *     `g++ -o approximate_alignment approximate_alignment.cpp
 *       ../shared/alignment_utils.cpp ../shared/cli_utils.cpp ../shared/data_structures.cpp
 *       ../shared/file_operations.cpp ../shared/json_operations.cpp ../shared/system_utils.cpp`
 *   - Run the executable with the following arguments:
 *     `./approximate_alignment [-c|-d|-r] query_file`
 *
 * Command-line arguments:
 *   - `-c`, `-d`, `-r`: Specify the search type (chromatic, diatonic, or rhythm).
 *   - `query_file`: Path to the query file (WAV for chromatic/diatonic, MIDI for rhythm).
 *
 * Key functionalities:
 *   1. Command-line argument validation.
 *   2. Feature extraction from the query using external scripts.
 *   3. Dynamic programming-based approximate alignment.
 *   4. Alignment scoring and result storage in JSON format.
 *
 * Dependencies:
 *   - A Linux environment supporting `/proc/self/exe` for executable path retrieval.
 *   - Bash shell for executing external scripts.
 *   - Python for running scoring scripts.
 *   - The cost map file for the search type (-c, -d, -r).
 *   - Included scripts for feature extraction and scoring.
 *   - Included alignment_utils.hpp, cli_utils.hpp, data_structures.hpp, file_operations.hpp,
 *     json_operations.hpp, and system_utils.hpp for shared functions.
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
#include <iostream>
#include <vector>
#include <sys/stat.h>
#include "shared/alignment_utils.hpp"
#include "shared/cli_utils.hpp"
#include "shared/data_structures.hpp"
#include "shared/file_operations.hpp"
#include "shared/json_operations.hpp"
#include "shared/system_utils.hpp"

using namespace std;

/**
 * @brief Computes the alignment score between two characters based on a cost map that stores
 * the matrix of match scores and mismatch penalties.
 *
 * @param text_char Character from the text sequence
 * @param query_char Character from the query sequence
 * @param cost_map Map containing mismatch penalties for character pairs
 * @param generic_mismatch Mismatch penalty to be returned if no value is found in the cost_map.
 *
 * @return int Alignment score:
 *         - cost_map match score or penalty if found, otherwise generic_mismatch
 */
float get_alignment_score(const char text_char, const char query_char,
                          const unordered_map<char, unordered_map<char, float>> &cost_map,
                          const int generic_mismatch)
{
    try
    {
        return cost_map.at(text_char).at(query_char);
    }
    catch (const out_of_range &)
    {
        return generic_mismatch;
    }
}

/**
 * @brief Returns the corresponding gap penalty given a search feature.
 *
 * From a given search feature (-c, chromatic; -d, diatonic; -r, rhythm),
 * it returns the related gap penalty for the approximate alignment computation.
 *
 * @param search_feature Search type flag specified by the user (-c, -d, or -r).
 * @return int Integer indicating the gap penalty value for the given feature.
 */
int get_gap_penalty(const string &search_feature)
{
    if (search_feature == "-c")
    {
        return -1;
    }
    else if (search_feature == "-d")
    {
        return -1;
    }
    else
    {
        return -1;
    }
}

/**
 * @brief Updates the top alignments vector with a new alignment result.
 *
 * This function inserts a new alignment result into the top alignments vector while maintaining
 * the descending order of alignment scores. If the vector exceeds the maximum size of 5, the
 * lowest score is removed.
 *
 * @param top_alignments Reference to the vector of top alignment results.
 * @param result The new alignment result to be inserted.
 */
void update_top_alignments(vector<AlignmentResult> &top_alignments, const AlignmentResult &result)
{
    // Find insertion point maintaining descending score order
    auto it = lower_bound(top_alignments.begin(), top_alignments.end(), result,
                          [](const AlignmentResult &a, const AlignmentResult &b)
                          {
                              return a.alignment_score > b.alignment_score;
                          });

    // Insert if we have space or if better than lowest score
    if (top_alignments.size() < 5 || it != top_alignments.end())
    {
        top_alignments.insert(it, result);
        if (top_alignments.size() > 5)
        {
            top_alignments.pop_back();
        }
    }
}

/**
 * @brief Computes the approximate alignment score between a given text and a query string.
 *
 * This function calculates the alignment score between a reference text and a query string
 * using dynamic programming. The algorithm uses a scoring scheme based on matching and mismatching
 * characters to determine the best alignment position. The function returns the Top 5 best aligned
 * musical sheets.
 *
 * @param scores Vector of feature values for each score
 * @param query The query sequence to search for
 * @param cost_map Map containing match scores and mismatch penalties for character pairs
 * @param score_ids Vector of musical sheet IDs
 * @param gap_penalty Gap penalty value for the alignment computation
 *
 * @return vector<AlignmentResult> Vector of the top 5 alignment results with the highest scores.
 */
vector<AlignmentResult> approximate_alignment(
    const vector<string> &scores,
    const string &query,
    const unordered_map<char, unordered_map<char, float>> &cost_map,
    const vector<string> &score_ids,
    const int gap_penalty)
{
    vector<AlignmentResult> top_alignments;
    size_t query_length = query.length();
    vector<Cell> column(query_length + 1);

    for (size_t score_index = 0; score_index < scores.size(); ++score_index)
    {
        const string &score_text = scores[score_index];
        const string &current_score_id = score_ids[score_index];
        size_t score_length = score_text.length();

        float current_max_score = 0;
        pair<size_t, size_t> current_max_position = {0, 0};
        pair<size_t, size_t> current_max_origin = {0, 0};

        // Initialize column of the dynamic programming matrix
        column[0] = {0, 0, 0};
        for (size_t j = 1; j <= query_length; ++j)
        {
            column[j] = {-static_cast<float>(j), 0, j - 1};
        }

        // Compute the distance matrix using dynamic programming
        for (size_t i = 1; i <= score_length; ++i)
        {
            Cell prev_diagonal = column[0];
            column[0].score = 0;
            column[0].text_origin_pos = i - 1;

            for (size_t j = 1; j <= query_length; ++j)
            {
                Cell temp = column[j];
                int align_score = get_alignment_score(score_text[i - 1], query[j - 1], cost_map, gap_penalty);

                int diagonal_score = prev_diagonal.score + align_score;
                int insertion_score = column[j - 1].score + gap_penalty;
                int deletion_score = column[j].score + gap_penalty;

                if (diagonal_score >= insertion_score && diagonal_score >= deletion_score)
                {
                    column[j].score = diagonal_score;
                    column[j].text_origin_pos = prev_diagonal.text_origin_pos;
                    column[j].query_origin_pos = prev_diagonal.query_origin_pos;
                }
                else if (insertion_score >= diagonal_score && insertion_score >= deletion_score)
                {
                    column[j].score = insertion_score;
                    column[j].text_origin_pos = column[j - 1].text_origin_pos;
                    column[j].query_origin_pos = column[j - 1].query_origin_pos;
                }
                else
                {
                    column[j].score = deletion_score;
                    column[j].text_origin_pos = column[j].text_origin_pos;
                    column[j].query_origin_pos = column[j].query_origin_pos;
                }

                prev_diagonal = temp;

                if (column[j].score > current_max_score)
                {
                    current_max_score = column[j].score;
                    current_max_position = {i - 1, j - 1};
                    current_max_origin = {column[j].text_origin_pos, column[j].query_origin_pos};
                }
            }
        }

        // Add last score's alignment if good enough
        if (current_max_score > 0)
        {
            AlignmentResult result{
                current_max_score,
                current_max_origin,
                current_max_position,
                current_score_id};
            update_top_alignments(top_alignments, result);
        }
    }

    return top_alignments;
}

/**
 * @brief Program main entry point to perform approximate alignment between a query and a text.
 *
 * This program reads a query file and a search feature flag from the command line arguments,
 * then performs an approximate alignment between the query and a reference text using several
 * components: extracting features, performing alignment, and locating the score. It tracks
 * the time and CPU usage for each operation and outputs the results as a JSON file.
 *
 * The following operations are performed:
 * 1. Validate the input arguments.
 * 2. Retrieve the reference text and query feature files based on the search type.
 * 3. Extract query features using a shell command and measure the CPU and execution time.
 * 4. Perform the approximate alignment between the query and the reference text.
 * 5. Locate the score for the alignment using a Python script.
 * 6. Save the execution times and results into a JSON file.
 *
 * @param argc The number of command line arguments.
 * @param argv The array of command line arguments.
 * @return int Return value indicating the success (0) or failure (1) of the program.
 */
int main(int argc, char **argv)
{
    string search_feature, query_file, query;
    if (!validate_args(argc, argv, search_feature, query_file, "approximate"))
    {
        return 1;
    }

    string base_dir = get_executable_directory();
    string query_sf_file;
    string text = load_file(get_search_files(base_dir, search_feature, query_sf_file, "approximate"));
    string ids = load_file(base_dir + "/../../scores/indexes/approximate_alignment/melodic_line_ids.txt");

    // Split text and ids into vectors
    vector<string> scores;
    vector<string> score_ids;
    size_t pos = 0;
    string token;
    while ((pos = text.find('\n')) != string::npos)
    {
        token = text.substr(0, pos);
        scores.push_back(token);
        text.erase(0, pos + 1);
    }
    scores.push_back(text); // Add the last score

    pos = 0;
    while ((pos = ids.find('\n')) != string::npos)
    {
        token = ids.substr(0, pos);
        score_ids.push_back(token);
        ids.erase(0, pos + 1);
    }
    score_ids.push_back(ids); // Add the last id

    // Define the shell commands for extracting query features and cleaning temporary files.
    string extract_query_features = base_dir + "/../src/extract_query_feature.sh";
    string clean_tmp = base_dir + "/../utils/clean_tmp.sh";
    string features_command = "bash " + extract_query_features + " " + search_feature + " " +
                              query_file + " -m approximate";
    string clean_command = "bash " + clean_tmp;

    // Measure the time taken to extract features from the query.
    double extract_feature_user_time, extract_feature_system_time;
    long extract_feature_clock_time;
    measure_time_and_cpu([&]()
                         { query = launch_command(features_command, query_sf_file); },
                         false, extract_feature_user_time, extract_feature_system_time,
                         extract_feature_clock_time, true);
    if (query == "ERROR") // If feature extraction fails, clean up and exit with failure.
    {
        system(clean_command.c_str());
        return EXIT_FAILURE;
    }

    string cost_map_file = get_cost_map_file(base_dir, search_feature);

    unordered_map<char, unordered_map<char, float>> cost_map = load_cost_map(cost_map_file);
    int gap_penalty = get_gap_penalty(search_feature);

    // Measure the time taken for approximate alignment between the query and text.
    double align_user_time, align_system_time;
    long align_clock_time;
    vector<AlignmentResult> top_alignments;
    measure_time_and_cpu([&]()
                         { top_alignments = approximate_alignment(scores, query, cost_map, score_ids, gap_penalty); },
                         true, align_user_time, align_system_time, align_clock_time, false);

    // Save the timing results and retrieved score into a JSON file.
    string results_dir = base_dir + "/../data/results";
    mkdir(results_dir.c_str(), 0755);
    save_result_and_timing_to_json(
        top_alignments, query, extract_feature_user_time, extract_feature_system_time, extract_feature_clock_time,
        align_user_time, align_system_time, align_clock_time, results_dir + "/score_and_timing_results.json");

    // Clean up temporary files.
    system(clean_command.c_str());

    return 0;
}
