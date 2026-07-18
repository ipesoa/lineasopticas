LÍNEAS ÓPTICAS — GITHUB PAGES
==============================

1. Sube todo el contenido del ZIP a la raíz del repositorio.
2. En GitHub abre Settings > Pages.
3. Selecciona Deploy from a branch, main y /root.
4. Guarda y espera la publicación.

ESCRITORIO
----------
Las noticias se desplazan horizontalmente:
- Con la rueda del ratón cuando el cursor está sobre las noticias.
- Con trackpad.
- Arrastrando el punto negro de la barra inferior.
- Pulsando directamente sobre la barra.

MÓVIL
-----
Las noticias se muestran en columna y se desplazan verticalmente.

DATOS
-----
La web lee data/news.json o la URL indicada en config.js.
Consulta API_PARA_LA_IA.txt para el formato exacto.

PRUEBA LOCAL
------------
Desde esta carpeta:

python -m http.server 8000

Abre http://localhost:8000

STRIPE
------
La web solo contiene enlaces públicos de Stripe. No contiene claves privadas y
Líneas Ópticas no recibe ni almacena los datos completos de las tarjetas.
