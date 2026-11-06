"""Configuración del scraper."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
RAW_DIR = ROOT / "raw"          # PDFs descargados (no se commitean)
STATE_FILE = DATA_DIR / "state.json"
HISTORY_FILE = DATA_DIR / "history.json"
INDEX_FILE = DATA_DIR / "index.json"

# Página del portal con los listados. Se siguen subpáginas un nivel.
SOURCES = [
    "https://ceice.gva.es/es/web/rrhh-educacion/adjudicaciones",
]
SUBPAGE_KEYWORDS = ("adjudic", "borsa", "bolsa", "interin")

# Listado diario:        261105_lis_mae.pdf        (AAMMDD_lis_<cuerpo>.pdf)
# Listado inicio curso:  ini_2026_adj_int_mae.pdf  (ini_<año>_adj_int_<cuerpo>.pdf)
LISTING_RE = re.compile(r"(\d{6})_lis_([a-z]+)\.pdf", re.IGNORECASE)
INICIO_RE = re.compile(r"ini_(\d{4})_adj_int_([a-z]+)\.pdf", re.IGNORECASE)

USER_AGENT = "interinos-gva-bot/0.1 (proyecto open source; consulta educativa)"
REQUEST_TIMEOUT = 60
REQUEST_DELAY_SECONDS = 1.0     # cortesía con el servidor
