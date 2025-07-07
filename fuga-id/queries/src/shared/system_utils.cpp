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

#include "system_utils.hpp"
#include "file_operations.hpp"
#include <cerrno>
#include <chrono>
#include <cstring>
#include <fstream>
#include <iostream>
#include <limits.h>
#include <stdexcept>
#include <sys/resource.h>
#include <unistd.h>

using namespace std;

/**
 * @brief Executes a command and loads the content of a file after execution.
 *
 * This function runs the given command using the system's shell. After the command has been
 * executed, it loads the content of a specified file and returns it as a string. If the
 * command fails, an error message is printed, and "ERROR" is returned instead of the file content.
 *
 * @param command The command to be executed as a string. It is expected to be a valid shell command.
 * @param filename The path of the file to load after the command execution.
 * @return string The content of the file specified by `filename`, or "ERROR" if the command fails.
 */
std::string launch_command(const std::string &command, const std::string &filename)
{
    int exit_code = system(command.c_str()); // Execute the command
    if (exit_code != 0)
    {
        cerr << "Error executing command: " << strerror(errno) << endl;
        return "ERROR"; // Return error if command fails
    }

    if (!filename.empty())
    {
        return load_file(filename); // Return file content after execution
    }

    return ""; // Return empty string if no file content is to be loaded
}

/**
 * @brief Retrieves the directory of the currently running executable.
 *
 * This function reads the symbolic link "/proc/self/exe", which points to the path of the
 * currently executing program. It then extracts the directory portion of the path and
 * returns it as a string. If the executable's path cannot be retrieved, an empty string
 * is returned.
 *
 * @return string The directory where the executable is located. If the path can't be retrieved,
 *                returns an empty string.
 */
string get_executable_directory()
{
    char path[PATH_MAX];

    // Get the path to the current executable (symlink to the actual binary)
    ssize_t count = readlink("/proc/self/exe", path, PATH_MAX);
    if (count == -1)
        return ""; // Return an empty string if the path can't be retrieved

    // Null-terminate the path string
    path[count] = '\0';

    string full_path(path);

    // Find the last occurrence of '/' to extract the directory
    size_t last_slash = full_path.find_last_of("/");

    // Return the directory portion of the full path (excluding the executable name)
    return (last_slash == string::npos) ? "" : full_path.substr(0, last_slash);
}

/**
 * @brief Retrieves the CPU times (user and system) for the child processes of the current process.
 *
 * This function uses `getrusage` to retrieve resource usage statistics, including user and
 * system CPU time for the child processes. The retrieved times are then converted from
 * seconds and microseconds to milliseconds and stored in the provided references.
 *
 * @param user_time_ms Reference to a variable where the user CPU time (in milliseconds) will
 *                     be stored.
 * @param system_time_ms Reference to a variable where the system CPU time (in milliseconds)
 *                       will be stored.
 * @param include_children A boolean indicating which time should be computed, the one for
 *                         children processes or the main usage of this script.
 */
void get_cpu_times(double &user_time_ms, double &system_time_ms, bool include_children)
{
    struct rusage usage;
    getrusage(include_children ? RUSAGE_CHILDREN : RUSAGE_SELF, &usage);
    user_time_ms = (usage.ru_utime.tv_sec * 1000) + (usage.ru_utime.tv_usec / 1000.0);
    system_time_ms = (usage.ru_stime.tv_sec * 1000) + (usage.ru_stime.tv_usec / 1000.0);
}

/**
 * @brief Measures the elapsed real time, user time, and system time for a given task.
 *
 * This function takes a task (as a lambda or any callable function), executes it, and measures
 * the elapsed real time as well as the CPU times (user and system) before and after execution.
 *
 * If the task is `approximate_alignment`, it executes the task 10 times and calculates
 * the average elapsed times. For other tasks, it executes the task once as usual.
 *
 * @param task The function or lambda representing the task to measure.
 * @param several_runs A boolean indicating if several runs should be executed for the task.
 * @param user_time_ms Difference in user time in milliseconds (output).
 * @param system_time_ms Difference in system time in milliseconds (output).
 * @param clock_time_ms Total elapsed real time (clock time) in milliseconds (output).
 * @param include_children A boolean indicating which time should be computed, the one for child
 *                         processes or the one for the main use of this script.
 */
void measure_time_and_cpu(
    const std::function<void()> &task,
    bool several_runs,
    double &user_time_ms,
    double &system_time_ms,
    long &clock_time_ms,
    bool include_children)
{
    // Initialize accumulators for the times
    double total_user_time_ms = 0.0, total_system_time_ms = 0.0;
    long total_clock_time_ms = 0;

    int iterations = several_runs ? 10 : 1;

    for (int i = 0; i < iterations; ++i)
    {
        // Record start time
        auto start = std::chrono::high_resolution_clock::now();
        double user_time_start, system_time_start;
        get_cpu_times(user_time_start, system_time_start, include_children);

        // Execute the task
        task();

        // Record end time
        auto end = chrono::high_resolution_clock::now();
        double user_time_end, system_time_end;
        get_cpu_times(user_time_end, system_time_end, include_children);

        // Accumulate time differences
        total_user_time_ms += (user_time_end - user_time_start);
        total_system_time_ms += (system_time_end - system_time_start);
        total_clock_time_ms += chrono::duration_cast<chrono::milliseconds>(end - start).count();
    }

    // Calculate averages if `approximate_alignment`, otherwise retain single execution results
    user_time_ms = total_user_time_ms / iterations;
    system_time_ms = total_system_time_ms / iterations;
    clock_time_ms = total_clock_time_ms / iterations;
}
