"""PDF de adjudicaciones -> filas normalizadas.

Detecta las columnas por el texto de la cabecera, no por posición, para
tolerar cambios de maquetación entre listados.
"""
from __future__ import annotations

import re
import unicodedata

import pdfplumber

HEADER_ALIASES = {
    "nif": ("nif", "dni", "nif/nie", "document"),
    "nombre": ("nombre", "nom", "apellidos y nombre", "cognoms i nom", "persona"),
    "especialidad": ("especialidad", "especialitat", "cuerpo", "especialidad/cuerpo"),
    "orden": ("orden", "ordre", "n orden", "num orden", "posicion", "posicio", "n.o"),
    "estado": ("estado", "estat", "situacion", "situacio"),
    "centro": ("centro", "centre", "centro adjudicado", "centre adjudicat"),
    "localidad": ("localidad", "localitat", "municipio", "municipi"),
    "provincia": ("provincia",),
}

STATUS_MAP = {
    "activo": "activo", "actiu": "activo", "a": "activo",
    "adjudicado": "adjudicado", "adjudicat": "adjudicado",
    "desactivado": "desactivado", "desactivat": "desactivado",
    "excluido": "excluido", "exclos": "excluido",
}


def _clean(s: str | None) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()


def _fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9/ ]", "", s).strip()


def match_header(cell: str) -> str | None:
    f = _fold(cell)
    if not f:
        return None
    for key, aliases in HEADER_ALIASES.items():
        if f in aliases or any(f.startswith(a) for a in aliases if len(a) > 3):
            return key
    return None


def normalize_status(raw: str) -> str:
    f = _fold(raw)
    return STATUS_MAP.get(f, f or "desconocido")


def parse_order(raw: str) -> int | None:
    m = re.search(r"\d+", raw.replace(".", ""))
    return int(m.group()) if m else None


def detect_columns(row: list[str | None]) -> dict[int, str]:
    mapping: dict[int, str] = {}
    for i, cell in enumerate(row):
        key = match_header(_clean(cell))
        if key and key not in mapping.values():
            mapping[i] = key
    return mapping


def rows_from_table(table: list[list[str | None]], mapping: dict[int, str] | None):
    """Devuelve (filas, mapping). Reutiliza el mapping si la tabla no trae cabecera."""
    out = []
    for raw in table:
        det = detect_columns(raw)
        if len(det) >= 3:           # fila de cabecera
            mapping = det
            continue
        if not mapping:
            continue
        rec = {key: _clean(raw[i]) for i, key in mapping.items() if i < len(raw)}
        order = parse_order(rec.get("orden", ""))
        if order is None:
            continue
        rec["orden"] = order
        rec["estado"] = normalize_status(rec.get("estado", ""))
        out.append(rec)
    return out, mapping


def parse_pdf(path: str) -> list[dict]:
    rows: list[dict] = []
    mapping = None
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                parsed, mapping = rows_from_table(table, mapping)
                rows.extend(parsed)
    return rows
