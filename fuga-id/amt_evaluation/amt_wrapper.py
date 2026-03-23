#!/usr/bin/env python3
"""
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
"""

"""
    Created by Hilda Romero-Velo on February 2026.
"""

"""
AMT (Automatic Music Transcription) wrapper.

Unified interface for multiple AMT systems used in this project:
- basic-pitch (Spotify)
- Swift-F0
- CREPE-Notes (https://github.com/xavriley/crepe_notes)
- pYIN (librosa)

This wrapper will synthesize MIDI inputs to WAV (using `timidity` or `fluidsynth`) when needed.
"""

import argparse
import os
import sys
import time
import tempfile
import subprocess
import warnings
import shutil

warnings.filterwarnings("ignore")


def ensure_audio(input_path):
    """If given a MIDI file, synthesize it to a temporary WAV and return (path, is_temp).

    Requires `timidity` or `fluidsynth` (with an available SF2) on PATH.
    """
    ext = os.path.splitext(input_path)[1].lower()
    if ext not in (".mid", ".midi"):
        return input_path, False

    out_tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    out_path = out_tmp.name
    out_tmp.close()

    if shutil.which("timidity"):
        cmd = ["timidity", input_path, "-Ow", "-o", out_path]
    elif shutil.which("fluidsynth"):
        sf2_candidates = [
            "/usr/share/sounds/sf2/FluidR3_GM.sf2",
            "/usr/share/soundfonts/FluidR3_GM.sf2",
            "/usr/share/soundfonts/GeneralUser_GS.sf2",
        ]
        sf2 = next((p for p in sf2_candidates if os.path.exists(p)), None)
        if sf2:
            cmd = ["fluidsynth", "-ni", sf2, input_path, "-F", out_path, "-r", "44100"]
        else:
            raise RuntimeError(
                "fluidsynth found but no SF2 soundfont located. Install a soundfont or install timidity."
            )
    else:
        raise RuntimeError("No MIDI renderer found: install timidity or fluidsynth")

    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return out_path, True


# Import core libraries
try:
    import librosa
    import numpy as np
    import pretty_midi
except ImportError as e:
    print(f"Error: Missing required library: {e}", file=sys.stderr)
    print("Install with: pip install librosa numpy pretty-midi", file=sys.stderr)
    sys.exit(1)


def f0_to_midi(f0_contour, sample_rate, hop_length=512, threshold=0.0):
    midi = pretty_midi.PrettyMIDI()
    instrument = pretty_midi.Instrument(program=0)

    midi_notes = np.zeros_like(f0_contour)
    valid = f0_contour > threshold
    midi_notes[valid] = librosa.hz_to_midi(f0_contour[valid])

    if not np.any(valid):
        midi.instruments.append(instrument)
        return midi

    midi_notes_rounded = np.round(midi_notes).astype(int)
    diff = np.diff(midi_notes_rounded, prepend=0)
    note_starts = np.where(diff != 0)[0]

    times = librosa.frames_to_time(
        np.arange(len(f0_contour)), sr=sample_rate, hop_length=hop_length
    )

    for i in range(len(note_starts) - 1):
        start_idx = note_starts[i]
        end_idx = note_starts[i + 1]
        if valid[start_idx]:
            pitch = int(midi_notes_rounded[start_idx])
            if 0 <= pitch <= 127:
                note = pretty_midi.Note(
                    velocity=80, pitch=pitch, start=times[start_idx], end=times[end_idx]
                )
                instrument.notes.append(note)

    midi.instruments.append(instrument)
    return midi


def f0_contour_to_midi(times, frequencies, confidence, threshold=0.5):
    midi = pretty_midi.PrettyMIDI()
    instrument = pretty_midi.Instrument(program=0)

    valid = (confidence > threshold) & ~np.isnan(frequencies) & (frequencies > 0)

    if not np.any(valid):
        midi.instruments.append(instrument)
        return midi

    midi_notes = np.zeros_like(frequencies)
    midi_notes[valid] = librosa.hz_to_midi(frequencies[valid])
    midi_notes_rounded = np.round(midi_notes).astype(int)

    in_note = False
    current_pitch = 0
    note_start_time = 0.0

    for i in range(len(times)):
        if valid[i]:
            pitch = midi_notes_rounded[i]
            if not in_note:
                in_note = True
                current_pitch = pitch
                note_start_time = times[i]
            elif pitch != current_pitch:
                if 0 <= current_pitch <= 127:
                    note = pretty_midi.Note(
                        velocity=80,
                        pitch=current_pitch,
                        start=note_start_time,
                        end=times[i],
                    )
                    instrument.notes.append(note)
                current_pitch = pitch
                note_start_time = times[i]
        else:
            if in_note:
                if 0 <= current_pitch <= 127:
                    note = pretty_midi.Note(
                        velocity=80,
                        pitch=current_pitch,
                        start=note_start_time,
                        end=times[i],
                    )
                    instrument.notes.append(note)
                in_note = False

    if in_note and 0 <= current_pitch <= 127:
        note = pretty_midi.Note(
            velocity=80, pitch=current_pitch, start=note_start_time, end=times[-1]
        )
        instrument.notes.append(note)

    midi.instruments.append(instrument)
    return midi


def transcribe_basic_pitch(audio_path, output_midi):
    try:
        from basic_pitch.inference import predict
    except ImportError:
        print(
            "Error: basic-pitch not installed. Install with: pip install basic-pitch",
            file=sys.stderr,
        )
        return None

    try:
        audio_path, temp_created = ensure_audio(audio_path)
    except Exception as e:
        print(f"Error preparing audio for basic-pitch: {e}", file=sys.stderr)
        return None

    start_time = time.time()
    try:
        model_output, midi_data, note_events = predict(audio_path)
        midi_data.write(output_midi)
        elapsed_time = int((time.time() - start_time) * 1000)
        return {
            "method": "basic-pitch",
            "transcription_time_ms": elapsed_time,
            "success": True,
            "output_file": output_midi,
        }
    except Exception as e:
        print(f"Error in basic-pitch transcription: {e}", file=sys.stderr)
        return None
    finally:
        if "temp_created" in locals() and temp_created:
            try:
                os.unlink(audio_path)
            except Exception:
                pass


def transcribe_swiftf0(audio_path, output_midi):
    try:
        import torch
        import torchaudio
        from swift_f0 import SwiftF0
    except ImportError as e:
        print(f"Error: SwiftF0 not available: {e}", file=sys.stderr)
        return None

    try:
        audio_path, temp_created = ensure_audio(audio_path)
    except Exception as e:
        print(f"Error preparing audio for SwiftF0: {e}", file=sys.stderr)
        return None

    start_time = time.time()
    try:
        waveform, sample_rate = torchaudio.load(audio_path)
        model = SwiftF0()

        pitch_contour = None
        try:
            if callable(model):
                with torch.no_grad():
                    pitch_contour = model(waveform, sample_rate)
        except Exception:
            pitch_contour = None

        if pitch_contour is None:
            for name in ("predict", "infer", "forward", "extract", "run"):
                fn = getattr(model, name, None)
                if fn is None:
                    continue
                try:
                    with torch.no_grad():
                        pitch_contour = fn(waveform, sample_rate)
                    break
                except Exception:
                    pitch_contour = None

        # try swift_f0 specific helpers
        if pitch_contour is None:
            fn = getattr(model, "detect_from_file", None)
            if fn is not None:
                try:
                    pitch_contour = fn(audio_path)
                except Exception:
                    pitch_contour = None

        if pitch_contour is None:
            fn = getattr(model, "detect_from_array", None)
            if fn is not None:
                try:
                    arr = (
                        waveform.detach().cpu().numpy()
                        if hasattr(waveform, "detach")
                        else waveform.numpy()
                    )
                    try:
                        pitch_contour = fn(arr, sample_rate)
                    except Exception:
                        # try mono 1D
                        mono = arr.mean(axis=0) if arr.ndim == 2 else arr
                        pitch_contour = fn(mono, sample_rate)
                except Exception:
                    pitch_contour = None

        if pitch_contour is None:
            raise RuntimeError(
                "SwiftF0 model did not produce pitch contour with known API"
            )

        # Extract array from PitchResult or similar objects
        try:
            if hasattr(pitch_contour, "detach"):
                arr = pitch_contour.detach().cpu().numpy()
            elif hasattr(pitch_contour, "pitch_hz"):
                arr = (
                    pitch_contour.pitch_hz
                    if isinstance(pitch_contour.pitch_hz, np.ndarray)
                    else np.array(pitch_contour.pitch_hz)
                )
            elif hasattr(pitch_contour, "pitch"):
                arr = (
                    pitch_contour.pitch
                    if isinstance(pitch_contour.pitch, np.ndarray)
                    else np.array(pitch_contour.pitch)
                )
            elif hasattr(pitch_contour, "frequency"):
                arr = (
                    pitch_contour.frequency
                    if isinstance(pitch_contour.frequency, np.ndarray)
                    else np.array(pitch_contour.frequency)
                )
            elif hasattr(pitch_contour, "frequencies"):
                arr = (
                    pitch_contour.frequencies
                    if isinstance(pitch_contour.frequencies, np.ndarray)
                    else np.array(pitch_contour.frequencies)
                )
            elif hasattr(pitch_contour, "f0"):
                arr = (
                    pitch_contour.f0
                    if isinstance(pitch_contour.f0, np.ndarray)
                    else np.array(pitch_contour.f0)
                )
            else:
                arr = (
                    np.array(pitch_contour)
                    if not isinstance(pitch_contour, np.ndarray)
                    else pitch_contour
                )
        except Exception:
            arr = (
                np.array(pitch_contour)
                if not isinstance(pitch_contour, np.ndarray)
                else pitch_contour
            )

        midi = f0_to_midi(arr, sample_rate)
        midi.write(output_midi)
        elapsed_time = int((time.time() - start_time) * 1000)
        return {
            "method": "swiftf0",
            "transcription_time_ms": elapsed_time,
            "success": True,
            "output_file": output_midi,
        }
    except Exception as e:
        print(f"Error in SwiftF0 transcription: {e}", file=sys.stderr)
        return None
    finally:
        if "temp_created" in locals() and temp_created:
            try:
                os.unlink(audio_path)
            except Exception:
                pass


def transcribe_crepe(audio_path, output_midi):
    """Transcribe using CREPE-Notes (https://github.com/xavriley/crepe_notes).

    CREPE-Notes combines CREPE pitch estimation with a note segmentation
    algorithm to produce discrete MIDI notes, unlike raw CREPE which only
    outputs an F0 contour.
    """
    from pathlib import Path as _Path

    try:
        audio_path, temp_created = ensure_audio(audio_path)
    except Exception as e:
        print(f"Error preparing audio for CREPE-Notes: {e}", file=sys.stderr)
        return None

    start_time = time.time()
    try:
        audio_path_obj = _Path(audio_path)
        used_cli = False

        # Prefer isolated crepe_notes CLI to avoid dependency conflicts with main env.
        crepe_bin_candidates = [
            os.environ.get("CREPE_NOTES_BIN"),
            "/opt/crepe-notes-venv/bin/crepe_notes",
            shutil.which("crepe_notes"),
        ]
        crepe_bin = next(
            (p for p in crepe_bin_candidates if p and os.path.exists(p)), None
        )

        if crepe_bin:
            try:
                subprocess.run(
                    [crepe_bin, str(audio_path_obj)],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                used_cli = True
            except Exception:
                used_cli = False

        if not used_cli:
            # Fallback to Python API if available in current environment.
            try:
                from crepe_notes.crepe_notes import run_crepe, process
            except ImportError:
                print(
                    "Error: crepe-notes not available (CLI/API). "
                    "Set CREPE_NOTES_BIN or install crepe-notes.",
                    file=sys.stderr,
                )
                return None

            # Step 1: run CREPE to get F0 contour (~40 s/file on CPU).
            # No caching: transcription_time_ms must reflect the real pipeline cost
            # so that timing comparisons across systems are fair.
            frequencies, confidence = run_crepe(audio_path_obj)
            # Step 2: segment F0 contour into discrete notes using CREPE-Notes.
            process(
                frequencies,
                confidence,
                audio_path_obj,
                output_label="transcription",
                use_cwd=False,
                save_analysis_files=False,
            )

        candidates = [
            audio_path_obj.parent / f"{audio_path_obj.stem}.transcription.mid",
            audio_path_obj.parent / f"{audio_path_obj.stem}.crepe.transcription.mid",
            _Path.cwd() / f"{audio_path_obj.stem}.transcription.mid",
            _Path.cwd() / f"{audio_path_obj.stem}.crepe.transcription.mid",
        ]

        wildcard_candidates = sorted(
            list(
                audio_path_obj.parent.glob(f"{audio_path_obj.stem}*.transcription.mid")
            )
            + list(_Path.cwd().glob(f"{audio_path_obj.stem}*.transcription.mid")),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        generated_midi = next((p for p in candidates if p.exists()), None)
        if generated_midi is None and wildcard_candidates:
            generated_midi = wildcard_candidates[0]

        if generated_midi is None:
            raise FileNotFoundError(
                "CREPE-Notes output not found. Checked expected patterns in "
                f"{audio_path_obj.parent} and {_Path.cwd()} for stem '{audio_path_obj.stem}'."
            )

        shutil.move(str(generated_midi), output_midi)
        elapsed_time = int((time.time() - start_time) * 1000)
        return {
            "method": "crepe-notes",
            "transcription_time_ms": elapsed_time,
            "success": True,
            "output_file": output_midi,
        }
    except Exception as e:
        print(f"Error in CREPE-Notes transcription: {e}", file=sys.stderr)
        # Clean up any orphaned .transcription.mid left by process() before the crash
        if "audio_path_obj" in locals():
            orphan = audio_path_obj.parent / (
                audio_path_obj.stem + ".transcription.mid"
            )
            if orphan.exists():
                try:
                    orphan.unlink()
                except Exception:
                    pass
        return None
    finally:
        if "temp_created" in locals() and temp_created:
            try:
                os.unlink(audio_path)
            except Exception:
                pass


def transcribe_pyin(audio_path, output_midi):
    try:
        audio_path, temp_created = ensure_audio(audio_path)
    except Exception as e:
        print(f"Error preparing audio for Pyin: {e}", file=sys.stderr)
        return None

    start_time = time.time()
    try:
        audio, sr = librosa.load(audio_path, sr=22050)
        f0, voiced_flag, voiced_probs = librosa.pyin(
            audio,
            fmin=librosa.note_to_hz("C2"),
            fmax=librosa.note_to_hz("C7"),
            sr=sr,
            frame_length=2048,
        )
        hop_length = 512
        times = librosa.frames_to_time(np.arange(len(f0)), sr=sr, hop_length=hop_length)
        midi = f0_contour_to_midi(times, f0, voiced_probs, threshold=0.5)
        midi.write(output_midi)
        elapsed_time = int((time.time() - start_time) * 1000)
        return {
            "method": "pyin",
            "transcription_time_ms": elapsed_time,
            "success": True,
            "output_file": output_midi,
        }
    except Exception as e:
        print(f"Error in Pyin transcription: {e}", file=sys.stderr)
        return None
    finally:
        if "temp_created" in locals() and temp_created:
            try:
                os.unlink(audio_path)
            except Exception:
                pass


def transcribe(audio_path, output_midi, method="basic-pitch"):
    method = method.lower()
    if method == "basic-pitch":
        result = transcribe_basic_pitch(audio_path, output_midi)
    elif method == "swiftf0":
        result = transcribe_swiftf0(audio_path, output_midi)
    elif method in ("crepe", "crepe-notes"):
        result = transcribe_crepe(audio_path, output_midi)
    elif method == "pyin":
        result = transcribe_pyin(audio_path, output_midi)
    else:
        print(f"Error: Unknown AMT method: {method}", file=sys.stderr)
        print(
            "Available methods: basic-pitch, swiftf0, crepe-notes, pyin",
            file=sys.stderr,
        )
        return None

    if result is None and method not in ("basic-pitch", "crepe", "crepe-notes"):
        # Fallback only for experimental/unknown methods, never for first-class
        # systems — a silent substitution would corrupt evaluation results.
        print(f"Warning: {method} failed, falling back to basic-pitch", file=sys.stderr)
        result = transcribe_basic_pitch(audio_path, output_midi)

    return result


def main():
    parser = argparse.ArgumentParser(
        description="AMT Wrapper - Unified interface for music transcription"
    )
    parser.add_argument("input_audio", help="Input audio file (WAV, MP3, MIDI, etc.)")
    parser.add_argument("output_midi", help="Output MIDI file")
    parser.add_argument(
        "--method",
        "-m",
        default="basic-pitch",
        choices=["basic-pitch", "swiftf0", "crepe-notes", "pyin"],
        help="AMT method to use (default: basic-pitch). 'crepe-notes' uses CREPE-Notes.",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Print verbose output"
    )
    args = parser.parse_args()

    if not os.path.exists(args.input_audio):
        print(f"Error: Input file not found: {args.input_audio}", file=sys.stderr)
        return 1

    output_dir = os.path.dirname(args.output_midi)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    if args.verbose:
        print(f"Transcribing {args.input_audio} using {args.method}...")

    result = transcribe(args.input_audio, args.output_midi, args.method)

    if result is None:
        print("Error: Transcription failed", file=sys.stderr)
        return 1

    if args.verbose:
        print(
            f"Success! Transcription completed in {result['transcription_time_ms']} ms"
        )
        print(f"Output: {result['output_file']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
