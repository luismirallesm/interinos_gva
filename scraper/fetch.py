"""Descubre y descarga PDFs de listados publicados por la GVA."""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from . import config


@dataclass
class Listing:
    url: str
    title: str
    path: str
    sha256: str


def _session() -> requests.Session:
    s = requests.Session()
    s.headers["User-Agent"] = config.USER_AGENT
    return s


def discover_links(session: requests.Session | None = None) -> list[tuple[str, str]]:
    """Return [(url, text)] of PDF links. Follow sub-pages one level."""
    session = session or _session()
    found: dict[str, str] = {}
    seen_pages: set[str] = set()
    queue = list(config.SOURCES)
    depth1 = set(config.SOURCES)

    while queue:
        page = queue.pop(0)
        if page in seen_pages:
            continue
        seen_pages.add(page)
        resp = session.get(page, timeout=config.REQUEST_TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for a in soup.find_all("a", href=True):
            href = urljoin(page, a["href"])
            text = a.get_text(" ", strip=True)
            path = urlparse(href).path.lower()
            if ".pdf" in path and config.PDF_PATH_PREFIX in path:
                found[href] = text
            elif (
                page in depth1
                and "/web/rrhh-educacion/" in path
                and any(k in path for k in config.SUBPAGE_KEYWORDS)
            ):
                queue.append(href)
        time.sleep(config.REQUEST_DELAY_SECONDS)
    print(f"{len(seen_pages)} paginas, {len(found)} PDF")
    return list(found.items())


def download(url: str, title: str, session: requests.Session | None = None) -> Listing:
    session = session or _session()
    resp = session.get(url, timeout=config.REQUEST_TIMEOUT)
    resp.raise_for_status()
    digest = hashlib.sha256(resp.content).hexdigest()
    config.RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = config.RAW_DIR / f"{digest[:16]}.pdf"
    path.write_bytes(resp.content)
    time.sleep(config.REQUEST_DELAY_SECONDS)
    return Listing(url=url, title=title, path=str(path), sha256=digest)
