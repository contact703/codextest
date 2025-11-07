"""Implementação principal do pipeline de audiodescrição.

SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import json
import logging
import math
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, List, Sequence

try:
    from rich.progress import Progress
except ImportError:  # pragma: no cover - fallback simplificado
    class Progress:  # type: ignore[override]
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def add_task(self, *_args, **_kwargs):
            return 0

        def update(self, *_args, **_kwargs):
            return None

        def advance(self, *_args, **_kwargs):
            return None

from ..config import AppConfig
from .detection import DetectedWindow, detect_windows
from .script import ADEntry, build_script
from .tts import synthesize_entries
from .util import ensure_ffmpeg, mux_with_ad, render_tts_track, write_srt, write_txt

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class PipelineArtifacts:
    """Caminhos de saída produzidos pelo pipeline."""

    workdir: Path
    audio_path: Path
    windows_path: Path
    script_srt: Path
    script_txt: Path
    tts_wav: Path
    tts_mp3: Path
    final_video: Path | None = None


class ADPipeline:
    """Coordena as etapas de processamento de audiodescrição."""

    def __init__(self, config: AppConfig | None = None) -> None:
        self.config = config or AppConfig()
        self.config.ensure_directories()

    def ingest(self, input_path: str, output_dir: Path) -> tuple[Path, dict]:
        """Ingesta mídia local ou remota usando FFmpeg/yt-dlp."""

        ensure_ffmpeg(self.config.ffmpeg_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        local_media = output_dir / "video.mp4"
        audio_path = output_dir / "audio.wav"
        meta_path = output_dir / "meta.json"

        if input_path.startswith("http"):
            LOGGER.info("Baixando mídia remota via yt-dlp...")
            subprocess.run(
                [
                    self.config.yt_dlp_path,
                    "-o",
                    str(local_media),
                    "-f",
                    "bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4",
                    input_path,
                ],
                check=True,
            )
        else:
            LOGGER.info("Copiando mídia local para área de trabalho...")
            subprocess.run(["cp", input_path, str(local_media)], check=True)

        LOGGER.info("Extraindo áudio PCM via FFmpeg...")
        subprocess.run(
            [
                self.config.ffmpeg_path,
                "-i",
                str(local_media),
                "-ac",
                "1",
                "-ar",
                "16000",
                str(audio_path),
            ],
            check=True,
        )

        LOGGER.info("Obtendo metadados da mídia...")
        probe = subprocess.run(
            [
                self.config.ffprobe_path,
                "-v",
                "error",
                "-show_entries",
                "format=duration:stream=codec_type,width,height",
                "-of",
                "json",
                str(local_media),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        meta = json.loads(probe.stdout)
        meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        return audio_path, meta

    def run(
        self,
        input_path: str,
        output_dir: Path,
        export_video: bool = False,
    ) -> PipelineArtifacts:
        """Executa todas as etapas do pipeline."""

        audio_path, meta = self.ingest(input_path, output_dir)

        with Progress() as progress:
            task_detect = progress.add_task("Detectando janelas", total=1)
            windows = detect_windows(audio_path, self.config)
            progress.update(task_detect, completed=1)

            task_script = progress.add_task("Gerando roteiro", total=1)
            script_entries = build_script(windows, meta, self.config)
            progress.update(task_script, completed=1)

            task_tts = progress.add_task("Sintetizando voz", total=len(script_entries))
            audio_segments = synthesize_entries(script_entries, self.config, progress, task_tts)
            progress.update(task_tts, completed=len(script_entries))

        windows_path = output_dir / "janelas.json"
        windows_path.write_text(
            json.dumps([window.model_dump() for window in windows], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        script_dir = output_dir / "ad"
        script_dir.mkdir(exist_ok=True)
        script_srt = script_dir / "ad.srt"
        script_txt = script_dir / "ad.txt"
        write_srt(script_entries, script_srt)
        write_txt(script_entries, script_txt)

        audio_dir = output_dir / "audio"
        audio_dir.mkdir(exist_ok=True)
        tts_wav = audio_dir / "ad.wav"
        tts_mp3 = audio_dir / "ad.mp3"
        render_tts_track(audio_segments, tts_wav, self.config)
        render_tts_track(audio_segments, tts_mp3, self.config, codec="libmp3lame")

        final_video = None
        if export_video:
            final_video = output_dir / "video_com_ad.mp4"
            mux_with_ad(output_dir / "video.mp4", tts_wav, script_srt, final_video, self.config)

        return PipelineArtifacts(
            workdir=output_dir,
            audio_path=audio_path,
            windows_path=windows_path,
            script_srt=script_srt,
            script_txt=script_txt,
            tts_wav=tts_wav,
            tts_mp3=tts_mp3,
            final_video=final_video,
        )
