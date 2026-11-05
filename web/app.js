// NutriGauss — lógica de la página.
// El cálculo lo hace el backend en Python (motor.py); aquí solo se dibuja.

const $ = (sel, el = document) => el.querySelector(sel);
const $$ = (sel, el = document) => [...el.querySelectorAll(sel)];

const MACROS = ["Proteína", "Carbohidratos", "Grasa"];
const CLAVES = ["proteina", "carbohidratos", "grasa"];
const COLOR = ["var(--proteina)", "var(--carbohidratos)", "var(--grasa)"];
const COLOR_HEX = ["#12898A", "#C99200", "#E4572E"];
const TONOS_PLATO = ["#2448B8", "#6F8BDD", "#B7C6EF"];
const EJEMPLO = { nombres: ["Arroz blanco cocido", "Pechuga de pollo cocida", "Aguacate"], metas: ["40", "60", "15"] };
const OTRO = "__otro__";
const SUB = "₀₁₂₃₄₅₆₇₈₉";

const estado = {
  catalogo: [],
  eleccion: [...EJEMPLO.nombres],
  metas: [...EJEMPLO.metas],
  res: null,
  paso: 0,
  anterior: -1,
  exacto: false,
  vista: "plantear",
  orden: [],
};

// ---------- formato ----------
const sub = (n) => String(n).split("").map((d) => SUB[+d]).join("");
function num(v, dec = 4) {
  if (Math.abs(v) < 5e-11) v = 0;
  let s = v.toFixed(dec);
  if (s.includes(".")) s = s.replace(/0+$/, "").replace(/\.$/, "");
  if (s === "-0") s = "0";
  return s.replace(".", ",").replace("-", "−");
}
const gramos = (v) => num(Math.round(v * 10) / 10, 1);
const texNum = (v, dec = 4) => num(v, dec).replace(",", "{,}").replace("−", "-");
function texFrac(s) {
  const neg = s.startsWith("-");
  const t = neg ? s.slice(1) : s;
  if (!t.includes("/")) return (neg ? "-" : "") + t;
  const [a, b] = t.split("/");
  return `${neg ? "-" : ""}\\frac{${a}}{${b}}`;
}
function tex(expr, display = false) {
  if (!window.katex) return expr;
  return window.katex.renderToString(expr, { throwOnError: false, displayMode: display, strict: "ignore" });
}
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const leerNumero = (s) => {
  const t = String(s).trim().replace(",", ".");
  if (t === "" || !/^\d*\.?\d+$|^\d+\.$/.test(t)) return NaN;
  return parseFloat(t);
};
const buscar = (nombre) => estado.catalogo.find((a) => a.nombre === nombre);

// ---------- 1. plantear ----------
function opciones(seleccion) {
  const base = estado.catalogo.map((a) =>
    `<option value="${esc(a.nombre)}"${a.nombre === seleccion ? " selected" : ""}>${esc(a.nombre)}</option>`).join("");
  return base + `<option value="${OTRO}">Otro alimento…</option>`;
}

function renderEcuacion() {
  let h = "";
  MACROS.forEach((m, k) => {
    h += `<div class="ec-macro" style="grid-row:${k + 2};--c:${COLOR[k]}">${m}</div>`;
  });
  for (let j = 0; j < 3; j++) {
    const cCoef = 2 + j * 3, cVec = cCoef + 1, cSig = cCoef + 2;
    const a = buscar(estado.eleccion[j]) || { proteina: 0, carbohidratos: 0, grasa: 0 };
    h += `<div class="ec-coef" style="grid-column:${cCoef}">${tex(`x_${j + 1}`)}</div>`;
    h += `<div class="ec-cabeza" style="grid-column:${cVec}">
            <label class="selector-etiqueta" for="sel-${j}">Alimento x${sub(j + 1)}</label>
            <div class="selector"><select id="sel-${j}" data-j="${j}">${opciones(estado.eleccion[j])}</select></div>
          </div>`;
    h += `<div class="vector" style="grid-column:${cVec}" aria-label="Composición por 100 g">
            ${CLAVES.map((c) => `<span>${num(a[c], 2)}</span>`).join("")}</div>`;
    h += `<div class="ec-pie" style="grid-column:${cVec}">gramos por cada 100 g</div>`;
    h += `<div class="ec-signo" style="grid-column:${cSig}">${j < 2 ? "+" : "="}</div>`;
  }
  h += `<div class="ec-cabeza ec-metas-cabeza" style="grid-column:11">Metas</div>`;
  h += `<div class="vector vector-metas" style="grid-column:11">
          ${MACROS.map((m, k) => `<label class="meta-campo"><input id="meta-${k}" data-k="${k}" inputmode="decimal"
             value="${esc(estado.metas[k])}" aria-label="Meta de ${m.toLowerCase()} en gramos"><span>g</span></label>`).join("")}
        </div>`;
  h += `<div class="ec-pie" style="grid-column:11" id="energia-metas"></div>`;
  $("#ecuacion").innerHTML = h;
  actualizarEnergiaMetas();
}

function actualizarEnergiaMetas() {
  const v = estado.metas.map(leerNumero);
  $("#energia-metas").textContent = v.every((x) => x >= 0)
    ? `Equivale a ${Math.round(4 * v[0] + 4 * v[1] + 9 * v[2])} kcal`
    : "Escribe números en gramos";
}

function invalidar() {
  if (!estado.res) return;
  estado.res = null;
  $$(".pestana").forEach((b) => { if (b.dataset.vista !== "plantear") b.disabled = true; });
}

function aviso(texto, el = $("#aviso")) {
  el.textContent = texto;
  el.hidden = !texto;
}

async function resolver() {
  aviso("");
  const nombres = estado.eleccion;
  if (new Set(nombres).size < 3) return aviso("Elige tres alimentos distintos.");
  const metas = estado.metas.map(leerNumero);
  if (metas.some((v) => !(v >= 0))) return aviso("Escribe las tres metas en gramos, con números mayores o iguales a cero.");
  const cuerpo = { alimentos: nombres.map(buscar), metas };
  const boton = $("#btn-resolver");
  boton.disabled = true;
  try {
    const r = await fetch("/api/resolver", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(cuerpo),
    });
    const datos = await r.json();
    if (!r.ok) return aviso(datos.error || "No se pudo resolver el sistema.");
    estado.res = datos;
    prepararOrden();
    estado.paso = 0;
    estado.anterior = -1;
    $$(".pestana").forEach((b) => (b.disabled = false));
    renderRiel();
    irVista("resolver");
  } catch {
    aviso("No hay conexión con el servidor. Revisa que la ventana donde corre servidor.py siga abierta.");
  } finally {
    boton.disabled = false;
  }
}

// Sigue a qué nutriente corresponde cada fila después de los intercambios.
function prepararOrden() {
  let orden = [0, 1, 2];
  estado.orden = estado.res.pasos.map((p) => {
    if (p.tipo === "intercambio") {
      orden = [...orden];
      [orden[p.info.a], orden[p.info.b]] = [orden[p.info.b], orden[p.info.a]];
    }
    return orden;
  });
}

// ---------- 2. paso a paso ----------
const GRUPOS = {
  planteamiento: "Planteamiento", buscar_pivote: "Eliminación hacia adelante", intercambio: "Eliminación hacia adelante",
  eliminacion: "Eliminación hacia adelante", sin_pivote: "Eliminación hacia adelante", triangular: "Eliminación hacia adelante",
  clasificacion: "Clasificación", sustitucion: "Sustitución regresiva", verificacion: "Verificación", resultado: "Resultado",
};

function nombreCorto(p) {
  const i = p.info;
  switch (p.tipo) {
    case "planteamiento": return "Plantear el sistema";
    case "buscar_pivote": return `Pivote de la columna ${i.col + 1}`;
    case "intercambio": return `Intercambiar F${sub(i.a + 1)} y F${sub(i.b + 1)}`;
    case "eliminacion": return `Cero en la fila F${sub(i.fila + 1)}`;
    case "sin_pivote": return `Columna ${i.col + 1} sin pivote`;
    case "triangular": return "Matriz triangular";
    case "clasificacion": return "Rangos y tipo de sistema";
    case "sustitucion": return `Despejar x${sub(i.i + 1)}`;
    case "verificacion": return "Comprobar las metas";
    default: return "Porciones finales";
  }
}

function tituloPaso(p) {
  const i = p.info;
  switch (p.tipo) {
    case "planteamiento": return "Planteamiento del sistema";
    case "buscar_pivote": return `Columna ${i.col + 1}: buscar el pivote`;
    case "intercambio": return `Intercambio de filas F${sub(i.a + 1)} ↔ F${sub(i.b + 1)}`;
    case "eliminacion": return `Eliminación: F${sub(i.fila + 1)} → F${sub(i.fila + 1)} − ${estado.exacto ? i.m_exacta : num(i.m)}·F${sub(i.fila_pivote + 1)}`;
    case "sin_pivote": return `Columna ${i.col + 1}: no hay pivote`;
    case "triangular": return "Matriz triangular superior";
    case "clasificacion": return {
      determinado: "Clasificación: compatible determinado",
      indeterminado: "Clasificación: compatible indeterminado",
      incompatible: "Clasificación: incompatible",
    }[i.sistema];
    case "sustitucion": return `Sustitución regresiva: x${sub(i.i + 1)}`;
    case "verificacion": return "Verificación";
    default: return "Resultado final";
  }
}

function renderRiel() {
  let h = "", grupo = "";
  estado.res.pasos.forEach((p, k) => {
    if (GRUPOS[p.tipo] !== grupo) {
      grupo = GRUPOS[p.tipo];
      h += `<li class="riel-grupo" aria-hidden="true">${grupo}</li>`;
    }
    h += `<li><button class="riel-paso" data-k="${k}"><span class="riel-num">${k + 1}</span><span class="riel-txt">${nombreCorto(p)}</span></button></li>`;
  });
  $("#riel").innerHTML = h;
}

function irPaso(k) {
  const total = estado.res.pasos.length;
  k = Math.max(0, Math.min(total - 1, k));
  estado.anterior = estado.paso;
  estado.paso = k;
  renderPaso();
}

function renderPaso() {
  const pasos = estado.res.pasos, k = estado.paso, p = pasos[k];
  $$(".riel-paso").forEach((b) => {
    const j = +b.dataset.k;
    b.toggleAttribute("aria-current", j === k);
    if (j === k) b.setAttribute("aria-current", "step");
    b.classList.toggle("visto", j < k);
  });
  $("#paso-contador").textContent = `Paso ${k + 1} de ${pasos.length}. ${GRUPOS[p.tipo]}`;
  $("#paso-titulo").textContent = tituloPaso(p);
  $("#hoja").innerHTML = p.mat ? htmlMatriz(k) : p.tipo === "verificacion" ? htmlVerificacion(p.info.filas) : htmlResumenFinal();
  $("#explicacion").innerHTML = htmlExplicacion(p);
  $("#btn-anterior").disabled = k === 0;
  $("#btn-siguiente").textContent = k === pasos.length - 1 ? "Ver el resultado" : "Siguiente";
  $$(".interruptor-op").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.exacto === String(estado.exacto))));
}

function valorCelda(p, r, c) {
  return estado.exacto ? tex(texFrac(p.mat_exacta[r][c])) : num(p.mat[r][c]);
}

function htmlMatriz(k) {
  const pasos = estado.res.pasos, p = pasos[k], orden = estado.orden[k];
  const vieneDeAntes = estado.anterior === k - 1;
  const previo = k > 0 && pasos[k - 1].mat ? pasos[k - 1].mat : null;
  const swap = p.tipo === "intercambio" && vieneDeAntes ? p.info : null;
  const solo = new Set();
  if (p.tipo === "triangular" || p.tipo === "clasificacion") {
    for (let r = 1; r < 3; r++) for (let c = 0; c < r; c++) solo.add(`${r},${c}`);
  }
  let h = `<div class="matriz">`;
  for (let c = 0; c < 3; c++) h += `<div class="m-cab" style="grid-column:${c + 2}">${tex(`x_${c + 1}`)}</div>`;
  h += `<div class="m-cab b" style="grid-column:5">Metas B</div>`;
  for (let r = 0; r < 3; r++) {
    const fila = r + 2;
    // En un intercambio, las dos filas se deslizan desde su posición anterior
    const se_mueve = swap && (r === swap.a || r === swap.b);
    const mov = se_mueve ? " mov" : "";
    const d = se_mueve ? `--d:calc(${(r === swap.a ? swap.b : swap.a) - r} * var(--fila));` : "";
    const banda = p.filas[r];
    if (banda) h += `<div class="m-banda ${banda}${mov}" style="${d}grid-row:${fila}"></div>`;
    h += `<div class="m-fila-etq" style="grid-row:${fila}"><span class="f">${tex(`F_${r + 1}`)}</span>
            <span class="macro${mov}" style="${d}--c:${COLOR[orden[r]]}">${MACROS[orden[r]]}</span></div>`;
    for (let c = 0; c < 4; c++) {
      const clases = ["m-celda"];
      if (c === 3) clases.push("b");
      if (p.celda && p.celda[0] === r && p.celda[1] === c) clases.push("pivote");
      if (solo.has(`${r},${c}`)) clases.push("cero-buscado");
      if (vieneDeAntes && previo && !swap && Math.abs(previo[r][c] - p.mat[r][c]) > 1e-12) clases.push("cambio");
      h += `<div class="${clases.join(" ")}${mov}" style="${d}grid-row:${fila};grid-column:${c + 2}">${valorCelda(p, r, c)}</div>`;
    }
  }
  h += `<div class="m-corchete" aria-hidden="true"></div>`;
  h += `<div class="m-margen">${htmlMargen(k)}</div>`;
  h += `</div>`;
  h += `<div class="leyenda" aria-label="Colores">
          <span><i style="background:var(--res-pivote-fila)"></i>Fila pivote</span>
          <span><i style="background:var(--res-modificada)"></i>Fila modificada</span>
          <span><i style="background:var(--res-intercambio)"></i>Filas intercambiadas</span>
          <span><i style="background:var(--pivote)"></i>Pivote</span>
        </div>`;
  return h;
}

// Anotaciones en tinta azul al margen de la matriz
function htmlMargen(k) {
  const p = estado.res.pasos[k], i = p.info;
  // alto real de una fila de la matriz (cambia en pantallas bajas)
  const raiz = getComputedStyle(document.documentElement);
  const F = parseFloat(raiz.getPropertyValue("--fila")) * parseFloat(raiz.fontSize);
  const y = (r) => (r + 0.5) * F;
  const nota = (r, contenido, clase = "") =>
    `<div class="nota ${clase}" style="top:${y(r)}px">${contenido}</div>`;
  const svg = (camino, dobles = false) => `<svg aria-hidden="true"><defs>
      <marker id="punta" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
        <path d="M1 1L9 5L1 9" style="stroke-width:1.6"/></marker></defs>
      <path d="${camino}" marker-end="url(#punta)"${dobles ? ' marker-start="url(#punta)"' : ""}/></svg>`;
  const m = (v, exacta) => (estado.exacto ? texFrac(exacta) : texNum(v));

  switch (p.tipo) {
    case "planteamiento":
      return nota(1, "Cada fila es un nutriente<br>y cada columna, un alimento.", "sin-flecha suave");
    case "buscar_pivote": {
      const val = i.valores.find((v) => v[0] === i.mejor)[1];
      const linea2 = i.mejor === i.desde ? "ya está en su lugar" : `sube a la fila ${tex(`F_${i.desde + 1}`)}`;
      return svg(`M40 ${y(i.mejor)}H6`) + nota(i.mejor, `${tex(`|${texNum(val)}|`)} es el mayor: pivote<br><span style="font-size:.92em">${linea2}</span>`);
    }
    case "intercambio": {
      const a = y(i.a), b = y(i.b);
      return svg(`M6 ${a}C38 ${a} 38 ${b} 6 ${b}`, true) + nota((i.a + i.b) / 2, tex(`F_${i.a + 1} \\leftrightarrow F_${i.b + 1}`));
    }
    case "eliminacion": {
      const a = y(i.fila_pivote), b = y(i.fila);
      return svg(`M6 ${a}C42 ${a} 42 ${b} 8 ${b}`) +
        nota(i.fila, tex(`F_${i.fila + 1} \\to F_${i.fila + 1} - ${m(i.m, i.m_exacta)}\\,F_${i.fila_pivote + 1}`));
    }
    case "sin_pivote":
      return nota(i.desde, `Columna ${i.col + 1}: todos los valores son cero`, "sin-flecha mal");
    case "triangular":
      return nota(1.5, "Debajo de la diagonal<br>solo quedan ceros", "sin-flecha ok");
    case "clasificacion":
      return [0, 1, 2].map((r) => {
        if (i.filas_nulas_ab[r]) return nota(r, "fila nula: no cuenta", "sin-flecha suave");
        if (i.filas_nulas_a[r]) return nota(r, `${tex(`0 = ${texNum(p.mat[r][3])}`)}: contradicción`, "sin-flecha mal");
        return nota(r, "fila no nula: cuenta para el rango", "sin-flecha ok");
      }).join("");
    case "sustitucion": {
      const hechos = estado.res.pasos.slice(0, k + 1).filter((q) => q.tipo === "sustitucion");
      return svg(`M40 ${y(i.i)}H6`) + hechos.map((q) => {
        const v = estado.exacto ? `${texFrac(q.info.x_exacta)} \\approx ${texNum(q.info.x)}` : texNum(q.info.x);
        return nota(q.info.i, tex(`x_${q.info.i + 1} = ${v}`), q === p ? "" : "suave");
      }).join("");
    }
    default:
      return "";
  }
}

function htmlExplicacion(p) {
  const i = p.info, res = estado.res;
  const n = res.nombres;
  switch (p.tipo) {
    case "planteamiento": {
      const filas = i.datos.map((f, k) =>
        `\\text{${MACROS[k]}}\\qquad & ${texNum(f[0], 2)}\\,x_1 + ${texNum(f[1], 2)}\\,x_2 + ${texNum(f[2], 2)}\\,x_3 = ${texNum(f[3], 2)}`).join(" \\\\ ");
      return `<p>Sean x₁, x₂ y x₃ las porciones de cada alimento, en unidades de 100 g. Cada nutriente da una ecuación, porque la suma de lo que aportan los tres alimentos debe dar la meta:</p>
        <div class="formula">${tex(`\\begin{array}{rl} ${filas} \\end{array}`, true)}</div>
        <p>x₁ = ${esc(n[0])}, x₂ = ${esc(n[1])} y x₃ = ${esc(n[2])}.</p>`;
    }
    case "buscar_pivote": {
      const lista = i.valores.map(([f, v]) => (f === i.mejor ? `\\mathbf{|${texNum(v)}|}` : `|${texNum(v)}|`)).join(",\\quad ");
      const extra = i.mejor === i.desde
        ? "Ya está en la fila que le corresponde, así que no hace falta intercambiar."
        : `Está en la fila F${sub(i.mejor + 1)}: se intercambia con la fila F${sub(i.desde + 1)}.`;
      return `<p><strong>Pivoteo parcial.</strong> Comparamos los valores absolutos de la columna ${i.col + 1}, desde la fila F${sub(i.desde + 1)} hacia abajo:</p>
        <div class="formula">${tex(lista, true)}</div>
        <p>El mayor será el pivote. ${extra}</p>`;
    }
    case "intercambio":
      return `<p>Intercambiamos F${sub(i.a + 1)} y F${sub(i.b + 1)} para que el pivote de mayor valor absoluto quede en la diagonal. Así nunca dividimos por un número pequeño y se reducen los errores de redondeo.</p>`;
    case "eliminacion": {
      const r = i.fila + 1, q = i.fila_pivote + 1, c = i.col + 1;
      const [a, piv, m] = estado.exacto
        ? [texFrac(i.a_i_exacta), texFrac(i.pivote_exacta), texFrac(i.m_exacta)]
        : [texNum(i.a_i), texNum(i.pivote), texNum(i.m)];
      return `<p>Calculamos el multiplicador con el elemento que queremos anular y el pivote:</p>
        <div class="formula">${tex(`m = \\frac{a_{${r}${c}}}{a_{${q}${c}}} = \\frac{${a}}{${piv}} = ${m}`, true)}</div>
        <p>Restamos m veces la fila pivote F${sub(q)} a la fila F${sub(r)}, y en la columna ${c} queda un cero.</p>`;
    }
    case "sin_pivote":
      return `<p>Todos los valores de la columna ${i.col + 1}, desde la fila F${sub(i.desde + 1)}, son cero. No hay nada que eliminar y se pasa a la siguiente columna.</p>`;
    case "triangular":
      return `<p>Todos los elementos debajo de la diagonal son cero: la matriz es triangular superior. Ahora se puede clasificar el sistema y despejar las incógnitas de la última fila hacia la primera.</p>`;
    case "clasificacion": {
      const etiqueta = { determinado: ["ok", "Solución única"], indeterminado: ["mal", "Infinitas soluciones"], incompatible: ["mal", "Sin solución"] }[i.sistema];
      const texto = {
        determinado: "Los dos rangos son 3, igual al número de incógnitas, así que el sistema tiene una única solución (teorema de Rouché–Frobenius).",
        indeterminado: "Los rangos son iguales pero menores que 3: hay infinitas soluciones. Dos alimentos aportan los nutrientes en la misma proporción, así que son redundantes.",
        incompatible: "El rango de A es menor que el de la matriz aumentada: aparece una fila del tipo 0 = número distinto de cero, y ninguna combinación de porciones cumple las metas.",
      }[i.sistema];
      return `<p>El rango es el número de filas no nulas de la matriz escalonada.</p>
        <div class="formula">${tex(`\\operatorname{rango}(A) = ${i.rango_a} \\qquad \\operatorname{rango}([A\\,|\\,B]) = ${i.rango_ab}`, true)}</div>
        <p><span class="etiqueta-sistema ${etiqueta[0]}">${etiqueta[1]}</span> ${texto}</p>`;
    }
    case "sustitucion": {
      const x = `x_${i.i + 1}`;
      const restas = i.terminos.map(([j, a, v]) => ` - (${texNum(a)})(${texNum(v)})`).join("");
      const valor = estado.exacto ? `${texFrac(i.x_exacta)} \\approx ${texNum(i.x)}` : texNum(i.x);
      const formula = i.terminos.length
        ? `${x} = \\frac{${texNum(i.b)}${restas}}{${texNum(i.a_ii)}} = ${valor}`
        : `${x} = \\frac{${texNum(i.b)}}{${texNum(i.a_ii)}} = ${valor}`;
      return `<p>Despejamos x${sub(i.i + 1)} de la fila F${sub(i.i + 1)}${i.terminos.length ? ", usando los valores que ya encontramos" : ""}:</p>
        <div class="formula">${tex(formula, true)}</div>
        <p>Es decir, <strong>${gramos(i.gramos)} g de ${esc(i.nombre)}</strong>.</p>`;
    }
    case "verificacion": {
      const exacto = i.filas.every((f) => f.exacto);
      return `<p>Reemplazamos x₁, x₂ y x₃ en las ecuaciones originales y comparamos con las metas.${exacto ? " Como el motor trabaja con fracciones exactas, las tres metas se cumplen sin ningún error de redondeo." : ""}</p>`;
    }
    default: {
      const info = i;
      if (info.sistema !== "determinado")
        return `<p>Las metas no se pueden cumplir de forma única con estos tres alimentos. Reemplaza uno de ellos por otro con un perfil nutricional distinto.</p>`;
      return info.factible
        ? `<p>La comida es posible: todas las porciones son positivas. En total tiene ${Math.round(info.kcal)} kcal (4 kcal por gramo de proteína y de carbohidrato, 9 por gramo de grasa).</p>`
        : `<p>La comida no es posible: hay porciones negativas, y una porción negativa no se puede servir. Cambia uno de los alimentos o ajusta las metas.</p>`;
    }
  }
}

function htmlVerificacion(filas) {
  return `<div class="verif">${filas.map((f, k) => {
    const ancho = f.meta > 0 ? Math.max(0, Math.min(100, (f.obtenido / f.meta) * 100)) : 100;
    return `<div class="verif-fila" style="--c:${COLOR[k]}">
        <span class="verif-nombre">${f.macro}</span>
        <span class="verif-barra" role="img" aria-label="${num(ancho, 1)} % de la meta"><b style="width:${ancho}%"></b></span>
        <span class="verif-valor">${num(f.obtenido)} g<small>meta: ${num(f.meta, 2)} g${f.exacto ? ", exacta" : ""}</small></span>
      </div>`;
  }).join("")}</div>`;
}

function htmlPorciones() {
  const r = estado.res;
  return `<div class="porciones">${r.sol.map((s, j) => `
      <div class="porcion">
        <span class="porcion-var">${tex(`x_${j + 1}`)}</span>
        <span class="porcion-gramos${s < 0 ? " negativo" : ""}">${gramos(s * 100)}<small>g</small></span>
        <p class="porcion-nombre">${r.factible ? `<span style="display:inline-block;width:.7rem;height:.7rem;border-radius:3px;margin-right:.4rem;background:${TONOS_PLATO[j]}"></span>` : ""}${esc(r.nombres[j])}</p>
        <p class="porcion-detalle">${num(s)} porciones de 100 g</p>
      </div>`).join("")}</div>`;
}

function htmlResumenFinal() {
  const r = estado.res;
  if (!r.sol) {
    return `<div class="verif"><p class="res-estado mal">${r.tipo === "incompatible" ? "Sistema incompatible: no tiene solución" : "Sistema indeterminado: infinitas soluciones"}</p></div>`;
  }
  return htmlPorciones();
}

// ---------- 3. resultado ----------
function renderResultado() {
  const r = estado.res, n = r.nombres;
  let estadoTxt, clase, titulo, texto;
  if (r.tipo === "determinado" && r.factible) {
    [clase, estadoTxt] = ["ok", "La comida es posible"];
    titulo = `Sirve ${gramos(r.sol[0] * 100)} g de ${n[0].toLowerCase()}, ${gramos(r.sol[1] * 100)} g de ${n[1].toLowerCase()} y ${gramos(r.sol[2] * 100)} g de ${n[2].toLowerCase()}.`;
    texto = `Con esas porciones la comida tiene exactamente ${num(r.datos[0][3], 2)} g de proteína, ${num(r.datos[1][3], 2)} g de carbohidratos y ${num(r.datos[2][3], 2)} g de grasa.`;
  } else if (r.tipo === "determinado") {
    [clase, estadoTxt] = ["mal", "La comida no es posible"];
    const neg = r.sol.map((s, j) => (s < 0 ? `${gramos(s * 100)} g de ${n[j].toLowerCase()}` : null)).filter(Boolean);
    titulo = `Habría que servir ${neg.join(" y ")}.`;
    texto = "El sistema tiene solución única, pero una porción negativa no se puede servir. Cambia uno de los alimentos o ajusta las metas.";
  } else if (r.tipo === "incompatible") {
    [clase, estadoTxt] = ["mal", "Sistema incompatible"];
    titulo = "Ninguna combinación de estos tres alimentos cumple las metas.";
    texto = "Al escalonar la matriz aparece una fila del tipo 0 = número distinto de cero. Reemplaza uno de los alimentos por otro con un perfil nutricional distinto.";
  } else {
    [clase, estadoTxt] = ["mal", "Sistema indeterminado"];
    titulo = "Hay infinitas combinaciones posibles.";
    texto = "Dos de los alimentos aportan los nutrientes en la misma proporción, así que son redundantes. Cambia uno de ellos para obtener una única respuesta.";
  }
  let h = `<p class="res-estado ${clase}">${estadoTxt}</p>
    <h2 class="res-titulo">${esc(titulo)}</h2>
    <p class="res-texto">${texto}</p>`;
  if (r.sol) {
    h += htmlPorciones();
    if (r.factible) {
      const total = r.sol.reduce((a, s) => a + s, 0);
      h += `<div class="plato" aria-label="Proporción de cada alimento en el plato"><div class="plato-barra">${r.sol.map((s, j) =>
        `<span style="width:${(s / total) * 100}%;background:${TONOS_PLATO[j]}" title="${esc(n[j])}"></span>`).join("")}</div></div>`;
    }
  }
  const metas = r.datos.map((f) => f[3]);
  h += `<div class="res-columnas">`;
  if (r.verificacion) {
    h += `<div><h3>Nutrientes de la comida</h3>${htmlVerificacion(r.verificacion)}</div>`;
  } else {
    h += `<div><h3>Por qué no hay respuesta única</h3><p class="res-texto" style="margin-top:0">Repasa el paso de clasificación: allí se comparan rango(A) y rango([A | B]).</p></div>`;
  }
  h += `<div class="energia"><h3>Energía de las metas</h3>
      <p class="energia-total">${Math.round(r.kcal)} <small>kcal</small></p>
      <ul>${MACROS.map((m, k) => `<li>${m}: ${num(metas[k], 2)} g × ${[4, 4, 9][k]}<b>${Math.round(metas[k] * [4, 4, 9][k])} kcal</b></li>`).join("")}</ul>
    </div></div>`;
  h += `<div class="res-acciones">
      <button class="boton boton-principal" data-ir="planos">Ver los planos en 3D</button>
      <button class="boton" data-ir="resolver">Repasar el paso a paso</button>
      <button class="boton boton-texto" data-ir="plantear">Cambiar alimentos o metas</button>
    </div>`;
  $("#vista-resultado").innerHTML = h;
}

// ---------- 4. planos en 3D ----------
function renderPlanos() {
  const r = estado.res;
  const g = r.sol ? r.sol.map((s) => s * 100) : null;
  let lo = 0, hi = 400;
  if (g) {
    hi = Math.max(250, Math.max(...g.map(Math.abs)) * 1.45);
    lo = Math.min(0, Math.min(...g) * 1.35);
  }
  const N = 32, paso = (hi - lo) / (N - 1);
  const ejes = Array.from({ length: N }, (_, t) => lo + t * paso);
  const trazas = r.datos.map((fila, k) => {
    const c = fila.slice(0, 3).map((v) => v / 100); // gramos de nutriente por gramo de alimento
    const d = fila[3];
    const kk = [0, 1, 2].reduce((a, b) => (Math.abs(c[b]) > Math.abs(c[a]) ? b : a), 0);
    const [o1, o2] = [0, 1, 2].filter((x) => x !== kk);
    const U = ejes.map(() => ejes.slice());
    const V = ejes.map((v) => ejes.map(() => v));
    const W = U.map((fu, a) => fu.map((u, b) => {
      const w = (d - c[o1] * u - c[o2] * V[a][b]) / c[kk];
      return w < lo - paso || w > hi + paso ? null : w;
    }));
    const A = []; A[o1] = U; A[o2] = V; A[kk] = W;
    return {
      type: "surface", x: A[0], y: A[1], z: A[2], name: MACROS[k],
      surfacecolor: W.map((f) => f.map(() => 0)), colorscale: [[0, COLOR_HEX[k]], [1, COLOR_HEX[k]]],
      showscale: false, opacity: 0.62, hovertemplate: `${MACROS[k]}<extra></extra>`,
      contours: { x: { highlight: false }, y: { highlight: false }, z: { highlight: false } },
      lighting: { ambient: 0.85, diffuse: 0.3, specular: 0.05 },
    };
  });
  if (g) {
    trazas.push({
      type: "scatter3d", mode: "markers+text", x: [g[0]], y: [g[1]], z: [g[2]],
      marker: { size: 7, color: "#12203B", symbol: "diamond" }, text: ["Solución"], textposition: "top center",
      textfont: { family: "Bricolage Grotesque, sans-serif", size: 14, color: "#12203B" },
      hovertemplate: `${esc(r.nombres[0])}: %{x:.1f} g<br>${esc(r.nombres[1])}: %{y:.1f} g<br>${esc(r.nombres[2])}: %{z:.1f} g<extra></extra>`,
    });
  }
  const eje = (t) => ({
    title: { text: `${t} (g)`, font: { size: 13 } }, range: [lo, hi], backgroundcolor: "#F7F9FC",
    gridcolor: "#DCE4EF", zerolinecolor: "#8C99B0", showbackground: true, tickfont: { size: 11 },
  });
  const layout = {
    margin: { l: 0, r: 0, t: 0, b: 0 }, paper_bgcolor: "rgba(0,0,0,0)", showlegend: false,
    font: { family: "Bricolage Grotesque, Helvetica Neue, sans-serif", color: "#12203B" },
    scene: {
      xaxis: eje(r.nombres[0]), yaxis: eje(r.nombres[1]), zaxis: eje(r.nombres[2]),
      aspectmode: "cube", camera: { eye: { x: 1.62, y: 1.52, z: 0.98 } },
    },
  };
  window.Plotly.react("grafico", trazas, layout, {
    responsive: true, displaylogo: false,
    modeBarButtonsToRemove: ["toImage", "resetCameraLastSave3d", "hoverClosest3d"],
  });
  $("#planos-leyenda").innerHTML = r.datos.map((f, k) =>
    `<li><i style="background:${COLOR_HEX[k]}"></i><span><strong>${MACROS[k]}</strong><br>${tex(`${texNum(f[0], 2)}x_1 + ${texNum(f[1], 2)}x_2 + ${texNum(f[2], 2)}x_3 = ${texNum(f[3], 2)}`)}</span></li>`).join("") +
    (g ? `<li><i style="background:#12203B;transform:rotate(45deg) scale(.75)"></i><span><strong>Solución</strong><br>${gramos(g[0])} g, ${gramos(g[1])} g y ${gramos(g[2])} g</span></li>`
       : `<li><i style="background:transparent"></i><span>Los planos no se cortan en un único punto: el sistema no tiene solución única.</span></li>`);
}

// ---------- navegación ----------
function irVista(v) {
  estado.vista = v;
  $$(".vista").forEach((s) => (s.hidden = s.dataset.vista !== v));
  $$(".pestana").forEach((b) => b.toggleAttribute("aria-current", b.dataset.vista === v));
  $$(".pestana").forEach((b) => b.dataset.vista === v && b.setAttribute("aria-current", "page"));
  window.scrollTo({ top: 0 });
  if (v === "resolver") renderPaso();
  if (v === "resultado") renderResultado();
  if (v === "planos") requestAnimationFrame(renderPlanos);
}

function cargarEjemplo() {
  estado.eleccion = [...EJEMPLO.nombres];
  estado.metas = [...EJEMPLO.metas];
  invalidar();
  aviso("");
  renderEcuacion();
}

// ---------- alimento propio ----------
let columnaDialogo = 0;
function abrirDialogo(j) {
  columnaDialogo = j;
  const f = $("#form-alimento");
  f.reset();
  aviso("", $("#aviso-alimento"));
  $("#dialogo-alimento").showModal();
}

$("#form-alimento").addEventListener("submit", (e) => {
  const boton = e.submitter;
  if (!boton || boton.value !== "guardar") { renderEcuacion(); return; }
  const f = new FormData(e.target);
  const nombre = String(f.get("nombre")).trim();
  const valores = CLAVES.map((c) => leerNumero(f.get(c)));
  let error = "";
  if (!nombre) error = "Escribe el nombre del alimento.";
  else if (estado.catalogo.some((a) => a.nombre.toLowerCase() === nombre.toLowerCase())) error = "Ya hay un alimento con ese nombre.";
  else if (valores.some((v) => !(v >= 0 && v <= 100))) error = "Cada nutriente debe ser un número entre 0 y 100 g.";
  else if (valores[0] + valores[1] + valores[2] > 100) error = "La suma de los tres nutrientes no puede pasar de 100 g.";
  if (error) { e.preventDefault(); aviso(error, $("#aviso-alimento")); return; }
  estado.catalogo.push({ nombre, proteina: valores[0], carbohidratos: valores[1], grasa: valores[2], propio: true });
  estado.eleccion[columnaDialogo] = nombre;
  invalidar();
  renderEcuacion();
});
$("#dialogo-alimento").addEventListener("cancel", () => setTimeout(renderEcuacion));

// ---------- eventos ----------
$("#ecuacion").addEventListener("change", (e) => {
  const sel = e.target.closest("select");
  if (!sel) return;
  const j = +sel.dataset.j;
  if (sel.value === OTRO) { abrirDialogo(j); return; }
  estado.eleccion[j] = sel.value;
  invalidar();
  aviso("");
  renderEcuacion();
});
$("#ecuacion").addEventListener("input", (e) => {
  const inp = e.target.closest("input[data-k]");
  if (!inp) return;
  estado.metas[+inp.dataset.k] = inp.value;
  invalidar();
  actualizarEnergiaMetas();
});
$("#ecuacion").addEventListener("keydown", (e) => {
  if (e.key === "Enter" && e.target.matches("input[data-k]")) resolver();
});
$("#btn-resolver").addEventListener("click", resolver);
$("#btn-ejemplo").addEventListener("click", cargarEjemplo);
$("#btn-anterior").addEventListener("click", () => irPaso(estado.paso - 1));
$("#btn-siguiente").addEventListener("click", () => {
  if (estado.paso === estado.res.pasos.length - 1) irVista("resultado");
  else irPaso(estado.paso + 1);
});
$("#riel").addEventListener("click", (e) => {
  const b = e.target.closest(".riel-paso");
  if (b) irPaso(+b.dataset.k);
});
$$(".interruptor-op").forEach((b) => b.addEventListener("click", () => {
  estado.exacto = b.dataset.exacto === "true";
  estado.anterior = -1;
  renderPaso();
}));
$$(".pestana").forEach((b) => b.addEventListener("click", () => irVista(b.dataset.vista)));
$("#vista-resultado").addEventListener("click", (e) => {
  const b = e.target.closest("[data-ir]");
  if (b) irVista(b.dataset.ir);
});
document.addEventListener("keydown", (e) => {
  if (estado.vista !== "resolver" || !estado.res) return;
  if (e.target.closest("input, select, textarea, dialog")) return;
  const total = estado.res.pasos.length;
  const destino = { ArrowRight: estado.paso + 1, ArrowLeft: estado.paso - 1, Home: 0, End: total - 1 }[e.key];
  if (destino === undefined) return;
  e.preventDefault();
  irPaso(destino);
});

// Si cambia el tamaño de la ventana, se recolocan las anotaciones del margen
let esperaRedibujo;
window.addEventListener("resize", () => {
  clearTimeout(esperaRedibujo);
  esperaRedibujo = setTimeout(() => {
    if (estado.vista === "resolver" && estado.res) { estado.anterior = -1; renderPaso(); }
  }, 150);
});

// ---------- inicio ----------
async function iniciar() {
  try {
    const r = await fetch("/api/alimentos");
    const datos = await r.json();
    estado.catalogo = datos.alimentos;
  } catch {
    aviso("No hay conexión con el servidor. Abre la página ejecutando servidor.py y entrando a http://localhost:8000.");
    $("#btn-resolver").disabled = true;
  }
  renderEcuacion();
}

if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", iniciar);
else iniciar();
