"""
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
"""

"""
  Created by Hilda Romero-Velo on May 2024.
"""

"""
This script counts the number of files in a specified directory and checks if any of them are empty.
For each empty file found, it outputs the filename to the console.

Usage:
    python count_directory_files.py /path/to/directory

Details:
- The `count_files_and_check_empty(directory)` function handles both counting and checking for empty files.
- If no directory path is provided, the script displays usage instructions and exits.
- If an error occurs, such as an inaccessible directory, an appropriate error message is displayed.

This script is useful for quick audits of directories to verify file content or ensure that all files contain data.
"""


import os
import sys


# Counts the number of files inside a directory and checks if they are empty.
def count_files_and_check_empty(directory):
    file_count = 0
    empty_files = []

    # Check if the directory exists
    if not os.path.exists(directory):
        print("Directory does not exist.")
        return

    # Loop through each item in the directory
    try:
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            # Confirm the item is a file
            if os.path.isfile(filepath):
                file_count += 1
                # Check if file is empty
                if os.path.getsize(filepath) == 0:
                    empty_files.append(filename)

        print(f"Total number of files: {file_count}")
        if empty_files:
            print("Empty files:")
            for empty_file in empty_files:
                print(empty_file)
        else:
            print("No empty files found.")

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    # Ensure directory argument is provided
    if len(sys.argv) != 2:
        print("Usage: python count_directory_files.py /path/to/directory")
        sys.exit(1)

    # Get directory path from command line argument
    directory_path = sys.argv[1]
    count_files_and_check_empty(directory_path)
