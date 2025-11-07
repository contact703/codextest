"""Interface de linha de comando baseada em Typer.

SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from .config import AppConfig
from .pipeline.core import ADPipeline
from .pipeline.detection import DetectedWindow, detect_windows
from .pipeline.script import ADEntry, build_script
from .pipeline.tts import synthesize_entries
from .pipeline.util import mux_with_ad, render_tts_track, timestamp_to_seconds, write_srt, write_txt

app = typer.Typer(help="Ferramentas para gerar audiodescrição brasileira")
console = Console()


def build_pipeline(config_path: Optional[Path]) -> ADPipeline:
    config = AppConfig()
    if config_path and config_path.exists():
        data = json.loads(config_path.read_text(encoding="utf-8"))
        for key, value in data.items():
            if hasattr(config, key):
                setattr(config, key, value)
    return ADPipeline(config)


@app.command()
def ingest(input: str, out: Path, config_path: Optional[Path] = typer.Option(None, help="Arquivo JSON de configuração.")) -> None:
    """Baixa/organiza mídia local ou remota."""

    pipeline = build_pipeline(config_path)
    audio_path, meta = pipeline.ingest(input, out)
    console.print(f"Áudio extraído em: {audio_path}")
    console.print_json(data=meta)


@app.command("detect-windows")
def detect_windows_cmd(
    input: Path,
    out: Path,
    config_path: Optional[Path] = typer.Option(None, help="Arquivo JSON de configuração."),
) -> None:
    """Detecta janelas livres de fala."""

    pipeline = build_pipeline(config_path)
    out.mkdir(parents=True, exist_ok=True)
    windows = detect_windows(input, pipeline.config)
    payload = [window.model_dump() for window in windows]
    out_file = out / "janelas.json"
    out_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    console.print(f"Janelas detectadas: {len(windows)}")
    console.print_json(data=payload)


def parse_srt(path: Path) -> list[ADEntry]:
    """Parser simples de arquivos SRT gerados pelo pipeline."""

    entries: list[ADEntry] = []
    with path.open("r", encoding="utf-8") as handle:
        block: list[str] = []
        for line in handle:
            line = line.strip()
            if not line:
                if block:
                    entries.extend(_block_to_entries(block))
                    block = []
                continue
            block.append(line)
        if block:
            entries.extend(_block_to_entries(block))
    return entries


def _block_to_entries(block: list[str]) -> list[ADEntry]:
    if len(block) < 3:
        return []
    index = int(block[0])
    start_raw, end_raw = block[1].split(" --> ")
    text = block[2]
    text = text.replace("[AD]", "").strip()
    return [
        ADEntry(
            index=index,
            start=timestamp_to_seconds(start_raw),
            end=timestamp_to_seconds(end_raw),
            text=text,
        )
    ]


@app.command("generate-ad")
def generate_ad_cmd(
    input: Path = typer.Argument(..., help="Arquivo JSON com janelas."),
    media: Path = typer.Option(..., help="Arquivo JSON com metadados da mídia."),
    out: Path = typer.Argument(..., help="Diretório de saída."),
    config_path: Optional[Path] = typer.Option(None, help="Arquivo JSON de configuração."),
) -> None:
    """Gera roteiro textual a partir das janelas detectadas."""

    pipeline = build_pipeline(config_path)
    windows_payload = json.loads(input.read_text(encoding="utf-8"))
    windows = [DetectedWindow.model_validate(window) for window in windows_payload]
    meta = json.loads(media.read_text(encoding="utf-8"))
    entries = build_script(windows, meta, pipeline.config)
    out.mkdir(parents=True, exist_ok=True)
    srt_path = out / "ad.srt"
    txt_path = out / "ad.txt"
    write_srt(entries, srt_path)
    write_txt(entries, txt_path)
    console.print(f"Blocos gerados: {len(entries)}")
    console.print(f"SRT: {srt_path}")
    console.print(f"TXT: {txt_path}")


@app.command("tts")
def tts_cmd(
    input: Path = typer.Argument(..., help="Arquivo SRT com AD."),
    out: Path = typer.Argument(..., help="Diretório de saída."),
    voice: Optional[str] = typer.Option(None, help="Voz TTS a ser utilizada."),
    config_path: Optional[Path] = typer.Option(None, help="Arquivo JSON de configuração."),
) -> None:
    """Gera faixa de áudio a partir de roteiro SRT."""

    pipeline = build_pipeline(config_path)
    if voice:
        pipeline.config.tts.voice = voice
    script_entries = parse_srt(input)
    out.mkdir(parents=True, exist_ok=True)
    segments = synthesize_entries(script_entries, pipeline.config)
    wav_path = out / "ad.wav"
    render_tts_track(segments, wav_path, pipeline.config)
    mp3_path = out / "ad.mp3"
    render_tts_track(segments, mp3_path, pipeline.config, codec="libmp3lame")
    console.print(f"Arquivo WAV gerado em {wav_path}")
    console.print(f"Arquivo MP3 gerado em {mp3_path}")


@app.command("mux")
def mux_cmd(
    video: Path = typer.Option(..., help="Arquivo de vídeo original."),
    ad: Path = typer.Option(..., help="Faixa de AD em WAV."),
    srt: Path = typer.Option(..., help="Arquivo SRT de AD."),
    out: Path = typer.Argument(..., help="Saída do vídeo com AD."),
    config_path: Optional[Path] = typer.Option(None, help="Arquivo JSON de configuração."),
) -> None:
    """Multiplexa vídeo com faixa de audiodescrição e legenda."""

    pipeline = build_pipeline(config_path)
    mux_with_ad(video, ad, srt, out, pipeline.config)
    console.print(f"Vídeo com AD disponível em {out}")


@app.command("pipeline")
def pipeline_cmd(
    input: str,
    out: Path,
    export_video: bool = typer.Option(False, help="Gera arquivo MP4 com AD."),
    config_path: Optional[Path] = typer.Option(None, help="Arquivo JSON de configuração."),
) -> None:
    """Executa o pipeline completo."""

    pipeline = build_pipeline(config_path)
    artifacts = pipeline.run(input, out, export_video=export_video)
    table = Table(title="Artefatos gerados")
    table.add_column("Tipo")
    table.add_column("Caminho")
    table.add_row("Áudio original", str(artifacts.audio_path))
    table.add_row("Janelas", str(artifacts.windows_path))
    table.add_row("SRT", str(artifacts.script_srt))
    table.add_row("TXT", str(artifacts.script_txt))
    table.add_row("WAV AD", str(artifacts.tts_wav))
    table.add_row("MP3 AD", str(artifacts.tts_mp3))
    if artifacts.final_video:
        table.add_row("MP4 mixado", str(artifacts.final_video))
    console.print(table)


@app.command()
def version() -> None:
    """Exibe versão do pacote."""

    console.print("adtool 0.1.0")
