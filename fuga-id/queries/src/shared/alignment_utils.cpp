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

#include "alignment_utils.hpp"
#include "file_operations.hpp"
#include <stdexcept>
#include <iostream>
#include <fstream>
#include <cstdint>

/**
 * @brief Loads a cost map from a binary file.
 *
 * This function reads a cost map from a binary file that was previously saved.
 * The cost map is stored as a map of maps representing the match scores and penalty values.
 *
 * @param filename Path to the binary file containing the cost map.
 * @return map<char, map<char, float>> The loaded cost map.
 */
std::unordered_map<char, std::unordered_map<char, float>> load_cost_map(const std::string &filename)
{
    std::unordered_map<char, std::unordered_map<char, float>> cost_map;
    std::ifstream file(filename, std::ios::binary);

    if (!file)
    {
        throw std::runtime_error("Cannot open file: " + filename);
    }

    // Read size of outer map
    uint32_t size;
    file.read(reinterpret_cast<char *>(&size), sizeof(size));

    // Read each key-value pair
    for (uint32_t i = 0; i < size; ++i)
    {
        uint32_t key_length;
        file.read(reinterpret_cast<char *>(&key_length), sizeof(key_length));
        std::string key(key_length, '\0');
        file.read(&key[0], key_length);

        uint32_t inner_size;
        file.read(reinterpret_cast<char *>(&inner_size), sizeof(inner_size));

        std::unordered_map<char, float> inner_map;
        for (uint32_t j = 0; j < inner_size; ++j)
        {
            uint32_t inner_key_length;
            file.read(reinterpret_cast<char *>(&inner_key_length), sizeof(inner_key_length));
            std::string inner_key(inner_key_length, '\0');
            file.read(&inner_key[0], inner_key_length);

            float value;
            file.read(reinterpret_cast<char *>(&value), sizeof(value));
            inner_map[inner_key[0]] = value;
        }
        cost_map[key[0]] = inner_map;
    }

    return cost_map;
}

/**
 * @brief Retrieves the cost map file based on the search feature.
 *
 * This function determines the cost map file containing mismatch penalties used
 * during the approximate alignment process based on the specified search feature.
 *
 * @param base_dir The base directory from which file paths are constructed.
 * @param search_feature The search type flag specified by the user (-c, -d, or -r).
 * @return string The corresponding cost map .bin file path.
 */
std::string get_cost_map_file(const std::string &base_dir, const std::string &search_feature)
{
    if (search_feature == "-c")
    {
        return base_dir + "/../../scores/indexes/approximate_alignment/chromatic_cost_map.bin";
    }
    else if (search_feature == "-d")
    {
        return base_dir + "/../../scores/indexes/approximate_alignment/diatonic_cost_map.bin";
    }
    else
    {
        return base_dir + "/../../scores/indexes/approximate_alignment/rhythmic_cost_map.bin";
    }
}
