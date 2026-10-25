#!/usr/bin/env python3
"""Auditoría automatizada de una URL (SEO técnico + accesibilidad base).

Stdlib puro (sin dependencias externas). Salida: JSON con checks automatizables
del registry configs/checks.json (campo script_key).

Uso:
    python3 audit_page.py https://ejemplo.com [--json salida.json]
    python3 audit_page.py --file pagina.html [--json salida.json]  # offline/tests

Códigos de salida: 0 = OK, 2 = error de obtención/parseo (ver campo "error").
"""

import argparse
import json
import logging
import re
import ssl
import sys
import time
import urllib.error
import urllib.request
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

logger = logging.getLogger("auditoria360.audit_page")

UA = "auditoria-360-web/2.0 (+compatible; audit bot)"
TIMEOUT = 20

# Errores de red acotados: DNS, conexión, TLS, timeout, URL malformada.
# (HTTPError hereda de URLError: se captura antes, por separado, para informar el código.)
NETWORK_ERRORS = (urllib.error.URLError, TimeoutError, OSError, ssl.SSLError, ValueError)


class PageParser(HTMLParser):
    """Extrae señales SEO/A11y del HTML en una sola pasada."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ""
        self._in_title = False
        self.meta = {}  # name/property -> content (lista)
        self.html_attrs = {}
        self.canonical = []
        self.hreflang = []
        self.headings = []  # (nivel, texto)
        self._heading_level = None
        self._heading_text = []
        self.imgs = []  # dict(src, alt, has_alt, w, h, loading)
        self.links = []  # dict(href, text)
        self._link_href = None
        self._link_text = []
        self.ldjson_raw = []  # contenido crudo de <script type=application/ld+json>
        self._in_ldjson = False
        self._ldjson_buf = []
        self.inputs = []  # dict(id, type, aria_label, aria_labelledby)
        self.labels_for = []
        self.has_viewport = None
        self.charset = None
        self.resources = []  # src/href de recursos (para mixed content)
        self.text_chunks = []

    # -- helpers ------------------------------------------------------
    def _attrs(self, attrs):
        return {k.lower(): (v or "") for k, v in attrs}

    def handle_starttag(self, tag, attrs):
        a = self._attrs(attrs)
        if tag == "html":
            self.html_attrs = a
        elif tag == "title":
            self._in_title = True
        elif tag == "meta":
            key = a.get("name") or a.get("property") or a.get("http-equiv") or ""
            if key:
                self.meta.setdefault(key.lower(), []).append(a.get("content", ""))
            if key.lower() == "viewport":
                self.has_viewport = a.get("content", "")
            if "charset" in a:
                self.charset = a["charset"]
        elif tag == "link":
            rel = a.get("rel", "").lower()
            if rel == "canonical":
                self.canonical.append(a.get("href", ""))
            if "alternate" in rel and a.get("hreflang"):
                self.hreflang.append({"hreflang": a["hreflang"], "href": a.get("href", "")})
            if a.get("href") and rel in ("stylesheet", "icon", "preload", "manifest"):
                self.resources.append(a["href"])
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._heading_level = int(tag[1])
            self._heading_text = []
        elif tag == "img":
            self.imgs.append(
                {
                    "src": a.get("src", "")[:200],
                    "alt": a.get("alt"),
                    "w": a.get("width"),
                    "h": a.get("height"),
                    "loading": a.get("loading"),
                }
            )
            if a.get("src"):
                self.resources.append(a["src"])
        elif tag == "a":
            self._link_href = a.get("href", "")
            self._link_text = []
        elif tag == "script":
            if a.get("src"):
                self.resources.append(a["src"])
            if a.get("type", "").strip().lower() == "application/ld+json":
                self._in_ldjson = True
                self._ldjson_buf = []
        elif tag in ("input", "select", "textarea"):
            if a.get("type", "text").lower() in ("hidden", "submit", "button"):
                return
            self.inputs.append(
                {
                    "id": a.get("id"),
                    "type": a.get("type", "text"),
                    "aria_label": a.get("aria-label"),
                    "aria_labelledby": a.get("aria-labelledby"),
                }
            )
        elif tag == "label" and a.get("for"):
            self.labels_for.append(a["for"])

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6") and self._heading_level:
            self.headings.append((self._heading_level, " ".join(self._heading_text).strip()))
            self._heading_level = None
        elif tag == "a" and self._link_href is not None:
            self.links.append({"href": self._link_href, "text": " ".join(self._link_text).strip()[:120]})
            self._link_href = None
        elif tag == "script" and self._in_ldjson:
            self.ldjson_raw.append("".join(self._ldjson_buf))
            self._in_ldjson = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        if self._heading_level:
            self._heading_text.append(data)
        if self._link_href is not None:
            self._link_text.append(data)
        if self._in_ldjson:
            self._ldjson_buf.append(data)
        if data.strip():
            self.text_chunks.append(data.strip())


# ----------------------------------------------------------------------
# Checks individuales: devuelven dict(script_key, status, evidencia, detalle)
# status: PASS | FAIL | WARN | NA
# ----------------------------------------------------------------------


def _res(key, status, evidencia, detalle=""):
    return {"script_key": key, "status": status, "evidencia": evidencia, "detalle": detalle}


def check_https(url, final_url, headers, local):
    if local:
        return _res("https_security", "NA", "Análisis offline de fichero local")
    https = urlparse(final_url).scheme == "https"
    hsts = "strict-transport-security" in headers
    if not https:
        return _res("https_security", "FAIL", f"URL final: {final_url}", "Sin HTTPS")
    st = "PASS" if hsts else "WARN"
    return _res(
        "https_security",
        st,
        f"HTTPS OK; HSTS={'sí' if hsts else 'no'}",
        "" if hsts else "Falta cabecera Strict-Transport-Security",
    )


def check_security_headers(headers, local):
    if local:
        return _res("security_headers", "NA", "Sin cabeceras en modo offline")
    wanted = [
        "strict-transport-security",
        "content-security-policy",
        "x-content-type-options",
        "referrer-policy",
        "permissions-policy",
        "x-frame-options",
    ]
    present = [h for h in wanted if h in headers]
    st = "PASS" if len(present) >= 4 else ("WARN" if len(present) >= 2 else "FAIL")
    return _res("security_headers", st, f"{len(present)}/6: {', '.join(present)}", "Mínimo 4 cabeceras de seguridad")


def check_title(p):
    t = p.title.strip()
    if not t:
        return _res("title", "FAIL", "Sin <title>", "Añadir title único 50-60 caracteres")
    n = len(t)
    st = "PASS" if 30 <= n <= 65 else "WARN"
    return _res("title", st, f"'{t[:70]}' ({n} caracteres)", "Rango óptimo 50-60")


def check_meta_description(p):
    d = (p.meta.get("description") or [""])[0].strip()
    if not d:
        return _res("meta_description", "FAIL", "Sin meta description", "Añadir 150-160 caracteres orientados a CTR")
    n = len(d)
    st = "PASS" if 70 <= n <= 170 else "WARN"
    return _res("meta_description", st, f"{n} caracteres", "Rango óptimo 150-160")


def check_canonical(p, final_url, local):
    if not p.canonical:
        return _res("canonical", "WARN", "Sin canonical", "Añadir canonical autorreferenciado")
    if len(p.canonical) > 1:
        return _res("canonical", "FAIL", f"{len(p.canonical)} canonicals", "Debe existir un único canonical")
    href = p.canonical[0]
    if local:
        return _res("canonical", "PASS", f"canonical={href}")
    same = href.rstrip("/") == final_url.rstrip("/")
    st = "PASS" if same else "WARN"
    return _res(
        "canonical", st, f"canonical={href}", "" if same else f"Canonical no autorreferenciado (final={final_url})"
    )


def check_robots_meta(p):
    vals = ",".join(p.meta.get("robots", [])).lower()
    if "noindex" in vals:
        return _res("robots_meta", "WARN", f"robots='{vals}'", "Página noindex: confirmar que es intencionado")
    return _res("robots_meta", "PASS", f"robots='{vals or 'no explícito (index,follow)'}'")


def check_hreflang(p):
    if not p.hreflang:
        return _res("hreflang", "NA", "Sin hreflang (sitio monolingüe o pendiente)")
    codes = [h["hreflang"].lower() for h in p.hreflang]
    valid = all(re.fullmatch(r"[a-z]{2,3}(-[a-z0-9]{2,8})*|x-default", c) for c in codes)
    st = "PASS" if valid and "x-default" in codes else ("WARN" if valid else "FAIL")
    return _res(
        "hreflang",
        st,
        f"hreflang: {', '.join(codes)}",
        "" if st == "PASS" else "Falta x-default o códigos ISO inválidos",
    )


def check_headings(p):
    h1 = [t for lv, t in p.headings if lv == 1]
    issues = []
    if len(h1) != 1:
        issues.append(f"H1 encontrados: {len(h1)} (esperado 1)")
    prev = 0
    for lv, _ in p.headings:
        if prev and lv > prev + 1:
            issues.append(f"Salto de jerarquía H{prev} -> H{lv}")
        prev = lv
    if issues:
        return _res("headings", "FAIL", "; ".join(issues), "Corregir jerarquía de encabezados")
    return _res("headings", "PASS", f"1 H1 ('{h1[0][:60]}'), {len(p.headings)} encabezados sin saltos")


def check_img_alt(p):
    if not p.imgs:
        return _res("img_alt_coverage", "NA", "Sin imágenes en la página")
    total = len(p.imgs)
    ok = sum(1 for i in p.imgs if i["alt"] is not None and (i["alt"].strip() or i["alt"] == ""))
    with_alt = sum(1 for i in p.imgs if i["alt"] is not None)
    cov = with_alt / total
    st = "PASS" if cov >= 0.98 else ("WARN" if cov >= 0.9 else "FAIL")
    missing = [i["src"] for i in p.imgs if i["alt"] is None][:5]
    return _res(
        "img_alt_coverage",
        st,
        f"{with_alt}/{total} imágenes con atributo alt ({cov:.0%})",
        "" if st == "PASS" else f"Sin alt: {missing}",
    )


def check_img_dimensions(p):
    if not p.imgs:
        return _res("img_dimensions", "NA", "Sin imágenes")
    total = len(p.imgs)
    withdim = sum(1 for i in p.imgs if i["w"] and i["h"])
    cov = withdim / total
    st = "PASS" if cov >= 0.95 else "WARN"
    return _res(
        "img_dimensions", st, f"{withdim}/{total} con width/height ({cov:.0%})", "Reservar espacio para evitar CLS"
    )


def check_html_lang(p):
    lang = p.html_attrs.get("lang", "").strip().lower()
    if not lang:
        return _res("html_lang", "FAIL", "<html> sin atributo lang", "Añadir lang ISO 639-1 (WCAG 3.1.1)")
    valid = bool(re.fullmatch(r"[a-z]{2,3}(-[a-z0-9]{2,8})*", lang))
    return _res(
        "html_lang", "PASS" if valid else "FAIL", f"lang='{lang}'", "" if valid else "Código de idioma inválido"
    )


def check_viewport(p):
    v = p.has_viewport
    if not v:
        return _res("viewport", "FAIL", "Sin meta viewport", "Añadir width=device-width, initial-scale=1")
    ok = "width=device-width" in v.lower()
    return _res("viewport", "PASS" if ok else "WARN", f"viewport='{v}'")


def check_skip_link(p):
    for l in p.links:
        href = l["href"].strip()
        if href.startswith("#") and re.search(r"(salt|skip|contenido|content|main)", l["text"], re.I):
            return _res("skip_link", "PASS", f"Skip link -> {href} ('{l['text'][:50]}')")
    return _res(
        "skip_link",
        "FAIL",
        "No se detectó enlace 'saltar al contenido'",
        "Añadir <a href='#main'> visible al foco (WCAG 2.4.1)",
    )


def check_form_labels(p):
    if not p.inputs:
        return _res("form_labels", "NA", "Sin campos de formulario")
    labeled = 0
    for i in p.inputs:
        if (i["id"] and i["id"] in p.labels_for) or i["aria_label"] or i["aria_labelledby"]:
            labeled += 1
    total = len(p.inputs)
    cov = labeled / total
    st = "PASS" if cov == 1.0 else ("WARN" if cov >= 0.8 else "FAIL")
    return _res(
        "form_labels",
        st,
        f"{labeled}/{total} campos con nombre accesible",
        "" if st == "PASS" else "Asociar <label for> o aria-label (WCAG 1.3.1/3.3.2)",
    )


def check_jsonld(p):
    if not p.ldjson_raw:
        return _res(
            "jsonld",
            "WARN",
            "Sin datos estructurados JSON-LD",
            "Añadir Organization + BreadcrumbList + tipo por plantilla",
        )
    types, errors = [], 0
    for raw in p.ldjson_raw:
        try:
            data = json.loads(raw)
            items = data if isinstance(data, list) else [data]
            for it in items:
                t = it.get("@type") if isinstance(it, dict) else None
                if t:
                    types.append(t if isinstance(t, str) else ",".join(t))
        except json.JSONDecodeError:
            errors += 1
    if errors:
        return _res("jsonld", "FAIL", f"{errors} bloque(s) JSON-LD inválidos", "Corregir sintaxis JSON")
    return _res("jsonld", "PASS", f"Tipos: {', '.join(sorted(set(types))) or 'sin @type'}")


def check_mixed_content(p, final_url, local):
    if local or urlparse(final_url).scheme != "https":
        return _res("mixed_content", "NA", "No aplica (offline o sin HTTPS)")
    mixed = [r for r in p.resources if r.startswith("http://")]
    st = "PASS" if not mixed else "FAIL"
    return _res(
        "mixed_content",
        st,
        f"{len(mixed)} recursos http:// en página HTTPS",
        "" if not mixed else f"Ejemplos: {mixed[:3]}",
    )


def check_content_parity(p):
    words = len(" ".join(p.text_chunks).split())
    st = "PASS" if words >= 50 else "WARN"
    return _res(
        "content_parity",
        st,
        f"~{words} palabras de texto en HTML inicial",
        "" if st == "PASS" else "Posible dependencia de renderizado JS: verificar DOM renderizado",
    )


def check_charset(p):
    c = (p.charset or "").lower()
    if "utf-8" in c:
        return _res("charset", "PASS", f"charset={c}")
    return _res("charset", "WARN", f"charset='{c or 'no declarado'}'", "Declarar UTF-8")


# ----------------------------------------------------------------------
# Fetch de robots.txt y sitemap.xml
# ----------------------------------------------------------------------


def fetch(url, timeout=TIMEOUT):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    t0 = time.monotonic()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = r.read()
        elapsed = (time.monotonic() - t0) * 1000
        headers = {k.lower(): v for k, v in r.headers.items()}
        return r.geturl(), r.status, headers, body, elapsed


def check_robots_txt(base, local):
    if local:
        return _res("robots_txt", "NA", "Modo offline")
    try:
        url, status, _, body, _ = fetch(urljoin(base, "/robots.txt"))
        if status != 200:
            return _res("robots_txt", "WARN", f"robots.txt HTTP {status}")
        text = body.decode("utf-8", "replace")
        has_sitemap = bool(re.search(r"(?im)^\s*sitemap:\s*\S+", text))
        blocks_all = bool(re.search(r"(?im)^\s*disallow:\s*/\s*$", text))
        if blocks_all:
            return _res("robots_txt", "FAIL", "Disallow: / global detectado", "Bloquea el rastreo completo del sitio")
        st = "PASS" if has_sitemap else "WARN"
        return _res("robots_txt", st, f"robots.txt 200 OK; Sitemap declarado={'sí' if has_sitemap else 'no'}")
    except urllib.error.HTTPError as e:
        logger.debug("robots_txt %s devolvió HTTP %s", base, e.code)
        return _res("robots_txt", "WARN", f"robots.txt HTTP {e.code}")
    except NETWORK_ERRORS as e:
        logger.debug("robots_txt no accesible (%s): %s: %s", base, type(e).__name__, e)
        return _res("robots_txt", "WARN", f"No accesible: {type(e).__name__}: {e}")


def check_sitemap(base, robots_text_url, local):
    if local:
        return _res("sitemap", "NA", "Modo offline")
    candidates = [robots_text_url] if robots_text_url else []
    candidates.append(urljoin(base, "/sitemap.xml"))
    for cand in candidates:
        try:
            url, status, headers, body, _ = fetch(cand)
            if status == 200 and (b"<urlset" in body or b"<sitemapindex" in body):
                n = body.count(b"<url>") or body.count(b"<sitemap>")
                return _res("sitemap", "PASS", f"{url} 200 OK, {n} entradas")
        except NETWORK_ERRORS as e:
            logger.debug("sitemap candidato %s falló: %s: %s", cand, type(e).__name__, e)
            continue
    return _res(
        "sitemap", "WARN", "No se encontró sitemap.xml válido", "Generar sitemap y declararlo en robots.txt y GSC"
    )


def check_og_tags(p):
    og = {k: v for k, v in p.meta.items() if k.startswith("og:")}
    tw = {k: v for k, v in p.meta.items() if k.startswith("twitter:")}
    required = ["og:title", "og:description", "og:image"]
    missing = [k for k in required if not og.get(k)]
    if not og and not tw:
        return _res(
            "og_tags",
            "WARN",
            "Sin Open Graph ni Twitter Cards",
            "Añadir og:title, og:description, og:image (>=1200x630)",
        )
    if missing:
        return _res("og_tags", "WARN", f"Faltan: {', '.join(missing)}", "Completar etiquetas Open Graph obligatorias")
    return _res("og_tags", "PASS", f"OG completo ({len(og)} tags); Twitter: {len(tw)} tags")


def check_cookie_banner(p):
    text = " ".join(p.text_chunks).lower()
    htmlish = text + " ".join(l["text"].lower() for l in p.links)
    hits = [k for k in ("cookie", "consent", "consentimiento", "privacidad") if k in htmlish]
    if hits:
        return _res(
            "cookie_banner",
            "PASS",
            f"Señales detectadas: {', '.join(hits)}",
            "Verificar manualmente bloqueo previo y granularidad (RGPD/ePrivacy)",
        )
    return _res(
        "cookie_banner",
        "WARN",
        "No se detectaron señales de CMP/cookies",
        "Si hay analítica o pauta, se requiere CMP con Consent Mode v2",
    )


# ----------------------------------------------------------------------
# Orquestador
# ----------------------------------------------------------------------


def audit(url=None, file=None):
    results = {"target": url or file, "modo": "offline" if file else "online", "checks": [], "error": None}
    try:
        if file:
            try:
                with open(file, "rb") as fh:
                    body = fh.read()
            except OSError as e:
                logger.error("no se pudo leer el fichero %s: %s: %s", file, type(e).__name__, e)
                results["error"] = f"Lectura de fichero {file}: {type(e).__name__}: {e}"
                return results
            final_url, status, headers, ttfb = url or "file://" + file, 200, {}, 0.0
        else:
            try:
                final_url, status, headers, body, ttfb = fetch(url)
            except urllib.error.HTTPError as e:
                logger.error("HTTP %s al obtener %s", e.code, url)
                results["error"] = f"HTTP {e.code} en {url}"
                return results
            except NETWORK_ERRORS as e:
                logger.error("fallo de red al obtener %s: %s: %s", url, type(e).__name__, e)
                results["error"] = f"{type(e).__name__}: {e}"
                return results
            results["http"] = {"status": status, "final_url": final_url, "ttfb_ms": round(ttfb)}
    except (TypeError, ValueError) as e:
        logger.error("URL objetivo inválida %r: %s: %s", url, type(e).__name__, e)
        results["error"] = f"{type(e).__name__}: {e}"
        return results

    p = PageParser()
    try:
        p.feed(body.decode("utf-8", "replace"))
    except Exception as e:  # HTMLParser ante HTML mal formado: degradar, no abortar
        logger.warning("parseo HTML parcial de %s: %s: %s", results["target"], type(e).__name__, e)
        results["checks"].append(_res("parse", "WARN", f"Parseo parcial: {type(e).__name__}"))

    local = bool(file)
    base = final_url
    c = results["checks"]
    c.append(check_https(url, final_url, headers, local))
    c.append(check_security_headers(headers, local))
    c.append(check_title(p))
    c.append(check_meta_description(p))
    c.append(check_canonical(p, final_url, local))
    c.append(check_robots_meta(p))
    c.append(check_hreflang(p))
    c.append(check_headings(p))
    c.append(check_img_alt(p))
    c.append(check_img_dimensions(p))
    c.append(check_html_lang(p))
    c.append(check_viewport(p))
    c.append(check_skip_link(p))
    c.append(check_form_labels(p))
    c.append(check_jsonld(p))
    c.append(check_mixed_content(p, final_url, local))
    c.append(check_content_parity(p))
    c.append(check_charset(p))
    c.append(check_og_tags(p))
    c.append(check_robots_txt(base, local))
    sitemap_hint = urljoin(base, "/sitemap-index.xml")
    c.append(check_sitemap(base, sitemap_hint, local))
    c.append(check_cookie_banner(p))
    return results


def main(argv=None) -> int:
    logging.basicConfig(stream=sys.stderr, level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    ap = argparse.ArgumentParser(description="Auditoría 360° - chequeo automatizado de página")
    ap.add_argument("url", nargs="?", help="URL a auditar (https://...)")
    ap.add_argument("--file", help="Fichero HTML local (modo offline/tests)")
    ap.add_argument("--json", help="Guardar resultado en JSON")
    args = ap.parse_args(argv)
    if not args.url and not args.file:
        ap.error("Indica una URL o --file")

    results = audit(url=args.url, file=args.file)
    out = json.dumps(results, ensure_ascii=False, indent=2)
    if args.json:
        try:
            with open(args.json, "w", encoding="utf-8") as fh:
                fh.write(out)
        except OSError as e:
            logger.error("no se pudo escribir %s: %s: %s", args.json, type(e).__name__, e)
            print(out)
            return 2
    try:
        print(out)
    except BrokenPipeError:
        return 0
    return 2 if results["error"] else 0


if __name__ == "__main__":
    sys.exit(main())
