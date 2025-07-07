"""
BSD 2-Clause License

Copyright (c) 2025, Hilda Romero-Velo
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
  Created by Hilda Romero-Velo on January 2025.
"""

"""
  This script analyzes the alignment statistics obtained from the global alignment.
  It returns an Excel file with general statistics from the chromatic, diatonic, 
  and rhythmic rates and the perfect found alignments (those with a rate of 0).
  It also generates distribution plots for each rate.
"""

import os
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


def get_alignment_stats(db_path):
    """
    Get alignment statistics grouped by score.

    Parameters:
        db_path (str): Path to the SQLite database.

    Returns:
        pd.DataFrame: DataFrame with alignment rates for each scores pair.
    """
    conn = sqlite3.connect(db_path)

    query = """
    SELECT 
        s1.score_id as score_id_1,
        s2.score_id as score_id_2,
        ga.chromatic_rate,
        ga.diatonic_rate,
        ga.rhythmic_rate
    FROM Global_Alignment ga
    JOIN Melodic_Line ml1 ON ga.melodic_line_id_1 = ml1.melodic_line_id
    JOIN Melodic_Line ml2 ON ga.melodic_line_id_2 = ml2.melodic_line_id
    JOIN Score s1 ON ml1.score_id = s1.score_id
    JOIN Score s2 ON ml2.score_id = s2.score_id
    """

    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def analyze_rates(df, output_dir):
    """
    Analyze distribution of alignment rates.

    Parameters:
        df (pd.DataFrame): DataFrame with alignment rates.
        output_dir (str): Output directory for results.

    Returns:
        None

    Note:
        Generates an Excel file with general statistics and distribution plots.
    """
    rates = ["chromatic_rate", "diatonic_rate", "rhythmic_rate"]

    os.makedirs(output_dir, exist_ok=True)

    with pd.ExcelWriter(
        os.path.join(output_dir, "global_alignment_analysis.xlsx")
    ) as writer:
        # General statistics
        stats = df[rates].describe()
        stats.to_excel(writer, sheet_name="General_Stats")

        # Count zeros per rate
        zero_counts = {rate: len(df[df[rate] == 0]) for rate in rates}
        pd.DataFrame.from_dict(zero_counts, orient="index", columns=["Count"]).to_excel(
            writer, sheet_name="Zero_Counts"
        )

        # List score pairs with zeros
        for rate in rates:
            zero_pairs = df[df[rate] == 0][["score_id_1", "score_id_2", rate]]
            zero_pairs.to_excel(writer, sheet_name=f"Zero_{rate}", index=False)

    # Generate distribution plots
    for rate in rates:
        plt.figure(figsize=(10, 6))
        sns.histplot(data=df, x=rate, bins=50)
        plt.title(f"Distribution of {rate}")
        plt.xlabel("Rate")
        plt.ylabel("Count")
        plt.savefig(os.path.join(output_dir, f"{rate}_distribution.png"))
        plt.close()

    # Generate a single figure with all three distributions (shared y-axis)
    fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharex=True, sharey=True)
    titles = [
        "Chromatic Distances Distribution",
        "Diatonic Distances Distribution",
        "Rhythmic Distances Distribution",
    ]

    # Define consistent bins for all plots (0 to 800 with 50 bins)
    bins = np.linspace(0, 800, 51)  # 51 endpoints create 50 bins

    # Plot each distribution with consistent bins and formatting
    for i, rate in enumerate(rates):
        sns.histplot(data=df, x=rate, bins=bins, ax=axes[i])
        axes[i].set_title(titles[i], fontsize=14, fontweight="bold")
        axes[i].set_xlabel("Distance", fontsize=12, fontweight="bold")
        if i == 0:  # Only set y-label for the first plot to avoid duplication
            axes[i].set_ylabel("Frequency", fontsize=12, fontweight="bold")
        else:
            axes[i].set_ylabel("")

        # Increase tick label size and make bold
        axes[i].tick_params(axis="both", which="major", labelsize=10)
        for label in axes[i].get_xticklabels() + axes[i].get_yticklabels():
            label.set_fontweight("bold")

    # Set x-axis limit to 800
    for ax in axes:
        ax.set_xlim(0, 800)

    plt.tight_layout()
    plt.savefig(
        os.path.join(output_dir, "combined_distances_distribution_shared_y.png")
    )
    plt.close()

    # Generate a version with separate y-axes to better show each distribution
    fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharex=True)

    # Plot each distribution with its own y-scale, consistent bins, and improved formatting
    for i, rate in enumerate(rates):
        sns.histplot(data=df, x=rate, bins=bins, ax=axes[i])
        axes[i].set_title(titles[i], fontsize=14, fontweight="bold")
        axes[i].set_xlabel("Distance", fontsize=12, fontweight="bold")
        axes[i].set_ylabel("Frequency", fontsize=12, fontweight="bold")
        axes[i].set_xlim(0, 800)  # Apply the x-limit to each plot

        # Increase tick label size and make bold
        axes[i].tick_params(axis="both", which="major", labelsize=10)
        for label in axes[i].get_xticklabels() + axes[i].get_yticklabels():
            label.set_fontweight("bold")

    plt.tight_layout()
    plt.savefig(
        os.path.join(output_dir, "combined_distances_distribution_separate_y.png")
    )
    plt.close()


if __name__ == "__main__":
    script_dir = os.path.dirname(__file__)
    db_path = os.path.join(script_dir, "global_folkoteca.db")
    output_dir = os.path.join(script_dir, "analysis_results")
    df = get_alignment_stats(db_path)
    analyze_rates(df, output_dir)
