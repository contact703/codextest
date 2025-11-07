"""Valida formatação de SRT e TXT.

SPDX-License-Identifier: MIT
"""

from pathlib import Path

from adtool.config import AppConfig
from adtool.pipeline.detection import DetectedWindow
from adtool.pipeline.script import ADEntry, build_script
from adtool.pipeline.util import seconds_to_timestamp, write_srt, write_txt


def test_script_generation_and_writing(tmp_path: Path) -> None:
    windows = [
        DetectedWindow(start=0.0, end=3.0, confidence=0.9),
        DetectedWindow(start=5.0, end=8.0, confidence=0.8),
    ]
    entries = build_script(windows, meta={}, config=AppConfig())
    srt_path = tmp_path / "ad.srt"
    txt_path = tmp_path / "ad.txt"
    write_srt(entries, srt_path)
    write_txt(entries, txt_path)
    srt_content = srt_path.read_text(encoding="utf-8")
    txt_content = txt_path.read_text(encoding="utf-8")
    assert "[AD]" in srt_content
    assert seconds_to_timestamp(entries[0].start) in srt_content
    assert "->" in txt_content
