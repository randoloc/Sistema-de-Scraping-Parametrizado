"""Entry point para HuggingFace Spaces.

HF Spaces espera un archivo app.py en la raíz.
Copiar este archivo como app.py en el Space de HF.
"""

import sys
from pathlib import Path

# Asegurar que el módulo está en el path
sys.path.insert(0, str(Path(__file__).parent))

from modulo_1_servicio.main import app  # noqa: E402, F401
