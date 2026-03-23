/*
BSD 2-Clause License

Copyright (c) 2026, Hilda Romero-Velo
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
*/

//
// Created by Hilda Romero-Velo on March 2026.
//

/**
 * N-gram Alignment
 *
 * Performs music retrieval using n-gram based exact or approximate matching.
 *
 * Usage:
 *   ngram_alignment -q <query_file> -n <3|5|7> -t <chromatic|diatonic|rhythm>
 *                   -m <exact|1mismatch> -i <index_dir>
 *
 * Example:
 *   ngram_alignment -q query.txt -n 5 -t chromatic -m exact -i scores/indexes/ngram
 */

#include <Python.h>
#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <map>
#include <array>
#include <algorithm>
#include <getopt.h>
#include <sys/times.h>
#include <unistd.h>
#include <cmath>
#include <sys/stat.h>
#include "shared/system_utils.hpp"
#include "shared/json_operations.hpp"
#include "shared/data_structures.hpp"

// N-gram specific result structure
struct NgramAlignmentResult
{
    std::string melodic_line_id;
    double alignment_score;
    int ranking_position;
    int melodic_line_origin_pos;
    int melodic_line_end_pos;
    int query_origin_pos;
    int query_end_pos;
};

struct Timing
{
    long user_ms;
    long system_ms;
    long clock_ms;
};

/**
 * Read query sequence from file.
 *
 * Assumes the file contains a single line with the feature sequence.
 *
 * Input:
 * - filename: path to the query feature file
 *
 * Output:
 * - feature sequence as a string (whitespace removed)
 */
std::string readQuerySequence(const std::string &filename)
{
    std::ifstream file(filename);
    if (!file.is_open())
    {
        std::cerr << "Error: Could not open query file " << filename << std::endl;
        return "";
    }

    std::string sequence;
    std::getline(file, sequence);
    file.close();

    // Remove whitespace
    sequence.erase(std::remove_if(sequence.begin(), sequence.end(), ::isspace), sequence.end());

    return sequence;
}

/**
 * Generate all 1-mismatch variants of an n-gram.
 *
 * Input:
 * - ngram: original n-gram string
 * - alphabet: string containing all possible characters (for generating variants)
 *
 * Output:
 * - vector of n-grams with one character replaced by any other character
 */
std::vector<std::string> generate1MismatchVariants(const std::string &ngram, const std::string &alphabet)
{
    std::vector<std::string> variants;

    for (size_t pos = 0; pos < ngram.length(); ++pos)
    {
        for (char c : alphabet)
        {
            if (c != ngram[pos])
            {
                std::string variant = ngram;
                variant[pos] = c;
                variants.push_back(variant);
            }
        }
    }

    return variants;
}

/*
 * Extract the alphabet from the n-gram index.
 *
 * Input:
 * - index: Python dictionary representing the n-gram index
 *
 * Output:
 * - string containing all unique characters found in the index
 */
std::string extractAlphabetFromIndex(PyObject *index)
{
    const std::string fallbackAlphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
    if (!index || !PyDict_Check(index))
    {
        return fallbackAlphabet;
    }

    PyObject *keys = PyDict_Keys(index);
    if (!keys || !PyList_Check(keys))
    {
        Py_XDECREF(keys);
        return fallbackAlphabet;
    }

    std::array<bool, 256> seen{};
    std::string alphabet;

    Py_ssize_t keyCount = PyList_Size(keys);
    for (Py_ssize_t i = 0; i < keyCount; ++i)
    {
        PyObject *keyObj = PyList_GetItem(keys, i); // Borrowed reference
        if (!keyObj || !PyUnicode_Check(keyObj))
        {
            continue;
        }

        const char *keyStr = PyUnicode_AsUTF8(keyObj);
        if (!keyStr)
        {
            PyErr_Clear();
            continue;
        }

        const std::string ngramKey(keyStr);
        for (unsigned char ch : ngramKey)
        {
            if (!seen[ch])
            {
                seen[ch] = true;
                alphabet.push_back(static_cast<char>(ch));
            }
        }
    }

    Py_DECREF(keys);
    return alphabet.empty() ? fallbackAlphabet : alphabet;
}

/**
 * Extract n-grams from query sequence.
 *
 * Input:
 * - sequence: input feature sequence string
 * - ngramSize: size of n-grams to extract (e.g., 3, 5, or 7)
 *
 * Output:
 * - vector of n-gram strings extracted from the sequence
 */
std::vector<std::string> extractQueryNgrams(const std::string &sequence, int ngramSize)
{
    std::vector<std::string> ngrams;

    if (sequence.length() < static_cast<size_t>(ngramSize))
    {
        return ngrams;
    }

    for (size_t i = 0; i <= sequence.length() - ngramSize; ++i)
    {
        ngrams.push_back(sequence.substr(i, ngramSize));
    }

    return ngrams;
}

/**
 * Load n-gram index using Python pickle module.
 *
 * Input:
 * - indexPath: path to the pickle file containing the n-gram index
 *
 * Output:
 * - PyObject* representing the loaded index (a Python dictionary), or nullptr on failure
 */
PyObject *loadNgramIndex(const std::string &indexPath)
{
    // Import pickle and builtins modules
    PyObject *pickleModule = PyImport_ImportModule("pickle");
    if (!pickleModule)
    {
        PyErr_Print();
        std::cerr << "Error: Could not import pickle module" << std::endl;
        return nullptr;
    }

    PyObject *builtinsModule = PyImport_ImportModule("builtins");
    if (!builtinsModule)
    {
        PyErr_Print();
        std::cerr << "Error: Could not import builtins module" << std::endl;
        Py_DECREF(pickleModule);
        return nullptr;
    }

    // Open file using Python's open()
    PyObject *openFunc = PyObject_GetAttrString(builtinsModule, "open");
    PyObject *pathObj = PyUnicode_FromString(indexPath.c_str());
    PyObject *modeObj = PyUnicode_FromString("rb");
    PyObject *fileObj = PyObject_CallFunctionObjArgs(openFunc, pathObj, modeObj, NULL);

    if (!fileObj)
    {
        PyErr_Print();
        std::cerr << "Error: Could not open index file " << indexPath << std::endl;
        Py_DECREF(builtinsModule);
        Py_DECREF(pickleModule);
        Py_DECREF(openFunc);
        Py_DECREF(pathObj);
        Py_DECREF(modeObj);
        return nullptr;
    }

    // Load pickle
    PyObject *pickleLoad = PyObject_GetAttrString(pickleModule, "load");
    PyObject *index = PyObject_CallFunctionObjArgs(pickleLoad, fileObj, NULL);

    // Close file
    PyObject *closeMethod = PyObject_GetAttrString(fileObj, "close");
    PyObject_CallObject(closeMethod, NULL);

    // Cleanup
    Py_DECREF(closeMethod);
    Py_DECREF(fileObj);
    Py_DECREF(modeObj);
    Py_DECREF(pathObj);
    Py_DECREF(openFunc);
    Py_DECREF(builtinsModule);
    Py_DECREF(pickleModule);
    Py_DECREF(pickleLoad);

    if (!index)
    {
        PyErr_Print();
        std::cerr << "Error: Could not load pickle index" << std::endl;
        return nullptr;
    }

    return index;
}

/**
 * Query n-gram index (exact match or 1-mismatch)
 *
 * Input:
 * - index: PyObject* representing the n-gram index (a Python dictionary)
 * - queryNgrams: vector of n-gram strings extracted from the query
 * - matchMode: "exact" for exact matches, "1mismatch" for allowing one mismatch
 *
 * Output:
 * - map of melodic_line_id to vector of positions where hits were found
 *
 * Index structure (Python dictionary):
 * {
 *   "ngram_string": [("melodic_line_id", position), ...],
 *   ...
 * }
 */
std::map<std::string, std::vector<int>> queryIndex(PyObject *index,
                                                   const std::vector<std::string> &queryNgrams,
                                                   const std::string &matchMode,
                                                   const std::string &alphabet)
{
    std::map<std::string, std::vector<int>> hits; // melodic_line_id -> positions

    for (const std::string &ngram : queryNgrams)
    {
        std::vector<std::string> ngramsToSearch;

        if (matchMode == "exact")
        {
            ngramsToSearch.push_back(ngram);
        }
        else if (matchMode == "1mismatch")
        {
            // Add original ngram
            ngramsToSearch.push_back(ngram);
            // Add all 1-mismatch variants
            std::vector<std::string> variants = generate1MismatchVariants(ngram, alphabet);
            ngramsToSearch.insert(ngramsToSearch.end(), variants.begin(), variants.end());
        }

        // Search each n-gram in index
        for (const std::string &searchNgram : ngramsToSearch)
        {
            PyObject *key = PyUnicode_FromString(searchNgram.c_str());
            if (!key)
            {
                // Failed to create Python string, skip
                PyErr_Clear();
                continue;
            }

            if (PyDict_Contains(index, key))
            {
                PyObject *hitList = PyDict_GetItem(index, key); // Borrowed reference

                if (hitList && PyList_Check(hitList))
                {
                    Py_ssize_t listSize = PyList_Size(hitList);

                    for (Py_ssize_t i = 0; i < listSize; ++i)
                    {
                        PyObject *tuple = PyList_GetItem(hitList, i); // Borrowed reference

                        if (tuple && PyTuple_Check(tuple) && PyTuple_Size(tuple) >= 2)
                        {
                            PyObject *melodicLineIdObj = PyTuple_GetItem(tuple, 0);
                            PyObject *positionObj = PyTuple_GetItem(tuple, 1);

                            if (!melodicLineIdObj || !positionObj)
                            {
                                continue;
                            }

                            const char *melodicLineId = PyUnicode_AsUTF8(melodicLineIdObj);
                            if (!melodicLineId)
                            {
                                // Error converting to UTF-8, skip this entry
                                PyErr_Clear();
                                continue;
                            }

                            long position = PyLong_AsLong(positionObj);
                            if (position == -1 && PyErr_Occurred())
                            {
                                // Error converting to long, skip this entry
                                PyErr_Clear();
                                continue;
                            }

                            hits[melodicLineId].push_back(static_cast<int>(position));
                        }
                    }
                }
            }

            Py_DECREF(key);
        }
    }

    return hits;
}

/**
 * Score and rank results based on hit frequency and density.
 *
 * Input:
 * - hits: map of melodic_line_id to vector of positions where hits were found
 * - queryLength: length of the original query sequence (for calculating density)
 * - ngramSize: size of n-grams used (for calculating span)
 * - topK: number of top results to return
 *
 * Output:
 * - vector of NgramAlignmentResult, sorted by alignment score and limited to topK
 *
 * Scoring approach:
 * - Hit count: more hits indicate a stronger match
 * - Position density: hits that are closer together in the melodic line may indicate a better alignment
 * - Combined score: hit count weighted by density to prioritize results with many hits that are also closely aligned
 *
 * Note: This is a heuristic scoring method and can be further refined based on specific retrieval goals or characteristics of the dataset.
 */
std::vector<NgramAlignmentResult> scoreAndRank(const std::map<std::string, std::vector<int>> &hits,
                                               int queryLength,
                                               int ngramSize,
                                               int topK = 5)
{
    std::vector<NgramAlignmentResult> results;

    for (const auto &[melodicLineId, positions] : hits)
    {
        NgramAlignmentResult result;
        result.melodic_line_id = melodicLineId;

        // Score based on number of hits and position density
        int hitCount = positions.size();

        // Calculate position span
        auto minmax = std::minmax_element(positions.begin(), positions.end());
        int minPos = *minmax.first;
        int maxPos = *minmax.second;
        int span = maxPos - minPos + ngramSize;

        // Density score: hits per unit length
        double density = (span > 0) ? static_cast<double>(hitCount) / span : 0.0;

        // Combined score: hit count weighted by density
        result.alignment_score = hitCount * (1.0 + density);

        result.query_origin_pos = 0;
        result.query_end_pos = queryLength - 1;
        result.melodic_line_origin_pos = minPos;
        result.melodic_line_end_pos = maxPos + ngramSize - 1;

        results.push_back(result);
    }

    // Sort by score (descending)
    std::sort(results.begin(), results.end(),
              [](const NgramAlignmentResult &a, const NgramAlignmentResult &b)
              {
                  return a.alignment_score > b.alignment_score;
              });

    // Assign ranking positions and keep Top-K
    for (size_t i = 0; i < results.size() && i < static_cast<size_t>(topK); ++i)
    {
        results[i].ranking_position = i + 1;
    }

    if (results.size() > static_cast<size_t>(topK))
    {
        results.resize(topK);
    }

    return results;
}

/**
 * Get executable base directory.
 *
 * Output:
 * - string representing the directory where the executable is located
 */
std::string getBaseDir()
{
    char result[PATH_MAX];
    ssize_t count = readlink("/proc/self/exe", result, PATH_MAX);
    std::string path(result, (count > 0) ? count : 0);
    size_t pos = path.find_last_of("/");
    return path.substr(0, pos);
}

void printUsage(const char *progname)
{
    std::cout << "Usage: " << progname << " [-c|-d|-r] <audio_file> -n <ngram_size> -m <mode> -i <index_dir>\n";
    std::cout << "       " << progname << " -q <feature_file> -n <ngram_size> -m <mode> -i <index_dir>\n";
    std::cout << "\nRequired options (audio mode):\n";
    std::cout << "  -c, -d, -r               Search type: chromatic, diatonic, or rhythm\n";
    std::cout << "  <audio_file>             Audio file (WAV or MIDI)\n";
    std::cout << "\nRequired options (pre-extracted mode):\n";
    std::cout << "  -q, --query-file <file>  Pre-extracted feature file (skips audio extraction)\n";
    std::cout << "\nCommon required options:\n";
    std::cout << "  -n, --ngram-size <N>     N-gram size: 3, 5, or 7\n";
    std::cout << "  -m, --match-mode <mode>  Match mode: exact or 1mismatch\n";
    std::cout << "  -i, --index-dir <dir>    N-gram index directory\n";
    std::cout << "\nOptional options:\n";
    std::cout << "  -k, --top-k <N>          Number of top results (default: 5)\n";
    std::cout << "  -h, --help               Display this help message\n";
}

int main(int argc, char *argv[])
{
    std::string audioFile;
    std::string queryFile;
    std::string indexDir;
    std::string featureType;
    std::string searchFeature;
    std::string matchMode;
    int ngramSize = 0;
    int topK = 5;

    // Parse command line arguments
    static struct option long_options[] = {
        {"query-file", required_argument, 0, 'q'},
        {"feature-type", required_argument, 0, 't'},
        {"ngram-size", required_argument, 0, 'n'},
        {"match-mode", required_argument, 0, 'm'},
        {"index-dir", required_argument, 0, 'i'},
        {"top-k", optional_argument, 0, 'k'},
        {"help", no_argument, 0, 'h'},
        {0, 0, 0, 0}};

    int opt;
    int option_index = 0;
    while ((opt = getopt_long(argc, argv, "q:t:cdrn:m:i:k:h", long_options, &option_index)) != -1)
    {
        switch (opt)
        {
        case 'q':
            queryFile = optarg;
            break;
        case 't':
            featureType = optarg;
            break;
        case 'c':
            searchFeature = "-c";
            featureType = "chromatic";
            break;
        case 'd':
            searchFeature = "-d";
            featureType = "diatonic";
            break;
        case 'r':
            searchFeature = "-r";
            featureType = "rhythm";
            break;
        case 'n':
            ngramSize = std::stoi(optarg);
            break;
        case 'm':
            matchMode = optarg;
            break;
        case 'i':
            indexDir = optarg;
            break;
        case 'k':
            topK = std::stoi(optarg);
            break;
        case 'h':
            printUsage(argv[0]);
            return 0;
        default:
            printUsage(argv[0]);
            return 1;
        }
    }

    // Get audio file from remaining argument
    if (optind < argc)
    {
        audioFile = argv[optind];
    }

    // Validate arguments: either (-q feature_file -t type) or (-c/-d/-r audio_file), plus common required
    bool usingQueryFile = !queryFile.empty() && !featureType.empty();
    bool usingAudio = !audioFile.empty() && !featureType.empty();
    if ((!usingQueryFile && !usingAudio) || indexDir.empty() || matchMode.empty() || ngramSize == 0)
    {
        std::cerr << "Error: Missing required arguments\n";
        printUsage(argv[0]);
        return 1;
    }

    // Extract features or read from pre-extracted file
    std::string base_dir = getBaseDir();
    std::string clean_tmp = base_dir + "/../utils/clean_tmp.sh";
    std::string clean_command = "bash " + clean_tmp;

    double extract_feature_user_time = 0, extract_feature_system_time = 0;
    long extract_feature_clock_time = 0;
    std::string querySequence;

    if (usingQueryFile)
    {
        // Use pre-extracted feature file directly (no audio extraction needed)
        querySequence = readQuerySequence(queryFile);
        if (querySequence.empty())
        {
            std::cerr << "Error: Could not read query sequence from file: " << queryFile << "\n";
            return 1;
        }
    }
    else
    {
        // Extract features from audio file
        std::string extract_query_features = base_dir + "/../src/extract_query_feature.sh";
        std::string query_sf_file = base_dir + "/../tmp/" + featureType + "_sf_query.txt";
        std::string features_command = "bash " + extract_query_features + " " + searchFeature + " " +
                                       audioFile + " -m fitting";

        measure_time_and_cpu([&]()
                             { querySequence = launch_command(features_command, query_sf_file); },
                             false, extract_feature_user_time, extract_feature_system_time,
                             extract_feature_clock_time, true);

        if (querySequence == "ERROR" || querySequence.empty())
        {
            std::cerr << "Error: Feature extraction failed\n";
            system(clean_command.c_str());
            return 1;
        }
    }

    // Extract query n-grams
    std::vector<std::string> queryNgrams = extractQueryNgrams(querySequence, ngramSize);
    if (queryNgrams.empty())
    {
        std::cerr << "Error: Query too short for " << ngramSize << "-grams\n";
        std::cerr << "Query sequence length: " << querySequence.length() << "\n";
        return 1;
    }

    std::cerr << "Query sequence length: " << querySequence.length() << ", n-grams: " << queryNgrams.size() << "\n";

    // Initialize Python interpreter
    Py_Initialize();

    // Start timing (after feature loading, before alignment)
    struct tms start_tms, end_tms;
    clock_t start_clock = times(&start_tms);

    // Load n-gram index
    std::string indexPath = indexDir + "/ngram_" + std::to_string(ngramSize) + "_" + featureType + ".pkl";
    std::cerr << "Loading index: " << indexPath << "\n";
    PyObject *index = loadNgramIndex(indexPath);
    if (!index)
    {
        std::cerr << "Error: Failed to load index\n";
        Py_Finalize();
        return 1;
    }

    std::string mismatchAlphabet = extractAlphabetFromIndex(index);

    // Query index
    std::cerr << "Querying index with " << queryNgrams.size() << " n-grams, match mode: " << matchMode << "\n";
    std::map<std::string, std::vector<int>> hits = queryIndex(index, queryNgrams, matchMode, mismatchAlphabet);
    std::cerr << "Query complete, found hits in " << hits.size() << " melodic lines\n";

    // Score and rank results
    std::vector<NgramAlignmentResult> results = scoreAndRank(hits, querySequence.length(), ngramSize, topK);
    std::cerr << "Scored and ranked results, top results: " << results.size() << "\n";

    // End timing (after alignment, before cleanup)
    clock_t end_clock = times(&end_tms);

    // Clean up Python objects
    Py_DECREF(index);
    Py_Finalize();
    long clk_tck = sysconf(_SC_CLK_TCK);

    Timing timing;
    timing.user_ms = ((end_tms.tms_utime - start_tms.tms_utime) * 1000) / clk_tck;
    timing.system_ms = ((end_tms.tms_stime - start_tms.tms_stime) * 1000) / clk_tck;
    timing.clock_ms = ((end_clock - start_clock) * 1000) / clk_tck;

    // Convert to standard AlignmentResult format for saving
    std::vector<AlignmentResult> standardResults;
    for (const auto &result : results)
    {
        AlignmentResult stdResult;
        stdResult.alignment_score = result.alignment_score;
        stdResult.origin_position = {result.melodic_line_origin_pos, result.query_origin_pos};
        stdResult.end_position = {result.melodic_line_end_pos, result.query_end_pos};
        stdResult.retrieved_score_id = result.melodic_line_id;
        standardResults.push_back(stdResult);
    }

    // Save results to JSON file
    std::string results_dir = base_dir + "/../data/results";
    mkdir(results_dir.c_str(), 0755);
    std::string json_file = results_dir + "/score_and_timing_results.json";

    save_result_and_timing_to_json(
        standardResults, querySequence,
        extract_feature_user_time, extract_feature_system_time, extract_feature_clock_time,
        timing.user_ms, timing.system_ms, timing.clock_ms,
        json_file);

    // Clean temporary files
    system(clean_command.c_str());

    return 0;
}
