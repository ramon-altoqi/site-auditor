import os
from datetime import datetime, timezone
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup

TIMEOUT_S = int(os.getenv("REQUEST_TIMEOUT_MS", "10000")) / 1000
USER_AGENT = "Mozilla/5.0 (compatible; SiteAuditor/1.0)"


class AuditError(Exception):
    def __init__(self, error_type: str, message: str, http_status: int = 502):
        self.error_type = error_type
        self.message = message
        self.http_status = http_status
        super().__init__(message)


# ── Validation ────────────────────────────────────────────────────────────────

def validate_url(raw: str) -> None:
    try:
        parsed = urlparse(raw)
        if parsed.scheme not in ("http", "https"):
            raise AuditError("INVALID_URL", "A URL deve usar o protocolo http ou https", 422)
        if not parsed.netloc:
            raise AuditError("INVALID_URL", f'URL inválida: "{raw}"', 422)
    except AuditError:
        raise
    except Exception:
        raise AuditError("INVALID_URL", f'URL inválida: "{raw}"', 422)


# ── Fetch ─────────────────────────────────────────────────────────────────────

def fetch_page(url: str) -> requests.Response:
    try:
        response = requests.get(
            url,
            timeout=TIMEOUT_S,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
            },
            allow_redirects=True,
        )
        return response
    except requests.exceptions.Timeout:
        raise AuditError("TIMEOUT", f"Timeout após {int(TIMEOUT_S)}s tentando acessar a URL", 504)
    except requests.exceptions.ConnectionError as e:
        msg = str(e)
        if any(k in msg for k in ("Name or service not known", "getaddrinfo", "nodename nor servname")):
            raise AuditError("DNS_ERROR", "Host não encontrado — verifique a URL", 502)
        raise AuditError("FETCH_ERROR", f"Erro de conexão: {e}", 502)
    except Exception as e:
        raise AuditError("FETCH_ERROR", f"Erro ao buscar a página: {e}", 502)


# ── Extraction ────────────────────────────────────────────────────────────────

def extract_seo(soup: BeautifulSoup) -> dict:
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else None

    meta_desc = soup.find("meta", attrs={"name": "description"})
    description = meta_desc.get("content", "").strip() if meta_desc else None
    description = description or None

    canonical_tag = soup.find("link", rel="canonical")
    canonical = canonical_tag.get("href", "").strip() if canonical_tag else None
    canonical = canonical or None

    robots_tag = soup.find("meta", attrs={"name": "robots"})
    robots = robots_tag.get("content", "").strip() if robots_tag else None
    robots = robots or None

    og_title_tag = soup.find("meta", property="og:title")
    og_title = og_title_tag.get("content", "").strip() if og_title_tag else None

    og_desc_tag = soup.find("meta", property="og:description")
    og_desc = og_desc_tag.get("content", "").strip() if og_desc_tag else None

    h1s = [h.get_text(strip=True) for h in soup.find_all("h1") if h.get_text(strip=True)]
    h2s = [h.get_text(strip=True) for h in soup.find_all("h2") if h.get_text(strip=True)]

    return {
        "title": title,
        "description": description,
        "canonical": canonical,
        "robots": robots,
        "og_title": og_title,
        "og_description": og_desc,
        "h1s": h1s,
        "h2s": h2s,
    }


def extract_links(soup: BeautifulSoup, page_url: str) -> dict:
    page_host = urlparse(page_url).hostname
    internal, external, without_text = [], [], []

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue

        try:
            absolute = urljoin(page_url, href)
            parsed = urlparse(absolute)
            if parsed.scheme not in ("http", "https"):
                continue
        except Exception:
            continue

        img_alt = a.find("img").get("alt", "").strip() if a.find("img") else ""
        visible_text = a.get_text(strip=True) or img_alt
        link = {"href": absolute, "text": visible_text or None}

        if parsed.hostname == page_host:
            internal.append(link)
        else:
            external.append(link)

        if not visible_text:
            without_text.append({"href": absolute})

    return {"internal": internal, "external": external, "without_text": without_text}


def extract_images(soup: BeautifulSoup) -> dict:
    without_alt = []
    for img in soup.find_all("img"):
        if img.get("alt") is None:
            without_alt.append({
                "src": img.get("src"),
                "title": img.get("title"),
            })
    return {"without_alt": without_alt}


# ── Issues ────────────────────────────────────────────────────────────────────

def generate_issues(seo: dict, links: dict, images: dict) -> list[dict]:
    issues = []

    def add(severity, code, message, details=None):
        issue = {"severity": severity, "code": code, "message": message}
        if details:
            issue["details"] = details
        issues.append(issue)

    # Title
    title = seo["title"]
    if not title:
        add("critical", "MISSING_TITLE", "Página sem tag <title>")
    elif len(title) < 30:
        add("warning", "TITLE_TOO_SHORT",
            f"Title muito curto ({len(title)} chars) — recomendado: 30–60",
            {"length": len(title)})
    elif len(title) > 60:
        add("warning", "TITLE_TOO_LONG",
            f"Title muito longo ({len(title)} chars) — recomendado: 30–60",
            {"length": len(title)})

    # Meta description
    desc = seo["description"]
    if not desc:
        add("critical", "MISSING_META_DESCRIPTION", "Meta description ausente")
    elif len(desc) < 50:
        add("warning", "META_DESCRIPTION_TOO_SHORT",
            f"Meta description muito curta ({len(desc)} chars) — recomendado: 50–160",
            {"length": len(desc)})
    elif len(desc) > 160:
        add("warning", "META_DESCRIPTION_TOO_LONG",
            f"Meta description muito longa ({len(desc)} chars) — recomendado: 50–160",
            {"length": len(desc)})

    # Canonical
    if not seo["canonical"]:
        add("warning", "MISSING_CANONICAL", "Tag canonical ausente")

    # Robots
    robots = seo["robots"]
    if robots:
        directives = {d.strip().lower() for d in robots.split(",")}
        if directives & {"noindex", "none"}:
            add("critical", "NOINDEX",
                f'Meta robots contém "{robots}" — página não será indexada pelo Google',
                {"value": robots})

    # H1
    h1s = seo["h1s"]
    if not h1s:
        add("critical", "MISSING_H1", "Nenhum H1 encontrado na página")
    elif len(h1s) > 1:
        add("warning", "MULTIPLE_H1",
            f"{len(h1s)} H1s encontrados — recomendado: apenas 1",
            {"count": len(h1s), "headings": h1s})

    # H2
    if not seo["h2s"]:
        add("info", "MISSING_H2",
            "Nenhum H2 encontrado — considere adicionar subtítulos para melhorar estrutura")

    # Links without text
    wt = links["without_text"]
    if wt:
        add("warning", "LINKS_WITHOUT_TEXT",
            f"{len(wt)} link(s) sem texto âncora visível",
            {"count": len(wt), "sample": wt[:5]})

    # Images without alt
    wa = images["without_alt"]
    if wa:
        add("warning", "IMAGES_WITHOUT_ALT",
            f"{len(wa)} imagem(ns) sem atributo alt",
            {"count": len(wa), "sample": wa[:5]})

    return issues


# ── Score ─────────────────────────────────────────────────────────────────────

PENALTY = {"critical": 20, "warning": 8, "info": 2}

def calculate_score(issues: list[dict]) -> int:
    deducted = sum(PENALTY.get(i["severity"], 0) for i in issues)
    return max(0, 100 - deducted)


# ── Main entry ────────────────────────────────────────────────────────────────

def audit_url(raw_url: str) -> dict:
    validate_url(raw_url)

    response = fetch_page(raw_url)

    if response.status_code >= 400:
        raise AuditError(
            "HTTP_ERROR",
            f"A página retornou HTTP {response.status_code}",
            502,
        )

    content_type = response.headers.get("content-type", "")
    if "text/html" not in content_type:
        raise AuditError(
            "NOT_HTML",
            f'Content-Type inesperado: "{content_type}" — esperado text/html',
            422,
        )

    soup = BeautifulSoup(response.text, "lxml")

    final_url = response.url
    seo = extract_seo(soup)
    links = extract_links(soup, raw_url)
    images = extract_images(soup)
    issues = generate_issues(seo, links, images)
    score = calculate_score(issues)

    summary = {
        "critical": sum(1 for i in issues if i["severity"] == "critical"),
        "warning": sum(1 for i in issues if i["severity"] == "warning"),
        "info": sum(1 for i in issues if i["severity"] == "info"),
    }

    result = {
        "url": raw_url,
        "status_code": response.status_code,
        "audited_at": datetime.now(timezone.utc).isoformat(),
        "score": score,
        "summary": summary,
        "seo": {
            "title": {"value": seo["title"], "length": len(seo["title"]) if seo["title"] else 0},
            "meta_description": {"value": seo["description"], "length": len(seo["description"]) if seo["description"] else 0},
            "canonical": seo["canonical"],
            "robots": seo["robots"],
            "open_graph": {"title": seo["og_title"], "description": seo["og_description"]},
            "headings": {"h1": seo["h1s"], "h2": seo["h2s"]},
        },
        "links": {
            "internal": {"count": len(links["internal"]), "items": links["internal"]},
            "external": {"count": len(links["external"]), "items": links["external"]},
            "without_text": {"count": len(links["without_text"]), "items": links["without_text"]},
        },
        "images": {
            "without_alt": {"count": len(images["without_alt"]), "items": images["without_alt"]},
        },
        "issues": issues,
    }

    if final_url != raw_url:
        result["final_url"] = final_url

    return result
