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

## Desarrollo
```
sudo apt-get install poppler-utils
pip install -r requirements.txt
pytest
python -m scraper.build --pdf 261105_lis_mae.pdf
```
