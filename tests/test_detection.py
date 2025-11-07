"""Testes para detecção de janelas de AD.

SPDX-License-Identifier: MIT
"""

from pathlib import Path
import math
import wave
import struct

from adtool.config import AppConfig
from adtool.pipeline.detection import detect_windows


def create_silence_with_tone(tmp_path: Path) -> Path:
    sample_rate = 16000
    duration_tone = 1
    duration_silence = 2
    tone_samples = [
        0.3 * math.sin(2 * math.pi * 440 * t / sample_rate)
        for t in range(sample_rate * duration_tone)
    ]
    silence_samples = [0.0 for _ in range(sample_rate * duration_silence)]
    audio = tone_samples + silence_samples + tone_samples
    path = tmp_path / "audio.wav"
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        frames = b"".join(struct.pack("<h", int(sample * 32767)) for sample in audio)
        handle.writeframes(frames)
    return path


def test_detect_windows_find_silence(tmp_path: Path) -> None:
    audio_path = create_silence_with_tone(tmp_path)
    config = AppConfig()
    windows = detect_windows(audio_path, config)
    assert windows, "Esperava detectar ao menos uma janela de silêncio"
    assert windows[0].duration > 1.5
