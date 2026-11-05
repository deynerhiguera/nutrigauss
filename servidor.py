"""
NutriGauss - Servidor local
===========================
Sirve la página web (carpeta web/) y expone el motor de Gauss como una API:

    GET  /api/alimentos   lista de alimentos con su composición por 100 g
    POST /api/resolver    {"alimentos": [3 alimentos], "metas": [P, C, G]}
                          -> pasos de la eliminación de Gauss y resultado

Solo usa la biblioteca estándar de Python: no hay que instalar nada.

Ejecutar:   python3 servidor.py          (Windows: python servidor.py)
Se abre el navegador en http://localhost:8000. Para detenerlo: Ctrl + C.
"""
import json
import math
import os
import sys
import webbrowser
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from motor import ALIMENTOS, MACROS, resolver

CARPETA_WEB = Path(__file__).resolve().parent / "web"
PUERTO_INICIAL = 8000


class ErrorDatos(ValueError):
    """Datos enviados por la página que no se pueden resolver."""


def leer_numero(valor, campo):
    try:
        x = float(str(valor).strip().replace(",", "."))
    except (TypeError, ValueError):
        raise ErrorDatos(f"«{campo}» debe ser un número.")
    if not math.isfinite(x) or x < 0:
        raise ErrorDatos(f"«{campo}» debe ser un número mayor o igual a cero.")
    return x


def validar(cuerpo):
    """Convierte el JSON de la página en los argumentos de resolver()."""
    lista = cuerpo.get("alimentos")
    if not isinstance(lista, list) or len(lista) != 3:
        raise ErrorDatos("Elige exactamente tres alimentos.")
    alimentos = []
    for i, a in enumerate(lista, start=1):
        if not isinstance(a, dict):
            raise ErrorDatos(f"El alimento {i} no es válido.")
        nombre = str(a.get("nombre", "")).strip()[:60]
        if not nombre:
            raise ErrorDatos(f"Falta el nombre del alimento {i}.")
        valores = [leer_numero(a.get(k), f"{m} de {nombre}")
                   for k, m in zip(("proteina", "carbohidratos", "grasa"), MACROS)]
        if any(v > 100 for v in valores):
            raise ErrorDatos(f"{nombre}: ningún nutriente puede pasar de 100 g por cada 100 g.")
        alimentos.append((nombre, *valores))
    if len({a[0].lower() for a in alimentos}) < 3:
        raise ErrorDatos("Elige tres alimentos distintos.")
    metas = cuerpo.get("metas")
    if not isinstance(metas, list) or len(metas) != 3:
        raise ErrorDatos("Escribe las tres metas: proteína, carbohidratos y grasa.")
    metas = [leer_numero(v, f"Meta de {m.lower()}") for v, m in zip(metas, MACROS)]
    return alimentos, metas


class Manejador(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(CARPETA_WEB), **kwargs)

    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".js": "text/javascript", ".mjs": "text/javascript", ".css": "text/css",
        ".woff2": "font/woff2", ".svg": "image/svg+xml", ".json": "application/json",
    }

    def responder_json(self, datos, estado=HTTPStatus.OK):
        cuerpo = json.dumps(datos, ensure_ascii=False).encode("utf-8")
        self.send_response(estado)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(cuerpo)

    def end_headers(self):
        if not self.path.startswith("/api/"):
            self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def do_GET(self):
        if self.path == "/api/alimentos":
            self.responder_json(dict(
                macros=list(MACROS),
                alimentos=[dict(nombre=a[0], proteina=a[1], carbohidratos=a[2], grasa=a[3]) for a in ALIMENTOS]))
            return
        if self.path.startswith("/api/"):
            self.responder_json(dict(error="Ruta no encontrada."), HTTPStatus.NOT_FOUND)
            return
        super().do_GET()

    def do_POST(self):
        if self.path != "/api/resolver":
            self.responder_json(dict(error="Ruta no encontrada."), HTTPStatus.NOT_FOUND)
            return
        try:
            largo = int(self.headers.get("Content-Length", 0))
            if largo > 20_000:
                raise ErrorDatos("La solicitud es demasiado grande.")
            cuerpo = json.loads(self.rfile.read(largo) or b"{}")
            if not isinstance(cuerpo, dict):
                raise ErrorDatos("Formato de datos no válido.")
            alimentos, metas = validar(cuerpo)
        except (ErrorDatos, json.JSONDecodeError, ValueError) as e:
            mensaje = str(e) if isinstance(e, ErrorDatos) else "Formato de datos no válido."
            self.responder_json(dict(error=mensaje), HTTPStatus.BAD_REQUEST)
            return
        self.responder_json(resolver(alimentos, metas))

    def log_message(self, formato, *args):
        if self.path.startswith("/api/resolver"):
            sys.stderr.write(f"  resolver  {self.command} {args[1] if len(args) > 1 else ''}\n")


def iniciar(puerto=PUERTO_INICIAL, abrir=True, host="127.0.0.1"):
    for p in range(puerto, puerto + 20):
        try:
            servidor = ThreadingHTTPServer((host, p), Manejador)
            break
        except OSError:
            continue
    else:
        sys.exit(f"No hay puertos libres entre {puerto} y {puerto + 19}.")
    url = f"http://localhost:{servidor.server_port}"
    print(f"\n  NutriGauss está corriendo en {url}")
    print("  Deja esta ventana abierta mientras usas la página. Para detenerlo: Ctrl + C\n")
    if abrir:
        webbrowser.open(url)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\n  Servidor detenido.")
    finally:
        servidor.server_close()


if __name__ == "__main__":
    # En la nube (Render u otro hosting) el puerto llega en la variable PORT.
    if os.environ.get("PORT"):
        iniciar(int(os.environ["PORT"]), abrir=False, host="0.0.0.0")
    else:
        iniciar(abrir="--sin-navegador" not in sys.argv)
