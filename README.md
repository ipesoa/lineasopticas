# Líneas Ópticas

Web pública: <https://ipesoa.github.io/lineasopticas/>

`data/news.json` es la fuente editorial. Sofista genera las páginas, los mapas
del sitio, el feed y un único PNG canónico por noticia en
`media/noticias/<slug>.png`.

## Archivos principales

- `app.js`, `styles.css` y `share.js`: interfaz pública.
- `index.template.html`: plantilla estable de la portada.
- `scripts/normalize_sofista_output.py`: corrige y unifica la salida de Sofista.
- `scripts/validate_site.py`: comprueba imágenes, enlaces, compartir y diseño móvil.
- `EDITORIAL_API.md`: formato de datos y reglas editoriales.
- `SOFISTA_FRONTEND_CONTRACT.md`: contrato visual y de publicación.

Antes de publicar una actualización generada por Sofista:

```text
python scripts/normalize_sofista_output.py
python scripts/validate_site.py
```

El TXT con nombre hexadecimal se conserva porque verifica el sitio para
IndexNow. `robots.txt`, los sitemaps y el feed también forman parte del SEO
público y no son archivos de documentación.
