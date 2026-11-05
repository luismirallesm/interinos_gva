# interinos_gva

Consulta gratuita y open source de bolsas de trabajo docente de la Conselleria d'Educació (GVA).

## Estado
Esqueleto del scraper (PR 1). Pendiente: frontend (PR 2).

## Pendiente de verificar antes de fiarse de los datos
- `scraper/config.py`: URLs y palabras clave son provisionales; comprobar contra el portal real.
- `scraper/parse_pdf.py`: los alias de cabecera son una suposición razonable; probar con PDFs reales
  (`python -m scraper.build --pdf listado.pdf --date AAAA-MM-DD --specialty "Infantil"`) y ampliar `HEADER_ALIASES`.
- Revisar aviso legal / condiciones de reutilización de la GVA y RGPD antes de publicar nombres (ver issue).

## Desarrollo
```
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
pytest
```

## Estructura de datos
- `data/index.json`: especialidades disponibles.
- `data/<especialidad>.json`: última situación por número de orden.
- `data/history.json`: foto diaria de totales por estado (base del panel de métricas).
- `data/state.json`: hashes de PDFs ya procesados.
