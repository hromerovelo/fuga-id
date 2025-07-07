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

#include "file_operations.hpp"
#include <fstream>
#include <iostream>
#include <cerrno>
#include <cstring>

using namespace std;

/**
 * @brief Checks if a file exists and is accessible.
 *
 * This function determines whether a file exists and can be opened for reading
 * by attempting to open it using `std::ifstream`. If the file can be opened,
 * the function returns `true`. Otherwise, it returns `false`.
 *
 * @note This function does not differentiate between a file not existing and
 *       other potential errors (e.g., insufficient permissions). If such
 *       distinctions are necessary, consider using `std::filesystem::exists`
 *       (available in C++17 and later) or implementing additional error handling.
 *
 * @param filename Path to the file to be checked.
 * @return bool `true` if the file exists and can be opened, `false` otherwise.
 */
bool file_exists(const std::string &filename)
{
    std::ifstream file(filename);
    return file.good();
}

/**
 * Attempts to delete a file. If the file does not exist, it directly returns true.
 * If the file exists and there is an error during deletion, it prints an error message and
 * returns false. If the file is deleted successfully, it returns true.
 *
 * @param filename Path to the file to be deleted.
 * @return true if the file does not exist or was successfully deleted, false if there was an
 * error during deletion.
 */
bool delete_file(const std::string &filename)
{
    if (file_exists(filename))
    {
        if (remove(filename.c_str()) != 0)
        {
            std::cerr << "Error deleting file: " << strerror(errno) << std::endl;
            return false;
        }
    }
    return true;
}

/**
 * @brief Loads the contents of a file into a string.
 *
 * This function reads the contents of a specified file and returns it as a string. If the file
 * cannot be opened or read, an empty string is returned.
 *
 * @param filename The path to the file to be loaded.
 * @return string The contents of the file as a string, or an empty string if the file cannot be
 *                opened.
 */
string load_file(const string &filename)
{
    ifstream file(filename);
    string content = file
                         ? string((istreambuf_iterator<char>(file)), istreambuf_iterator<char>())
                         : "";
    content.erase(content.find_last_not_of('\n') + 1);
    return content;
}

/**
 * @brief Retrieves the reference text file and query feature file based on the search type.
 *
 * This function determines both the reference text file (for alignment) and the temporary query
 * feature file (stored in single-byte format) based on the specified search type flag.
 *
 * @param base_dir The base directory from which file paths are constructed.
 * @param search_feature The search type flag specified by the user (-c, -d, or -r).
 * @param query_sf_file Reference to the string that will hold the path of the temporary query
 *                      feature file.
 * @param context The context in which the function is called ("blast" or "approximate").
 * @return string The reference text file path to be used in the alignment.
 */
string get_search_files(const string &base_dir, const string &search_feature, string &query_sf_file, const string &context)
{
    if (context == "blast")
    {
        if (search_feature == "-c")
        {
            query_sf_file = base_dir + "/../tmp/chromatic_sf_query.fasta";
            return base_dir + "/../../scores/indexes/blast/chromatic_db";
        }
        else if (search_feature == "-d")
        {
            query_sf_file = base_dir + "/../tmp/diatonic_sf_query.fasta";
            return base_dir + "/../../scores/indexes/blast/diatonic_db";
        }
        else
        {
            query_sf_file = base_dir + "/../tmp/rhythm_sf_query.fasta";
            return base_dir + "/../../scores/indexes/blast/rhythm_db";
        }
    }
    else if (context == "approximate")
    {
        if (search_feature == "-c")
        {
            query_sf_file = base_dir + "/../tmp/chromatic_sf_query.txt";
            return base_dir + "/../../scores/indexes/approximate_alignment/chromatic_text.txt";
        }
        else if (search_feature == "-d")
        {
            query_sf_file = base_dir + "/../tmp/diatonic_sf_query.txt";
            return base_dir + "/../../scores/indexes/approximate_alignment/diatonic_text.txt";
        }
        else
        {
            query_sf_file = base_dir + "/../tmp/rhythm_sf_query.txt";
            return base_dir + "/../../scores/indexes/approximate_alignment/rhythm_text.txt";
        }
    }
    else
    {
        throw invalid_argument("Invalid context provided to get_search_files");
    }
}