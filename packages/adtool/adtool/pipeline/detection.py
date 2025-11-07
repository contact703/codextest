"""Detecção de janelas livres de fala.

SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, List

try:
    import numpy as np
except ImportError:  # pragma: no cover - fallback sem NumPy
    np = None  # type: ignore

try:
    import soundfile as sf
except ImportError:  # pragma: no cover - fallback usa wave
    sf = None  # type: ignore

from array import array
import wave
from ..config import AppConfig


def _load_audio(audio_path: Path) -> tuple[list[float], int]:
    if sf is not None:
        audio, sample_rate = sf.read(audio_path)
        if hasattr(audio, "ndim") and audio.ndim > 1:
            audio = audio.mean(axis=1)
        return audio.tolist() if hasattr(audio, "tolist") else list(audio), sample_rate
    with wave.open(str(audio_path), "rb") as handle:
        sample_rate = handle.getframerate()
        frames = handle.readframes(handle.getnframes())
        audio_array = array("h", frames)
        audio = [sample / 32768.0 for sample in audio_array]
        return audio, sample_rate


def _frame_rms(frame: list[float]) -> float:
    if np is not None:
        arr = np.array(frame)
        return float(np.sqrt(np.mean(arr**2)))
    if not frame:
        return 0.0
    return float(sum(sample * sample for sample in frame) / len(frame)) ** 0.5


def energy_to_db_single(value: float) -> float:
    if value <= 1e-12:
        return -120.0
    import math

    return 20.0 * math.log10(value)


@dataclass
class DetectedWindow:
    """Janela detectada para inserção de AD."""

    start: float
    end: float
    confidence: float

    @property
    def duration(self) -> float:
        return max(self.end - self.start, 0.0)

    def model_dump(self) -> dict:
        return asdict(self)

    @classmethod
    def model_validate(cls, data: dict) -> "DetectedWindow":
        return cls(**data)


@dataclass
class DetectionResult:
    windows: List[DetectedWindow]
    rms_floor_db: float


def energy_to_db(energy: "np.ndarray") -> "np.ndarray":  # type: ignore[name-defined]
    """Converte energia RMS em dBFS usando NumPy."""

    return 20.0 * np.log10(np.maximum(energy, 1e-12))


def detect_windows(audio_path: Path, config: AppConfig) -> List[DetectedWindow]:
    """Detecção simples baseada em RMS + janela deslizante."""

    audio, sample_rate = _load_audio(audio_path)
    frame_length = int(sample_rate * 0.2)
    hop_length = int(sample_rate * 0.1)
    rms_values: List[float] = []
    for idx in range(0, len(audio) - frame_length, hop_length):
        frame = audio[idx : idx + frame_length]
        rms = _frame_rms(frame)
        rms_values.append(rms)
    if not rms_values:
        return []
    rms_array = np.array(rms_values) if np is not None else rms_values  # type: ignore[assignment]
    rms_db = energy_to_db(rms_array) if np is not None else [energy_to_db_single(val) for val in rms_values]
    floor = float(np.percentile(rms_db, 25)) if np is not None else sorted(rms_db)[len(rms_db) // 4]
    threshold = max(floor, config.detection.rms_floor_db)

    windows: List[DetectedWindow] = []
    current_start = None
    for index, value in enumerate(rms_db):  # type: ignore[arg-type]
        time = index * hop_length / sample_rate
        if value < threshold:
            if current_start is None:
                current_start = time
        else:
            if current_start is not None:
                end_time = time
                if end_time - current_start >= config.detection.min_silence_duration:
                    windows.append(
                        DetectedWindow(
                            start=current_start,
                            end=end_time,
                            confidence=float(1.0 - (value - threshold) / 100.0),
                        )
                    )
                current_start = None
    if current_start is not None:
        end_time = len(audio) / sample_rate
        if end_time - current_start >= config.detection.min_silence_duration:
            windows.append(DetectedWindow(start=current_start, end=end_time, confidence=0.8))

    merged: List[DetectedWindow] = []
    for window in windows:
        if not merged:
            merged.append(window)
            continue
        last = merged[-1]
        if window.start - last.end <= config.detection.min_gap_between_segments:
            merged[-1] = DetectedWindow(start=last.start, end=window.end, confidence=min(last.confidence, window.confidence))
        else:
            merged.append(window)

    return merged
