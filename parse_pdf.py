"""Listado diario de adjudicación (AAMMDD_lis_<cuerpo>.pdf) -> filas.

El PDF NO es una tabla. Es texto con este patrón por persona:

    163   APELLIDOS, NOMBRE            Petición:   1   Voluntaria   (solo si adjudicada)
          858392 LOCALIDAD(12004916)NOMBRE DEL CENTRO               (solo si adjudicada)
                 153 / ESPECIALIDAD                                  (solo si adjudicada)
          23 horas   [Itinerante]   VACANT        Adjudicat          (solo si adjudicada)
    164   APELLIDOS, NOMBRE
                                                 Desactivat

El listado no trae NIF. Se extrae el texto con `pdftotext -layout` (poppler).
"""
from __future__ import annotations

import re
import subprocess

STATUS_MAP = {
    "adjudicat": "adjudicado",
    "desactivat": "desactivado",
    "no adjudicat": "no_adjudicado",
    "ha participat": "ha_participado",
    "no ha participat": "no_ha_participado",
}
PROVINCIAS = {"03": "Alicante", "12": "Castellón", "46": "Valencia"}

STATUS_RE = re.compile(r"(No ha participat|Ha participat|No adjudicat|Adjudicat|Desactivat)\s*$")
ORDER_RE = re.compile(r"^ {0,4}(\d{1,6}) {2,}(\S.*?)\s*$")
PETICION_RE = re.compile(r"^(?:Petici.n:\s*(\d+)\s+)?(\S.*)$")
CENTRE_RE = re.compile(r"^\s*(\d+)\s+(.+?)\((\d{8})\)(.+?)\s*$")
SPEC_RE = re.compile(r"^\s*([0-9][0-9A-Z]*)\s*/\s*(.+?)\s*$")
TIPO_RE = re.compile(r"(VACANT|SUBSTITUCI\S*\s+INDETERMINADA|SUBSTITUCI\S*)")
DATE_RE = re.compile(r"(\d{2})/(\d{2})/(\d{4})")


def pdf_to_text(path: str) -> str:
    try:
        res = subprocess.run(
            ["pdftotext", "-layout", path, "-"],
            capture_output=True, text=True, check=True,
        )
    except FileNotFoundError as e:
        raise RuntimeError("Falta pdftotext (instala poppler-utils)") from e
    return res.stdout


def _norm_tipo(raw: str) -> str:
    return "vacante" if raw.upper().startswith("VACANT") else "sustitucion_indeterminada"


def _parse_job(before: str, adj: dict) -> None:
    tm = TIPO_RE.search(before)
    jornada = before[: tm.start()] if tm else before
    if tm:
        adj["tipo"] = _norm_tipo(tm.group(1))
    adj["itinerante"] = "Itinerante" in jornada
    adj["jornada"] = re.sub(r"\s+", " ", jornada.replace("Itinerante", "")).strip()


def parse_text(text: str) -> tuple[list[dict], str | None]:
    """Devuelve (filas, fecha ISO del encabezado)."""
    rows: list[dict] = []
    cur: dict | None = None
    fecha = None

    for line in text.splitlines():
        if fecha is None:
            dm = DATE_RE.search(line)
            if dm:
                fecha = f"{dm.group(3)}-{dm.group(2)}-{dm.group(1)}"

        om = ORDER_RE.match(line)
        if om and "," in om.group(2):
            # nombre y (opcional) petición van separados por 2+ espacios:
            #   "NOMBRE, X     Petición:  1  Voluntaria"  /  "NOMBRE, X     Voluntaria"
            parts = re.split(r"\s{2,}", om.group(2).strip(), maxsplit=1)
            cur = {"orden": int(om.group(1)), "nombre": parts[0].strip()}
            if len(parts) > 1:
                pm = PETICION_RE.match(re.sub(r"\s+", " ", parts[1]).strip())
                if pm:
                    adj = cur.setdefault("adj", {})
                    if pm.group(1):
                        adj["peticion"] = int(pm.group(1))
                    adj["tipo_peticion"] = pm.group(2).lower()
            rows.append(cur)
            continue
        if cur is None:
            continue

        sm = STATUS_RE.search(line)
        if sm:
            cur["estado"] = STATUS_MAP[sm.group(1).lower()]
            before = line[: sm.start()].strip()
            if before:
                _parse_job(before, cur.setdefault("adj", {}))
            continue
        cm = CENTRE_RE.match(line)
        if cm:
            adj = cur.setdefault("adj", {})
            code = cm.group(3)
            adj.update(
                puesto=cm.group(1),
                localidad=cm.group(2).strip(),
                centro_codigo=code,
                centro=cm.group(4).strip(),
                provincia=PROVINCIAS.get(code[:2]),
            )
            continue
        pm = SPEC_RE.match(line)
        # la especialidad va justo tras el centro; ignora líneas de fecha de cabecera
        if pm and "centro" in cur.get("adj", {}) and "especialidad" not in cur["adj"]:
            adj = cur["adj"]
            adj["especialidad_codigo"] = pm.group(1)
            adj["especialidad"] = pm.group(2).strip()
    return rows, fecha


def parse_pdf(path: str) -> tuple[list[dict], str | None]:
    return parse_text(pdf_to_text(path))
