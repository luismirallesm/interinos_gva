"""Orquesta: descubrir -> descargar -> parsear -> escribir data/*.json.

Salida:
  data/<cuerpo>/<AAAA-MM-DD>.json   foto completa de ese día
  data/index.json                   cuerpos y fechas disponibles
  data/history.json                 totales por estado y día (métricas)
  data/state.json                   hashes de PDFs ya procesados

Uso:
  python -m scraper.build                    # modo normal (CI)
  python -m scraper.build --pdf 261105_lis_mae.pdf   # PDF local
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections import Counter

from . import config
from .fetch import discover_links, download
from .parse_pdf import parse_pdf


def _load(path, default):
    return json.loads(path.read_text("utf-8")) if path.exists() else default


def _dump(path, obj, indent=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=indent, sort_keys=True, separators=(",", ":") if indent is None else None) + "\n", "utf-8")


def date_cuerpo_from_name(name: str) -> tuple[str | None, str | None]:
    """(fecha, cuerpo). En el listado de inicio de curso la fecha viene del encabezado."""
    m = config.LISTING_RE.search(name)
    if m:
        yymmdd, cuerpo = m.groups()
        return f"20{yymmdd[:2]}-{yymmdd[2:4]}-{yymmdd[4:]}", cuerpo.lower()
    m = config.INICIO_RE.search(name)
    if m:
        return None, m.group(2).lower()
    return None, None


def kind_from_name(name: str) -> str:
    return "inicio_curso" if config.INICIO_RE.search(name) else "diario"


def store_snapshot(rows: list[dict], fecha: str, cuerpo: str, kind: str = "diario") -> None:
    counts = Counter(r.get("estado", "desconocido") for r in rows)
    _dump(config.DATA_DIR / cuerpo / f"{fecha}.json", {"cuerpo": cuerpo, "fecha": fecha, "tipo": kind, "rows": rows})

    idx = _load(config.INDEX_FILE, {"cuerpos": {}})
    fechas = set(idx["cuerpos"].get(cuerpo, {}).get("fechas", [])) | {fecha}
    idx["cuerpos"][cuerpo] = {"fechas": sorted(fechas), "latest": max(fechas)}
    _dump(config.INDEX_FILE, idx, indent=1)

    hist = _load(config.HISTORY_FILE, {})
    hist.setdefault(cuerpo, {})[fecha] = {"tipo": kind, "total": len(rows), **counts}
    _dump(config.HISTORY_FILE, hist, indent=1)
    print(f"{cuerpo} {fecha}: {len(rows)} filas {dict(counts)}")


def process(path: str, name: str) -> int:
    fecha, cuerpo = date_cuerpo_from_name(name)
    if cuerpo not in config.CUERPOS:
        print(f"IGNORADO {name}: cuerpo {cuerpo!r} no está en CUERPOS {config.CUERPOS}")
        return 0
    rows, header_date = parse_pdf(path)
    fecha = fecha or header_date
    if not rows or not fecha or not cuerpo:
        print(f"SALTADO {name}: filas={len(rows)} fecha={fecha} cuerpo={cuerpo}")
        return 0
    store_snapshot(rows, fecha, cuerpo, kind_from_name(name))
    return len(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", help="parsear un PDF local en vez de descargar")
    args = ap.parse_args()

    if args.pdf:
        process(args.pdf, os.path.basename(args.pdf))
        return

    state = _load(config.STATE_FILE, {"processed": {}})

    # 1) Modo seguro: PDFs subidos a mano a inbox/
    inbox = sorted(config.INBOX_DIR.glob("*.pdf")) if config.INBOX_DIR.exists() else []
    print(f"inbox: {len(inbox)} PDF")
    for pdf in inbox:
        digest = hashlib.sha256(pdf.read_bytes()).hexdigest()
        if digest in state["processed"]:
            print(f"ya procesado: {pdf.name}")
            continue
        n = process(str(pdf), pdf.name)
        if n:
            state["processed"][digest] = {"url": f"inbox/{pdf.name}", "rows": n}

    # 2) URLs directas de PDF (workflow_dispatch -> variable PDF_URLS, separadas por espacios)
    for url in os.environ.get("PDF_URLS", "").split():
        try:
            listing = download(url)
            if listing.sha256 in state["processed"]:
                print(f"ya procesado: {url}")
                continue
            n = process(listing.path, url.split("?")[0].rsplit("/", 1)[-1])
            if n:
                state["processed"][listing.sha256] = {"url": url, "rows": n}
        except Exception as e:  # noqa: BLE001
            print(f"ERROR con {url}: {type(e).__name__}: {e}")

    # 3) Descarga automática (opcional; un fallo aquí no rompe el resto)
    if os.environ.get("SCRAPE_WEB", "1") == "1":
        try:
            for url in discover_links():
                listing = download(url)
                if listing.sha256 in state["processed"]:
                    continue
                n = process(listing.path, url.split("?")[0].rsplit("/", 1)[-1])
                if n:
                    state["processed"][listing.sha256] = {"url": url, "rows": n}
        except Exception as e:  # noqa: BLE001
            print(f"AVISO descarga automática falló: {type(e).__name__}: {e}")
    _dump(config.STATE_FILE, state, indent=1)
    prune_cuerpos()


def prune_cuerpos() -> None:
    """Quita de index.json e history.json los cuerpos no permitidos (p.ej. sec)."""
    idx = _load(config.INDEX_FILE, None)
    if idx:
        idx["cuerpos"] = {k: v for k, v in idx["cuerpos"].items() if k in config.CUERPOS}
        _dump(config.INDEX_FILE, idx, indent=1)
    hist = _load(config.HISTORY_FILE, None)
    if hist:
        _dump(config.HISTORY_FILE, {k: v for k, v in hist.items() if k in config.CUERPOS}, indent=1)


if __name__ == "__main__":
    main()
