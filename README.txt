LÍNEAS ÓPTICAS — INSTALACIÓN EN GITHUB PAGES
================================================

1. Descomprime el ZIP.
2. Sube todo el contenido a la raíz del repositorio.
3. En GitHub: Settings > Pages.
4. Source: Deploy from a branch.
5. Branch: main / root.
6. Guarda y espera la publicación.

ARCHIVOS
--------
index.html              Estructura de la página.
styles.css              Diseño responsive.
app.js                  Carga, búsqueda, destacados, popup y compartir.
config.js               URL de la API, 40 noticias/página y enlaces Stripe.
data/news.json          Datos de demostración.
API_PARA_LA_IA.txt      Contrato exacto para el generador de noticias.
.nojekyll               Evita procesamiento innecesario de Jekyll.

STRIPE
------
Ya están configurados dos Payment Links reales de la cuenta “ipesoa”:
- Donación libre desde 5 €, con 10 € como cantidad sugerida.
- Apoyo mensual de 5 €.

La página nunca contiene claves privadas; solo usa URLs públicas alojadas por Stripe.

PRUEBA LOCAL
------------
No abras index.html directamente con doble clic porque fetch puede bloquear el JSON.
Desde la carpeta ejecuta:

    python -m http.server 8000

Después abre:

    http://localhost:8000

CAMBIAR EL NOMBRE O LOS PAGOS
-----------------------------
Edita config.js.

CAMBIAR LAS NOTICIAS
---------------------
Edita data/news.json o apunta apiUrl a tu API.
