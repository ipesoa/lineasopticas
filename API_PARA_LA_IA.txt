LÍNEAS ÓPTICAS — API PARA LA IA
================================

El contrato vigente está documentado en:
ORDENES_IA_GENERADOR_SEO_SVG.txt

Resumen:
- La IA envía únicamente JSON o JSONL UTF-8.
- El token va solo en Authorization: Bearer TU_TOKEN.
- No enviar HTML ni SVG dentro de content.
- Para altas se requieren title, seoTitle, summary, metaDescription, content,
  publishedAt, updatedAt, author, authorType, section, featured, tags,
  hiddenTags, sources, language y status.
- GitHub Actions crea páginas HTML, sitemap, RSS y SVG automáticamente.
