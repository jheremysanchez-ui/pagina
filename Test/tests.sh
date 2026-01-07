#!/usr/bin/env bash
set -e

FECHA=$(date +"%Y-%m-%d_%H-%M")
OUT="pruebas/$FECHA"

mkdir -p "$OUT"

pytest \
  --html="$OUT/reporte_pruebas.html" \
  --self-contained-html \
  --cov=apps \
  --cov-report=html:"$OUT/cobertura_html" \
  --cov-report=term-missing \
  --metadata Proyecto "FULL PC TECHNOLOGY - Plataforma Web" \
  --metadata Entorno "Django + DRF + React" \
  --metadata Autor "Jheremy Nicolas Sanchez Guerrero"

echo "✅ Reportes generados en: $OUT"
