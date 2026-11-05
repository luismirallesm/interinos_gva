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
    """Devuelve [(url, texto)] de enlaces candidatos en las páginas fuente."""
    session = session or _session()
    found: dict[str, str] = {}
    for page in config.SOURCES:
        resp = session.get(page, timeout=config.REQUEST_TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for a in soup.find_all("a", href=True):
            href = urljoin(page, a["href"])
            text = a.get_text(" ", strip=True)
            blob = f"{href} {text}".lower()
            is_pdf = href.lower().split("?")[0].endswith(".pdf")
            if is_pdf and any(k in blob for k in config.LINK_KEYWORDS):
                found[href] = text
        time.sleep(config.REQUEST_DELAY_SECONDS)
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
