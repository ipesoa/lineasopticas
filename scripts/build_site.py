#!/usr/bin/env python3
"""Compila Líneas Ópticas desde data/news.json a un sitio estático indexable."""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import sys
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote, urlparse

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "_site"
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PUBLIC_FILES = (
    "styles.css",
    "config.js",
    "app.js",
    "share.js",
    ".nojekyll",
)


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"Falta el archivo: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"JSON inválido en {path}: {exc}") from exc


def parse_datetime(value: str, field: str, slug: str) -> datetime:
    try:
        normalized = value.replace("Z", "+00:00")
        result = datetime.fromisoformat(normalized)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{slug}: {field} no es una fecha ISO 8601 válida") from exc
    if result.tzinfo is None:
        raise ValueError(f"{slug}: {field} debe incluir zona horaria")
    return result


def plain_excerpt(value: str, maximum: int = 160) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(text) <= maximum:
        return text
    shortened = text[: maximum + 1].rsplit(" ", 1)[0].rstrip(" ,;:.-")
    return f"{shortened}…"


def normalize_source(source: object, slug: str) -> dict[str, str] | None:
    if isinstance(source, str):
        url = source.strip()
        name = urlparse(url).netloc or "Fuente"
    elif isinstance(source, dict):
        url = str(source.get("url", "")).strip()
        name = str(source.get("name") or source.get("title") or urlparse(url).netloc or "Fuente").strip()
    else:
        raise ValueError(f"{slug}: cada fuente debe ser una URL o un objeto con name y url")

    if not url:
        return None
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"{slug}: URL de fuente inválida: {url}")
    return {"name": name, "url": url}


def normalize_articles(raw: dict, config: dict) -> list[dict]:
    source = raw if isinstance(raw, list) else raw.get("articles", raw.get("news", []))
    if not isinstance(source, list):
        raise SystemExit("data/news.json debe contener un array o una clave articles")

    articles: list[dict] = []
    ids: set[str] = set()
    slugs: set[str] = set()
    errors: list[str] = []

    for index, item in enumerate(source, start=1):
        if not isinstance(item, dict):
            errors.append(f"Noticia {index}: debe ser un objeto JSON")
            continue
        if str(item.get("status", "published")).lower() in {"draft", "deleted", "trash"}:
            continue

        article_id = str(item.get("id") or item.get("slug") or "").strip()
        slug = str(item.get("slug") or item.get("id") or "").strip()
        title = str(item.get("title") or item.get("titular") or "").strip()
        content = str(item.get("content") or item.get("body") or item.get("text") or item.get("texto") or "").strip()
        published_at = str(item.get("publishedAt") or item.get("date") or item.get("fecha") or "").strip()

        try:
            if not article_id:
                raise ValueError(f"Noticia {index}: falta id")
            if article_id in ids:
                raise ValueError(f"{article_id}: id duplicado")
            if not slug or not SLUG_RE.fullmatch(slug):
                raise ValueError(f"{article_id}: slug inválido; usa minúsculas, números y guiones")
            if slug in slugs:
                raise ValueError(f"{slug}: slug duplicado")
            if not title:
                raise ValueError(f"{slug}: falta title")
            compact = compact_title(title)
            if len(compact) < 3:
                raise ValueError(f"{slug}: el título necesita al menos 3 letras o números")
            if not content:
                raise ValueError(f"{slug}: falta content")
            published_dt = parse_datetime(published_at, "publishedAt", slug)
            updated_at = str(item.get("updatedAt") or published_at).strip()
            updated_dt = parse_datetime(updated_at, "updatedAt", slug)

            raw_sources = item.get("sources") or item.get("fuentes") or []
            if not isinstance(raw_sources, list):
                raise ValueError(f"{slug}: sources debe ser un array")
            sources = [normalized for src in raw_sources if (normalized := normalize_source(src, slug))]

            tags = [str(tag).strip() for tag in item.get("tags", item.get("etiquetas", [])) if str(tag).strip()]
            hidden_tags = [str(tag).strip() for tag in item.get("hiddenTags", item.get("etiquetasOcultas", [])) if str(tag).strip()]
            summary = str(item.get("summary") or item.get("excerpt") or item.get("resumen") or "").strip()
            summary = summary or plain_excerpt(content, 175)
            meta_description = str(item.get("metaDescription") or "").strip() or plain_excerpt(summary, 160)
            section = str(item.get("section") or item.get("seccion") or (tags[0] if tags else config["defaultSection"])).strip()
            author = str(item.get("author") or item.get("autor") or config["defaultAuthor"]).strip()
            author_type = str(item.get("authorType") or "Organization").strip()
            if author_type not in {"Person", "Organization"}:
                author_type = "Organization"

            articles.append({
                "id": article_id,
                "slug": slug,
                "title": title,
                "seoTitle": str(item.get("seoTitle") or "").strip(),
                "summary": summary,
                "metaDescription": meta_description,
                "content": content,
                "publishedAt": published_at,
                "publishedDt": published_dt,
                "updatedAt": updated_at,
                "updatedDt": updated_dt,
                "featured": bool(item.get("featured", item.get("destacada", False))),
                "section": section,
                "sectionSlug": slugify(section),
                "author": author,
                "authorType": author_type,
                "tags": tags,
                "hiddenTags": hidden_tags,
                "sources": sources,
                "language": str(item.get("language") or config["language"]).strip(),
            })
            ids.add(article_id)
            slugs.add(slug)
        except ValueError as exc:
            errors.append(str(exc))

    if errors:
        raise SystemExit("Errores en data/news.json:\n- " + "\n- ".join(errors))

    return sorted(articles, key=lambda article: article["publishedDt"], reverse=True)


def slugify(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    ascii_text = "".join(char for char in decomposed if not unicodedata.combining(char))
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")
    return slug or "actualidad"


def compact_title(title: str) -> str:
    normalized = unicodedata.normalize("NFC", title).lower()
    return "".join(character for character in normalized if character.isalnum())


def split_three(value: str) -> list[str]:
    quotient, remainder = divmod(len(value), 3)
    lengths = [quotient + (1 if index < remainder else 0) for index in range(3)]
    result: list[str] = []
    cursor = 0
    for length in lengths:
        result.append(value[cursor : cursor + length])
        cursor += length
    return result


def build_svg(title: str) -> str:
    lines = split_three(compact_title(title))
    escaped = [html.escape(line, quote=False) for line in lines]
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="1200" viewBox="0 0 1200 1200">'
        '<rect width="1200" height="1200" fill="#f7f7f5"/>'
        '<g fill="#2d2d2b" font-family="Arial,Helvetica,sans-serif" font-size="300" font-weight="700" font-style="italic">'
        f'<text x="120" y="370" textLength="960" lengthAdjust="spacingAndGlyphs">{escaped[0]}</text>'
        f'<text x="120" y="650" textLength="960" lengthAdjust="spacingAndGlyphs">{escaped[1]}</text>'
        f'<text x="120" y="930" textLength="960" lengthAdjust="spacingAndGlyphs">{escaped[2]}</text>'
        '</g></svg>'
    )


def h(value: object) -> str:
    return html.escape(str(value), quote=True)


def article_url(config: dict, slug: str) -> str:
    return f'{config["siteUrl"]}/noticias/{quote(slug)}/'


def image_url(config: dict, slug: str) -> str:
    return f'{config["siteUrl"]}/media/noticias/{quote(slug)}.svg'


def formatted_date(value: datetime) -> str:
    months = (
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
    )
    return f"{value.day} de {months[value.month - 1]} de {value.year} · {value:%H:%M}"


def paragraphs(value: str) -> str:
    chunks = [chunk.strip() for chunk in re.split(r"\n{2,}", value) if chunk.strip()]
    return "\n".join(f"<p>{h(chunk).replace(chr(10), '<br>')}</p>" for chunk in chunks)


def title_tag(article: dict, publication: str) -> str:
    base = article["seoTitle"] or article["title"]
    return base if publication.casefold() in base.casefold() else f"{base} | {publication}"


def static_card(article: dict, prefix: str = "./") -> str:
    preview = plain_excerpt(article["content"], 520)
    return f'''<a class="article-card" href="{prefix}noticias/{h(article['slug'])}/" data-article-id="{h(article['id'])}">
  <h2 class="card-title"><span class="card-title-text">{h(article['title'])}</span></h2>
  <p class="card-summary">{h(preview)}</p>
  <div class="card-footer">
    <time class="card-date" datetime="{h(article['publishedAt'])}">{h(formatted_date(article['publishedDt']))}</time>
    <span class="read-more">seguir leyendo...</span>
  </div>
</a>'''


def sources_html(article: dict) -> str:
    if not article["sources"]:
        return ""
    items = "\n".join(
        f'<li><a href="{h(source["url"])}" target="_blank" rel="noopener noreferrer">{h(source["name"])}</a></li>'
        for source in article["sources"]
    )
    return f'''<section class="article-sources" aria-labelledby="sourcesTitle">
<h2 id="sourcesTitle">Fuentes</h2>
<ul>{items}</ul>
</section>'''


def share_panel(article: dict, image_relative: str) -> str:
    return f'''<section class="share-panel" aria-label="Compartir noticia" data-share-panel
  data-share-title="{h(article['title'])}"
  data-share-text="{h(plain_excerpt(article['summary'], 180))}"
  data-share-url="{h(article_url(CONFIG, article['slug']))}">
  <div class="share-actions">
    <button class="share-action" type="button" data-share>compartir</button>
    <button class="share-image-button" type="button" data-share aria-label="Compartir {h(article['title'])}">
      <img class="share-image" src="{h(image_relative)}" width="1200" height="1200" alt="Composición tipográfica del titular {h(article['title'])}">
    </button>
    <button class="share-action" type="button" data-copy>copiar link</button>
  </div>
</section>'''


def article_json_ld(article: dict, config: dict) -> str:
    payload = {
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "mainEntityOfPage": {"@type": "WebPage", "@id": article_url(config, article["slug"])},
        "headline": article["title"],
        "description": article["metaDescription"],
        "image": [image_url(config, article["slug"])],
        "datePublished": article["publishedAt"],
        "dateModified": article["updatedAt"],
        "author": {"@type": article["authorType"], "name": article["author"]},
        "publisher": {"@type": "Organization", "name": config["publicationName"], "url": f'{config["siteUrl"]}/'},
        "articleSection": article["section"],
        "keywords": article["tags"] + article["hiddenTags"],
        "citation": [source["url"] for source in article["sources"]],
        "wordCount": len(re.findall(r"\b\w+\b", article["content"], flags=re.UNICODE)),
        "inLanguage": article["language"],
        "isAccessibleForFree": True,
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def article_page(article: dict, config: dict) -> str:
    canonical = article_url(config, article["slug"])
    image = image_url(config, article["slug"])
    tags = "\n".join(f'<meta property="article:tag" content="{h(tag)}">' for tag in article["tags"])
    verification = (
        f'<meta name="google-site-verification" content="{h(config["googleSiteVerification"])}">'
        if config.get("googleSiteVerification") else ""
    )
    return f'''<!doctype html>
<html lang="{h(article['language'])}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
  <meta name="theme-color" content="#f7f7f5">
  <title>{h(title_tag(article, config['publicationName']))}</title>
  <meta name="description" content="{h(article['metaDescription'])}">
  <meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1">
  {verification}
  <link rel="canonical" href="{h(canonical)}">
  <link rel="home" href="{h(config['siteUrl'])}/">
  <link rel="index" href="{h(config['siteUrl'])}/archivo/">
  <link rel="alternate" type="application/rss+xml" title="{h(config['publicationName'])}" href="{h(config['siteUrl'])}/feed.xml">
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="{h(config['publicationName'])}">
  <meta property="og:locale" content="{h(config['locale'])}">
  <meta property="og:url" content="{h(canonical)}">
  <meta property="og:title" content="{h(article['title'])}">
  <meta property="og:description" content="{h(article['metaDescription'])}">
  <meta property="og:image" content="{h(image)}">
  <meta property="og:image:type" content="image/svg+xml">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="1200">
  <meta property="og:image:alt" content="Composición tipográfica de {h(article['title'])}">
  <meta property="article:published_time" content="{h(article['publishedAt'])}">
  <meta property="article:modified_time" content="{h(article['updatedAt'])}">
  <meta property="article:section" content="{h(article['section'])}">
  {tags}
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{h(article['title'])}">
  <meta name="twitter:description" content="{h(article['metaDescription'])}">
  <meta name="twitter:image" content="{h(image)}">
  <script type="application/ld+json">{article_json_ld(article, config)}</script>
  <link rel="stylesheet" href="../../styles.css">
</head>
<body class="article-page-body">
  <header class="site-header article-site-header">
    <a class="brand" href="../../" aria-label="Inicio">{h(config['publicationName'])}</a>
  </header>
  <main class="article-page">
    <article class="article-page-content">
      <h1 class="article-modal-title">{h(article['title'])}</h1>
      <p class="article-byline">
        <time datetime="{h(article['publishedAt'])}">{h(formatted_date(article['publishedDt']))}</time>
        <span aria-hidden="true"> · </span>{h(article['author'])}
        <span aria-hidden="true"> · </span><a href="../../secciones/{h(article['sectionSlug'])}/">{h(article['section'])}</a>
      </p>
      <div class="article-body">{paragraphs(article['content'])}</div>
      {sources_html(article)}
      {share_panel(article, f'../../media/noticias/{article["slug"]}.svg')}
    </article>
  </main>
  <script src="../../share.js" defer></script>
</body>
</html>'''


def listing_page(title: str, description: str, articles: list[dict], config: dict, canonical: str, prefix: str) -> str:
    cards = "\n".join(static_card(article, prefix=prefix) for article in articles)
    return f'''<!doctype html>
<html lang="{h(config['language'])}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
  <meta name="theme-color" content="#f7f7f5">
  <title>{h(title)} | {h(config['publicationName'])}</title>
  <meta name="description" content="{h(description)}">
  <meta name="robots" content="index,follow,max-image-preview:large">
  <link rel="canonical" href="{h(canonical)}">
  <link rel="alternate" type="application/rss+xml" title="{h(config['publicationName'])}" href="{h(config['siteUrl'])}/feed.xml">
  <link rel="stylesheet" href="{prefix}styles.css">
</head>
<body>
  <header class="site-header">
    <a class="brand" href="{prefix}" aria-label="Inicio">{h(config['publicationName'])}</a>
  </header>
  <main>
    <h1 class="listing-title">{h(title)}</h1>
    <section class="news-grid static-listing" aria-label="{h(title)}">{cards}</section>
  </main>
</body>
</html>'''


def replace_static_news(index_template: str, cards: str) -> str:
    start = "<!-- STATIC_NEWS_START -->"
    end = "<!-- STATIC_NEWS_END -->"
    if start not in index_template or end not in index_template:
        raise SystemExit("index.html no contiene los marcadores STATIC_NEWS_START/END")
    before, remainder = index_template.split(start, 1)
    _, after = remainder.split(end, 1)
    return f"{before}{start}\n{cards}\n    {end}{after}"


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def build_sitemap(articles: list[dict], config: dict) -> str:
    entries: list[str] = []
    newest = articles[0]["updatedDt"] if articles else datetime.now(timezone.utc)
    entries.append(f'<url><loc>{h(config["siteUrl"])}/</loc><lastmod>{newest.isoformat()}</lastmod></url>')
    entries.append(f'<url><loc>{h(config["siteUrl"])}/archivo/</loc><lastmod>{newest.isoformat()}</lastmod></url>')

    sections: dict[str, datetime] = {}
    for article in articles:
        sections[article["sectionSlug"]] = max(sections.get(article["sectionSlug"], article["updatedDt"]), article["updatedDt"])
    for section_slug, modified in sorted(sections.items()):
        entries.append(f'<url><loc>{h(config["siteUrl"])}/secciones/{h(section_slug)}/</loc><lastmod>{modified.isoformat()}</lastmod></url>')

    for article in articles:
        entries.append(
            f'<url><loc>{h(article_url(config, article["slug"]))}</loc>'
            f'<lastmod>{article["updatedDt"].isoformat()}</lastmod>'
            f'<image:image><image:loc>{h(image_url(config, article["slug"]))}</image:loc>'
            f'<image:title>{h(article["title"])}</image:title></image:image></url>'
        )
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + (
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        'xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">'
        + "".join(entries) + "</urlset>"
    )


def build_news_sitemap(articles: list[dict], config: dict) -> str:
    cutoff = datetime.now(timezone.utc) - timedelta(days=2)
    entries = []
    for article in articles:
        if article["publishedDt"].astimezone(timezone.utc) < cutoff:
            continue
        entries.append(
            f'<url><loc>{h(article_url(config, article["slug"]))}</loc><news:news>'
            f'<news:publication><news:name>{h(config["publicationName"])}</news:name>'
            f'<news:language>{h(config["language"])}</news:language></news:publication>'
            f'<news:publication_date>{article["publishedDt"].isoformat()}</news:publication_date>'
            f'<news:title>{h(article["title"])}</news:title>'
            '</news:news></url>'
        )
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + (
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        'xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">'
        + "".join(entries) + "</urlset>"
    )


def build_feed(articles: list[dict], config: dict) -> str:
    latest = articles[0]["updatedDt"] if articles else datetime.now(timezone.utc)
    items = []
    for article in articles[:50]:
        items.append(
            '<item>'
            f'<title>{h(article["title"])}</title>'
            f'<link>{h(article_url(config, article["slug"]))}</link>'
            f'<guid isPermaLink="true">{h(article_url(config, article["slug"]))}</guid>'
            f'<pubDate>{article["publishedDt"].strftime("%a, %d %b %Y %H:%M:%S %z")}</pubDate>'
            f'<description>{h(article["summary"])}</description>'
            f'<content:encoded>{h(paragraphs(article["content"]))}</content:encoded>'
            '</item>'
        )
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + (
        '<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/"><channel>'
        f'<title>{h(config["publicationName"])}</title>'
        f'<link>{h(config["siteUrl"])}/</link>'
        f'<description>{h(config["description"])}</description>'
        f'<language>{h(config["language"])}</language>'
        f'<lastBuildDate>{latest.strftime("%a, %d %b %Y %H:%M:%S %z")}</lastBuildDate>'
        + "".join(items) + '</channel></rss>'
    )


def copy_public_source(output: Path) -> None:
    for name in PUBLIC_FILES:
        source = ROOT / name
        if source.exists():
            shutil.copy2(source, output / name)
    for directory in ("data", "assets", "static", "media"):
        source = ROOT / directory
        if source.exists():
            shutil.copytree(source, output / directory, dirs_exist_ok=True)


def build(output: Path) -> None:
    global CONFIG
    CONFIG = load_json(ROOT / "site.config.json")
    CONFIG["siteUrl"] = CONFIG["siteUrl"].rstrip("/")
    raw_news = load_json(ROOT / "data" / "news.json")
    articles = normalize_articles(raw_news, CONFIG)

    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    copy_public_source(output)

    # media/noticias contiene únicamente SVG generados. Al recompilar se vacía
    # para que una noticia eliminada no deje imágenes huérfanas publicadas.
    shutil.rmtree(output / "media" / "noticias", ignore_errors=True)

    index_template_path = ROOT / "index.template.html"
    if not index_template_path.exists():
        index_template_path = ROOT / "index.html"
    index_template = index_template_path.read_text(encoding="utf-8")
    verification = (
        f'<meta name="google-site-verification" content="{h(CONFIG["googleSiteVerification"])}">'
        if CONFIG.get("googleSiteVerification") else ""
    )
    index_template = index_template.replace("<!-- GOOGLE_SITE_VERIFICATION -->", verification)
    index_template = index_template.replace("https://ipesoa.github.io/lineasopticas", CONFIG["siteUrl"])
    visible_cards = "\n".join(static_card(article) for article in articles[: int(CONFIG.get("itemsPerPage", 40))])
    write_text(output / "index.html", replace_static_news(index_template, visible_cards))

    for article in articles:
        write_text(output / "media" / "noticias" / f'{article["slug"]}.svg', build_svg(article["title"]))
        write_text(output / "noticias" / article["slug"] / "index.html", article_page(article, CONFIG))

    write_text(
        output / "archivo" / "index.html",
        listing_page(
            "Archivo",
            "Archivo completo de noticias de Líneas Ópticas.",
            articles,
            CONFIG,
            f'{CONFIG["siteUrl"]}/archivo/',
            "../",
        ),
    )

    sections: dict[str, list[dict]] = {}
    for article in articles:
        sections.setdefault(article["sectionSlug"], []).append(article)
    for section_slug, section_articles in sections.items():
        section_name = section_articles[0]["section"]
        write_text(
            output / "secciones" / section_slug / "index.html",
            listing_page(
                section_name,
                f"Noticias y textos de {section_name} en {CONFIG['publicationName']}.",
                section_articles,
                CONFIG,
                f'{CONFIG["siteUrl"]}/secciones/{section_slug}/',
                "../../",
            ),
        )

    write_text(output / "sitemap.xml", build_sitemap(articles, CONFIG))
    write_text(output / "news-sitemap.xml", build_news_sitemap(articles, CONFIG))
    write_text(output / "feed.xml", build_feed(articles, CONFIG))
    write_text(
        output / "robots.txt",
        f'User-agent: *\nAllow: /\n\nSitemap: {CONFIG["siteUrl"]}/sitemap.xml\nSitemap: {CONFIG["siteUrl"]}/news-sitemap.xml\n',
    )

    total_svg = sum(path.stat().st_size for path in (output / "media" / "noticias").glob("*.svg"))
    print(f"Sitio compilado: {output}")
    print(f"Noticias publicadas: {len(articles)}")
    print(f"SVG generados: {len(articles)} · {total_svg / 1024:.1f} KiB en total")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    build(args.output.resolve())


CONFIG: dict = {}

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # defensa final para que Actions muestre un error legible
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
