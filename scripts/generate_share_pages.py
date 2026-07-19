#!/usr/bin/env python3
"""
Regenera noticias/<slug>/ y share/<slug>.svg/.png desde data/news.json.

Ejecutar desde la raíz:
    python scripts/generate_share_pages.py
"""
from pathlib import Path
from itertools import combinations
import html
import json
import re

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError as exc:
    raise SystemExit("Instala Pillow: pip install -r requirements-share.txt") from exc

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://ipesoa.github.io/lineasopticas/"
WIDTH, HEIGHT = 1200, 630
PAPER = "#f7f7f5"
INK = "#111111"

def clean(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()

def balanced_lines(title, max_lines=3):
    words = clean(title).upper().split()
    if len(words) <= 1:
        return words or ["SIN TITULAR"]

    best = None
    for count in range(1, min(max_lines, len(words)) + 1):
        choices = [()] if count == 1 else combinations(range(1, len(words)), count - 1)
        for cuts in choices:
            points = (0,) + tuple(cuts) + (len(words),)
            lines = [" ".join(words[points[i]:points[i + 1]]) for i in range(len(points) - 1)]
            lengths = [len(line) for line in lines]
            average = sum(lengths) / len(lengths)
            variance = sum((length - average) ** 2 for length in lengths)
            score = max(lengths) ** 2 + variance * 2 + abs(count - 2) * 5
            if best is None or score < best[0]:
                best = (score, lines)
    return best[1]

def svg_text(title):
    lines = balanced_lines(title)
    longest = max(len(line) for line in lines)
    size_width = int(1040 / max(1, longest * 0.57))
    size_height = int(470 / max(1, len(lines)))
    size = max(54, min(190, size_width, size_height))
    line_height = int(size * .88)
    total_height = line_height * len(lines)
    first_y = (HEIGHT - total_height) / 2 + size * .72

    nodes = []
    for index, line in enumerate(lines):
        y = first_y + index * line_height
        nodes.append(f'<text x="600" y="{y:.1f}" text-anchor="middle">{html.escape(line)}</text>')

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">\n'
        f'  <rect width="100%" height="100%" fill="{PAPER}"/>\n'
        f'  <g fill="{INK}" font-family="Arial, Helvetica, sans-serif" font-size="{size}px" '
        f'font-weight="900" font-style="italic" letter-spacing="-0.025em">\n'
        f'    {"".join(nodes)}\n'
        f'  </g>\n'
        f'</svg>\n'
    )

def font_path():
    candidates = [
        "/usr/share/fonts/truetype/arimo/Arimo-BoldItalic.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-BoldItalic.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-BoldItalic.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return candidate
    raise SystemExit("No se encontró una fuente Arial-compatible Bold Italic")

def write_png(title, target):
    lines = balanced_lines(title)
    image = Image.new("RGB", (WIDTH, HEIGHT), PAPER)
    draw = ImageDraw.Draw(image)
    path = font_path()
    size = 190

    while size > 54:
        font = ImageFont.truetype(path, size)
        widths = [draw.textbbox((0, 0), line, font=font)[2] for line in lines]
        line_height = int(size * .9)
        if max(widths) <= 1060 and line_height * len(lines) <= 500:
            break
        size -= 2

    font = ImageFont.truetype(path, size)
    line_height = int(size * .9)
    y = (HEIGHT - line_height * len(lines)) / 2

    for line in lines:
        box = draw.textbbox((0, 0), line, font=font)
        x = (WIDTH - (box[2] - box[0])) / 2
        draw.text((x, y), line, font=font, fill=INK)
        y += line_height

    image.save(target, "PNG", optimize=True)

def page_html(article):
    slug = clean(article.get("slug") or article.get("id"))
    title = clean(article.get("title"))
    content = str(article.get("content") or article.get("summary") or "")
    description = clean(content)[:180]
    article_url = f"{BASE_URL}noticias/{slug}/"
    popup_url = f"{BASE_URL}?article={slug}"
    png_url = f"{BASE_URL}share/{slug}.png"
    svg_url = f"{BASE_URL}share/{slug}.svg"
    body = "".join(
        f"<p>{html.escape(block).replace(chr(10), '<br>')}</p>"
        for block in re.split(r"\n{2,}", content)
        if block.strip()
    )

    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{html.escape(title)}</title>
  <meta name="description" content="{html.escape(description, quote=True)}">
  <link rel="canonical" href="{article_url}">
  <meta property="og:type" content="article">
  <meta property="og:title" content="{html.escape(title, quote=True)}">
  <meta property="og:description" content="{html.escape(description, quote=True)}">
  <meta property="og:url" content="{article_url}">
  <meta property="og:image" content="{png_url}">
  <meta property="og:image:type" content="image/png">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{html.escape(title, quote=True)}">
  <meta name="twitter:description" content="{html.escape(description, quote=True)}">
  <meta name="twitter:image" content="{png_url}">
  <link rel="alternate" type="image/svg+xml" href="{svg_url}">
  <script>location.replace({json.dumps(popup_url)});</script>
  <style>
    *{{box-sizing:border-box}}
    body{{margin:0;background:#f7f7f5;color:#2d2d2b;font-family:Arial,Helvetica,sans-serif;font-weight:700}}
    .fallback{{position:fixed;inset:0;background:rgba(0,0,0,.24);display:grid;place-items:center;padding:20px}}
    article{{position:relative;width:min(980px,94vw);height:min(84vh,880px);overflow:auto;background:#f7f7f5;border:3px solid #111;padding:clamp(30px,5vw,64px)}}
    .close{{position:absolute;right:14px;top:8px;color:#111;text-decoration:none;font-size:44px;line-height:1}}
    h1{{margin:0 45px 30px;font-size:clamp(42px,8vw,94px);line-height:1;letter-spacing:-.015em;text-align:center}}
    .body{{font-size:clamp(19px,2vw,27px);line-height:1.28}}
    .share{{margin-top:40px;padding-top:18px;border-top:3px solid #111;text-align:center;font-weight:400}}
  </style>
</head>
<body>
  <div class="fallback">
    <article>
      <a class="close" href="{BASE_URL}" aria-label="Cerrar">×</a>
      <h1>{html.escape(title)}</h1>
      <div class="body">{body}</div>
      <div class="share">compartir · copiar link · whatsapp</div>
    </article>
  </div>
</body>
</html>
"""

def main():
    data = json.loads((ROOT / "data" / "news.json").read_text(encoding="utf-8"))
    articles = data if isinstance(data, list) else data.get("articles", [])
    share_dir = ROOT / "share"
    news_dir = ROOT / "noticias"
    share_dir.mkdir(exist_ok=True)
    news_dir.mkdir(exist_ok=True)

    valid = set()
    for article in articles:
        slug = clean(article.get("slug") or article.get("id"))
        if not slug:
            continue
        valid.add(slug)

        (share_dir / f"{slug}.svg").write_text(svg_text(article.get("title", "")), encoding="utf-8")
        write_png(article.get("title", ""), share_dir / f"{slug}.png")

        folder = news_dir / slug
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "index.html").write_text(page_html(article), encoding="utf-8")

    for folder in news_dir.iterdir():
        if folder.is_dir() and folder.name not in valid:
            import shutil
            shutil.rmtree(folder)

    for file in share_dir.iterdir():
        if file.is_file() and file.stem not in valid:
            file.unlink()

if __name__ == "__main__":
    main()
