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
// Created by Hilda Romero-Velo on December 2024.
//

/**
 * @file global_approximate_alignment.cpp
 * @brief Program to compute global approximate alignments between two score features.
 *
 * This program implements a sequence alignment algorithm using dynamic programming
 * to approximate the best match between two score features. It supports different
 * feature types (chromatic, diatonic, rhythmic) and computes the global alignment distance
 * between the two provided score features sequences. It uses a cost map to store the matrix
 * of match scores and mismatch penalties and calculates the alignment score based on this map.
 *
 * Usage:
 *   - Compile the program using a C++ compiler supporting C++11 or later (e.g., g++).
 *     `g++ -o global_approximate_alignment global_approximate_alignment.cpp
 *      ../queries/src/shared/alignment_utils.cpp ../queries/src/shared/system_utils.cpp
 *      ../queries/src/shared/file_operations.cpp -std=c++11`
 *   - Run the executable with the following arguments:
 *     `./global_approximate_alignment first_score_feature second_score_feature -f <feature>`
 *
 * Command-line arguments:
 *   - `first_score_feature`: String of characters for the first score feature to be compared.
 *   - `second_score_feature`: String of characters for the second score feature to be compared.
 *   - `-f <feature>`: Feature type (chromatic, diatonic, rhythmic).
 *
 * Key functionalities:
 *   1. Command-line argument validation.
 *   2. Cost map loading and gap penalty calculation based on the feature type.
 *   3. Global alignment distance computation between two score features.
 *
 * Dependencies:
 *   - A Linux environment supporting `/proc/self/exe` for executable path retrieval.
 *   - The cost map file for the feature type (chromatic, diatonic, rhythmic).
 *   - Included alignment_utils.hpp and system_utils.hpp for shared functions.
 *
 * Output:
 *  - The global alignment distance between the two provided score features printed to the console.
 *
 * @author Hilda Romero-Velo
 * @date 2024-12-29
 * @version 1.0
 */

#include <string>
#include <iostream>
#include <algorithm>
#include <vector>
#include <fstream>
#include <numeric>
#include <sstream>
#include "../queries/src/shared/alignment_utils.hpp"
#include "../queries/src/shared/system_utils.hpp"

using namespace std;

/**
 * @brief Function to compute the minimum of three integers.
 *
 * @param a First integer to compare.
 * @param b Second integer to compare.
 * @param c Third integer to compare.
 *
 * @return int The minimum value between the three integers.
 */
int min_of_three(int a, int b, int c)
{
    return min(min(a, b), c);
}

/**
 * @brief Returns the gap penalty value based on the feature type.
 *
 * From a given feature type (chromatic, diatonic, rhythmic),
 * it returns the related gap penalty.
 *
 * @param feature_type Feature type (chromatic, diatonic, rhythmic).
 * @return float Gap penalty value for the given feature type.
 */
float get_gap_penalty(const string &feature_type)
{
    if (feature_type == "chromatic")
    {
        return 1.0;
    }
    else if (feature_type == "diatonic")
    {
        return 1.0;
    }
    else if (feature_type == "rhythmic")
    {
        return 1.0;
    }
    return 1.0;
}

/**
 * @brief Computes the alignment score between two characters based on a cost map that stores
 * the matrix of match scores and mismatch penalties.
 *
 * @param s1_char Character from the text sequence
 * @param s2_char Character from the query sequence
 * @param cost_map Map containing mismatch penalties for character pairs
 * @param generic_mismatch Mismatch penalty to be returned if no value is found in the cost_map.
 *
 * @return float Alignment score:
 *         - cost_map match score or penalty if found, otherwise generic_mismatch
 */
float get_alignment_score(const char s1_char, const char s2_char,
                          const unordered_map<char, unordered_map<char, float>> &cost_map,
                          const float generic_mismatch)
{
    try
    {
        return cost_map.at(s1_char).at(s2_char);
    }
    catch (const out_of_range &)
    {
        return generic_mismatch;
    }
}

/**
 * @brief Computes the global alignment distance between two score features.
 *
 * This function calculates the global alignment distance between two score features
 * using dynamic programming. The algorithm uses a scoring scheme based on matching and mismatching
 * characters to determine the best alignment position. The function returns the distance between
 * the two provided score features.
 *
 * @param score_1_feature The first score feature to be compared.
 * @param score_2_feature The second score feature to be compared.
 * @param cost_map Map containing match values and mismatch penalties for character pairs
 * @param gap_penalty Gap penalty value for the alignment computation
 *
 * @return float The global alignment distance between the two score features.
 */
float global_alignment(const string &score_1_feature, const string &score_2_feature,
                       const unordered_map<char, unordered_map<char, float>> &cost_map,
                       const float gap_penalty)
{

    size_t f1_size = score_1_feature.size();
    size_t f2_size = score_2_feature.size();

    // The alignment matrix is computed using two columns
    vector<float> prev_column(f2_size + 1);
    vector<float> current_column(f2_size + 1);

    // Initializes prev_column vector from 0 to its size -1
    iota(begin(prev_column), end(prev_column), 0);

    // Initialize current_column as a copy of prev_column for edge cases
    current_column = prev_column;

    // Compute distance matrix
    for (int i = 1; i <= f1_size; ++i)
    {
        // First row initialized to ascending number from 0 within each iteration
        current_column[0] = i;
        for (int j = 1; j <= f2_size; ++j)
        {
            // Check if both values match (add 0 distance)
            float score = get_alignment_score(score_1_feature[i - 1], score_2_feature[j - 1], cost_map, gap_penalty);

            // Compute minimum distance between modifying the value, adding it or removing it
            current_column[j] = min_of_three(prev_column[j - 1] + score, prev_column[j] + gap_penalty, current_column[j - 1] + gap_penalty);
        }

        // Move current column to previous column
        prev_column = current_column;
    }

    return current_column[f2_size];
}

/**
 * @brief Main function to calculate the global distance between two score features.
 *
 * This program calculates the global distance between two score features with the approximate
 * alignment algorithm using dynamic programming. The alignment score is computed based on a cost map
 * that stores the matrix of match scores and mismatch penalties. The program receives the string of
 * characters representing the two score features and the feature type (chromatic, diatonic, rhythmic).
 * Finally, it prints the computed global distance.
 *
 * @param argc The number of command line arguments.
 * @param argv The array of command line arguments.
 * @return int Return value indicating the success (0) or failure (1) of the program.
 */
int main(int argc, char **argv)
{
    if (argc != 5 || string(argv[3]) != "-f")
    {
        cout << "Usage: " << argv[0] << " first_score_feature second_score_feature -f <feature>" << endl;
        cout << "    This program calculates the global distance between two score features." << endl;
        cout << "    first_score_feature      First score feature to be compared." << endl;
        cout << "    second_score_feature     Second score feature to be compared." << endl;
        cout << "    -f <feature>             Feature type (chromatic, diatonic, rhythmic)." << endl;
        return 1;
    }

    string score_1_feature = argv[1];
    string score_2_feature = argv[2];
    string feature_type = argv[4];

    if (feature_type != "chromatic" && feature_type != "diatonic" && feature_type != "rhythmic")
    {
        cout << "Error: Invalid feature type. Valid options are 'chromatic', 'diatonic', 'rhythmic'." << endl;
        cout << "Usage: " << argv[0] << " first_score_feature second_score_feature -f <feature>" << endl;
        return 1;
    }

    string base_dir = get_executable_directory();
    string cost_map_file = base_dir + "/../scores/indexes/global_alignment/" + feature_type + "_cost_map.bin";
    unordered_map<char, unordered_map<char, float>> cost_map = load_cost_map(cost_map_file);
    float gap_penalty = get_gap_penalty(feature_type);

    // Compute the alignment and obtain the distance between the two provided scores
    float distance = global_alignment(score_1_feature, score_2_feature, cost_map, gap_penalty);

    cout << distance << endl;

    cout << endl;
}