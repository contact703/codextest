"""Geração de roteiro textual para audiodescrição.

SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Iterable, List

from ..config import AppConfig
from .detection import DetectedWindow


def estimate_reading_duration(text: str, max_wps: float) -> float:
    """Estima duração de leitura em segundos."""

    words = max(len(text.split()), 1)
    return words / max(max_wps, 0.1)


@dataclass
class ADEntry:
    """Bloco de audiodescrição com texto e timecodes."""

    index: int
    start: float
    end: float
    text: str


def default_text_for_window(window: DetectedWindow, meta: dict) -> str:
    """Cria texto genérico quando análises profundas não estiverem disponíveis."""

    duration = window.duration
    base_text = "Corte de cena." if duration < 3.0 else "Descrição visual da cena em andamento."
    return base_text


def build_script(windows: Iterable[DetectedWindow], meta: dict, config: AppConfig) -> List[ADEntry]:
    """Gera roteiro de AD respeitando limite de palavras e janelas disponíveis."""

    entries: List[ADEntry] = []
    for idx, window in enumerate(windows, start=1):
        text = default_text_for_window(window, meta)
        estimated = estimate_reading_duration(text, config.text.max_words_per_second)
        if estimated > window.duration:
            words = text.split()
            allowed = max(int(window.duration * config.text.max_words_per_second), 1)
            text = " ".join(words[:allowed])
        entries.append(
            ADEntry(
                index=idx,
                start=window.start,
                end=window.end,
                text=text,
            )
        )
    return entries
