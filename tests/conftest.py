"""Configuração de testes.

SPDX-License-Identifier: MIT
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "packages" / "adtool"
if str(PACKAGE) not in sys.path:
    sys.path.insert(0, str(PACKAGE))
