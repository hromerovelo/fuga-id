/*
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
*/

-- -----------------------------------------------------------------------------
-- Script: Database Schema for storing queries search times and results in the 
-- scores corpus using Approximate Alignment and BLAST algorithms.
-- Author: Hilda Romero-Velo
-- Date: 2024-11-20
-- -----------------------------------------------------------------------------

-- Drop existing tables to avoid conflicts when creating new ones
DROP TABLE IF EXISTS Search_Results;
DROP TABLE IF EXISTS Search;
DROP TABLE IF EXISTS Query;
DROP TABLE IF EXISTS Recording;
DROP TABLE IF EXISTS Global_Alignment;
DROP TABLE IF EXISTS Melodic_Line;
DROP TABLE IF EXISTS Score;

-- Table: Score
-- Represents a musical score
CREATE TABLE Score (
    score_id VARCHAR(255) PRIMARY KEY, -- String identifier for the score (the MusicXML filename)
    musical_form VARCHAR(50), -- Musical form of the score
    file_extension VARCHAR(15) -- File extension of the score (e.g., .musicxml, .xml, .mid, .mei)
);

-- Table: Melodic_Line
-- Represents a melodic line from a musical score
CREATE TABLE Melodic_Line (
    melodic_line_id VARCHAR(255) PRIMARY KEY, -- String identifier for melodic line
    line_number INTEGER, -- Melodic line number (e.g. 1, 2, 3...)
    chromatic_feature VARCHAR(255), -- Chromatic feature of the melodic line
    diatonic_feature VARCHAR(255), -- Diatonic feature of the melodic line
    rhythmic_feature VARCHAR(255), -- Rhythmic feature of the melodic line
    -- Foreign key to Score table (relating the melodic line to a score)
    score_id VARCHAR(255) NOT NULL,

    -- Ensures each melodic_line is related to one score
    FOREIGN KEY (score_id) REFERENCES Score(score_id)

);

-- Table: Recording
-- Represents a musical recording with attributes describing it
CREATE TABLE Recording (
    recording_id VARCHAR(255) PRIMARY KEY, -- String identifier for the recording
    musician_code VARCHAR(5), -- Code representing the musician (max 5 characters)
    instrument VARCHAR(50), -- Instrument used in the recording
    format VARCHAR(10), -- Format of the recording (e.g., WAV, MIDI)
    -- Foreign key to Melodic_Line table (relating the recording to a melodic line from a score)
    melodic_line_id VARCHAR(255) NOT NULL, 
    
    -- Ensures each recording is related to one melodic_line
    FOREIGN KEY (melodic_line_id) REFERENCES Melodic_Line(melodic_line_id) 
);

-- Table: Query
-- Represents a query extracted from a recording
CREATE TABLE Query (
    query_id INTEGER PRIMARY KEY, -- Artificial primary key
    start_timestamp INTEGER NOT NULL, -- Start time of the query in the recording in milliseconds
    end_timestamp INTEGER NOT NULL,   -- End time of the query in the recording in milliseconds
    recording_id VARCHAR(255) NOT NULL, -- Foreign key referencing Recording
    
    -- Ensures uniqueness based on (recording_id, start_timestamp, end_timestamp)
    CONSTRAINT unique_query_time UNIQUE (recording_id, start_timestamp, end_timestamp), 
    
    -- Foreign key reference to the Recording table
    FOREIGN KEY (recording_id) REFERENCES Recording(recording_id) 
);

-- Table: Search
-- Represents a search operation with
CREATE TABLE Search (
    search_id INTEGER PRIMARY KEY, -- Artificial primary key
    algorithm VARCHAR(20) NOT NULL CHECK (algorithm IN ('BLAST', 'Approximate_Alignment')), -- Search algorithm used
    search_type VARCHAR(20) NOT NULL CHECK (search_type IN ('chromatic', 'diatonic', 'rhythmic')), -- Type of search
    sequence VARCHAR(20) NOT NULL, -- Query sequence in single-character format employed in the search
    fe_user_ms INT, -- Feature extraction process user time in milliseconds
    fe_system_ms INT, -- Feature extraction process system time in milliseconds
    fe_clock_ms INT, -- Feature extraction process clock time in milliseconds
    alignment_user_ms INT, -- Alignment process user time in milliseconds
    alignment_system_ms INT, -- Alignment process system time in milliseconds
    alignment_clock_ms INT, -- Alignment process clock time in milliseconds
    -- Foreign key referencing Query (relating the search to a specific query)
    query_id INTEGER NOT NULL, 

    -- Natural key to ensure unique searches per query, algorithm and search type
    CONSTRAINT unique_search_algorithm_type_query UNIQUE (query_id, algorithm, search_type),

    -- Foreign key constraint to ensure query_id references a valid Query
    FOREIGN KEY (query_id) REFERENCES Query(query_id)
);

-- Table: Search_Results
-- Represents the results of a search operation
CREATE TABLE Search_Results (
    result_id INTEGER PRIMARY KEY, -- Artificial primary key
    melodic_line_id VARCHAR NOT NULL, -- Foreign key referencing Melodic_Line
    alignment_score FLOAT NOT NULL, -- Score of the alignment
    ranking_position INT NOT NULL, -- Ranking position of the Melodic_Line in the BLAST_Search
    melodic_line_origin_pos INT NOT NULL, -- Origin position of the alignment in the melodic line
    melodic_line_end_pos INT NOT NULL, -- End position of the alignment in the melodic line
    query_origin_pos INT NOT NULL, -- Origin position of the alignment in the query
    query_end_pos INT NOT NULL, -- End position of the alignment in the query
    -- Foreign key referencing Search (relating the result to a specific search)
    search_id INTEGER NOT NULL, -- Foreign key referencing Search

    -- Ensure the combination of search_id and ranking_position is unique
    CONSTRAINT unique_result UNIQUE (search_id, ranking_position),

    -- Foreign key constraints
    FOREIGN KEY (search_id) REFERENCES Search(search_id),
    FOREIGN KEY (melodic_line_id) REFERENCES Melodic_Line(melodic_line_id)
);

-- Table: Global_Alignment
-- Represents a many-to-many relationship between melodic lines with alignment rates
CREATE TABLE Global_Alignment (
    melodic_line_id_1 VARCHAR(255) NOT NULL, -- Foreign key referencing Melodic_Line
    melodic_line_id_2 VARCHAR(255) NOT NULL, -- Foreign key referencing Melodic_Line
    chromatic_rate FLOAT NOT NULL, -- Chromatic alignment rate
    diatonic_rate FLOAT NOT NULL, -- Diatonic alignment rate
    rhythmic_rate FLOAT NOT NULL, -- Rhythmic alignment rate

    -- Ensure the combination of melodic_line_id_1 and melodic_line_id_2 is unique
    CONSTRAINT unique_aligns UNIQUE (melodic_line_id_1, melodic_line_id_2),

    -- Foreign key constraints
    FOREIGN KEY (melodic_line_id_1) REFERENCES Melodic_Line(melodic_line_id),
    FOREIGN KEY (melodic_line_id_2) REFERENCES Melodic_Line(melodic_line_id)
);
