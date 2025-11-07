"""Funções auxiliares para escrita de arquivos e mixagem.

SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Iterable, List

from .tts import AudioSegment


def ensure_ffmpeg(path: str) -> None:
    """Verifica se o binário FFmpeg está disponível."""

    if subprocess.run([path, "-version"], check=False, capture_output=True).returncode != 0:
        raise RuntimeError("FFmpeg não encontrado. Configure o caminho em AppConfig.ffmpeg_path.")


def write_srt(entries: Iterable, output: Path) -> None:
    """Grava arquivo SRT com marcação [AD]."""

    lines = []
    for entry in entries:
        start = seconds_to_timestamp(entry.start)
        end = seconds_to_timestamp(entry.end)
        lines.append(str(entry.index))
        lines.append(f"{start} --> {end}")
        lines.append(f"[AD] {entry.text}")
        lines.append("")
    output.write_text("\n".join(lines), encoding="utf-8")


def write_txt(entries: Iterable, output: Path) -> None:
    """Grava roteiro textual com intervalos."""

    lines = []
    for entry in entries:
        start = seconds_to_timestamp(entry.start)
        end = seconds_to_timestamp(entry.end)
        lines.append(f"{start} -> {end} | {entry.text}")
    output.write_text("\n".join(lines), encoding="utf-8")


def seconds_to_timestamp(value: float) -> str:
    hours = int(value // 3600)
    minutes = int((value % 3600) // 60)
    seconds = int(value % 60)
    milliseconds = int((value - int(value)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def timestamp_to_seconds(timestamp: str) -> float:
    """Converte timestamp SRT para segundos."""

    time_part, milli_part = timestamp.split(",")
    hours, minutes, seconds = [int(part) for part in time_part.split(":")]
    return hours * 3600 + minutes * 60 + seconds + int(milli_part) / 1000


def render_tts_track(segments: List[AudioSegment], output: Path, config, codec: str = "pcm_s16le") -> None:
    """Gera faixa contínua de AD a partir de segmentos individuais."""

    ensure_ffmpeg(config.ffmpeg_path)
    if not segments:
        raise RuntimeError("Nenhum segmento TTS disponível para renderizar.")
    duration = max(segment.end for segment in segments)
    inputs = [
        "-f",
        "lavfi",
        "-i",
        f"anullsrc=r={config.tts.piper_sample_rate}:cl=mono",
        "-t",
        f"{duration:.3f}",
    ]
    for segment in segments:
        inputs.extend(["-i", str(segment.path)])
    mix_parts = []
    for idx, segment in enumerate(segments, start=1):
        delay = int(max(segment.start, 0.0) * 1000)
        mix_parts.append(f"[{idx}:a]adelay={delay}|{delay}[s{idx}]")
    sum_inputs = "[0:a]" + "".join([f"[s{idx}]" for idx in range(1, len(segments) + 1)])
    filter_complex = ";".join(mix_parts + [f"{sum_inputs}amix=inputs={len(segments)+1}:dropout_transition=0[out]"])
    command = [
        config.ffmpeg_path,
        *inputs,
        "-filter_complex",
        filter_complex,
        "-map",
        "[out]",
        "-c:a",
        codec,
        str(output),
    ]
    subprocess.run(command, check=True)


def mux_with_ad(video: Path, ad_audio: Path, srt: Path, output: Path, config) -> None:
    """Multiplexa vídeo original com faixa de AD e legenda SRT."""

    ensure_ffmpeg(config.ffmpeg_path)
    command = [
        config.ffmpeg_path,
        "-i",
        str(video),
        "-i",
        str(ad_audio),
        "-i",
        str(srt),
        "-map",
        "0:v",
        "-map",
        "0:a",
        "-map",
        "1:a",
        "-map",
        "2:0",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-c:s",
        "srt",
        "-metadata:s:1",
        "language=por",
        "-metadata:s:2",
        "title=Audiodescricao",
        str(output),
    ]
    subprocess.run(command, check=True)
