// NutriGauss en GitHub Pages: no hay servidor, así que el mismo motor.py y la
// validación de servidor.py corren dentro del navegador con Pyodide (Python
// compilado a WebAssembly). Este archivo atiende /api/alimentos y /api/resolver
// igual que servidor.py, de modo que app.js no cambia.
// Solo se incluye en la versión publicada; en local se usa servidor.py.
(() => {
  const PYODIDE = "https://cdn.jsdelivr.net/pyodide/v0.26.4/full/";
  const CARPETA_PY = new URL("py/", document.baseURI).href;
  const fetchOriginal = window.fetch.bind(window);
  let motor;

  function cargarScript(src) {
    return new Promise((ok, mal) => {
      const s = document.createElement("script");
      s.src = src;
      s.onload = ok;
      s.onerror = () => mal(new Error("No se pudo cargar " + src));
      document.head.appendChild(s);
    });
  }

  function cargarMotor() {
    motor ??= (async () => {
      await cargarScript(PYODIDE + "pyodide.js");
      const py = await window.loadPyodide({ indexURL: PYODIDE });
      py.FS.mkdirTree("/nutrigauss");
      for (const archivo of ["motor.py", "servidor.py"]) {
        const r = await fetchOriginal(CARPETA_PY + archivo);
        if (!r.ok) throw new Error("No se encontró " + archivo);
        py.FS.writeFile("/nutrigauss/" + archivo, await r.text());
      }
      py.runPython(`
import sys, json
sys.path.insert(0, "/nutrigauss")
from motor import ALIMENTOS, MACROS, resolver
from servidor import validar, ErrorDatos

def api_alimentos():
    return 200, json.dumps(dict(
        macros=list(MACROS),
        alimentos=[dict(nombre=a[0], proteina=a[1], carbohidratos=a[2], grasa=a[3]) for a in ALIMENTOS]),
        ensure_ascii=False)

def api_resolver(texto):
    try:
        if len(texto) > 20_000:
            raise ErrorDatos("La solicitud es demasiado grande.")
        cuerpo = json.loads(texto or "{}")
        if not isinstance(cuerpo, dict):
            raise ErrorDatos("Formato de datos no válido.")
        alimentos, metas = validar(cuerpo)
    except (ErrorDatos, json.JSONDecodeError, ValueError) as e:
        mensaje = str(e) if isinstance(e, ErrorDatos) else "Formato de datos no válido."
        return 400, json.dumps(dict(error=mensaje), ensure_ascii=False)
    return 200, json.dumps(resolver(alimentos, metas), ensure_ascii=False)
`);
      return py;
    })();
    return motor;
  }

  function respuesta([estado, cuerpo]) {
    return new Response(cuerpo, {
      status: estado,
      headers: { "Content-Type": "application/json; charset=utf-8" },
    });
  }

  window.fetch = async (recurso, opciones = {}) => {
    const url = new URL(typeof recurso === "string" ? recurso : recurso.url, location.href);
    const ruta = url.pathname.replace(/^.*\/api\//, "/api/");
    if (!ruta.startsWith("/api/")) return fetchOriginal(recurso, opciones);
    const py = await cargarMotor();
    if (ruta === "/api/alimentos") return respuesta(py.globals.get("api_alimentos")().toJs());
    if (ruta === "/api/resolver") return respuesta(py.globals.get("api_resolver")(String(opciones.body ?? "")).toJs());
    return respuesta([404, JSON.stringify({ error: "Ruta no encontrada." })]);
  };

  cargarMotor().catch(() => {});
})();
