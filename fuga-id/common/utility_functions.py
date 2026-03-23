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
  Created by Hilda Romero-Velo on November 2024.
"""

import struct


def extract_feature(filepath, ignore_value=None):
    """
    Extracts and cleans feature values from a **kern format file by removing "+" signs,
    converting values to integers, and omitting those that match a specified ignore_value
    (representing no change in frequency).

    Args:
        filepath (str): Path to a file containing feature analysis in **kern format.
        ignore_value [optional] (int): Integer value representing no change in frequency; values
                                       that match this are excluded from the result.

    Returns:
        str: A string of cleaned feature values, separated by semicolons.

    Notes:
        Lines that cannot be converted to integers are skipped.
    """
    feature = ""
    with open(filepath, "r", encoding="utf8") as f:
        for line in f:
            try:
                step = int(line.strip().replace("+", ""))
                if step != ignore_value:
                    feature += f"{step};"
            except ValueError:
                continue
    return feature


def to_single_notation(data, dictionary):
    """
    Translates feature values to single-character notation using a specified dictionary.

    Args:
        data (str): Semicolon-separated feature values.
        dictionary (dict): Mapping of feature values to single-character representations.

    Returns:
        str: Translated feature values as a single string.
    """
    values = data.split(";")
    values.pop()  # Remove the last empty element
    result = ""
    for v in values:
        try:
            result += dictionary[
                v.replace("r", "")
            ]  # Use dictionary to get single character
        except KeyError:
            result += ""  # Skip unmaped values
    return result


def save_cost_map(cost_map, filename):
    """
    Save the cost map to a binary file.

    Args:
        cost_map (dict): The cost map to save. It should be a dictionary of dictionaries.
        filename (str): The name of the file where the cost map will be saved.

    Returns:
        None
    """
    with open(filename, "wb") as file:
        # Write the number of items in the outer dictionary
        file.write(len(cost_map).to_bytes(4, byteorder="little"))
        for key, inner_map in cost_map.items():
            # Write the length of the outer key and the outer key itself
            key_bytes = key.encode("utf-8")
            file.write(len(key_bytes).to_bytes(4, byteorder="little"))
            file.write(key_bytes)
            # Write the number of items in the inner dictionary
            file.write(len(inner_map).to_bytes(4, byteorder="little"))
            for inner_key, value in inner_map.items():
                # Write the length of the inner key and the inner key itself
                inner_key_bytes = inner_key.encode("utf-8")
                file.write(len(inner_key_bytes).to_bytes(4, byteorder="little"))
                file.write(inner_key_bytes)
                # Write the value
                file.write(bytearray(struct.pack("f", value)))


def load_cost_map(filename):
    """
    Load the cost map from a binary file.

    Args:
        filename (str): The name of the file from which to load the cost map.

    Returns:
        dict: The loaded cost map.
    """
    cost_map = {}
    with open(filename, "rb") as file:
        # Read the number of items in the outer dictionary
        num_items = int.from_bytes(file.read(4), byteorder="little")
        for _ in range(num_items):
            # Read the length of the outer key and the outer key itself
            key_length = int.from_bytes(file.read(4), byteorder="little")
            key = file.read(key_length).decode("utf-8")
            # Read the number of items in the inner dictionary
            inner_size = int.from_bytes(file.read(4), byteorder="little")
            inner_map = {}
            for _ in range(inner_size):
                # Read the length of the inner key and the inner key itself
                inner_key_length = int.from_bytes(file.read(4), byteorder="little")
                inner_key = file.read(inner_key_length).decode("utf-8")
                # Read the value
                value = struct.unpack("f", file.read(4))[0]
                inner_map[inner_key] = value
            cost_map[key] = inner_map
    return cost_map


def write_text_to_file(filename, text):
    """
    Writes text data to a specified file, appending to the file if it already exists.

    Args:
        filename (str): The name of the file where the text will be written.
        text (str): The text data to write to the file.

    Returns:
        None
    """
    with open(filename, "a", encoding="utf8") as file:
        file.write(text)
