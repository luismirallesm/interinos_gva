"""Configuración del scraper."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
INBOX_DIR = ROOT / "inbox"      # PDFs subidos a mano (modo seguro)
RAW_DIR = ROOT / "raw"          # PDFs descargados (no se commitean)
STATE_FILE = DATA_DIR / "state.json"
HISTORY_FILE = DATA_DIR / "history.json"
INDEX_FILE = DATA_DIR / "index.json"

# Página del portal con los listados. Se siguen subpáginas un nivel.
SOURCES = [
    # Aquí está el enlace "listado de adjudicaciones maestros" (verificado por el usuario)
    "https://ceice.gva.es/es/web/rrhh-educacion/resolucion",
    "https://ceice.gva.es/es/web/rrhh-educacion/adjudicaciones",
]
SUBPAGE_KEYWORDS = ("resoluc", "adjudic", "borsa", "bolsa", "interin")

# Listado diario:        261105_lis_mae.pdf        (AAMMDD_lis_<cuerpo>.pdf)
# Listado inicio curso:  ini_2026_adj_int_mae.pdf  (ini_<año>_adj_int_<cuerpo>.pdf)
LISTING_RE = re.compile(r"(\d{6})_lis_([a-z]+)\.pdf", re.IGNORECASE)
INICIO_RE = re.compile(r"ini_(\d{4})_adj_int_([a-z]+)\.pdf", re.IGNORECASE)

# Cuerpos que se procesan (mae = maestros). Secundaria (sec) queda fuera por ahora.
CUERPOS = ("mae",)

# Descubrimiento por patrón de URL (sin saber qué día salió cada listado):
#   https://ceice.gva.es/documents/162909733/<carpeta>/<AAMMDD>_lis_<cuerpo>.pdf
# El número de carpeta cambia de vez en cuando; se prueban las conocidas y se aprenden nuevas.
DOC_URL = "https://ceice.gva.es/documents/162909733/{folder}/{name}"
KNOWN_FOLDERS = (414354213, 415637604, 416766492)   # 10/09, 22-29/10, 03-05/11
PROBE_START = "2026-07-16"       # día siguiente al listado de inicio de curso
PROBE_DELAY_SECONDS = 0.5
RECHECK_DAYS = 7                 # un día sin listado se vuelve a probar durante estos días

USER_AGENT = "interinos-gva-bot/0.1 (proyecto open source; consulta educativa)"
REQUEST_TIMEOUT = 60
REQUEST_DELAY_SECONDS = 1.0     # cortesía con el servidor
