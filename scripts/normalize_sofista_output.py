#!/usr/bin/env python3
"""Unifica la salida HTML de Sofista con la interfaz pública de la portada."""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

try:
    from PIL import Image
except ImportError as error:
    raise SystemExit("Instala Pillow: pip install -r requirements-share.txt") from error


ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://ipesoa.github.io/lineasopticas/"
FRONTEND_VERSION = "20260721-2"
PNG_SIZE = (1200, 1200)


def clean(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def write_preserving_line_endings(path: Path, raw: str, normalized: str) -> bool:
    line_ending = "\r\n" if "\r\n" in raw else "\n"
    serialized = normalized.replace("\n", line_ending)
    if serialized == raw:
        return False
    path.write_bytes(serialized.encode("utf-8"))
    return True


def normalize_frontend() -> int:
    changed = 0

    homepage_path = ROOT / "index.html"
    raw_homepage = homepage_path.read_bytes().decode("utf-8")
    homepage = raw_homepage.replace("\r\n", "\n")
    homepage = re.sub(
        r'\s*<style id="sofista-home-title-fix">.*?</style>\s*',
        "\n",
        homepage,
        flags=re.DOTALL,
    )
    homepage = re.sub(
        r'(\./styles\.css)(?:\?v=[^"\s]+)?',
        rf'\1?v={FRONTEND_VERSION}',
        homepage,
    )
    homepage = re.sub(
        r'(\./app\.js)(?:\?v=[^"\s]+)?',
        rf'\1?v={FRONTEND_VERSION}',
        homepage,
    )
    version_meta = (
        f'<meta name="sofista-frontend-version" content="{FRONTEND_VERSION}">'
    )
    if 'name="sofista-frontend-version"' in homepage:
        homepage = re.sub(
            r'<meta name="sofista-frontend-version" content="[^"]*">',
            version_meta,
            homepage,
        )
    else:
        homepage = homepage.replace("</head>", f"{version_meta}\n</head>", 1)
    changed += write_preserving_line_endings(homepage_path, raw_homepage, homepage)

    styles_path = ROOT / "styles.css"
    raw_styles = styles_path.read_bytes().decode("utf-8")
    styles = raw_styles.replace("\r\n", "\n")
    styles = re.sub(
        r'\n*/\* SOFISTA_POPUP_V\d+ \*/.*\Z',
        "\n",
        styles,
        flags=re.DOTALL,
    )
    changed += write_preserving_line_endings(styles_path, raw_styles, styles)

    return changed


def load_articles() -> list[dict]:
    raw = json.loads((ROOT / "data" / "news.json").read_text(encoding="utf-8"))
    return raw if isinstance(raw, list) else raw.get("articles", [])


def share_markup(article: dict) -> str:
    slug = clean(article.get("slug") or article.get("id"))
    title = clean(article.get("title"))
    description = clean(article.get("summary") or article.get("content"))[:180]
    article_url = f"{BASE_URL}noticias/{slug}/"
    image_url = f"{BASE_URL}media/noticias/{slug}.png"

    return f"""      <section class="share-panel" aria-label="Compartir noticia"
        data-share-panel data-share-title="{html.escape(title, quote=True)}"
        data-share-text="{html.escape(description, quote=True)}"
        data-share-url="{html.escape(article_url, quote=True)}">
        <div class="share-actions">
          <button class="share-action" type="button" data-share>compartir</button>
          <button class="share-image-button" type="button" data-share
            aria-label="Compartir {html.escape(title, quote=True)}">
            <img class="share-image" src="{html.escape(image_url, quote=True)}"
              width="1200" height="1200" loading="lazy" decoding="async"
              alt="Composición tipográfica del titular {html.escape(title, quote=True)}">
          </button>
          <button class="share-action" type="button" data-copy>copiar link</button>
        </div>
      </section>"""


def normalize_png(article: dict) -> bool:
    slug = clean(article.get("slug") or article.get("id"))
    image_path = ROOT / "media" / "noticias" / f"{slug}.png"
    if not image_path.exists():
        raise FileNotFoundError(f"Falta el PNG de la noticia: {image_path.relative_to(ROOT)}")

    with Image.open(image_path) as source:
        if source.size == PNG_SIZE and source.mode == "P":
            return False
        image = source.convert("RGB")
        if image.size != PNG_SIZE:
            image = image.resize(PNG_SIZE, Image.Resampling.LANCZOS)
        image = image.quantize(colors=64, method=Image.Quantize.MEDIANCUT)
        image.save(image_path, "PNG", optimize=True)
    return True


def normalize_page(article: dict) -> bool:
    slug = clean(article.get("slug") or article.get("id"))
    page_path = ROOT / "noticias" / slug / "index.html"
    if not page_path.exists():
        raise FileNotFoundError(f"Falta la página de la noticia: {page_path.relative_to(ROOT)}")

    raw_page = page_path.read_bytes().decode("utf-8")
    line_ending = "\r\n" if "\r\n" in raw_page else "\n"
    page = raw_page.replace("\r\n", "\n")
    original = page

    page = re.sub(
        rf'{re.escape(BASE_URL)}styles\.css(?:\?v=[^"\s]+)?',
        f"{BASE_URL}styles.css?v={FRONTEND_VERSION}",
        page,
    )

    share_script_url = f"{BASE_URL}share.js?v={FRONTEND_VERSION}"
    if "share.js" in page:
        page = re.sub(
            rf'{re.escape(BASE_URL)}share\.js(?:\?v=[^"\s]+)?',
            share_script_url,
            page,
        )
    else:
        page, count = re.subn(
            r'(<link rel="stylesheet" href="[^"]*styles\.css[^"]*">)',
            rf'\1\n      <script src="{share_script_url}" defer></script>',
            page,
            count=1,
        )
        if count != 1:
            raise ValueError(f"No se pudo insertar share.js en {page_path.relative_to(ROOT)}")

    old_share = re.compile(
        r'      <div class="lo-share">.*?</div>\s*'
        r'      <figure class="lo-title-image">.*?</figure>',
        re.DOTALL,
    )
    existing_share = re.compile(
        r'      <section class="share-panel".*?</section>',
        re.DOTALL,
    )

    if old_share.search(page):
        page = old_share.sub(share_markup(article), page, count=1)
    elif existing_share.search(page):
        page = existing_share.sub(share_markup(article), page, count=1)
    else:
        raise ValueError(f"No se encontró el bloque de compartir en {page_path.relative_to(ROOT)}")

    serialized = page.replace("\n", line_ending)
    if page != original or serialized != raw_page:
        page_path.write_bytes(serialized.encode("utf-8"))
        return True
    return False


def main() -> None:
    articles = load_articles()
    normalize_frontend()
    resized = sum(normalize_png(article) for article in articles)
    changed = sum(normalize_page(article) for article in articles)
    print(f"PNG normalizados: {resized}; páginas normalizadas: {changed}")


if __name__ == "__main__":
    main()
