"""Orquesta: descubrir -> descargar -> parsear -> escribir data/*.json.

Uso:
  python -m scraper.build                       # modo normal (CI)
  python -m scraper.build --pdf f.pdf --date 2026-09-01 --specialty "Infantil"
"""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
from datetime import date

from . import config
from .fetch import discover_links, download
from .parse_pdf import parse_pdf


def slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-") or "sin-especialidad"


def _load(path, default):
    return json.loads(path.read_text("utf-8")) if path.exists() else default


def _dump(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=True) + "\n", "utf-8")


def merge_rows(rows: list[dict], today: str, default_specialty: str | None) -> set[str]:
    """Fusiona filas en data/<especialidad>.json; la clave es el número de orden."""
    by_spec: dict[str, list[dict]] = {}
    for r in rows:
        spec = r.get("especialidad") or default_specialty or "sin-especialidad"
        r["especialidad"] = spec
        by_spec.setdefault(slug(spec), []).append(r)

    touched = set()
    for sid, new_rows in by_spec.items():
        path = config.DATA_DIR / f"{sid}.json"
        db = _load(path, {"especialidad": new_rows[0]["especialidad"], "rows": {}})
        for r in new_rows:
            db["rows"][str(r["orden"])] = r
        db["updated"] = today
        _dump(path, db)
        touched.add(sid)
        _update_history(sid, db, today)
    return touched


def _update_history(sid: str, db: dict, today: str) -> None:
    hist = _load(config.HISTORY_FILE, {})
    counts: dict[str, int] = {}
    for r in db["rows"].values():
        counts[r["estado"]] = counts.get(r["estado"], 0) + 1
    hist.setdefault(sid, {})[today] = {"total": len(db["rows"]), **counts}
    _dump(config.HISTORY_FILE, hist)


def write_index(touched: set[str]) -> None:
    idx = _load(config.DATA_DIR / "index.json", {"especialidades": {}})
    for sid in touched:
        db = _load(config.DATA_DIR / f"{sid}.json", {})
        idx["especialidades"][sid] = {
            "nombre": db.get("especialidad", sid),
            "updated": db.get("updated"),
            "total": len(db.get("rows", {})),
        }
    _dump(config.DATA_DIR / "index.json", idx)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", help="parsear un PDF local en vez de descargar")
    ap.add_argument("--date", default=date.today().isoformat())
    ap.add_argument("--specialty", help="especialidad por defecto si el PDF no la trae")
    args = ap.parse_args()

    state = _load(config.STATE_FILE, {"processed": {}})
    touched: set[str] = set()

    if args.pdf:
        touched |= merge_rows(parse_pdf(args.pdf), args.date, args.specialty)
    else:
        for url, title in discover_links():
            listing = download(url, title)
            if listing.sha256 in state["processed"]:
                continue
            rows = parse_pdf(listing.path)
            print(f"{url}: {len(rows)} filas")
            if rows:
                touched |= merge_rows(rows, args.date, None)
                state["processed"][listing.sha256] = {"url": url, "date": args.date, "rows": len(rows)}

    if touched:
        write_index(touched)
        _dump(config.STATE_FILE, state)


if __name__ == "__main__":
    main()
