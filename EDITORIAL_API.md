# Contrato editorial de la API

La IA envía únicamente JSON o JSONL UTF-8. El token se utiliza exclusivamente
en la cabecera `Authorization: Bearer ...`; nunca debe incluirse en los datos,
el artículo ni un archivo público.

## Campos de una noticia

- `action`: `add`, `update` o `delete`.
- `title` y `seoTitle`.
- `summary`, `metaDescription` y `content` en texto plano.
- `publishedAt` y `updatedAt` en ISO 8601 con zona horaria.
- `author` y `authorType` (`Person` u `Organization`).
- `section`, `featured`, `tags` y `hiddenTags`.
- `sources`: nombre y URL pública HTTPS de cada fuente.
- `language`: `es`.
- `status`: `published`.

Sofista crea un `id` y un `slug` estables al añadir una noticia. Las
actualizaciones y eliminaciones deben usar ese identificador; no deben inventar
uno nuevo.

```json
{
  "action": "add",
  "title": "Dos días después del huracán",
  "seoTitle": "Qué ocurre dos días después del huracán",
  "summary": "Balance de daños, respuesta institucional y situación de la población.",
  "metaDescription": "Daños y respuesta institucional dos días después del huracán.",
  "content": "Primer párrafo.\n\nSegundo párrafo.",
  "publishedAt": "2026-07-19T20:30:00+02:00",
  "updatedAt": "2026-07-19T20:30:00+02:00",
  "author": "Líneas Ópticas",
  "authorType": "Organization",
  "section": "Actualidad",
  "featured": false,
  "tags": ["huracán", "emergencias"],
  "hiddenTags": ["daños", "evacuaciones"],
  "sources": [{"name": "Fuente", "url": "https://ejemplo.org/documento"}],
  "language": "es",
  "status": "published"
}
```

## Reglas editoriales

- El titular visible debe ser claro, legible y preferentemente breve.
- `seoTitle` debe ser explícito, descriptivo y evitar el clickbait.
- El resumen explica qué ocurre y por qué importa sin copiar el primer párrafo.
- El contenido se envía sin HTML y separa párrafos con dos saltos de línea.
- No se inventan datos, cifras, citas, nombres, lugares ni fechas.
- Las fuentes primarias tienen prioridad y toda incertidumbre se expresa.
- Una actualización conserva `id` y `slug`, y modifica `updatedAt`.

Las reglas de imágenes, interfaz, normalización y publicación están en
`SOFISTA_FRONTEND_CONTRACT.md`.
