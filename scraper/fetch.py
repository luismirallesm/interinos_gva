"""Descubre y descarga PDFs de listados diarios publicados por la GVA."""
from __future__ import annotations

import datetime as dt
import hashlib
import time
import urllib.robotparser
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from . import config


@dataclass
class Listing:
    url: str
    path: str
    sha256: str


def _session() -> requests.Session:
    s = requests.Session()
    s.headers["User-Agent"] = config.USER_AGENT
    return s


def allowed_by_robots(url: str, session: requests.Session) -> bool:
    """Respeta robots.txt del sitio. Si no se puede leer, se asume permitido."""
    p = urlparse(url)
    try:
        r = session.get(f"{p.scheme}://{p.netloc}/robots.txt", timeout=config.REQUEST_TIMEOUT)
    except requests.RequestException:
        return True
    if r.status_code != 200:
        return True
    rp = urllib.robotparser.RobotFileParser()
    rp.parse(r.text.splitlines())
    return rp.can_fetch(config.USER_AGENT, url)


def discover_links(session: requests.Session | None = None) -> list[str]:
    """URLs de PDFs con nombre AAMMDD_lis_<cuerpo>.pdf. Sigue subpáginas un nivel."""
    session = session or _session()
    found: set[str] = set()
    seen: set[str] = set()
    first_level = set(config.SOURCES)
    queue = list(config.SOURCES)

    while queue:
        page = queue.pop(0)
        if page in seen:
            continue
        seen.add(page)
        if not allowed_by_robots(page, session):
            print(f"robots.txt NO permite {page}: se omite")
            continue
        resp = session.get(page, timeout=config.REQUEST_TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for a in soup.find_all("a", href=True):
            href = urljoin(page, a["href"])
            path = urlparse(href).path
            m = config.LISTING_RE.search(path) or config.INICIO_RE.search(path)
            if m:
                if m.group(2).lower() in config.CUERPOS:
                    found.add(href)
            elif (
                page in first_level
                and "/web/rrhh-educacion/" in path.lower()
                and any(k in path.lower() for k in config.SUBPAGE_KEYWORDS)
            ):
                queue.append(href)
        time.sleep(config.REQUEST_DELAY_SECONDS)
    print(f"{len(seen)} páginas, {len(found)} listados")
    return sorted(found)


def _save(content: bytes, url: str) -> Listing:
    digest = hashlib.sha256(content).hexdigest()
    config.RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = config.RAW_DIR / f"{digest[:16]}.pdf"
    path.write_bytes(content)
    return Listing(url=url, path=str(path), sha256=digest)


def download(url: str, session: requests.Session | None = None) -> Listing:
    session = session or _session()
    if not allowed_by_robots(url, session):
        raise PermissionError(f"robots.txt no permite {url}")
    resp = session.get(url, timeout=config.REQUEST_TIMEOUT)
    resp.raise_for_status()
    listing = _save(resp.content, url)
    time.sleep(config.REQUEST_DELAY_SECONDS)
    return listing


def folder_of(url: str) -> int | None:
    m = config.DOC_URL.split("{folder}")[0]
    if url.startswith(m):
        part = url[len(m):].split("/")[0]
        return int(part) if part.isdigit() else None
    return None


def probe_listings(cuerpo, known_dates, folders, skip, today=None, session=None):
    """Prueba URLs AAMMDD_lis_<cuerpo>.pdf para cada día laborable aún sin listado.

    skip: {fecha: nº de carpetas ya probadas}; un día sin listado solo se salta si
    ya se probaron todas las carpetas actuales y tiene más de RECHECK_DAYS días.
    Devuelve (encontrados [(url, Listing)], sin_listado {fecha: n_carpetas}).
    """
    session = session or _session()
    today = today or dt.date.today()
    folders = sorted(set(folders), reverse=True)        # las más nuevas primero
    sample = config.DOC_URL.format(folder=folders[0], name=f"000000_lis_{cuerpo}.pdf")
    if not allowed_by_robots(sample, session):
        print("robots.txt NO permite /documents/: se omite la búsqueda por patrón")
        return [], {}
    found, missing = [], {}
    d = dt.date.fromisoformat(config.PROBE_START)
    while d <= today:
        iso = d.isoformat()
        old = (today - d).days > config.RECHECK_DAYS
        if d.weekday() < 5 and iso not in known_dates and not (old and skip.get(iso, 0) >= len(folders)):
            name = f"{d:%y%m%d}_lis_{cuerpo}.pdf"
            hit = None
            for folder in folders:
                url = config.DOC_URL.format(folder=folder, name=name)
                try:
                    r = session.get(url, timeout=config.REQUEST_TIMEOUT)
                except requests.RequestException as e:
                    print(f"error de red en {url}: {e}")
                    continue
                time.sleep(config.PROBE_DELAY_SECONDS)
                if r.status_code == 200 and r.content[:5] == b"%PDF-":
                    hit = (url, r.content)
                    break
            if hit:
                found.append((hit[0], _save(hit[1], hit[0])))
            else:
                missing[iso] = len(folders)
        d += dt.timedelta(days=1)
    return found, missing
