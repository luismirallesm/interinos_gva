"""Configuración del scraper.

IMPORTANTE: las URLs y palabras clave son un punto de partida. Hay que
verificarlas contra el portal real y ajustarlas (ver README).
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
RAW_DIR = ROOT / "raw"          # PDFs descargados (no se commitean)
STATE_FILE = DATA_DIR / "state.json"
HISTORY_FILE = DATA_DIR / "history.json"

# Páginas del portal donde se publican los listados.
SOURCES = [
    "https://ceice.gva.es/es/web/rrhh-educacion",
]

# Un enlace se considera listado si apunta a .pdf y su texto/URL contiene alguna de estas palabras.
LINK_KEYWORDS = ("adjudicaci", "adjudicacio", "bolsa", "borsa")

USER_AGENT = "interinos-gva-bot/0.1 (proyecto open source; consulta educativa)"
REQUEST_TIMEOUT = 30
REQUEST_DELAY_SECONDS = 1.0     # cortesía con el servidor
