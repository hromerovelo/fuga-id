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
// Created by Hilda Romero-Velo on December 2024.
//

#include "json_operations.hpp"
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>

using namespace std;

/**
 * @brief Generates the "alignment" section of the JSON file.
 *
 * This function takes a vector of results and formats them into a JSON array string representation.
 *
 * @param results A vector containing the alignment results.
 * @return A string representing the "alignment" section of the JSON file.
 */
string generate_results_json(const vector<AlignmentResult> &results)
{
    stringstream results_json;
    results_json << "  \"alignment\": {\n";

    // Score IDs array
    results_json << "    \"score_ids\": [";
    if (!(results.size() == 0 || (results.size() == 1 && results[0].retrieved_score_id.empty())))
    {
        for (size_t i = 0; i < results.size(); ++i)
        {
            results_json << (i == 0 ? "\n      \"" : ",\n      \"")
                         << results[i].retrieved_score_id << "\"";
        }
    }
    results_json << "\n    ],\n";

    // Alignment scores array
    results_json << "    \"scores\": [";
    for (size_t i = 0; i < results.size(); ++i)
    {
        results_json << (i == 0 ? "\n      " : ",\n      ")
                     << results[i].alignment_score;
    }
    results_json << "\n    ],\n";

    // Score origin positions
    results_json << "    \"score_origin_pos\": [";
    for (size_t i = 0; i < results.size(); ++i)
    {
        results_json << (i == 0 ? "\n      " : ",\n      ")
                     << results[i].origin_position.first;
    }
    results_json << "\n    ],\n";

    // Query origin positions
    results_json << "    \"query_origin_pos\": [";
    for (size_t i = 0; i < results.size(); ++i)
    {
        results_json << (i == 0 ? "\n      " : ",\n      ")
                     << results[i].origin_position.second;
    }
    results_json << "\n    ],\n";

    // Score end positions
    results_json << "    \"score_end_pos\": [";
    for (size_t i = 0; i < results.size(); ++i)
    {
        results_json << (i == 0 ? "\n      " : ",\n      ")
                     << results[i].end_position.first;
    }
    results_json << "\n    ],\n";

    // Query end positions
    results_json << "    \"query_end_pos\": [";
    for (size_t i = 0; i < results.size(); ++i)
    {
        results_json << (i == 0 ? "\n      " : ",\n      ")
                     << results[i].end_position.second;
    }
    results_json << "\n    ]\n";

    results_json << "  },\n";
    return results_json.str();
}

/**
 * @brief Generates the "timing" section of the JSON file.
 *
 * This function takes timing data for the feature extraction and alignment steps
 * and formats them into the appropriate JSON structure.
 *
 * @param extract_features_user_time_ms User time for the feature extraction step in ms.
 * @param extract_features_system_time_ms System time for the feature extraction step in ms.
 * @param extract_features_clock_time_ms Total clock time for the feature extraction step in ms.
 * @param alignment_user_time_ms User time for the alignment step in ms.
 * @param alignment_system_time_ms System time for the alignment step in ms.
 * @param alignment_clock_time_ms Total clock time for the alignment step in ms.
 * @return A string representing the "timing" section of the JSON file.
 */
std::string generate_timing_json(
    double extract_features_user_time_ms,
    double extract_features_system_time_ms,
    long extract_features_clock_time_ms,
    double alignment_user_time_ms,
    double alignment_system_time_ms,
    long alignment_clock_time_ms)
{
    stringstream timing_json;
    timing_json << "  \"timing\": {\n";
    timing_json << "    \"feature_extraction\": {\n";
    timing_json << "      \"user_time_ms\": " << extract_features_user_time_ms << ",\n";
    timing_json << "      \"system_time_ms\": " << extract_features_system_time_ms << ",\n";
    timing_json << "      \"clock_time_ms\": " << extract_features_clock_time_ms << "\n";
    timing_json << "    },\n";
    timing_json << "    \"alignment\": {\n";
    timing_json << "      \"user_time_ms\": " << alignment_user_time_ms << ",\n";
    timing_json << "      \"system_time_ms\": " << alignment_system_time_ms << ",\n";
    timing_json << "      \"clock_time_ms\": " << alignment_clock_time_ms << "\n";
    timing_json << "    }\n";
    timing_json << "  }\n";
    return timing_json.str();
}

/**
 * @brief Saves timing information and the results of alignment to a JSON file.
 *
 * This function generates a JSON file containing the extracted timing data for each stage
 * (feature extraction and alignment) and writes it to the specified filename.
 * Each timing entry includes user time, system time, and total clock time for that step.
 *
 * @param results Vector containing the results from the alignment.
 * @param query The query string used for alignment.
 * @param extract_features_user_time_ms User time in ms for feature extraction step.
 * @param extract_features_system_time_ms System time in ms for feature extraction step.
 * @param extract_features_clock_time_ms Total clock time in ms for feature extraction step.
 * @param alignment_user_time_ms User time in ms for alignment step.
 * @param alignment_system_time_ms System time in ms for alignment step.
 * @param alignment_clock_time_ms Total clock time in ms for alignment step.
 * @param filename Name of the output file where JSON data is saved.
 */
void save_result_and_timing_to_json(
    const std::vector<AlignmentResult> &results,
    const std::string &query,
    double extract_features_user_time_ms,
    double extract_features_system_time_ms,
    long extract_features_clock_time_ms,
    double alignment_user_time_ms,
    double alignment_system_time_ms,
    long alignment_clock_time_ms,
    const std::string &filename)
{
    ofstream output_file(filename, ios::trunc);
    if (!output_file)
    {
        throw runtime_error("Could not open file: " + filename);
    }
    output_file << fixed << setprecision(3);

    // Generate complete JSON structure
    stringstream json_output;
    json_output << "{\n";
    json_output << "  \"query\": \"" << query << "\",\n";

    // Add alignment section
    json_output << generate_results_json(results);

    // Add timing section
    json_output << generate_timing_json(
        extract_features_user_time_ms,
        extract_features_system_time_ms,
        extract_features_clock_time_ms,
        alignment_user_time_ms,
        alignment_system_time_ms,
        alignment_clock_time_ms);

    // Write the complete JSON to file
    json_output << "}\n"; // Ensure proper closing of the JSON object
    output_file << json_output.str();
    output_file.close();
}
