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
    MIDI-to-WAV synthesis using FluidSynth.
"""

import os
import subprocess
import tempfile
from typing import Optional


def find_soundfont() -> Optional[str]:
    """Find an available soundfont on the local system."""
    common_locations = [
        "/usr/share/sounds/sf2/FluidR3_GM.sf2",
        "/usr/share/sounds/sf2/default.sf2",
        "/usr/share/soundfonts/FluidR3_GM.sf2",
        "/usr/share/soundfonts/default.sf2",
    ]

    for path in common_locations:
        if os.path.exists(path):
            return path

    return None


def synthesize_midi_to_wav(
    midi_path: str,
    output_wav: Optional[str] = None,
    sample_rate: int = 44100,
    soundfont: Optional[str] = None,
) -> str:
    """
    Synthesize WAV audio from MIDI using FluidSynth.

    Args:
        midi_path: Path to the input MIDI file.
        output_wav: Output WAV path (temporary file if None).
        sample_rate: Output sample rate.
        soundfont: Path to the soundfont (auto-detected if None).

    Returns:
        Path to the generated WAV file.

    Raises:
        RuntimeError: If synthesis fails.
    """
    if soundfont is None:
        soundfont = find_soundfont()
        if soundfont is None:
            raise RuntimeError(
                "No soundfont found. Install: sudo apt-get install fluid-soundfont-gm"
            )

    # Create temporary output file if none is provided
    if output_wav is None:
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        output_wav = tmp.name
        tmp.close()

    try:
        cmd = [
            "fluidsynth",
            "-ni",  # Non-interactive
            soundfont,
            midi_path,
            "-F",
            output_wav,
            "-r",
            str(sample_rate),
        ]

        result = subprocess.run(cmd, capture_output=True, check=True, timeout=30)

        if not os.path.exists(output_wav) or os.path.getsize(output_wav) == 0:
            raise RuntimeError(f"Failed to generate audio file")

        return output_wav

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"FluidSynth error: {e.stderr.decode()}")
    except subprocess.TimeoutExpired:
        raise RuntimeError("FluidSynth timeout")
    except FileNotFoundError:
        raise RuntimeError(
            "FluidSynth not found. Install: sudo apt-get install fluidsynth"
        )
