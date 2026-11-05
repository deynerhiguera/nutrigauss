#!/bin/bash
# Doble clic en macOS: arranca el servidor de NutriGauss y abre el navegador.
cd "$(dirname "$0")" || exit 1
if ! command -v python3 >/dev/null 2>&1; then
  echo "No se encontró Python 3. Instálalo desde https://www.python.org/downloads/macos/ y vuelve a abrir este archivo."
  read -r -p "Pulsa Enter para cerrar."
  exit 1
fi
python3 servidor.py
