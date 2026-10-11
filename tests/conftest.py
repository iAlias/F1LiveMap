"""Carica sessions.py senza eseguire custom_components/f1_live_map/__init__.py (che importa HA)."""

import importlib.util
import sys
from pathlib import Path

_percorso = Path(__file__).parent.parent / "custom_components" / "f1_live_map" / "sessions.py"
_spec = importlib.util.spec_from_file_location("sessions", _percorso)
_modulo = importlib.util.module_from_spec(_spec)
sys.modules["sessions"] = _modulo
_spec.loader.exec_module(_modulo)
