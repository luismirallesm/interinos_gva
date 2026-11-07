# interinos_gva

Consulta gratuita y open source de adjudicaciones de personal docente interino de la Conselleria d'Educació (GVA).

## Formato real del listado (verificado con 261105_lis_mae.pdf)
- Diario: `AAMMDD_lis_<cuerpo>.pdf` (`mae` = maestros), martes y jueves. Inicio de curso: `ini_2026_adj_int_mae.pdf` (17 051 maestros, todo el curso 26/27).
- El orden es la posición en ESE listado; no es un id fijo. Los adjudicados desaparecen del listado siguiente. Seguir personas por nombre (hay homónimos).
- No es una tabla: texto por persona. **No trae NIF.** Solo nº de orden y nombre.
- Estados: Adjudicat, Desactivat, No adjudicat, Ha participat, No ha participat.
- Solo las personas adjudicadas traen centro, localidad, especialidad del puesto, jornada y tipo.
- Provincia = primeros 2 dígitos del código de centro (03/12/46).

## Estructura de datos
- `data/<cuerpo>/<AAAA-MM-DD>.json`: foto completa del día.
- `data/index.json`: cuerpos y fechas disponibles.
- `data/history.json`: totales por estado y día.
- `data/state.json`: hashes de PDFs ya procesados.

## Subir un listado a mano (modo seguro)
Sube el PDF a la carpeta `inbox/` (GitHub: Add file → Upload files). El workflow se lanza solo, genera `data/` y hace commit.

## Desarrollo
```
sudo apt-get install poppler-utils
pip install -r requirements.txt
pytest
python -m scraper.build --pdf 261105_lis_mae.pdf
```

## Web (GitHub Pages)
`index.html` en la raíz lee `data/` directamente. Activar en *Settings → Pages → Deploy from a branch → main / (root)*.
Para probar en local: `python -m http.server` y abrir http://localhost:8000
- Posición efectiva = 1 + personas por delante que no están desactivadas ni adjudicadas.
- Las personas se enlazan entre listados por nombre (+ nº de aparición si hay homónimos), porque el orden cambia cada día.

## Descubrimiento automático de listados
1. Rastrea las páginas de `SOURCES` (enlaces a PDF) y aprende el número de carpeta de cada enlace.
2. Prueba `https://ceice.gva.es/documents/162909733/<carpeta>/<AAMMDD>_lis_mae.pdf` para cada día laborable
   sin listado desde `PROBE_START`, con las carpetas conocidas (`KNOWN_FOLDERS` + las aprendidas en `data/state.json`).
3. Respeta `robots.txt`; si no lo permite, no descarga y lo dice en el log.

Si sale una carpeta nueva que el rastreo no ve: lanza *Run workflow* con la URL del PDF en `pdf_url` una vez;
el bot aprende la carpeta y encuentra los siguientes solo.
