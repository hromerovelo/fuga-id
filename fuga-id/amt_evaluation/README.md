# AMT Evaluation Module

**Version:** 1.0.0  
**License:** BSD 2-Clause

Unified module for evaluating AMT (Automatic Music Transcription) systems with metrics that are useful for folk melody retrieval.

## Structure

```text
amt_evaluation/
├── __init__.py
├── README.md
├── amt_wrapper.py
├── evaluate_amt.py
├── generate_amt_report.py
├── generate_comparison_excel.py
├── metrics.py
├── midi_comparison.py
├── run_full_evaluation.py
└── core/
    ├── __init__.py
    ├── audio_synthesis.py
    ├── file_mapping.py
    └── interval_extraction.py
```

## What It Evaluates

The pipeline supports three scenarios:

1. `synthesized`: MIDI -> synthesized WAV -> AMT -> compare with source MIDI
2. `piano_wav`: piano WAV -> AMT -> compare with matching piano MIDI
3. `instruments`: real instrument WAV -> AMT -> compare with:
   - piano MIDI (`ground_truth_type = piano_midi`)
   - original score MIDI (`ground_truth_type = original_score`)

## Main Metrics

1. Note-level metrics (via `mir_eval`): precision, recall, F1
2. Interval-level metrics: relative melodic interval similarity/accuracy
3. Rhythm-level metrics: relative duration pattern similarity/accuracy
4. Timing metrics: transcription runtime per file

For folk melody retrieval, prioritize interval and rhythm metrics over strict note-level F1.

## Quick Usage

Run one AMT system:

```bash
cd fuga-id/amt_evaluation
python evaluate_amt.py \
  --mode all \
  --amt-system basic-pitch \
  --output ./results/amt_results.csv
```

Run the full matrix (systems x scenarios):

```bash
python run_full_evaluation.py
```

Generate text report:

```bash
python generate_amt_report.py \
  --input ./results/amt_results.csv \
  --output ./results/amt_report.txt
```

Generate comparative Excel:

```bash
python generate_comparison_excel.py \
  --input ./results/amt_results.csv \
  --output ./results/amt_comparison.xlsx
```

## Notes

1. Real instrument audio is expected to produce lower strict note-level scores than synthesized baseline audio.
2. For search use cases, interval and rhythm robustness are generally more informative than exact pitch/timing match.
