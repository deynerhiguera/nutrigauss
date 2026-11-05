"""
Pruebas de NutriGauss: motor de Gauss y servidor.

Ejecutar con:   python3 pruebas.py      (Windows: python pruebas.py)

Las primeras pruebas arman sistemas 3x3 de solución conocida y comprueban que
resolver() de motor.py da el resultado correcto. Las últimas levantan el
servidor en un puerto libre y llaman a la API igual que lo hace la página.
"""
import json
import threading
import urllib.error
import urllib.request

from motor import ALIMENTOS, resolver


def sistema(A, B):
    """Convierte una matriz A (3x3) y un vector B al formato que usa resolver():
    cada columna de A se pasa como un 'alimento' y B como las 'metas'."""
    columnas = [(f"x{j + 1}", A[0][j], A[1][j], A[2][j]) for j in range(3)]
    return resolver(columnas, B)


def prueba_primer_avance():
    """Ejemplo del primer avance: 2x + y − z = 8, −3x − y + 2z = −11, −2x + y + 2z = −3."""
    r = sistema([[2, 1, -1], [-3, -1, 2], [-2, 1, 2]], [8, -11, -3])
    assert r["tipo"] == "determinado"
    assert r["sol"] == [2.0, 3.0, -1.0], r["sol"]


def prueba_ejemplo_del_documento():
    """Arroz, pollo y aguacate para 40 g de proteína, 60 g de carbohidratos y 15 g de grasa."""
    r = resolver(ALIMENTOS[:3], [40, 60, 15])
    assert r["tipo"] == "determinado"
    assert [round(s * 100, 1) for s in r["sol"]] == [191.1, 107.8, 71.8]
    assert round(r["kcal"]) == 535
    assert len(r["pasos"]) == 15
    assert all(v["exacto"] for v in r["verificacion"])


def prueba_pivote_cero():
    """El primer elemento es 0: sin pivoteo parcial el método se detendría."""
    r = sistema([[0, 2, 1], [1, 1, 1], [2, 1, 3]], [5, 6, 13])
    assert r["tipo"] == "determinado"
    assert any(p["tipo"] == "intercambio" for p in r["pasos"])


def prueba_infinitas_soluciones():
    """La tercera ecuación es la suma de las dos primeras."""
    r = sistema([[1, 1, 1], [1, -1, 2], [2, 0, 3]], [6, 3, 9])
    assert r["tipo"] == "indeterminado"
    assert r["sol"] is None


def prueba_sin_solucion():
    """Mismos coeficientes que el caso anterior, pero metas incompatibles."""
    r = sistema([[1, 1, 1], [1, -1, 2], [2, 0, 3]], [6, 3, 10])
    assert r["tipo"] == "incompatible"
    assert r["sol"] is None


def prueba_porcion_negativa():
    """Mucha grasa y casi nada de carbohidratos: el arroz sale negativo (comida no factible)."""
    r = resolver(ALIMENTOS[:3], [40, 5, 30])
    assert r["tipo"] == "determinado"
    assert r["sol"][0] < 0 and r["factible"] is False


def prueba_servidor():
    """El servidor responde la lista de alimentos y resuelve el ejemplo por la API."""
    from http.server import ThreadingHTTPServer
    from servidor import Manejador

    srv = ThreadingHTTPServer(("127.0.0.1", 0), Manejador)
    hilo = threading.Thread(target=srv.serve_forever, daemon=True)
    hilo.start()
    base = f"http://127.0.0.1:{srv.server_port}"
    try:
        with urllib.request.urlopen(base + "/api/alimentos") as r:
            assert len(json.load(r)["alimentos"]) == len(ALIMENTOS)
        with urllib.request.urlopen(base + "/") as r:
            assert b"NutriGauss" in r.read()
        cuerpo = {
            "alimentos": [dict(nombre=a[0], proteina=a[1], carbohidratos=a[2], grasa=a[3]) for a in ALIMENTOS[:3]],
            "metas": [40, 60, 15],
        }
        pedido = urllib.request.Request(base + "/api/resolver", data=json.dumps(cuerpo).encode(),
                                        headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(pedido) as r:
            res = json.load(r)
        assert [round(s * 100, 1) for s in res["sol"]] == [191.1, 107.8, 71.8]
        cuerpo["alimentos"][1] = cuerpo["alimentos"][0]
        pedido = urllib.request.Request(base + "/api/resolver", data=json.dumps(cuerpo).encode())
        try:
            urllib.request.urlopen(pedido)
            raise AssertionError("debía rechazar alimentos repetidos")
        except urllib.error.HTTPError as e:
            assert e.code == 400 and "distintos" in json.load(e)["error"]
    finally:
        srv.shutdown()
        srv.server_close()


if __name__ == "__main__":
    pruebas = [v for k, v in list(globals().items()) if k.startswith("prueba_")]
    fallas = 0
    for prueba in pruebas:
        try:
            prueba()
            print(f"  OK     {prueba.__doc__.strip().splitlines()[0]}")
        except Exception as e:  # noqa: BLE001 - se informa cualquier falla
            fallas += 1
            print(f"  FALLA  {prueba.__name__}: {e!r}")
    print(f"\n{len(pruebas) - fallas} de {len(pruebas)} pruebas correctas.")
