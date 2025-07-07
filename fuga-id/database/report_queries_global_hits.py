"""
BSD 2-Clause License

Copyright (c) 2025, Hilda Romero-Velo
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice, this
  list of conditions and the following disclaimer in the documentation
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
  Created by Hilda Romero-Velo on January 2025.
"""

""" 
  This script compiles the database queries to generate the statistics 
  in the analyze_results.py file considering the global alingment results
  to compute the number of hits.
"""

general_metrics = {
    "num_queries": """
        SELECT algorithm, search_type, COUNT(query_id) as num_queries
        FROM search GROUP BY algorithm, search_type;
    """,
    "avg_times": """
        SELECT algorithm, search_type, AVG(fe_user_ms) as fe_user_ms, AVG(fe_system_ms) as fe_system_ms, AVG(fe_clock_ms) as fe_clock_ms, AVG(alignment_user_ms) as alignment_user_ms, AVG(alignment_system_ms) as alignment_system_ms, AVG(alignment_clock_ms) as alignment_clock_ms
        FROM search GROUP BY algorithm, search_type;
    """,
    "count_top_1": """
        SELECT algorithm, search_type, COUNT(DISTINCT s.search_id) as count_top_1
        FROM melodic_line mlr 
        JOIN recording r ON mlr.melodic_line_id = r.melodic_line_id
        JOIN query q ON r.recording_id = q.recording_id
        JOIN search s ON q.query_id = s.query_id
        JOIN search_results sr ON s.search_id = sr.search_id AND sr.ranking_position = 1
        JOIN melodic_line mls ON sr.melodic_line_id = mls.melodic_line_id
        LEFT JOIN Global_Alignment ga1 ON mlr.melodic_line_id = ga1.melodic_line_id_1 AND mls.melodic_line_id = ga1.melodic_line_id_2
        LEFT JOIN Global_Alignment ga2 ON mlr.melodic_line_id = ga2.melodic_line_id_2 AND mls.melodic_line_id = ga2.melodic_line_id_1
        WHERE mlr.score_id = mls.score_id or (ga1.chromatic_rate < 10 AND ga1.diatonic_rate < 10 AND ga1.rhythmic_rate < 10)
           OR (ga2.chromatic_rate < 10 AND ga2.diatonic_rate < 10 AND ga2.rhythmic_rate < 10)
        GROUP BY algorithm, search_type;
    """,
    "count_top_3": """
        SELECT algorithm, search_type, COUNT(DISTINCT s.search_id) as count_top_3
        FROM melodic_line mlr 
        JOIN recording r ON mlr.melodic_line_id = r.melodic_line_id
        JOIN query q ON r.recording_id = q.recording_id
        JOIN search s ON q.query_id = s.query_id
        JOIN search_results sr ON s.search_id = sr.search_id AND sr.ranking_position <= 3
        JOIN melodic_line mls ON sr.melodic_line_id = mls.melodic_line_id
        LEFT JOIN Global_Alignment ga1 ON mlr.melodic_line_id = ga1.melodic_line_id_1 AND mls.melodic_line_id = ga1.melodic_line_id_2
        LEFT JOIN Global_Alignment ga2 ON mlr.melodic_line_id = ga2.melodic_line_id_2 AND mls.melodic_line_id = ga2.melodic_line_id_1
        WHERE mlr.score_id = mls.score_id or (ga1.chromatic_rate < 10 AND ga1.diatonic_rate < 10 AND ga1.rhythmic_rate < 10)
           OR (ga2.chromatic_rate < 10 AND ga2.diatonic_rate < 10 AND ga2.rhythmic_rate < 10)
        GROUP BY algorithm, search_type;
    """,
    "count_top_5": """
        SELECT algorithm, search_type, COUNT(DISTINCT s.search_id) as count_top_5
        FROM melodic_line mlr 
        JOIN recording r ON mlr.melodic_line_id = r.melodic_line_id
        JOIN query q ON r.recording_id = q.recording_id
        JOIN search s ON q.query_id = s.query_id
        JOIN search_results sr ON s.search_id = sr.search_id AND sr.ranking_position <= 5
        JOIN melodic_line mls ON sr.melodic_line_id = mls.melodic_line_id
        LEFT JOIN Global_Alignment ga1 ON mlr.melodic_line_id = ga1.melodic_line_id_1 AND mls.melodic_line_id = ga1.melodic_line_id_2
        LEFT JOIN Global_Alignment ga2 ON mlr.melodic_line_id = ga2.melodic_line_id_2 AND mls.melodic_line_id = ga2.melodic_line_id_1
        WHERE mlr.score_id = mls.score_id or (ga1.chromatic_rate < 10 AND ga1.diatonic_rate < 10 AND ga1.rhythmic_rate < 10)
           OR (ga2.chromatic_rate < 10 AND ga2.diatonic_rate < 10 AND ga2.rhythmic_rate < 10)
        GROUP BY algorithm, search_type;
    """,
    "mrr_sum": """
        SELECT algorithm, search_type, SUM(1.0/ranking_position) as sum_ranking_pos FROM 
        (SELECT s.search_id, s.algorithm, s.search_type, MIN(sr.ranking_position) as ranking_position
        FROM melodic_line mlr 
        JOIN recording r ON mlr.melodic_line_id = r.melodic_line_id
        JOIN query q ON r.recording_id = q.recording_id
        JOIN search s ON q.query_id = s.query_id
        JOIN search_results sr ON s.search_id = sr.search_id
        JOIN melodic_line mls ON sr.melodic_line_id = mls.melodic_line_id
        LEFT JOIN Global_Alignment ga1 ON mlr.melodic_line_id = ga1.melodic_line_id_1 AND mls.melodic_line_id = ga1.melodic_line_id_2
        LEFT JOIN Global_Alignment ga2 ON mlr.melodic_line_id = ga2.melodic_line_id_2 AND mls.melodic_line_id = ga2.melodic_line_id_1
        WHERE mlr.score_id = mls.score_id or (ga1.chromatic_rate < 10 AND ga1.diatonic_rate < 10 AND ga1.rhythmic_rate < 10)
           OR (ga2.chromatic_rate < 10 AND ga2.diatonic_rate < 10 AND ga2.rhythmic_rate < 10)
        GROUP BY s.search_id, s.algorithm, s.search_type)
        GROUP BY algorithm, search_type;
    """,
}


metrics_by_instrument = {
    "num_queries": """
        SELECT instrument, algorithm, search_type, COUNT(DISTINCT q.query_id) as num_queries
        FROM search s JOIN query q ON s.query_id = q.query_id JOIN recording r ON q.recording_id = r.recording_id 
        GROUP BY instrument, algorithm, search_type;
    """,
    "count_top_1": """
        SELECT instrument, algorithm, search_type, COUNT(DISTINCT s.search_id) as count_top_1
        FROM melodic_line mlr 
        JOIN recording r ON mlr.melodic_line_id = r.melodic_line_id
        JOIN query q ON r.recording_id = q.recording_id
        JOIN search s ON q.query_id = s.query_id
        JOIN search_results sr ON s.search_id = sr.search_id AND sr.ranking_position = 1
        JOIN melodic_line mls ON sr.melodic_line_id = mls.melodic_line_id
        LEFT JOIN Global_Alignment ga1 ON mlr.melodic_line_id = ga1.melodic_line_id_1 AND mls.melodic_line_id = ga1.melodic_line_id_2
        LEFT JOIN Global_Alignment ga2 ON mlr.melodic_line_id = ga2.melodic_line_id_2 AND mls.melodic_line_id = ga2.melodic_line_id_1
        WHERE mlr.score_id = mls.score_id or (ga1.chromatic_rate < 10 AND ga1.diatonic_rate < 10 AND ga1.rhythmic_rate < 10)
           OR (ga2.chromatic_rate < 10 AND ga2.diatonic_rate < 10 AND ga2.rhythmic_rate < 10)
        GROUP BY instrument, algorithm, search_type;
    """,
    "count_top_3": """
        SELECT instrument, algorithm, search_type, COUNT(DISTINCT s.search_id) as count_top_3
        FROM melodic_line mlr 
        JOIN recording r ON mlr.melodic_line_id = r.melodic_line_id
        JOIN query q ON r.recording_id = q.recording_id
        JOIN search s ON q.query_id = s.query_id
        JOIN search_results sr ON s.search_id = sr.search_id AND sr.ranking_position <= 3
        JOIN melodic_line mls ON sr.melodic_line_id = mls.melodic_line_id
        LEFT JOIN Global_Alignment ga1 ON mlr.melodic_line_id = ga1.melodic_line_id_1 AND mls.melodic_line_id = ga1.melodic_line_id_2
        LEFT JOIN Global_Alignment ga2 ON mlr.melodic_line_id = ga2.melodic_line_id_2 AND mls.melodic_line_id = ga2.melodic_line_id_1
        WHERE mlr.score_id = mls.score_id or (ga1.chromatic_rate < 10 AND ga1.diatonic_rate < 10 AND ga1.rhythmic_rate < 10)
           OR (ga2.chromatic_rate < 10 AND ga2.diatonic_rate < 10 AND ga2.rhythmic_rate < 10)
        GROUP BY instrument, algorithm, search_type;
    """,
    "count_top_5": """
        SELECT instrument, algorithm, search_type, COUNT(DISTINCT s.search_id) as count_top_5
        FROM melodic_line mlr 
        JOIN recording r ON mlr.melodic_line_id = r.melodic_line_id
        JOIN query q ON r.recording_id = q.recording_id
        JOIN search s ON q.query_id = s.query_id
        JOIN search_results sr ON s.search_id = sr.search_id AND sr.ranking_position <= 5
        JOIN melodic_line mls ON sr.melodic_line_id = mls.melodic_line_id
        LEFT JOIN Global_Alignment ga1 ON mlr.melodic_line_id = ga1.melodic_line_id_1 AND mls.melodic_line_id = ga1.melodic_line_id_2
        LEFT JOIN Global_Alignment ga2 ON mlr.melodic_line_id = ga2.melodic_line_id_2 AND mls.melodic_line_id = ga2.melodic_line_id_1
        WHERE mlr.score_id = mls.score_id or (ga1.chromatic_rate < 10 AND ga1.diatonic_rate < 10 AND ga1.rhythmic_rate < 10)
           OR (ga2.chromatic_rate < 10 AND ga2.diatonic_rate < 10 AND ga2.rhythmic_rate < 10)
        GROUP BY instrument, algorithm, search_type;
    """,
    "mrr_sum": """
        SELECT instrument, algorithm, search_type, SUM(1.0/ranking_position) as sum_ranking_pos FROM 
        (SELECT s.search_id, instrument, s.algorithm, s.search_type, MIN(sr.ranking_position) as ranking_position
        FROM melodic_line mlr 
        JOIN recording r ON mlr.melodic_line_id = r.melodic_line_id
        JOIN query q ON r.recording_id = q.recording_id
        JOIN search s ON q.query_id = s.query_id
        JOIN search_results sr ON s.search_id = sr.search_id
        JOIN melodic_line mls ON sr.melodic_line_id = mls.melodic_line_id
        LEFT JOIN Global_Alignment ga1 ON mlr.melodic_line_id = ga1.melodic_line_id_1 AND mls.melodic_line_id = ga1.melodic_line_id_2
        LEFT JOIN Global_Alignment ga2 ON mlr.melodic_line_id = ga2.melodic_line_id_2 AND mls.melodic_line_id = ga2.melodic_line_id_1
        WHERE mlr.score_id = mls.score_id or (ga1.chromatic_rate < 10 AND ga1.diatonic_rate < 10 AND ga1.rhythmic_rate < 10)
           OR (ga2.chromatic_rate < 10 AND ga2.diatonic_rate < 10 AND ga2.rhythmic_rate < 10)
        GROUP BY s.search_id, instrument, s.algorithm, s.search_type)
        GROUP BY instrument, algorithm, search_type;
    """,
}

metrics_by_musical_form = {
    "num_queries": """
        SELECT musical_form, algorithm, search_type, COUNT(DISTINCT q.query_id) as num_queries
        FROM search s JOIN query q ON s.query_id = s.query_id JOIN recording r ON q.recording_id = r.recording_id
        JOIN melodic_line ml ON ml.melodic_line_id = r.melodic_line_id JOIN score sc ON ml.score_id = sc.score_id
        GROUP BY musical_form, algorithm, search_type;
    """,
    "count_top_1": """
        SELECT musical_form, algorithm, search_type, COUNT(DISTINCT s.search_id) as count_top_1
        FROM melodic_line mlr 
        JOIN recording r ON mlr.melodic_line_id = r.melodic_line_id
        JOIN query q ON r.recording_id = q.recording_id
        JOIN search s ON q.query_id = s.query_id
        JOIN search_results sr ON s.search_id = sr.search_id AND sr.ranking_position = 1
        JOIN melodic_line mls ON sr.melodic_line_id = mls.melodic_line_id
        JOIN score sc ON sc.score_id = mlr.score_id
        LEFT JOIN Global_Alignment ga1 ON mlr.melodic_line_id = ga1.melodic_line_id_1 AND mls.melodic_line_id = ga1.melodic_line_id_2
        LEFT JOIN Global_Alignment ga2 ON mlr.melodic_line_id = ga2.melodic_line_id_2 AND mls.melodic_line_id = ga2.melodic_line_id_1
        WHERE mlr.score_id = mls.score_id or (ga1.chromatic_rate < 10 AND ga1.diatonic_rate < 10 AND ga1.rhythmic_rate < 10)
           OR (ga2.chromatic_rate < 10 AND ga2.diatonic_rate < 10 AND ga2.rhythmic_rate < 10)
        GROUP BY musical_form, algorithm, search_type;
    """,
    "count_top_3": """
        SELECT musical_form, algorithm, search_type, COUNT(DISTINCT s.search_id) as count_top_3
        FROM melodic_line mlr 
        JOIN recording r ON mlr.melodic_line_id = r.melodic_line_id
        JOIN query q ON r.recording_id = q.recording_id
        JOIN search s ON q.query_id = s.query_id
        JOIN search_results sr ON s.search_id = sr.search_id AND sr.ranking_position <= 3
        JOIN melodic_line mls ON sr.melodic_line_id = mls.melodic_line_id
        JOIN score sc ON sc.score_id = mlr.score_id
        LEFT JOIN Global_Alignment ga1 ON mlr.melodic_line_id = ga1.melodic_line_id_1 AND mls.melodic_line_id = ga1.melodic_line_id_2
        LEFT JOIN Global_Alignment ga2 ON mlr.melodic_line_id = ga2.melodic_line_id_2 AND mls.melodic_line_id = ga2.melodic_line_id_1
        WHERE mlr.score_id = mls.score_id or (ga1.chromatic_rate < 10 AND ga1.diatonic_rate < 10 AND ga1.rhythmic_rate < 10)
           OR (ga2.chromatic_rate < 10 AND ga2.diatonic_rate < 10 AND ga2.rhythmic_rate < 10)
        GROUP BY musical_form, algorithm, search_type;
    """,
    "count_top_5": """
        SELECT musical_form, algorithm, search_type, COUNT(DISTINCT s.search_id) as count_top_5
        FROM melodic_line mlr 
        JOIN recording r ON mlr.melodic_line_id = r.melodic_line_id
        JOIN query q ON r.recording_id = q.recording_id
        JOIN search s ON q.query_id = s.query_id
        JOIN search_results sr ON s.search_id = sr.search_id AND sr.ranking_position <= 5
        JOIN melodic_line mls ON sr.melodic_line_id = mls.melodic_line_id
        JOIN score sc ON sc.score_id = mlr.score_id
        LEFT JOIN Global_Alignment ga1 ON mlr.melodic_line_id = ga1.melodic_line_id_1 AND mls.melodic_line_id = ga1.melodic_line_id_2
        LEFT JOIN Global_Alignment ga2 ON mlr.melodic_line_id = ga2.melodic_line_id_2 AND mls.melodic_line_id = ga2.melodic_line_id_1
        WHERE mlr.score_id = mls.score_id or (ga1.chromatic_rate < 10 AND ga1.diatonic_rate < 10 AND ga1.rhythmic_rate < 10)
           OR (ga2.chromatic_rate < 10 AND ga2.diatonic_rate < 10 AND ga2.rhythmic_rate < 10)
        GROUP BY musical_form, algorithm, search_type;
    """,
    "mrr_sum": """
        SELECT musical_form, algorithm, search_type, SUM(1.0/ranking_position) as sum_ranking_pos FROM 
        (SELECT s.search_id, musical_form, s.algorithm, s.search_type, MIN(sr.ranking_position) as ranking_position
        FROM melodic_line mlr 
        JOIN recording r ON mlr.melodic_line_id = r.melodic_line_id
        JOIN query q ON r.recording_id = q.recording_id
        JOIN search s ON q.query_id = s.query_id
        JOIN search_results sr ON s.search_id = sr.search_id
        JOIN melodic_line mls ON sr.melodic_line_id = mls.melodic_line_id
        JOIN score sc ON sc.score_id = mlr.score_id
        LEFT JOIN Global_Alignment ga1 ON mlr.melodic_line_id = ga1.melodic_line_id_1 AND mls.melodic_line_id = ga1.melodic_line_id_2
        LEFT JOIN Global_Alignment ga2 ON mlr.melodic_line_id = ga2.melodic_line_id_2 AND mls.melodic_line_id = ga2.melodic_line_id_1
        WHERE mlr.score_id = mls.score_id or (ga1.chromatic_rate < 10 AND ga1.diatonic_rate < 10 AND ga1.rhythmic_rate < 10)
           OR (ga2.chromatic_rate < 10 AND ga2.diatonic_rate < 10 AND ga2.rhythmic_rate < 10)
        GROUP BY s.search_id, musical_form, s.algorithm, s.search_type)
        GROUP BY musical_form, algorithm, search_type;
    """,
}

metrics_by_query_sequence = {
    "num_queries": """
        SELECT algorithm, search_type,                
        CASE 
            WHEN LENGTH(sequence) < 10 THEN '<10'
            WHEN LENGTH(sequence) BETWEEN 10 AND 15 THEN '10-15'
            WHEN LENGTH(sequence) BETWEEN 15 AND 20 THEN '15-20'
            WHEN LENGTH(sequence) BETWEEN 20 AND 25 THEN '20-25'
            WHEN LENGTH(sequence) BETWEEN 25 AND 30 THEN '25-30'
            WHEN LENGTH(sequence) BETWEEN 30 AND 35 THEN '30-35'
            WHEN LENGTH(sequence) BETWEEN 35 AND 40 THEN '35-40'
            WHEN LENGTH(sequence) BETWEEN 40 AND 45 THEN '40-45'
            WHEN LENGTH(sequence) BETWEEN 45 AND 50 THEN '45-50'
            ELSE '>50' END AS sequence_length, 
        COUNT(DISTINCT query_id) as num_queries
        FROM search 
        GROUP BY sequence_length, algorithm, search_type;
    """,
    "count_top_1": """
        SELECT algorithm, search_type,
        CASE 
            WHEN LENGTH(sequence) < 10 THEN '<10'
            WHEN LENGTH(sequence) BETWEEN 10 AND 15 THEN '10-15'
            WHEN LENGTH(sequence) BETWEEN 15 AND 20 THEN '15-20'
            WHEN LENGTH(sequence) BETWEEN 20 AND 25 THEN '20-25'
            WHEN LENGTH(sequence) BETWEEN 25 AND 30 THEN '25-30'
            WHEN LENGTH(sequence) BETWEEN 30 AND 35 THEN '30-35'
            WHEN LENGTH(sequence) BETWEEN 35 AND 40 THEN '35-40'
            WHEN LENGTH(sequence) BETWEEN 40 AND 45 THEN '40-45'
            WHEN LENGTH(sequence) BETWEEN 45 AND 50 THEN '45-50'
            ELSE '>50' END AS sequence_length, 
        COUNT(DISTINCT s.search_id) as count_top_1
        FROM melodic_line mlr JOIN recording r ON mlr.melodic_line_id = r.melodic_line_id
        JOIN query q ON r.recording_id = q.recording_id
        JOIN search s ON q.query_id = s.query_id
        JOIN search_results sr ON s.search_id = sr.search_id AND sr.ranking_position = 1
        JOIN melodic_line mls ON sr.melodic_line_id = mls.melodic_line_id
        LEFT JOIN Global_Alignment ga1 ON mlr.melodic_line_id = ga1.melodic_line_id_1 AND mls.melodic_line_id = ga1.melodic_line_id_2
        LEFT JOIN Global_Alignment ga2 ON mlr.melodic_line_id = ga2.melodic_line_id_2 AND mls.melodic_line_id = ga2.melodic_line_id_1
        WHERE mlr.score_id = mls.score_id or (ga1.chromatic_rate < 10 AND ga1.diatonic_rate < 10 AND ga1.rhythmic_rate < 10)
           OR (ga2.chromatic_rate < 10 AND ga2.diatonic_rate < 10 AND ga2.rhythmic_rate < 10)
        GROUP BY algorithm, search_type, sequence_length;
    """,
    "count_top_3": """
        SELECT algorithm, search_type, 
        CASE 
            WHEN LENGTH(sequence) < 10 THEN '<10'
            WHEN LENGTH(sequence) BETWEEN 10 AND 15 THEN '10-15'
            WHEN LENGTH(sequence) BETWEEN 15 AND 20 THEN '15-20'
            WHEN LENGTH(sequence) BETWEEN 20 AND 25 THEN '20-25'
            WHEN LENGTH(sequence) BETWEEN 25 AND 30 THEN '25-30'
            WHEN LENGTH(sequence) BETWEEN 30 AND 35 THEN '30-35'
            WHEN LENGTH(sequence) BETWEEN 35 AND 40 THEN '35-40'
            WHEN LENGTH(sequence) BETWEEN 40 AND 45 THEN '40-45'
            WHEN LENGTH(sequence) BETWEEN 45 AND 50 THEN '45-50'
            ELSE '>50' END AS sequence_length, 
        COUNT(DISTINCT s.search_id) as count_top_3
        FROM melodic_line mlr JOIN recording r ON mlr.melodic_line_id = r.melodic_line_id
        JOIN query q ON r.recording_id = q.recording_id
        JOIN search s ON q.query_id = s.query_id
        JOIN search_results sr ON s.search_id = sr.search_id AND sr.ranking_position <= 3
        JOIN melodic_line mls ON sr.melodic_line_id = mls.melodic_line_id
        LEFT JOIN Global_Alignment ga1 ON mlr.melodic_line_id = ga1.melodic_line_id_1 AND mls.melodic_line_id = ga1.melodic_line_id_2
        LEFT JOIN Global_Alignment ga2 ON mlr.melodic_line_id = ga2.melodic_line_id_2 AND mls.melodic_line_id = ga2.melodic_line_id_1
        WHERE mlr.score_id = mls.score_id or (ga1.chromatic_rate < 10 AND ga1.diatonic_rate < 10 AND ga1.rhythmic_rate < 10)
           OR (ga2.chromatic_rate < 10 AND ga2.diatonic_rate < 10 AND ga2.rhythmic_rate < 10)
        GROUP BY algorithm, search_type, sequence_length;
    """,
    "count_top_5": """
        SELECT algorithm, search_type, 
        CASE 
            WHEN LENGTH(sequence) < 10 THEN '<10'
            WHEN LENGTH(sequence) BETWEEN 10 AND 15 THEN '10-15'
            WHEN LENGTH(sequence) BETWEEN 15 AND 20 THEN '15-20'
            WHEN LENGTH(sequence) BETWEEN 20 AND 25 THEN '20-25'
            WHEN LENGTH(sequence) BETWEEN 25 AND 30 THEN '25-30'
            WHEN LENGTH(sequence) BETWEEN 30 AND 35 THEN '30-35'
            WHEN LENGTH(sequence) BETWEEN 35 AND 40 THEN '35-40'
            WHEN LENGTH(sequence) BETWEEN 40 AND 45 THEN '40-45'
            WHEN LENGTH(sequence) BETWEEN 45 AND 50 THEN '45-50'
            ELSE '>50' END AS sequence_length, 
        COUNT(DISTINCT s.search_id) as count_top_5
        FROM melodic_line mlr JOIN recording r ON mlr.melodic_line_id = r.melodic_line_id
        JOIN query q ON r.recording_id = q.recording_id
        JOIN search s ON q.query_id = s.query_id
        JOIN search_results sr ON s.search_id = sr.search_id AND sr.ranking_position <=5
        JOIN melodic_line mls ON sr.melodic_line_id = mls.melodic_line_id
        LEFT JOIN Global_Alignment ga1 ON mlr.melodic_line_id = ga1.melodic_line_id_1 AND mls.melodic_line_id = ga1.melodic_line_id_2
        LEFT JOIN Global_Alignment ga2 ON mlr.melodic_line_id = ga2.melodic_line_id_2 AND mls.melodic_line_id = ga2.melodic_line_id_1
        WHERE mlr.score_id = mls.score_id or (ga1.chromatic_rate < 10 AND ga1.diatonic_rate < 10 AND ga1.rhythmic_rate < 10)
           OR (ga2.chromatic_rate < 10 AND ga2.diatonic_rate < 10 AND ga2.rhythmic_rate < 10)
        GROUP BY algorithm, search_type, sequence_length;
    """,
    "mrr_sum": """
        SELECT algorithm, search_type, 
        CASE 
            WHEN LENGTH(sequence) < 10 THEN '<10'
            WHEN LENGTH(sequence) BETWEEN 10 AND 15 THEN '10-15'
            WHEN LENGTH(sequence) BETWEEN 15 AND 20 THEN '15-20'
            WHEN LENGTH(sequence) BETWEEN 20 AND 25 THEN '20-25'
            WHEN LENGTH(sequence) BETWEEN 25 AND 30 THEN '25-30'
            WHEN LENGTH(sequence) BETWEEN 30 AND 35 THEN '30-35'
            WHEN LENGTH(sequence) BETWEEN 35 AND 40 THEN '35-40'
            WHEN LENGTH(sequence) BETWEEN 40 AND 45 THEN '40-45'
            WHEN LENGTH(sequence) BETWEEN 45 AND 50 THEN '45-50'
            ELSE '>50' END AS sequence_length, 
        SUM(1.0/ranking_position) as sum_ranking_pos FROM 
        (SELECT s.search_id, sequence, s.algorithm, s.search_type, MIN(sr.ranking_position) as ranking_position
        FROM melodic_line mlr JOIN recording r ON mlr.melodic_line_id = r.melodic_line_id
        JOIN query q ON r.recording_id = q.recording_id
        JOIN search s ON q.query_id = s.query_id
        JOIN search_results sr ON s.search_id = sr.search_id
        JOIN melodic_line mls ON sr.melodic_line_id = mls.melodic_line_id
        LEFT JOIN Global_Alignment ga1 ON mlr.melodic_line_id = ga1.melodic_line_id_1 AND mls.melodic_line_id = ga1.melodic_line_id_2
        LEFT JOIN Global_Alignment ga2 ON mlr.melodic_line_id = ga2.melodic_line_id_2 AND mls.melodic_line_id = ga2.melodic_line_id_1
        WHERE mlr.score_id = mls.score_id or (ga1.chromatic_rate < 10 AND ga1.diatonic_rate < 10 AND ga1.rhythmic_rate < 10)
           OR (ga2.chromatic_rate < 10 AND ga2.diatonic_rate < 10 AND ga2.rhythmic_rate < 10)
        GROUP BY s.search_id, sequence, s.algorithm, s.search_type)
        GROUP BY algorithm, search_type, sequence_length;
    """,
}

metrics_by_score = {
    "num_queries": """
        SELECT score_id as score, algorithm, search_type, COUNT(DISTINCT q.query_id) as num_queries
        FROM search s 
        JOIN query q ON s.query_id = q.query_id 
        JOIN recording r ON q.recording_id = r.recording_id
        JOIN melodic_line ml ON r.melodic_line_id = ml.melodic_line_id 
        GROUP BY score_id, algorithm, search_type;
    """,
    "count_top_1": """
        SELECT mlr.score_id as score, algorithm, search_type, COUNT(DISTINCT sr.search_id) as count_top_1
        FROM melodic_line mlr 
        JOIN recording r ON mlr.melodic_line_id = r.melodic_line_id
        JOIN query q ON r.recording_id = q.recording_id
        JOIN search s ON q.query_id = s.query_id
        JOIN search_results sr ON s.search_id = sr.search_id AND sr.ranking_position = 1
        JOIN melodic_line mls ON sr.melodic_line_id = mls.melodic_line_id
        LEFT JOIN Global_Alignment ga1 ON mlr.melodic_line_id = ga1.melodic_line_id_1 AND mls.melodic_line_id = ga1.melodic_line_id_2
        LEFT JOIN Global_Alignment ga2 ON mlr.melodic_line_id = ga2.melodic_line_id_2 AND mls.melodic_line_id = ga2.melodic_line_id_1
        WHERE mlr.score_id = mls.score_id or (ga1.chromatic_rate < 10 AND ga1.diatonic_rate < 10 AND ga1.rhythmic_rate < 10)
           OR (ga2.chromatic_rate < 10 AND ga2.diatonic_rate < 10 AND ga2.rhythmic_rate < 10)
        GROUP BY mlr.score_id, algorithm, search_type;
    """,
    "count_top_3": """
        SELECT mlr.score_id as score, algorithm, search_type, COUNT(DISTINCT sr.search_id) as count_top_3
        FROM melodic_line mlr 
        JOIN recording r ON mlr.melodic_line_id = r.melodic_line_id
        JOIN query q ON r.recording_id = q.recording_id
        JOIN search s ON q.query_id = s.query_id
        JOIN search_results sr ON s.search_id = sr.search_id AND sr.ranking_position <= 3
        JOIN melodic_line mls ON sr.melodic_line_id = mls.melodic_line_id
        LEFT JOIN Global_Alignment ga1 ON mlr.melodic_line_id = ga1.melodic_line_id_1 AND mls.melodic_line_id = ga1.melodic_line_id_2
        LEFT JOIN Global_Alignment ga2 ON mlr.melodic_line_id = ga2.melodic_line_id_2 AND mls.melodic_line_id = ga2.melodic_line_id_1
        WHERE mlr.score_id = mls.score_id or (ga1.chromatic_rate < 10 AND ga1.diatonic_rate < 10 AND ga1.rhythmic_rate < 10)
           OR (ga2.chromatic_rate < 10 AND ga2.diatonic_rate < 10 AND ga2.rhythmic_rate < 10)
        GROUP BY mlr.score_id, algorithm, search_type;
    """,
    "count_top_5": """
        SELECT mlr.score_id as score, algorithm, search_type, COUNT(DISTINCT sr.search_id) as count_top_5
        FROM melodic_line mlr 
        JOIN recording r ON mlr.melodic_line_id = r.melodic_line_id
        JOIN query q ON r.recording_id = q.recording_id
        JOIN search s ON q.query_id = s.query_id
        JOIN search_results sr ON s.search_id = sr.search_id AND sr.ranking_position <= 5
        JOIN melodic_line mls ON sr.melodic_line_id = mls.melodic_line_id
        LEFT JOIN Global_Alignment ga1 ON mlr.melodic_line_id = ga1.melodic_line_id_1 AND mls.melodic_line_id = ga1.melodic_line_id_2
        LEFT JOIN Global_Alignment ga2 ON mlr.melodic_line_id = ga2.melodic_line_id_2 AND mls.melodic_line_id = ga2.melodic_line_id_1
        WHERE mlr.score_id = mls.score_id or (ga1.chromatic_rate < 10 AND ga1.diatonic_rate < 10 AND ga1.rhythmic_rate < 10)
           OR (ga2.chromatic_rate < 10 AND ga2.diatonic_rate < 10 AND ga2.rhythmic_rate < 10)
        GROUP BY mlr.score_id, algorithm, search_type;
    """,
    "mrr_sum": """
        SELECT score_id as score, algorithm, search_type, SUM(1.0/ranking_position) as sum_ranking_pos FROM 
        (SELECT s.search_id, mlr.score_id as score_id, s.algorithm, s.search_type, MIN(sr.ranking_position) as ranking_position
        FROM melodic_line mlr 
        JOIN recording r ON mlr.melodic_line_id = r.melodic_line_id
        JOIN query q ON r.recording_id = q.recording_id
        JOIN search s ON q.query_id = s.query_id
        JOIN search_results sr ON s.search_id = sr.search_id
        JOIN melodic_line mls ON sr.melodic_line_id = mls.melodic_line_id
        LEFT JOIN Global_Alignment ga1 ON mlr.melodic_line_id = ga1.melodic_line_id_1 AND mls.melodic_line_id = ga1.melodic_line_id_2
        LEFT JOIN Global_Alignment ga2 ON mlr.melodic_line_id = ga2.melodic_line_id_2 AND mls.melodic_line_id = ga2.melodic_line_id_1
        WHERE mlr.score_id = mls.score_id or (ga1.chromatic_rate < 10 AND ga1.diatonic_rate < 10 AND ga1.rhythmic_rate < 10)
           OR (ga2.chromatic_rate < 10 AND ga2.diatonic_rate < 10 AND ga2.rhythmic_rate < 10)
        GROUP BY s.search_id, mlr.score_id, s.algorithm, s.search_type)
        GROUP BY score_id, algorithm, search_type;
    """,
}
