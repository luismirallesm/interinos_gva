"""Lista de participantes de inicio de curso (ini_<año>_par_def_int_lis_<cuerpo>.pdf) -> habilitaciones.

Es la bolsa única de maestros, en el mismo orden que el listado de inicio de curso, con las
especialidades habilitadas de cada persona. Patrón por persona:

    11    ARANDA CATALA, ENCARNACION       AMB SERVEIS         PRI            PT  AL
  13038 GONZALEZ DE LA ALEJA RUIZ DE LA HERMOSA,SENSE        (nombres largos ocupan varias líneas
                                               ISABELSERVEIS  y a veces se pegan a AMB/SENSE/SERVEIS)
                                                      MARIA                   PRI

Un `*` tras el código indica «habilitació desactivada».
"""
from __future__ import annotations

import re
import unicodedata

from .parse_pdf import pdf_to_text

CODIGOS = {
    "INF": "Educación infantil",
    "PRI": "Educación primaria",
    "ING": "Inglés",
    "FRA": "Francés",
    "EF": "Educación física",
    "PT": "Pedagogía terapéutica",
    "AL": "Audición y lenguaje",
    "MUS": "Música",
}
ROW_RE = re.compile(r"^\s{0,4}(\d{1,6})\s+([^\s\d].*)$")
CODE_RE = re.compile(r"^(%s)(\*?)$" % "|".join(CODIGOS))
SKIP = ("(*)", "Bolsa del cuerpo", '"Listado')


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Z ]", " ", s.upper())


def parse_text(text: str) -> list[dict]:
    blocks: list[tuple[int, list[str]]] = []
    for line in text.splitlines():
        m = ROW_RE.match(line)
        if m and "," in line:
            blocks.append((int(m.group(1)), [m.group(2)]))
        elif blocks and line.strip() and not line.strip().startswith(SKIP):
            blocks[-1][1].append(line.strip())
    rows = []
    for orden, parts in blocks:
        toks = re.sub(r"\s+\*", "*", " ".join(parts)).split()  # «INF *» -> «INF*»
        habs, desact = [], []
        while toks and CODE_RE.match(toks[-1]):
            code, star = CODE_RE.match(toks.pop()).groups()
            (desact if star else habs).insert(0, code)
        txt = " ".join(toks)
        servicios = "SENSE" not in txt
        nombre = re.sub(r"\s*(AMB|SENSE)\b|SERVEIS", " ", txt)
        nombre = re.sub(r"(AMB|SENSE)$", "", re.sub(r"\s+", " ", nombre).strip()).strip().replace(" ,", ",")
        rows.append({"orden": orden, "nombre": nombre, "servicios": servicios, "habs": habs, "desact": desact})
    return rows


def parse_pdf(path: str) -> list[dict]:
    return parse_text(pdf_to_text(path))


def _same(a: str, b: str) -> bool:
    """Mismo nombre, tolerando nombres truncados o pegados en uno de los dos PDF."""
    a, b = _norm(a).split(), _norm(b).split()
    if not a or not b:
        return False
    n = min(len(a), len(b))
    return a[0] == b[0] and sum(x == y for x, y in zip(a, b)) >= max(1, n - 1)


def align(base_rows: list[dict], habil_rows: list[dict], window: int = 40) -> list[str]:
    """Habilitaciones por orden inicial: lista de len(base_rows), «INF PRI PT*» o "" si no se encuentra.

    Ambos PDF siguen el orden de la bolsa, pero el de participantes tiene más gente
    (quien no entra en la adjudicación). Se recorren a la vez buscando el nombre en una ventana.
    """
    out, j = [], 0
    for r in base_rows:
        hit = next((k for k in range(j, min(j + window, len(habil_rows))) if _same(r["nombre"], habil_rows[k]["nombre"])), None)
        if hit is None:
            out.append("")
            continue
        h = habil_rows[hit]
        out.append(" ".join(h["habs"] + [c + "*" for c in h["desact"]]))
        j = hit + 1
    return out


# Especialidad del puesto adjudicado (listados diarios) -> código de bolsa.
_ESP = {
    "EDUCACIO PRIMARIA": "PRI",
    "EDUCACIO INFANTIL": "INF",
    "PEDAGOGIA TERAPEUTICA": "PT",
    "EDUCACIO ESPECIAL PEDAGOGIA TERAPEUTICA": "PT",
    "AUDICIO I LLENGUATGE": "AL",
    "EDUCACIO ESPECIAL AUDICIO I LLENGUATGE": "AL",
    "LLENGUA ESTRANGERA ANGLES": "ING",
    "LLENGUA ESTRANGERA FRANCES": "FRA",
    "EDUCACIO FISICA": "EF",
    "MUSICA": "MUS",
}


def codigo_especialidad(esp: str | None) -> str | None:
    return _ESP.get(" ".join(_norm(esp or "").split())) if esp else None
