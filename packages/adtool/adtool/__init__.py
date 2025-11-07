"""SPDX-FileCopyrightText: 2024 Audiodescricao Toolkit Contributors
SPDX-License-Identifier: MIT

Módulo de alto nível para o pacote adtool."""

from .config import AppConfig
from .pipeline.core import ADPipeline

__all__ = ["AppConfig", "ADPipeline"]
