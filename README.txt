LÍNEAS ÓPTICAS — GITHUB PAGES + SEO ESTÁTICO
=============================================

QUÉ HACE ESTA VERSIÓN
---------------------
El diseño principal sigue siendo el mismo. data/news.json continúa siendo la
fuente única. Cada push a main compila automáticamente:

- portada con contenido HTML real y enlaces rastreables;
- /noticias/slug/ para cada noticia;
- SVG cuadrado ultraligero por titular;
- sitemap.xml y news-sitemap.xml;
- feed.xml;
- archivo y páginas de sección;
- datos estructurados NewsArticle y etiquetas sociales.


PORTADA YA COMPILADA
---------------------
Este paquete incluye index.html ya lleno, las páginas /noticias/, los SVG y los
sitemaps. Por tanto, al subirlo al repositorio la portada no queda vacía.
index.template.html es la plantilla que utiliza GitHub Actions para reconstruir
el sitio cada vez que cambia data/news.json. No debe sustituirse por index.html.

Al abrir index.html directamente desde el disco, el navegador puede bloquear la
lectura del JSON por seguridad. En ese caso se conservan las tarjetas estáticas
ya compiladas, por lo que la portada sigue siendo visible. Para probar todas las
funciones dinámicas usa el servidor local indicado más abajo.

PUBLICACIÓN EN GITHUB
---------------------
1. Sube todo el contenido del ZIP a la raíz del repositorio.
2. En GitHub abre Settings > Pages.
3. En Build and deployment selecciona Source: GitHub Actions.
4. Haz un push a main o ejecuta manualmente:
   Actions > Compilar y publicar Líneas Ópticas > Run workflow.
5. La IA puede seguir actualizando data/news.json mediante su token. Cada commit
   en main vuelve a compilar y publicar la web.

No selecciones "Deploy from a branch" en esta versión: la carpeta pública se
crea durante GitHub Actions y se despliega como artefacto.

CONFIGURACIÓN
-------------
- site.config.json: URL pública, nombre, idioma y valores editoriales.
- config.js: configuración usada por la interfaz del navegador.
- Ambos contienen ahora https://ipesoa.github.io/lineasopticas.
- Si cambia el dominio, actualiza siteUrl en ambos archivos.

DATOS DE LA IA
--------------
Lee ORDENES_IA_GENERADOR_SEO_SVG.txt. Es el contrato completo del payload, las
reglas editoriales y el algoritmo exacto del SVG.

PRUEBA LOCAL COMPILADA
----------------------
Desde la raíz:

python scripts/build_site.py --output _site
python -m http.server 8000 --directory _site

Abre http://localhost:8000

VALIDACIONES
------------
La compilación se detiene si news.json contiene identificadores duplicados,
slugs inválidos, fechas sin zona horaria, fuentes incorrectas o campos esenciales
vacíos. El error aparecerá en la pestaña Actions de GitHub.

SEARCH CONSOLE
--------------
Después del primer despliegue:
- verifica la propiedad en Google Search Console;
- envía /sitemap.xml y /news-sitemap.xml;
- inspecciona la portada y una URL /noticias/slug/;
- añade el código de verificación a googleSiteVerification en site.config.json
  si utilizas la etiqueta HTML de verificación.

STRIPE
------
La web solo contiene enlaces públicos de Stripe. No contiene claves privadas y
Líneas Ópticas no recibe ni almacena los datos completos de las tarjetas.
