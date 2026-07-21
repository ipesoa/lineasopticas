#!/usr/bin/env python3
"""Validaciones rápidas que Sofista debe superar antes de publicar."""

from __future__ import annotations

import json
import re
import struct
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://ipesoa.github.io/lineasopticas/"
EXPECTED_VIEWPORTS = (360, 390, 430)
errors: list[str] = []


def fail(message: str) -> None:
    errors.append(message)


def clean(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def png_size(path: Path) -> tuple[int, int] | None:
    try:
        data = path.read_bytes()[:24]
    except OSError:
        return None
    if len(data) != 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        return None
    return struct.unpack(">II", data[16:24])


def main() -> None:
    raw = json.loads((ROOT / "data" / "news.json").read_text(encoding="utf-8"))
    articles = raw if isinstance(raw, list) else raw.get("articles", [])
    expected_related = min(3, max(0, len(articles) - 1))

    for article in articles:
        slug = clean(article.get("slug") or article.get("id"))
        title = clean(article.get("title"))
        if not slug or not title:
            fail("Hay una noticia sin slug o titular.")
            continue

        image = ROOT / "media" / "noticias" / f"{slug}.png"
        dimensions = png_size(image)
        if dimensions is None:
            fail(f"Falta un PNG válido: {image.relative_to(ROOT)}")
        elif dimensions != (1200, 1200):
            fail(f"{image.relative_to(ROOT)} mide {dimensions[0]}x{dimensions[1]}; debe medir 1200x1200.")

        page_path = ROOT / "noticias" / slug / "index.html"
        if not page_path.exists():
            fail(f"Falta la página {page_path.relative_to(ROOT)}")
            continue

        page = page_path.read_text(encoding="utf-8")
        image_url = f"{BASE_URL}media/noticias/{slug}.png"
        if image_url not in page:
            fail(f"La página {slug} no referencia su PNG canónico.")
        if "data-share-panel" not in page or page.count("data-share") < 3:
            fail(f"La página {slug} no tiene compartir, miniatura y copiar enlace unificados.")
        if "share.js" not in page:
            fail(f"La página {slug} no carga share.js.")

        related_match = re.search(
            r'<nav class="lo-related"[^>]*>(.*?)</nav>', page, re.DOTALL
        )
        related_count = len(re.findall(r"<a\s", related_match.group(1))) if related_match else 0
        if related_count != expected_related:
            fail(
                f"La página {slug} tiene {related_count} enlaces para seguir leyendo; "
                f"debe tener {expected_related}."
            )

    app = (ROOT / "app.js").read_text(encoding="utf-8")
    if "${encodeURIComponent(article.slug)}.png" not in app:
        fail("app.js no apunta al PNG canónico de cada noticia.")
    if re.search(r"articleImageUrl[\s\S]{0,250}\.svg", app):
        fail("app.js todavía contiene una referencia SVG para la imagen de la noticia.")

    styles = (ROOT / "styles.css").read_text(encoding="utf-8")
    if "SOFISTA_POPUP_V04414" in styles:
        fail("Sigue presente el bloque antiguo de Sofista que rompe el diseño.")
    for required in (
        "@media (max-width: 739px)",
        "aspect-ratio: 1 / 1",
        "overflow-x: clip",
        ".related-news",
    ):
        if required not in styles:
            fail(f"Falta la protección de diseño: {required}")

    for html_path in ROOT.rglob("*.html"):
        page = html_path.read_text(encoding="utf-8")
        for relative in re.findall(
            r'https://ipesoa\.github\.io/lineasopticas/(media/noticias/[^"\s>]+\.png)',
            page,
        ):
            if not (ROOT / relative).exists():
                fail(f"{html_path.relative_to(ROOT)} referencia una imagen inexistente: {relative}")

    if errors:
        print("VALIDACIÓN FALLIDA")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    checked = ", ".join(f"{width}px" for width in EXPECTED_VIEWPORTS)
    print(
        f"Validación correcta: {len(articles)} noticias, PNG y protecciones "
        f"responsive declaradas para {checked}."
    )


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"VALIDACIÓN FALLIDA: {error}", file=sys.stderr)
        raise SystemExit(1) from error
