"""Síntese de voz com múltiplos motores.

SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import json
import platform
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

try:
    from rich.progress import Progress
except ImportError:  # pragma: no cover
    class Progress:  # type: ignore[override]
        def advance(self, *_args, **_kwargs):
            return None

        def __getattr__(self, _name):
            def _noop(*_args, **_kwargs):
                return None

            return _noop

from ..config import AppConfig
from .script import ADEntry


@dataclass
class AudioSegment:
    path: Path
    start: float
    end: float


def synthesize_entries(
    entries: Iterable[ADEntry],
    config: AppConfig,
    progress: Progress | None = None,
    task_id: int | None = None,
) -> List[AudioSegment]:
    """Gera arquivos de áudio individuais para cada bloco."""

    segments: List[AudioSegment] = []
    workdir = config.work_dir / "tts"
    workdir.mkdir(parents=True, exist_ok=True)

    for entry in entries:
        path = workdir / f"segment_{entry.index:04d}.wav"
        synthesize_text(entry.text, path, config)
        segments.append(AudioSegment(path=path, start=entry.start, end=entry.end))
        if progress and task_id is not None:
            progress.advance(task_id, 1)
    return segments


def synthesize_text(text: str, output: Path, config: AppConfig) -> None:
    """Seleciona motor disponível e gera áudio para o texto."""

    for engine in config.tts.engine_priority:
        if engine == "system" and platform.system() == "Darwin":
            if try_macos_tts(text, output, config):
                return
        if engine == "web":
            # Web Speech API não está disponível em ambiente CLI; pular.
            continue
        if engine == "piper":
            if try_piper(text, output, config):
                return
    raise RuntimeError("Nenhum motor TTS disponível. Configure Piper ou utilize macOS.")


def try_macos_tts(text: str, output: Path, config: AppConfig) -> bool:
    """Utiliza AVSpeechSynthesizer via comando `say` no macOS."""

    if platform.system() != "Darwin":
        return False
    command = [
        "say",
        "-v",
        config.tts.voice,
        text,
        "-o",
        str(output),
        "--data-format=LEF32@22050",
    ]
    return subprocess.run(command, check=False).returncode == 0


def try_piper(text: str, output: Path, config: AppConfig) -> bool:
    """Invoca Piper (voz CC0) para síntese offline."""

    voice = config.tts.piper_voice
    model_dir = config.cache_dir / "piper"
    model_dir.mkdir(parents=True, exist_ok=True)
    voice_path = model_dir / f"{voice}.onnx"
    if not voice_path.exists():
        raise RuntimeError(
            "Modelo Piper não encontrado. Execute `adtool assets download-piper` para obter a voz CC0."\
        )
    command = [
        "piper-tts",
        "--model",
        str(voice_path),
        "--output_file",
        str(output),
    ]
    proc = subprocess.Popen(command, stdin=subprocess.PIPE)
    assert proc.stdin is not None
    proc.stdin.write(text.encode("utf-8"))
    proc.stdin.close()
    return proc.wait() == 0
