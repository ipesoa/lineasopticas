# Contrato de publicación de Sofista

Este archivo define la salida que Sofista debe producir y comprobar antes de
enviar un commit a `main`. `data/news.json` continúa siendo la fuente única de
las noticias.

## Imagen del titular

- Sofista crea la imagen; la página únicamente la muestra.
- Formato único: PNG.
- Ruta canónica: `media/noticias/<slug>.png`.
- Dimensiones: 1200 × 1200 píxeles.
- La misma URL se utiliza en la portada, la página estática, Open Graph,
  Twitter Card y `Article.image`.
- No se deben generar referencias `.svg` ni copias del PNG en carpetas internas
  de cada noticia.

## Interfaz de la noticia

La ventana abierta desde la portada y `/noticias/<slug>/` deben mostrar la misma
estructura, en este orden:

1. titular;
2. texto de la noticia;
3. fila centrada `compartir · miniatura PNG · copiar link`;
4. tres noticias distintas para seguir leyendo.

`compartir` y la miniatura ejecutan la misma acción nativa. Si el navegador no
dispone de ella, abren la pantalla de compartir de WhatsApp; nunca sustituyen su
acción por copiar. Solo `copiar link` copia la URL canónica de la noticia y
ofrece un cuadro de copia manual si el navegador deniega el portapapeles. Las
tres noticias se eligen de forma pseudoaleatoria pero estable a partir del slug,
para que no cambien en cada recarga.

## Reglas de diseño que Sofista no debe anular

- No añadir reglas con `overflow: visible` a `.article-card` o `.card-title`.
- No cambiar `.share-actions` de cuadrícula centrada a `flex` alineado a la
  izquierda.
- No imponer un tamaño mínimo de titular que ensanche su contenedor.
- En móvil, cada tarjeta tiene `min-width: 0`, ancho máximo del 100 %,
  `overflow: hidden` y proporción 1:1.
- El encabezado, el menú y las tarjetas deben permanecer dentro del ancho útil
  de la pantalla.
- Sofista no debe reescribir `app.js`, `styles.css` ni `share.js` al publicar
  una noticia, salvo que esté instalando una versión frontal probada más nueva.

## Orden obligatorio antes de publicar

Después de generar HTML, metadatos y PNG, Sofista ejecuta desde la raíz:

```text
python scripts/normalize_sofista_output.py
python scripts/validate_site.py
```

Si cualquiera de los dos procesos falla, Sofista no publica el commit.

Después renderiza la portada y una noticia a 360 × 800, 390 × 844 y 430 × 932.
En los tres tamaños debe verificar:

- `document.documentElement.scrollWidth <= window.innerWidth`;
- el borde derecho de encabezado, menú y tarjetas no supera el viewport;
- cada tarjeta móvil conserva la proporción cuadrada;
- el rectángulo del titular queda dentro de la tarjeta y ocupa una sola línea;
- el PNG termina de cargar y tiene `naturalWidth > 0`;
- compartir, miniatura y copiar enlace permanecen centrados en la misma fila;
- la miniatura mide entre 56 y 68 píxeles en móvil;
- aparecen exactamente tres enlaces para seguir leyendo.

Solo después de superar estas comprobaciones puede enviar los cambios a GitHub.
