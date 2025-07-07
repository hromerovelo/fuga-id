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

#include "cli_utils.hpp"
#include <iostream>

using namespace std;

/**
 * @brief Prints the usage instructions for the program.
 *
 * This function displays the correct command-line usage for the program, including the required
 * arguments and their descriptions. It helps users understand how to execute the program with
 * the appropriate parameters.
 *
 * @param prog_name The name of the program (typically `argv[0]`).
 * @param context The context in which the function is called ("blast" or "approximate").
 */
void print_usage(const char *prog_name, const std::string &context)
{

    cout << "Usage: " << prog_name << " [-c|-d|-r] query_file\n";
    cout << "This program computes the " << context << " alignment between a given query and the scores corpus.\n";
    cout << "Arg 1: [-c|-d|-r]   Search type: -c (chromatic), -d (diatonic), -r (rhythm).\n";
    cout << "Arg 2: query_file   Query file. WAV for chromatic/diatonic, MIDI for rhythm.\n";
}

/**
 * @brief Validates the command-line arguments passed to the program.
 *
 * This function checks that the correct number of arguments are provided and verifies that the
 * search feature argument is one of the valid options ("-c", "-d", or "-r"). It also assigns the
 * values of the arguments to the provided `search_feature` and `query_file` references.
 *
 * @param argc The number of command-line arguments passed to the program.
 * @param argv An array of command-line argument strings.
 * @param search_feature A reference to a string that will hold the selected search feature
 *                       ("-c", "-d", or "-r").
 * @param query_file A reference to a string that will hold the path to the query file.
 * @param print_usage A function that prints the program's usage instructions.
 * @param context The context in which the function is called ("blast" or "approximate").
 * @return bool `true` if the arguments are valid, `false` otherwise.
 */
bool validate_args(int argc, char **argv,
                   std::string &search_feature,
                   std::string &query_file, const std::string &context)
{
    if (argc != 3)
    {
        print_usage(argv[0], context);
        return false;
    }
    search_feature = argv[1];
    query_file = argv[2];
    if (search_feature != "-c" && search_feature != "-d" && search_feature != "-r")
    {
        std::cerr << "Error: Invalid search feature. Options: -c, -d, -r.\n";
        return false;
    }
    return true;
}