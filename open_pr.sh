#!/usr/bin/env bash
# Crea la rama, copia los ficheros de ./repo y abre un PR en luismirallesm/interinos_gva.
# Requisitos: git y gh (GitHub CLI) instalados y autenticados (gh auth login).
set -euo pipefail

REPO="luismirallesm/interinos_gva"
BRANCH="feat/scraper-skeleton"
HERE="$(cd "$(dirname "$0")" && pwd)"
WORK="$HERE/clone"

command -v gh >/dev/null || { echo "Falta gh (https://cli.github.com)"; exit 1; }
gh auth status >/dev/null || { echo "Ejecuta antes: gh auth login"; exit 1; }

if ! gh repo view "$REPO" >/dev/null 2>&1; then
  echo "El repo no existe; creándolo (público)..."
  gh repo create "$REPO" --public
fi

rm -rf "$WORK"
gh repo clone "$REPO" "$WORK"
cd "$WORK"

# Un repo vacío no tiene rama base: crear commit inicial en main.
if ! git rev-parse HEAD >/dev/null 2>&1; then
  git checkout -B main
  git commit --allow-empty -m "chore: initial commit"
  git push -u origin main
fi

BASE="$(git symbolic-ref --short HEAD)"
git checkout -b "$BRANCH"
cp -R "$HERE/repo/." .
git add -A
git commit -m "feat: esqueleto del scraper (fetch, parser PDF, build JSON) y workflow de Actions"
git push -u origin "$BRANCH"

gh pr create --base "$BASE" --head "$BRANCH" \
  --title "feat: esqueleto del scraper y workflow de Actions" \
  --body "Primer PR: scraper en Python (descubrir/descargar PDFs, parser tolerante de cabeceras ES/VA, generación de data/*.json e historial), tests y workflow con cron.

**Pendiente de verificar con datos reales:** URLs/palabras clave en scraper/config.py y alias de cabecera en scraper/parse_pdf.py (ver README).

Siguiente PR: frontend."
