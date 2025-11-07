"""Configurações centrais do pacote.

SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional


@dataclass(slots=True)
class AudioMixConfig:
    """Configurações de mixagem para faixa de audiodescrição."""

    ducking_db: float = -12.0
    lufs_target: float = -16.0
    fade_ms: int = 120


@dataclass(slots=True)
class ADTextConfig:
    """Configurações textuais da audiodescrição."""

    max_words_per_second: float = 2.8
    language: Literal["pt-BR"] = "pt-BR"
    tag_label: str = "[AD]"


@dataclass(slots=True)
class TTSConfig:
    """Definições de síntese de voz."""

    voice: str = "pt-BR"
    engine_priority: tuple[str, ...] = ("system", "web", "piper")
    piper_voice: str = "pt_BR-Edilson-medium"
    piper_sample_rate: int = 22050


@dataclass(slots=True)
class DetectionConfig:
    """Parâmetros de detecção de janelas."""

    vad_threshold: float = 0.6
    min_silence_duration: float = 1.8
    min_gap_between_segments: float = 0.5
    rms_floor_db: float = -35.0


@dataclass(slots=True)
class WhisperConfig:
    """Configurações do ASR opcional."""

    model_size: str = "medium"
    device: Literal["cpu", "cuda", "auto"] = "auto"
    compute_type: Literal["float16", "int8", "int8_float16"] = "float16"
    enable: bool = True


@dataclass(slots=True)
class AppConfig:
    """Configurações gerais da aplicação."""

    ffmpeg_path: str = "ffmpeg"
    ffprobe_path: str = "ffprobe"
    yt_dlp_path: str = "yt-dlp"
    cache_dir: Path = field(default_factory=lambda: Path.home() / ".cache" / "adtool")
    work_dir: Path = field(default_factory=lambda: Path.cwd() / "outputs")
    detection: DetectionConfig = field(default_factory=DetectionConfig)
    mix: AudioMixConfig = field(default_factory=AudioMixConfig)
    text: ADTextConfig = field(default_factory=ADTextConfig)
    tts: TTSConfig = field(default_factory=TTSConfig)
    whisper: WhisperConfig = field(default_factory=WhisperConfig)
    attribution: Optional[str] = None

    def ensure_directories(self) -> None:
        """Cria diretórios necessários."""

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.work_dir.mkdir(parents=True, exist_ok=True)
