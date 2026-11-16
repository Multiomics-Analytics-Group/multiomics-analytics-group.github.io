#!/usr/bin/env python3
"""Generate the data behind the Research (publications), Tools and Education
(courses) pages from the link lists in ``_content/``.

Input (edited by people):
    _content/publications.yml   links to papers / preprints (DOI, bioRxiv, journal URL)
    _content/tools.yml          links to tool repositories (GitHub) or websites
    _content/courses.yml        links to course repositories (GitHub) or websites

Output (generated, committed by CI - do not edit by hand):
    _data/auto_publications.json
    _data/auto_tools.json
    _data/auto_courses.json
    public/auto/<kind>/<slug>.<ext>   downloaded figures / images

Every entry in the input files can override any generated field (title,
date, abstract, summary, image, ...). See README.md for the format.

Entries already present in the generated JSON are reused (cached) unless the
entry changed in the input file or ``--refresh`` is given, so CI does not
re-download everything on each run.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import html
import io
import json
import os
import re
import sys
import time
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse, quote

import requests
import yaml

try:
    from PIL import Image
except ImportError:  # pragma: no cover - Pillow is in requirements.txt
    Image = None

ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / "_content"
DATA_DIR = ROOT / "_data"
IMG_DIR = ROOT / "public" / "auto"
SITE_IMG_PREFIX = "public/auto"

KINDS = ("publications", "tools", "courses")
SCHEMA_VERSION = 1  # bump to force regeneration of every cached entry

BOT_UA = "MoNA-website-bot/1.0 (+https://multiomics-analytics-group.github.io)"
BROWSER_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0 Safari/537.36"
)
TIMEOUT = 30
MAX_IMG_WIDTH = 1400
MAX_RAW_IMG_BYTES = 8 * 1024 * 1024  # svg / gif are stored as-is up to this size

BIORXIV_DOI_PREFIXES = ("10.1101/", "10.64898/")

SESSION = requests.Session()
SESSION.headers["User-Agent"] = BOT_UA
_GH_TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

FAILURES: list[str] = []


# --------------------------------------------------------------------------
# Logging helpers (GitHub Actions annotations when running in CI)
# --------------------------------------------------------------------------
IN_CI = os.environ.get("GITHUB_ACTIONS") == "true"


def info(msg: str) -> None:
    print(msg, flush=True)


def warn(msg: str) -> None:
    print(f"::warning::{msg}" if IN_CI else f"WARNING: {msg}", flush=True)


def error(msg: str) -> None:
    FAILURES.append(msg)
    print(f"::error::{msg}" if IN_CI else f"ERROR: {msg}", flush=True)


# --------------------------------------------------------------------------
# HTTP helpers
# --------------------------------------------------------------------------
def http_get(url: str, *, accept: str | None = None, browser: bool = False,
             github: bool = False, retries: int = 3) -> requests.Response | None:
    headers = {}
    if accept:
        headers["Accept"] = accept
    if browser:
        headers["User-Agent"] = BROWSER_UA
        headers.setdefault("Accept", "text/html,application/xhtml+xml,image/avif,image/webp,*/*")
        headers["Accept-Language"] = "en-US,en;q=0.9"
    if github and _GH_TOKEN:
        headers["Authorization"] = f"Bearer {_GH_TOKEN}"
    for attempt in range(retries):
        try:
            r = SESSION.get(url, headers=headers, timeout=TIMEOUT, allow_redirects=True)
        except requests.RequestException as exc:
            info(f"  ! {url}: {exc}")
            r = None
        if r is not None:
            if r.status_code == 200:
                return r
            if r.status_code in (404, 410, 401, 403):
                info(f"  ! {url}: HTTP {r.status_code}")
                return None
            info(f"  ! {url}: HTTP {r.status_code} (attempt {attempt + 1})")
        time.sleep(2 * (attempt + 1))
    return None


def get_json(url: str, **kw) -> dict | list | None:
    r = http_get(url, accept=kw.pop("accept", "application/json"), **kw)
    if r is None:
        return None
    try:
        return r.json()
    except ValueError:
        return None


# --------------------------------------------------------------------------
# Text helpers
# --------------------------------------------------------------------------
TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")


def strip_tags(text: str) -> str:
    text = re.sub(r"</(p|jats:p|sec|jats:sec|title|jats:title)>", "\n\n", text or "")
    text = TAG_RE.sub("", text)
    text = html.unescape(text)
    paras = [WS_RE.sub(" ", p).strip() for p in text.split("\n\n")]
    return "\n\n".join(p for p in paras if p)


def clean_abstract(text: str) -> str:
    text = strip_tags(text)
    # Drop leading "Abstract" heading that Crossref / JATS often include
    text = re.sub(r"^\s*(abstract|summary)\s*[:.]?\s*", "", text, flags=re.I)
    return text.strip()


def slugify(text: str, maxlen: int = 60) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return s[:maxlen].strip("-") or hashlib.sha1(text.encode()).hexdigest()[:10]


def normalize_date(value) -> str | None:
    """Return ISO yyyy-mm-dd (or None)."""
    if value is None or value == "":
        return None
    if isinstance(value, (date, datetime)):
        return value.strftime("%Y-%m-%d")
    s = str(value).strip()
    m = re.match(r"^(\d{4})(?:-(\d{1,2}))?(?:-(\d{1,2}))?", s)
    if not m:
        return None
    y, mo, d = m.group(1), m.group(2) or "1", m.group(3) or "1"
    return f"{int(y):04d}-{int(mo):02d}-{int(d):02d}"


def date_parts_to_iso(parts) -> str | None:
    try:
        p = parts["date-parts"][0]
    except (KeyError, IndexError, TypeError):
        return None
    if not p or p[0] is None:
        return None
    return normalize_date("-".join(str(x) for x in p))


INLINE_CODE_RE = re.compile(r"`([^`]+)`")
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
BOLD_RE = re.compile(r"(\*\*|__)(.+?)\1")
ITALIC_RE = re.compile(r"(?<![\w*])([*_])(?!\s)(.+?)(?<!\s)\1(?![\w*])")
EMOJI_SHORTCODE_RE = re.compile(r":[a-z0-9_+-]+:")


def md_inline_to_html(text: str, base_url: str | None = None) -> str:
    """Convert a small, safe subset of inline Markdown to HTML.

    The input is HTML-escaped first, so README content can never inject
    markup into the site; only links, bold, italics and code are recreated.
    """
    text = TAG_RE.sub("", text)  # drop inline HTML from READMEs
    text = EMOJI_SHORTCODE_RE.sub("", text)
    placeholders: list[str] = []

    def keep(fragment: str) -> str:
        placeholders.append(fragment)
        return f"\x00{len(placeholders) - 1}\x00"

    def link(m: re.Match) -> str:
        label, href = m.group(1), m.group(2)
        if href.startswith("#"):
            return label
        if base_url and not re.match(r"^[a-z]+:", href):
            href = urljoin(base_url, href)
        if not href.startswith(("http://", "https://", "mailto:")):
            return label
        return keep(f'<a href="{html.escape(href, quote=True)}">') + label + keep("</a>")

    text = INLINE_CODE_RE.sub(lambda m: keep(f"<code>{html.escape(m.group(1))}</code>"), text)
    text = LINK_RE.sub(link, text)
    text = html.escape(html.unescape(text), quote=False)
    text = BOLD_RE.sub(r"<b>\2</b>", text)
    text = ITALIC_RE.sub(r"<i>\2</i>", text)
    text = re.sub(r"\x00(\d+)\x00", lambda m: placeholders[int(m.group(1))], text)
    return WS_RE.sub(" ", text).strip()


def md_inline_to_text(text: str) -> str:
    text = TAG_RE.sub("", text)
    text = EMOJI_SHORTCODE_RE.sub("", text)
    text = LINK_RE.sub(r"\1", text)
    text = INLINE_CODE_RE.sub(r"\1", text)
    text = BOLD_RE.sub(r"\2", text)
    text = ITALIC_RE.sub(r"\2", text)
    return WS_RE.sub(" ", html.unescape(text)).strip()


def strip_leading_emoji(text: str) -> str:
    # Remove pictographic characters / variation selectors at the start of titles
    return re.sub(r"^[\W_]+(?=\w)", "", text, flags=re.UNICODE).strip()


# --------------------------------------------------------------------------
# Images
# --------------------------------------------------------------------------
def download_image(url: str, kind: str, slug: str, *, browser: bool = False) -> str | None:
    """Download ``url`` into public/auto/<kind>/ and return the site-relative path."""
    if url.startswith(("public/", "/public/")):
        return url.lstrip("/")  # already a local asset in the repository
    r = http_get(url, browser=browser, accept="image/avif,image/webp,image/png,image/svg+xml,image/*,*/*;q=0.8")
    if r is None:
        return None
    ctype = r.headers.get("Content-Type", "").split(";")[0].strip().lower()
    data = r.content
    path_ext = Path(urlparse(r.url).path).suffix.lower()
    out_dir = IMG_DIR / kind
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob(f"{slug}.*"):
        old.unlink()

    is_svg = ctype == "image/svg+xml" or path_ext == ".svg" or data[:200].lstrip().startswith((b"<svg", b"<?xml"))
    is_gif = ctype == "image/gif" or data[:6] in (b"GIF87a", b"GIF89a")
    if is_svg or is_gif:
        if b"<html" in data[:500].lower():
            return None
        if len(data) > MAX_RAW_IMG_BYTES:
            warn(f"{url}: image larger than {MAX_RAW_IMG_BYTES // 2**20} MB, linking it instead of storing it")
            return url
        ext = ".svg" if is_svg else ".gif"
        (out_dir / f"{slug}{ext}").write_bytes(data)
        return f"{SITE_IMG_PREFIX}/{kind}/{slug}{ext}"

    if Image is None:
        return None
    try:
        img = Image.open(io.BytesIO(data))
        img.load()
    except Exception:  # not an image (e.g. an HTML challenge page)
        info(f"  ! {url}: response is not an image ({ctype or 'unknown type'})")
        return None
    if img.width < 120 or img.height < 60:
        info(f"  ! {url}: image too small ({img.width}x{img.height}), skipping")
        return None
    if img.width > MAX_IMG_WIDTH:
        h = round(img.height * MAX_IMG_WIDTH / img.width)
        img = img.resize((MAX_IMG_WIDTH, h), Image.LANCZOS)
    has_alpha = img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info)
    if has_alpha:
        out = out_dir / f"{slug}.png"
        img.convert("RGBA").save(out, "PNG", optimize=True)
    else:
        out = out_dir / f"{slug}.jpg"
        img.convert("RGB").save(out, "JPEG", quality=85, optimize=True, progressive=True)
    return f"{SITE_IMG_PREFIX}/{kind}/{out.name}"


def try_images(candidates: list[str], kind: str, slug: str, *, browser: bool = False) -> tuple[str | None, str | None]:
    seen = set()
    for url in candidates:
        if not url or url in seen:
            continue
        seen.add(url)
        local = download_image(url, kind, slug, browser=browser)
        if local:
            return local, url
    return None, None


# --------------------------------------------------------------------------
# Publications
# --------------------------------------------------------------------------
DOI_RE = re.compile(r"(10\.\d{4,9}/[^\s\"'<>?#]+)", re.I)


def parse_publication_url(url: str) -> dict:
    """Extract DOI (+ bioRxiv/medRxiv server & version) from a URL or DOI string."""
    out = {"doi": None, "server": None, "version": None}
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if "biorxiv.org" in host:
        out["server"] = "biorxiv"
    elif "medrxiv.org" in host:
        out["server"] = "medrxiv"
    m = DOI_RE.search(url)
    if m:
        doi = m.group(1)
        doi = re.sub(r"\.(full|abstract|supplementary-material|article-info|article-metrics)(\.pdf)?$", "", doi)
        doi = re.sub(r"\.full-text$", "", doi)
        v = re.search(r"v(\d+)$", doi)
        if v and (out["server"] or doi.startswith(BIORXIV_DOI_PREFIXES)):
            out["version"] = int(v.group(1))
            doi = doi[: v.start()]
        out["doi"] = doi.rstrip("/.")
    if out["doi"] and not out["server"] and out["doi"].startswith(BIORXIV_DOI_PREFIXES):
        out["server"] = "biorxiv"  # resolved via api; may also be medRxiv (handled below)
    return out


def format_authors_biorxiv(s: str) -> list[str]:
    """'Cunha, A. F.; Vidal, E.' -> ['Cunha AF', 'Vidal E']"""
    names = []
    for part in (s or "").split(";"):
        part = part.strip()
        if not part:
            continue
        if "," in part:
            last, first = [x.strip() for x in part.split(",", 1)]
            initials = "".join(ch for ch in first if ch.isupper())
            names.append(f"{last} {initials}".strip())
        else:
            names.append(part)
    return names


def format_authors_crossref(authors: list) -> list[str]:
    names = []
    for a in authors or []:
        if a.get("family"):
            initials = "".join(w[0] for w in re.split(r"[\s.\-]+", a.get("given", "")) if w)
            names.append(f"{a['family']} {initials.upper()}".strip())
        elif a.get("name"):
            names.append(a["name"])
    return names


def fetch_biorxiv(doi: str, server_hint: str | None, version: int | None) -> dict | None:
    servers = [server_hint] if server_hint else []
    servers += [s for s in ("biorxiv", "medrxiv") if s not in servers]
    for server in servers:
        data = get_json(f"https://api.biorxiv.org/details/{server}/{doi}")
        coll = (data or {}).get("collection") or []
        if not coll:
            continue
        rec = None
        if version:
            rec = next((c for c in coll if str(c.get("version")) == str(version)), None)
        rec = rec or coll[-1]  # latest version
        return {
            "title": WS_RE.sub(" ", rec.get("title", "")).strip(),
            "authors": format_authors_biorxiv(rec.get("authors", "")),
            "date": normalize_date(rec.get("date")),
            "abstract": clean_abstract(rec.get("abstract", "")),
            "venue": {"biorxiv": "bioRxiv", "medrxiv": "medRxiv"}[server],
            "server": server,
            "version": rec.get("version"),
            "license": rec.get("license"),
            "category": rec.get("category"),
            "jatsxml": rec.get("jatsxml"),
            "published_doi": None if rec.get("published") in (None, "", "NA") else rec.get("published"),
            "first_version_date": normalize_date(coll[0].get("date")),
        }
    return None


def fetch_crossref(doi: str) -> dict | None:
    data = get_json(f"https://api.crossref.org/works/{quote(doi, safe='/')}")
    msg = (data or {}).get("message")
    if not msg:
        return None
    title = (msg.get("title") or [""])[0]
    venue = (msg.get("container-title") or [None])[0]
    if not venue and msg.get("type") == "posted-content":
        venue = (msg.get("institution") or [{}])[0].get("name") or msg.get("group-title") or "Preprint"
    d = None
    for key in ("published-online", "published-print", "posted", "published", "issued", "created"):
        d = date_parts_to_iso(msg.get(key))
        if d:
            break
    lic = None
    for l in msg.get("license") or []:
        if "creativecommons" in l.get("URL", ""):
            lic = l["URL"]
            break
    return {
        "title": strip_tags(title),
        "authors": format_authors_crossref(msg.get("author")),
        "date": d,
        "abstract": clean_abstract(msg.get("abstract", "")),
        "venue": venue,
        "license": lic,
        "landing_url": (msg.get("resource") or {}).get("primary", {}).get("URL"),
    }


def fetch_europepmc_abstract(doi: str) -> str | None:
    q = quote(f'DOI:"{doi}"')
    data = get_json(
        f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={q}&resultType=core&format=json"
    )
    try:
        res = data["resultList"]["result"][0]
    except (TypeError, KeyError, IndexError):
        return None
    return clean_abstract(res.get("abstractText", "")) or None


META_IMG_RE = re.compile(
    r"<meta[^>]+(?:property|name)=[\"'](?:og:image|twitter:image|citation_image)[\"'][^>]*>", re.I
)
CONTENT_ATTR_RE = re.compile(r"content=[\"']([^\"']+)[\"']", re.I)
GENERIC_IMG_RE = re.compile(r"(logo|icon|favicon|default|placeholder|social|share|brand|cover-image)", re.I)


def biorxiv_figure_candidates(rec: dict, page_url: str) -> list[str]:
    """Build candidate figure URLs for a bioRxiv/medRxiv preprint."""
    cands = []
    jats = rec.get("jatsxml") or ""
    # https://www.biorxiv.org/content/early/2026/11/01/2026.10.27.762128.source.xml
    m = re.match(r"(https?://www\.(?:bio|med)rxiv\.org)/content/early/(\d{4}/\d{2}/\d{2})/([^/]+?)\.source\.xml$", jats)
    if m:
        base, dpath, ident = m.groups()
        server = rec.get("server", "biorxiv")
        for fig in ("F1", "F2"):
            cands.append(f"{base}/content/{server}/early/{dpath}/{ident}/{fig}.large.jpg")
        # The JATS source can reveal the actual first figure id (e.g. a graphical abstract)
        r = http_get(jats, browser=True)
        if r is not None and "<fig" in r.text:
            figs = re.findall(r"<fig[^>]*\sid=[\"']([^\"']+)[\"']", r.text)
            for fid in figs[:2]:
                fid_clean = fid.upper() if re.match(r"^f\d+$", fid, re.I) else None
                if fid_clean:
                    url = f"{base}/content/{server}/early/{dpath}/{ident}/{fid_clean}.large.jpg"
                    if url not in cands:
                        cands.insert(0, url)
    # Article page (may be behind a bot challenge; best effort)
    for suffix in (".full", ""):
        r = http_get(page_url.rstrip("/") + suffix, browser=True, retries=1)
        if r is None:
            continue
        found = re.findall(r"(https?://[^\"'\s]+/F1\.large\.jpg)", r.text)
        cands = found[:1] + cands
        break
    return cands


def page_figure_candidates(url: str) -> list[str]:
    """og:image / twitter:image / citation_image from a landing page, excluding logos."""
    r = http_get(url, browser=True, retries=1)
    if r is None:
        return []
    out = []
    for tag in META_IMG_RE.findall(r.text[:200_000]):
        m = CONTENT_ATTR_RE.search(tag)
        if m:
            img = urljoin(r.url, html.unescape(m.group(1)))
            if not GENERIC_IMG_RE.search(urlparse(img).path):
                out.append(img)
    return out


def build_publication(item: dict) -> dict | None:
    url = item["url"]
    ids = parse_publication_url(item.get("doi") or url)
    doi = item.get("doi") or ids["doi"]
    rec: dict = {}
    if doi and (ids["server"] or doi.startswith(BIORXIV_DOI_PREFIXES)):
        rec = fetch_biorxiv(doi, ids["server"], ids["version"]) or {}
    if doi and (not rec.get("title") or not rec.get("abstract") or not rec.get("authors")):
        cr = fetch_crossref(doi) or {}
        for k, v in cr.items():
            if v and not rec.get(k):
                rec[k] = v
    if doi and not rec.get("abstract"):
        rec["abstract"] = fetch_europepmc_abstract(doi) or ""
    if not rec.get("title") and not item.get("title"):
        error(f"Publication {url}: could not retrieve metadata (no DOI found or APIs unreachable). "
              "Add 'title', 'date' and 'abstract' to the entry to override.")
        return None

    slug = slugify(doi or url)
    image = None
    image_source = None
    if not item.get("image"):
        cands: list[str] = []
        if rec.get("jatsxml") or (ids["server"]):
            cands += biorxiv_figure_candidates(rec, url)
        else:
            cands += page_figure_candidates(url)
            if doi and rec.get("landing_url") and rec["landing_url"] != url:
                cands += page_figure_candidates(rec["landing_url"])
        image, image_source = try_images(cands, "publications", slug, browser=True)
        if not image:
            warn(f"Publication {url}: no figure could be downloaded automatically. "
                 "Add 'image: <url or public/... path>' to the entry to set one.")

    authors = rec.get("authors") or []
    pub = {
        "id": slug,
        "url": url,
        "doi": doi,
        "doi_url": f"https://doi.org/{doi}" if doi else None,
        "title": rec.get("title"),
        "authors": authors,
        "authors_str": ", ".join(authors),
        "authors_short": (f"{authors[0].split(' ')[0]} et al." if len(authors) > 2
                          else " & ".join(a.split(" ")[0] for a in authors)),
        "date": rec.get("date"),
        "venue": rec.get("venue"),
        "abstract": rec.get("abstract") or "",
        "license": rec.get("license"),
        "published_doi": rec.get("published_doi"),
        "image": image,
        "image_source": image_source,
        "image_caption": "Figure 1" if image_source and re.search(r"/F1\.large\.jpg$", image_source) else None,
    }
    return pub


# --------------------------------------------------------------------------
# Repositories (tools & courses)
# --------------------------------------------------------------------------
GH_RE = re.compile(r"^https?://(?:www\.)?github\.com/([^/\s]+)/([^/\s#?]+)", re.I)
BADGE_RE = re.compile(
    r"(shields\.io|badge|badgen|travis-ci|codecov|coveralls|circleci|/workflows/|actions/workflows|"
    r"readthedocs\.org/projects/.+/badge|zenodo\.org/badge|colab-badge|binder|mybinder\.org/badge|"
    r"pepy\.tech|anaconda\.org/.+/badges|codacy|sonarcloud|deepsource|star-history|contrib\.rocks|"
    r"github-readme-stats|hits\.|visitor|komarev|api\.netlify)",
    re.I,
)
FIGURE_HINT_RE = re.compile(
    r"(figure|fig\d|schem|workflow|overview|abstract|pipeline|diagram|architecture|graph|banner|cover|"
    r"header|summary|framework|screenshot|demo|example|nb_logo)",
    re.I,
)
INSTITUTION_HINT_RE = re.compile(
    r"(\bdtu\b|dtu[_\-.]|udea|universit|\buni[_\-]|nnf|novo|nordisk|funding|funder|sponsor|partner|"
    r"eu[_\-]?flag|\berc\b|horizon|biosustain_logo|institut|acknowledg)",
    re.I,
)
ACK_HEADING_RE = re.compile(r"(acknowledg|funding|sponsor|partner|support|credits|citation|license|contributors)", re.I)
HIGHLIGHT_HEADING_RE = re.compile(
    r"(objective|learning (goal|outcome|objective)|goals?\b|aims?\b|key features|features|highlights|"
    r"what you will learn|you will learn|capabilities|main functionalit)",
    re.I,
)
KEYWORDS_HEADING_RE = re.compile(r"^(keywords|key words|tags)$", re.I)
MD_IMG_RE = re.compile(r"!\[([^\]]*)\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
HTML_IMG_RE = re.compile(r"<img\b[^>]*?\bsrc=[\"']([^\"']+)[\"'][^>]*>", re.I)
HTML_ALT_RE = re.compile(r"\balt=[\"']([^\"']*)[\"']", re.I)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
HTML_HEADING_RE = re.compile(r"^\s*<h([1-6])[^>]*>(.*?)</h\1>\s*$", re.I | re.S)


def resolve_repo_url(src: str, owner: str, repo: str, branch: str, readme_dir: str) -> str:
    src = html.unescape(src.strip())
    if src.startswith("//"):
        src = "https:" + src
    if re.match(r"^https?://", src):
        # github.com/<o>/<r>/blob/<b>/path  ->  raw
        m = re.match(r"^https?://github\.com/([^/]+)/([^/]+)/(?:blob|raw)/(.+?)(\?raw=(true|1))?$", src)
        if m:
            return f"https://raw.githubusercontent.com/{m.group(1)}/{m.group(2)}/{m.group(3)}"
        return src
    path = src.split("?")[0].split("#")[0]
    if path.startswith("/"):
        path = path.lstrip("/")
    else:
        path = os.path.normpath(os.path.join(readme_dir, path)).replace("\\", "/")
    return f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{quote(path)}"


def parse_readme(md: str) -> dict:
    """Split a README into structured pieces used for the website."""
    md = re.sub(r"<!--.*?-->", "", md, flags=re.S)
    md = re.sub(r"^(```|~~~).*?^\1\s*$", "", md, flags=re.S | re.M)  # code fences
    md = md.replace("\r\n", "\n")

    blocks: list[dict] = []
    current_heading = None
    current_level = 0
    first_heading_seen = False
    para_lines: list[str] = []

    def flush():
        nonlocal para_lines
        if para_lines:
            blocks.append({"type": "text", "lines": para_lines, "heading": current_heading,
                           "level": current_level, "before_first_heading": not first_heading_seen})
            para_lines = []

    for line in md.split("\n"):
        h = HEADING_RE.match(line) or HTML_HEADING_RE.match(line)
        if h:
            flush()
            level = len(h.group(1)) if h.re is HEADING_RE else int(h.group(1))
            text = md_inline_to_text(MD_IMG_RE.sub("", h.group(2)))
            blocks.append({"type": "heading", "level": level, "text": text})
            current_heading, current_level = text, level
            first_heading_seen = True
            continue
        if not line.strip():
            flush()
            continue
        para_lines.append(line)
    flush()

    title = next((b["text"] for b in blocks if b["type"] == "heading" and b["level"] == 1 and b["text"]), None)
    if not title:  # a README may start with an HTML <h1> / <p align=center> banner
        m = re.search(r"<h1[^>]*>(.*?)</h1>", md, flags=re.S | re.I)
        if m:
            title = md_inline_to_text(m.group(1)) or None

    # ---- images (in document order, with context) ----
    images = []
    for b in blocks:
        if b["type"] != "text":
            continue
        text = "\n".join(b["lines"])
        found = [(m.start(), m.group(2), m.group(1)) for m in MD_IMG_RE.finditer(text)]
        for m in HTML_IMG_RE.finditer(text):
            alt = HTML_ALT_RE.search(m.group(0))
            found.append((m.start(), m.group(1), alt.group(1) if alt else ""))
        found.sort()
        non_badge = [f for f in found if not BADGE_RE.search(f[1])]
        for _, src, alt in non_badge:
            images.append({
                "src": src, "alt": alt,
                "heading": b["heading"],
                "in_row": len(non_badge) > 1,
                "before_first_heading": b["before_first_heading"],
            })

    # ---- summary paragraphs ----
    paragraphs = []
    for b in blocks:
        if b["type"] != "text":
            continue
        if b["heading"] and ACK_HEADING_RE.search(b["heading"]):
            continue
        lines = b["lines"]
        first = lines[0].lstrip()
        if first.startswith(("|", ">", "<", "![", "[![", "- ", "* ", "+ ", "    ")) or re.match(r"^\d+[.)]\s", first):
            continue
        text = " ".join(l.strip() for l in lines)
        text_wo_imgs = MD_IMG_RE.sub("", text)
        plain = md_inline_to_text(text_wo_imgs)
        if len(plain) < 60 or plain.endswith(":") and len(plain) < 120:
            continue
        if b["heading"] and KEYWORDS_HEADING_RE.match(b["heading"]):
            continue
        paragraphs.append({"md": text_wo_imgs, "plain": plain, "heading": b["heading"]})

    # ---- highlights (bullets under objectives / features headings) ----
    highlights = []
    for b in blocks:
        if b["type"] != "text" or not b["heading"] or not HIGHLIGHT_HEADING_RE.search(b["heading"]):
            continue
        for line in b["lines"]:
            m = re.match(r"^\s{0,3}(?:[-*+]|\d+[.)])\s+(.*)$", line)
            if m:
                highlights.append(m.group(1).strip())
        if highlights:
            break

    keywords = []
    for b in blocks:
        if b["type"] == "text" and b["heading"] and KEYWORDS_HEADING_RE.match(b["heading"]):
            kw_text = md_inline_to_text(" ".join(b["lines"]))
            keywords = [k.strip(" .") for k in re.split(r"[,;·•|]", kw_text) if k.strip(" .")]
            break

    return {"title": title, "paragraphs": paragraphs, "highlights": highlights,
            "keywords": keywords, "images": images}


def rank_image(img: dict, repo: str) -> int:
    """Lower is better. 9 = do not use."""
    name = (Path(urlparse(img["src"]).path).name + " " + (img.get("alt") or "")).lower()
    repo_tokens = [t for t in re.split(r"[^a-z0-9]+", repo.lower()) if len(t) > 2]
    own_logo = "logo" in name and any(t in name for t in repo_tokens)
    if img.get("heading") and ACK_HEADING_RE.search(img["heading"]):
        return 9
    if INSTITUTION_HINT_RE.search(name) and not own_logo:
        return 9
    if img["in_row"] and img["before_first_heading"] and not own_logo:
        return 9  # a row of institutional logos above the title
    if FIGURE_HINT_RE.search(name):
        return 0
    if own_logo:
        return 1
    return 2


def summarize_paragraphs(paragraphs: list[dict], base_url: str, max_chars: int = 900, max_paras: int = 2) -> tuple[str, str]:
    chosen: list[dict] = []
    total = 0
    for p in paragraphs:
        if chosen and (total + len(p["plain"]) > max_chars or len(chosen) >= max_paras):
            break
        # stay within the opening part of the README (intro / overview sections)
        if chosen and p["heading"] != chosen[0]["heading"] and not re.search(
                r"(about|overview|introduction|description|summary|what is)", p["heading"] or "", re.I):
            break
        chosen.append(p)
        total += len(p["plain"])
    html_out = "".join(f"<p>{md_inline_to_html(p['md'], base_url)}</p>" for p in chosen)
    plain = " ".join(p["plain"] for p in chosen)
    return html_out, plain


def fetch_github_repo(owner: str, repo: str) -> tuple[dict | None, dict | None]:
    meta = get_json(f"https://api.github.com/repos/{owner}/{repo}", github=True,
                    accept="application/vnd.github+json")
    if not meta:
        return None, None
    readme = get_json(f"https://api.github.com/repos/{owner}/{repo}/readme", github=True,
                      accept="application/vnd.github+json")
    return meta, readme


def build_repo_entry(item: dict, kind: str) -> dict | None:
    url = item["url"].rstrip("/")
    m = GH_RE.match(url)
    if not m:
        return build_website_entry(item, kind)
    owner, repo = m.group(1), re.sub(r"\.git$", "", m.group(2))
    meta, readme = fetch_github_repo(owner, repo)
    if not meta:
        error(f"{kind[:-1].title()} {url}: GitHub repository not found or API unreachable.")
        return None
    branch = meta.get("default_branch", "main")
    md, readme_path = "", "README.md"
    if readme and readme.get("content"):
        md = base64.b64decode(readme["content"]).decode("utf-8", errors="replace")
        readme_path = readme.get("path", "README.md")
    readme_dir = os.path.dirname(readme_path)
    base_url = f"https://github.com/{owner}/{repo}/blob/{branch}/{readme_dir + '/' if readme_dir else ''}"
    parsed = parse_readme(md) if md else {"title": None, "paragraphs": [], "highlights": [], "keywords": [], "images": []}

    summary_html, summary_text = summarize_paragraphs(parsed["paragraphs"], base_url)
    if not summary_html and meta.get("description"):
        summary_html = f"<p>{html.escape(meta['description'])}</p>"
        summary_text = meta["description"]

    slug = slugify(f"{owner}-{repo}")
    image, image_source = None, None
    if not item.get("image"):
        ranked = sorted(
            ((rank_image(img, repo), i, img) for i, img in enumerate(parsed["images"])),
            key=lambda t: (t[0], t[1]),
        )
        cands = [resolve_repo_url(img["src"], owner, repo, branch, readme_dir) for r, _, img in ranked if r < 9]
        image, image_source = try_images(cands, kind, slug)
        if not image:
            # Fall back to the repository's social preview card
            card = f"https://opengraph.githubassets.com/1/{owner}/{repo}"
            image, image_source = try_images([card], kind, slug)
            if image:
                warn(f"{url}: no suitable README image found, using the GitHub preview card. "
                     "Set 'image:' in the entry to choose another one.")

    title = parsed["title"] or meta.get("name")
    title = strip_leading_emoji(title) if title else repo
    topics = meta.get("topics") or []
    keywords = parsed["keywords"] or [t.replace("-", " ") for t in topics]

    entry = {
        "id": slug,
        "url": meta.get("html_url", url),
        "repo": f"{owner}/{repo}",
        "title": title,
        "description": meta.get("description") or "",
        "summary_html": summary_html,
        "summary": summary_text,
        "highlights": [md_inline_to_html(h, base_url) for h in parsed["highlights"][:6]],
        "keywords": keywords[:12],
        "homepage": meta.get("homepage") or None,
        "date": normalize_date(meta.get("created_at")),
        "updated": normalize_date(meta.get("pushed_at")),
        "language": meta.get("language"),
        "license": (meta.get("license") or {}).get("spdx_id") if meta.get("license") else None,
        "stars": meta.get("stargazers_count"),
        "image": image,
        "image_source": image_source,
    }
    return entry


def build_website_entry(item: dict, kind: str) -> dict | None:
    """Non-GitHub link: use the page's <title>, meta description and og:image."""
    url = item["url"]
    r = http_get(url, browser=True)
    if r is None and not item.get("title"):
        error(f"{kind[:-1].title()} {url}: page could not be fetched. Add 'title' and 'summary' to override.")
        return None
    text = r.text if r is not None else ""

    def meta(name: str) -> str | None:
        m = re.search(rf"<meta[^>]+(?:property|name)=[\"']{name}[\"'][^>]*>", text, re.I)
        if m:
            c = CONTENT_ATTR_RE.search(m.group(0))
            return html.unescape(c.group(1)).strip() if c else None
        return None

    title = meta("og:title") or (re.search(r"<title[^>]*>(.*?)</title>", text, re.S | re.I) or [None, None])[1]
    desc = meta("og:description") or meta("description") or ""
    slug = slugify(urlparse(url).netloc + urlparse(url).path)
    image = image_source = None
    if not item.get("image"):
        img = meta("og:image")
        if img:
            image, image_source = try_images([urljoin(url, img)], kind, slug, browser=True)
    return {
        "id": slug, "url": url, "repo": None,
        "title": WS_RE.sub(" ", html.unescape(title or url)).strip(),
        "description": desc, "summary_html": f"<p>{html.escape(desc)}</p>" if desc else "",
        "summary": desc, "highlights": [], "keywords": [], "homepage": None,
        "date": None, "updated": None, "language": None, "license": None, "stars": None,
        "image": image, "image_source": image_source,
    }


# --------------------------------------------------------------------------
# Overrides, cache and main loop
# --------------------------------------------------------------------------
def apply_overrides(entry: dict, item: dict, kind: str) -> dict:
    for key, value in item.items():
        if key == "url" or value is None:
            continue
        if key == "date":
            entry["date"] = normalize_date(value)
        elif key == "image":
            slug = entry.get("id") or slugify(item["url"])
            local = download_image(str(value), kind, slug, browser=True)
            entry["image"] = local or str(value)
            entry["image_source"] = str(value)
        elif key == "summary":
            entry["summary"] = str(value).strip()
            entry["summary_html"] = "".join(
                f"<p>{md_inline_to_html(p)}</p>" for p in re.split(r"\n\s*\n", str(value).strip()) if p.strip())
        elif key == "highlights" and isinstance(value, list):
            entry["highlights"] = [md_inline_to_html(str(v)) for v in value]
        elif key == "authors":
            entry["authors"] = value if isinstance(value, list) else [a.strip() for a in str(value).split(",")]
            entry["authors_str"] = ", ".join(entry["authors"])
        elif key == "abstract":
            entry["abstract"] = str(value).strip()
        else:
            entry[key] = value
    if entry.get("date"):
        entry["year"] = entry["date"][:4]
    if kind == "publications":
        paras = [p.strip() for p in re.split(r"\n\s*\n", entry.get("abstract") or "") if p.strip()]
        entry["abstract_html"] = "".join(f"<p>{html.escape(p, quote=False)}</p>" for p in paras)
    return entry


def load_items(kind: str) -> list[dict]:
    path = CONTENT_DIR / f"{kind}.yml"
    if not path.exists():
        return []
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or []
    if isinstance(raw, dict):
        raw = raw.get(kind) or raw.get("items") or []
    items = []
    seen = set()
    for i, it in enumerate(raw):
        if isinstance(it, str):
            it = {"url": it}
        if not isinstance(it, dict) or not it.get("url"):
            error(f"{path.name} entry #{i + 1} has no 'url': {it!r}")
            continue
        it["url"] = str(it["url"]).strip()
        if it["url"] in seen:
            warn(f"{path.name}: duplicated url {it['url']} (ignored)")
            continue
        seen.add(it["url"])
        items.append(it)
    return items


def item_hash(item: dict) -> str:
    payload = json.dumps({"v": SCHEMA_VERSION, "item": item}, sort_keys=True, default=str)
    return hashlib.sha1(payload.encode()).hexdigest()[:12]


def image_exists(entry: dict) -> bool:
    img = entry.get("image")
    if not img:
        return False
    if re.match(r"^https?://", img):
        return True
    return (ROOT / img).exists()


def process(kind: str, refresh: bool, only: str | None) -> None:
    items = load_items(kind)
    out_path = DATA_DIR / f"auto_{kind}.json"
    cache = {}
    if out_path.exists():
        try:
            cache = {e["source_url"]: e for e in json.loads(out_path.read_text(encoding="utf-8"))}
        except (ValueError, KeyError, TypeError):
            cache = {}

    info(f"\n== {kind} ({len(items)} entries) ==")
    entries = []
    for item in items:
        if item.get("hidden"):
            continue
        h = item_hash(item)
        cached = cache.get(item["url"])
        if (cached and cached.get("source_hash") == h and not refresh and image_exists(cached)
                and not (only and only in item["url"])):
            info(f"- cached  {item['url']}")
            entries.append(cached)
            continue
        info(f"- fetch   {item['url']}")
        try:
            entry = build_publication(item) if kind == "publications" else build_repo_entry(item, kind)
        except Exception as exc:  # keep going; report at the end
            error(f"{item['url']}: unexpected error {type(exc).__name__}: {exc}")
            entry = None
        if entry is None:
            if cached:
                warn(f"{item['url']}: keeping previously generated data")
                entries.append(cached)
            continue
        entry = apply_overrides(entry, item, kind)
        entry["source_url"] = item["url"]
        entry["source_hash"] = h
        entry["featured"] = bool(item.get("featured", False))
        entries.append(entry)
        info(f"  -> {entry.get('title')!r} ({entry.get('date')}), image: {entry.get('image')}")

    # newest first; entries without a date go last
    entries.sort(key=lambda e: e.get("date") or "0000-00-00", reverse=True)
    DATA_DIR.mkdir(exist_ok=True)
    out_path.write_text(json.dumps(entries, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    info(f"wrote {out_path.relative_to(ROOT)} ({len(entries)} entries)")

    # remove images that no longer belong to any entry
    used = {Path(e["image"]).name for e in entries if e.get("image") and not re.match(r"^https?://", e["image"])}
    img_dir = IMG_DIR / kind
    if img_dir.exists():
        for f in img_dir.iterdir():
            if f.is_file() and f.name not in used:
                info(f"removing unused image {f.relative_to(ROOT)}")
                f.unlink()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--kind", choices=KINDS + ("all",), default="all")
    ap.add_argument("--refresh", action="store_true", help="ignore cached entries and fetch everything again")
    ap.add_argument("--only", help="re-fetch only entries whose url contains this text")
    ap.add_argument("--strict", action="store_true", help="exit with status 1 if any entry failed")
    args = ap.parse_args()

    kinds = KINDS if args.kind == "all" else (args.kind,)
    for kind in kinds:
        process(kind, args.refresh, args.only)

    if FAILURES:
        info(f"\n{len(FAILURES)} problem(s):")
        for f in FAILURES:
            info(f"  - {f}")
        return 1 if args.strict else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
