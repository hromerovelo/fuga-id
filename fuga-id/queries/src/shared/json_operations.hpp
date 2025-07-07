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

#ifndef JSON_OPERATIONS_HPP
#define JSON_OPERATIONS_HPP

#include <string>
#include <vector>
#include "data_structures.hpp"

std::string generate_results_json(const std::vector<AlignmentResult> &results);
std::string generate_timing_json(
    double extract_features_user_time_ms,
    double extract_features_system_time_ms,
    long extract_features_clock_time_ms,
    double alignment_user_time_ms,
    double alignment_system_time_ms,
    long alignment_clock_time_ms);

void save_result_and_timing_to_json(
    const std::vector<AlignmentResult> &results,
    const std::string &query,
    double extract_features_user_time_ms,
    double extract_features_system_time_ms,
    long extract_features_clock_time_ms,
    double alignment_user_time_ms,
    double alignment_system_time_ms,
    long alignment_clock_time_ms,
    const std::string &filename);

#endif