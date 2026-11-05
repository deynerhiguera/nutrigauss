#!/bin/bash
# Arma la versión estática para GitHub Pages: la carpeta web/ más motor.py y
# servidor.py, que corren en el navegador con Pyodide (web/motor-navegador.js).
set -euo pipefail
destino="${1:-_site}"
rm -rf "$destino"
cp -R web "$destino"
mkdir -p "$destino/py"
cp motor.py servidor.py "$destino/py/"
sed -i.bak 's#<script src="app.js" type="module"></script>#<script src="motor-navegador.js"></script>\n  &#' "$destino/index.html"
rm "$destino/index.html.bak"
touch "$destino/.nojekyll"
