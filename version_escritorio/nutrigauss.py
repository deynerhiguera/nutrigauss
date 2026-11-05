"""
NutriGauss - Planificador de porciones por macronutrientes
==========================================================
Aplicación de escritorio en Python (tkinter) que resuelve un sistema 3x3 con el
método de eliminación de Gauss con pivoteo parcial, programado por el grupo.

Qué hace:
  1. El usuario elige 3 alimentos de una lista (la composición ya está cargada).
  2. Ingresa las metas de la comida en gramos (proteína, carbohidratos, grasa).
  3. El programa plantea el sistema, resuelve paso a paso, clasifica el sistema
     por rangos, hace la sustitución regresiva, verifica y valida el resultado.
  4. Muestra los tres planos en 3D con el punto solución (opcional).

Autores: Sebastian Mantilla Piñeres, Deyner Santiago Higuera Cardenas y
         Jeins Schneider Suarez Godoy. Álgebra Lineal, UDES.

Cómo ejecutar:   python3 nutrigauss.py      (Windows: python nutrigauss.py)
Gráfico 3D:      pip install matplotlib numpy   (opcional)
"""
import sys
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from fractions import Fraction  # números exactos: sin errores de redondeo

# ------------------------------------------------------------
# DATOS: (nombre, proteína, carbohidratos, grasa) por cada 100 g
# Valores aproximados tomados de FoodData Central (USDA).
# ------------------------------------------------------------
ALIMENTOS = [
    ("Arroz blanco cocido", 2.7, 28.2, 0.3),
    ("Pechuga de pollo cocida", 31.0, 0.0, 3.6),
    ("Aguacate", 2.0, 8.5, 14.7),
    ("Huevo cocido", 12.6, 1.1, 10.6),
    ("Atún en agua", 25.5, 0.0, 0.8),
    ("Salmón cocido", 22.1, 0.0, 12.4),
    ("Carne de res magra cocida", 26.0, 0.0, 9.0),
    ("Papa cocida", 1.9, 20.1, 0.1),
    ("Pasta cocida", 5.8, 30.9, 0.9),
    ("Yuca cocida", 1.4, 38.1, 0.3),
    ("Frijoles negros cocidos", 8.9, 23.7, 0.5),
    ("Lentejas cocidas", 9.0, 20.1, 0.4),
    ("Plátano maduro", 1.1, 22.8, 0.3),
    ("Avena cocida", 2.5, 12.0, 1.5),
    ("Leche entera", 3.2, 4.8, 3.3),
    ("Almendras", 21.2, 21.7, 49.9),
    ("Aceite de oliva", 0.0, 0.0, 100.0),
]
MACROS = ("Proteína", "Carbohidratos", "Grasa")
OTRO = "Otro alimento (ingresar valores)..."


# ------------------------------------------------------------
# MOTOR DE GAUSS (genera la lista de pasos que se muestra en pantalla)
# ------------------------------------------------------------
def resolver(alimentos, metas):
    """Resuelve A·X = B y devuelve todos los pasos explicados."""
    nombres = [a[0] for a in alimentos]
    # Cada columna es un alimento; cada fila, un macronutriente
    datos = [[a[k] for a in alimentos] + [metas[k - 1]] for k in (1, 2, 3)]
    A = [[Fraction(str(v)) for v in fila] for fila in datos]
    n = 3
    pasos = []

    def snap():
        return [[float(x) for x in fila] for fila in A]

    def add(titulo, texto, mat=True, filas=None, celda=None):
        pasos.append(dict(titulo=titulo, texto=texto, mat=snap() if mat else None,
                          filas=filas or {}, celda=celda))

    # --- Paso 1: planteamiento ---
    variables = "\n".join(f"   x{i+1} = porciones de 100 g de {nombres[i]}" for i in range(n))
    ecuaciones = "\n".join(
        f"   {MACROS[k]:<14}: {datos[k][0]}·x1 + {datos[k][1]}·x2 + {datos[k][2]}·x3 = {datos[k][3]}"
        for k in range(n))
    add("Planteamiento del sistema de ecuaciones",
        f"Sean x1, x2 y x3 las porciones de cada alimento, en unidades de 100 g:\n{variables}\n\n"
        f"Cada alimento aporta los tres nutrientes, así que hay una ecuación por nutriente "
        f"(la suma debe dar la meta):\n{ecuaciones}\n\n"
        f"Matriz aumentada [A | B]: filas = nutrientes, columnas = alimentos, B = metas.")

    # --- Eliminación de Gauss con pivoteo parcial ---
    fila_act = 0
    for col in range(n):
        if fila_act >= n:
            break
        valores = ",  ".join(f"F{i+1}: {abs(float(A[i][col])):.4f}" for i in range(fila_act, n))
        mejor = max(range(fila_act, n), key=lambda i: abs(A[i][col]))
        if A[mejor][col] == 0:
            add(f"Columna {col+1}: no hay pivote",
                f"Todos los valores de la columna {col+1} (desde la fila {fila_act+1}) son cero. "
                f"No se puede eliminar; se pasa a la siguiente columna.")
            continue
        extra = ("Ya está en la fila actual: no hace falta intercambiar."
                 if mejor == fila_act else
                 f"Está en la fila {mejor+1}: se intercambiará con la fila {fila_act+1}.")
        add(f"Columna {col+1}: buscar el pivote",
            f"Pivoteo parcial: se compara el valor absoluto de la columna {col+1}, desde la fila {fila_act+1} hacia abajo.\n"
            f"   {valores}\nEl mayor es {abs(float(A[mejor][col])):.4f} (fila {mejor+1}) y será el pivote.\n{extra}",
            filas={mejor: "piv_fila"}, celda=(mejor, col))
        if mejor != fila_act:
            A[fila_act], A[mejor] = A[mejor], A[fila_act]
            add(f"Intercambio de filas: F{fila_act+1} <-> F{mejor+1}",
                "Se coloca el pivote de mayor valor absoluto en la posición correcta. "
                "Esto evita dividir por números pequeños y reduce los errores de redondeo.",
                filas={fila_act: "swap_fila", mejor: "swap_fila"}, celda=(fila_act, col))
        pivote = A[fila_act][col]
        for i in range(fila_act + 1, n):
            if A[i][col] == 0:
                continue
            a_i = A[i][col]
            m = a_i / pivote
            A[i] = [x - m * y for x, y in zip(A[i], A[fila_act])]
            add(f"Eliminación: F{i+1} = F{i+1} − ({float(m):.4f})·F{fila_act+1}",
                f"Multiplicador: m = {float(a_i):.4f} / {float(pivote):.4f} = {float(m):.4f}\n"
                f"Se resta m veces la fila pivote (F{fila_act+1}) a la fila F{i+1} "
                f"para dejar un cero en la columna {col+1}.",
                filas={fila_act: "piv_fila", i: "mod_fila"}, celda=(fila_act, col))
        fila_act += 1

    add("Matriz triangular superior",
        "Todos los elementos debajo de la diagonal son cero. "
        "Ahora las incógnitas se pueden despejar de la última fila hacia la primera.")

    # --- Clasificación por rangos (Rouché–Frobenius) ---
    rango_a = sum(1 for f in A if any(x != 0 for x in f[:3]))
    rango_ab = sum(1 for f in A if any(x != 0 for x in f))
    base = (f"rango(A) = {rango_a}  (filas no nulas de los coeficientes)\n"
            f"rango([A | B]) = {rango_ab}  (filas no nulas incluyendo las metas)\n\n")
    if rango_a < rango_ab:
        tipo = "incompatible"
        add("Clasificación: sistema INCOMPATIBLE",
            base + "rango(A) < rango([A | B]): hay una fila del tipo 0 = número distinto de cero.\n"
                   "No existe ninguna combinación de porciones que cumpla las metas.")
    elif rango_a < 3:
        tipo = "indeterminado"
        add("Clasificación: sistema INDETERMINADO",
            base + "Los rangos son iguales pero menores que 3: hay infinitas soluciones.\n"
                   "Dos alimentos aportan nutrientes de forma redundante (proporcional).")
    else:
        tipo = "determinado"
        add("Clasificación: sistema COMPATIBLE DETERMINADO",
            base + "Ambos rangos son 3: el sistema tiene solución única.")

    sol, kcal = None, 4 * metas[0] + 4 * metas[1] + 9 * metas[2]
    if tipo == "determinado":
        # --- Sustitución regresiva ---
        x = [Fraction(0)] * 3
        for i in (2, 1, 0):
            suma = sum(A[i][j] * x[j] for j in range(i + 1, 3))
            x[i] = (A[i][3] - suma) / A[i][i]
            if i == 2:
                f = f"x3 = {float(A[i][3]):.4f} / {float(A[i][i]):.4f}"
            else:
                restas = " − ".join(f"({float(A[i][j]):.4f})({float(x[j]):.4f})" for j in range(i + 1, 3))
                f = f"x{i+1} = ({float(A[i][3]):.4f} − {restas}) / {float(A[i][i]):.4f}"
            add(f"Sustitución regresiva: x{i+1}",
                f"Se despeja desde la última fila hacia la primera.\n   {f} = {float(x[i]):.4f}\n"
                f"   Es decir, {float(x[i]) * 100:.1f} g de {nombres[i]}.",
                filas={i: "piv_fila"})
        sol = [float(v) for v in x]
        # --- Verificación ---
        lineas = []
        for k in range(n):
            total = sum(Fraction(str(datos[k][j])) * x[j] for j in range(3))
            lineas.append(f"   {MACROS[k]:<14}: obtenido {float(total):8.4f} g    meta {datos[k][3]} g")
        add("Verificación", "Se reemplazan x1, x2 y x3 en las ecuaciones originales:\n" + "\n".join(lineas),
            mat=False)

    # --- Resultado final ---
    if tipo == "determinado":
        factible = all(v >= 0 for v in sol)
        porciones = "\n".join(f"   {nombres[i]:<28}{sol[i] * 100:8.1f} g" for i in range(n))
        estado = ("La comida es FACTIBLE: todas las porciones son positivas." if factible else
                  "La comida NO es factible: hay porciones negativas. Cambie algún alimento o las metas.")
        add("Resultado final", f"Cantidad que debe servir de cada alimento:\n{porciones}\n\n{estado}\n"
            f"Energía total: {kcal:.0f} kcal  (4 kcal/g de proteína y carbohidrato, 9 kcal/g de grasa)", mat=False)
    else:
        add("Resultado final",
            "Las metas no se pueden cumplir de forma única con estos tres alimentos.\n"
            "Sugerencia: reemplace uno de los alimentos por otro con un perfil nutricional distinto.", mat=False)
    return dict(pasos=pasos, tipo=tipo, sol=sol, kcal=kcal, datos=datos, nombres=nombres)


# ------------------------------------------------------------
# INTERFAZ GRÁFICA
# ------------------------------------------------------------
def fuente_ui():
    """Fuente de la interfaz: Segoe UI en Windows y la equivalente en Mac/Linux."""
    from tkinter import font
    fams = set(font.families())
    for f in ("Segoe UI", "Helvetica Neue", "SF Pro Text", "DejaVu Sans", "Arial"):
        if f in fams:
            return f
    return "TkDefaultFont"


def fuente_mono():
    from tkinter import font
    fams = set(font.families())
    for f in ("Consolas", "Menlo", "DejaVu Sans Mono", "Courier New"):
        if f in fams:
            return f
    return "Courier"


class App:
    def __init__(self, root):
        self.root = root
        root.title("NutriGauss - Planificador de porciones con eliminación de Gauss")
        root.geometry("1280x780")
        root.minsize(1100, 700)
        self.alimentos = list(ALIMENTOS)
        self.res = None
        self.idx = 0
        if sys.platform == "darwin":
            # En Mac, tkinter calcula los puntos a 72 ppp y todo se ve pequeño;
            # con este factor los tamaños quedan iguales a los de Windows.
            root.tk.call("tk", "scaling", 1.3333)
            try:  # ventana en modo claro aunque el Mac esté en modo oscuro
                root.tk.call("::tk::unsupported::MacWindowStyle", "appearance", root._w, "aqua")
            except tk.TclError:
                pass
        self.ui = fuente_ui()
        self.mono = fuente_mono()
        ttk.Style().configure("TButton", font=(self.ui, 11), padding=5)
        self.construir()
        self.ejemplo()
        for tecla, f in (("<Right>", self.siguiente), ("<Left>", self.anterior),
                         ("<Home>", self.inicio), ("<End>", self.final)):
            root.bind(tecla, lambda e, f=f: None if isinstance(e.widget, (tk.Entry, ttk.Entry)) else f())

    # ---------- construcción de la ventana ----------
    def construir(self):
        r = self.root
        r.columnconfigure(1, weight=1)
        r.rowconfigure(0, weight=1)
        izq = ttk.Frame(r, padding=12)
        izq.grid(row=0, column=0, sticky="ns")
        der = ttk.Frame(r, padding=(0, 12, 12, 12))
        der.grid(row=0, column=1, sticky="nsew")

        tk.Label(izq, text="NutriGauss", font=(self.ui, 20, "bold"), fg="#1f4e79").pack(anchor="w")
        tk.Label(izq, text="Porciones por macronutrientes\ncon eliminación de Gauss", font=(self.ui, 10),
                 justify="left", fg="#555").pack(anchor="w", pady=(0, 10))

        caja = ttk.LabelFrame(izq, text=" 1. Elija 3 alimentos ", padding=8)
        caja.pack(fill="x")
        self.combos, self.info = [], []
        for i in range(3):
            tk.Label(caja, text=f"Alimento x{i+1}", font=(self.ui, 10, "bold")).pack(anchor="w")
            c = ttk.Combobox(caja, state="readonly", width=34, font=(self.ui, 11))
            c.pack(fill="x")
            c.bind("<<ComboboxSelected>>", lambda e, i=i: self.al_elegir(i))
            lbl = tk.Label(caja, text="", font=(self.ui, 9), fg="#555")
            lbl.pack(anchor="w", pady=(0, 6))
            self.combos.append(c)
            self.info.append(lbl)
        self.refrescar_valores()

        metas = ttk.LabelFrame(izq, text=" 2. Metas de la comida (gramos) ", padding=8)
        metas.pack(fill="x", pady=10)
        self.metas = []
        for m in MACROS:
            fila = ttk.Frame(metas)
            fila.pack(fill="x", pady=2)
            tk.Label(fila, text=m, width=14, anchor="w", font=(self.ui, 11)).pack(side="left")
            v = tk.StringVar()
            ttk.Entry(fila, textvariable=v, width=10, font=(self.ui, 11)).pack(side="left")
            self.metas.append(v)

        ttk.Button(izq, text="Resolver con Gauss", command=self.resolver).pack(fill="x", pady=(4, 3))
        ttk.Button(izq, text="Ver gráfico 3D", command=self.grafico).pack(fill="x", pady=3)
        ttk.Button(izq, text="Cargar ejemplo del documento", command=self.ejemplo).pack(fill="x", pady=3)
        tk.Label(izq, text="Teclas: ← → para cambiar de paso\nInicio / Fin: primer y último paso"
                         + ("\n(en Mac: fn + ← / fn + →)" if sys.platform == "darwin" else ""),
                 font=(self.ui, 9), fg="#777", justify="left").pack(anchor="w", pady=(10, 0))

        # ----- panel derecho: paso a paso -----
        der.columnconfigure(0, weight=1)
        der.rowconfigure(1, weight=1)
        cab = ttk.Frame(der)
        cab.grid(row=0, column=0, sticky="ew")
        cab.columnconfigure(0, weight=1)
        self.lbl_titulo = tk.Label(cab, text="Elija los alimentos y pulse «Resolver con Gauss»",
                                   font=(self.ui, 17, "bold"), fg="#1f4e79", anchor="w")
        self.lbl_titulo.grid(row=0, column=0, sticky="w")
        self.lbl_paso = tk.Label(cab, text="", font=(self.ui, 12), fg="#555")
        self.lbl_paso.grid(row=0, column=1, sticky="e")

        centro = ttk.Frame(der)
        centro.grid(row=1, column=0, sticky="nsew", pady=8)
        centro.columnconfigure(0, weight=1)
        centro.rowconfigure(0, weight=3)
        centro.rowconfigure(2, weight=2)
        self.txt = tk.Text(centro, wrap="word", font=(self.ui, 13), height=9, relief="solid", bd=1,
                           padx=10, pady=8, state="disabled", bg="#fbfbfb")
        self.txt.grid(row=0, column=0, sticky="nsew")
        tk.Label(centro, text="Amarillo: fila pivote   |   Verde: fila modificada   |   "
                              "Naranja: filas intercambiadas   |   Dorado: pivote",
                 font=(self.ui, 9), fg="#777").grid(row=1, column=0, sticky="w", pady=(6, 2))
        self.mat = tk.Text(centro, font=(self.mono, 16), height=6, relief="solid", bd=1, padx=14, pady=8,
                           state="disabled", wrap="none", bg="white")
        self.mat.grid(row=2, column=0, sticky="nsew")
        for nombre, color in (("piv_fila", "#FFF2B3"), ("mod_fila", "#C9F0D3"), ("swap_fila", "#FFD9B3")):
            self.mat.tag_config(nombre, background=color)
        self.mat.tag_config("pivote", background="#FFC107", font=(self.mono, 16, "bold"))

        nav = ttk.Frame(der)
        nav.grid(row=2, column=0, sticky="ew")
        self.botones = {}
        for texto, f in (("|< Inicio", self.inicio), ("< Anterior", self.anterior),
                         ("Siguiente >", self.siguiente), ("Resultado >|", self.final)):
            b = ttk.Button(nav, text=texto, command=f)
            b.pack(side="left", padx=(0, 6))
            self.botones[texto] = b

        self.res_frame = tk.Frame(der, bg="#eaf2fb", highlightbackground="#9bbbe0", highlightthickness=1)
        self.res_frame.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        self.lbl_res = tk.Label(self.res_frame, text="Resultado: aún no se ha resuelto el sistema.",
                                font=(self.ui, 13, "bold"), bg="#eaf2fb", fg="#1f4e79",
                                justify="left", anchor="w", padx=12, pady=8)
        self.lbl_res.pack(fill="x")
        # el texto del resultado pasa a otra línea si no cabe (fuentes más anchas en Mac)
        self.res_frame.bind("<Configure>", lambda e: self.lbl_res.config(wraplength=e.width - 30))

    # ---------- alimentos y metas ----------
    def refrescar_valores(self):
        vals = [a[0] for a in self.alimentos] + [OTRO]
        for c in self.combos:
            c["values"] = vals

    def buscar(self, nombre):
        return next(a for a in self.alimentos if a[0] == nombre)

    def actualizar_info(self, i):
        a = self.buscar(self.combos[i].get())
        self.info[i].config(text=f"por 100 g:  proteína {a[1]}  |  carbohidratos {a[2]}  |  grasa {a[3]}")

    def al_elegir(self, i):
        if self.combos[i].get() == OTRO:
            nuevo = self.pedir_alimento()
            if nuevo is None:
                self.combos[i].set(getattr(self, "previo", [None] * 3)[i] or self.alimentos[i][0])
            else:
                self.alimentos.append(nuevo)
                self.refrescar_valores()
                self.combos[i].set(nuevo[0])
        self.previo = [c.get() for c in self.combos]
        self.actualizar_info(i)

    def pedir_alimento(self):
        nombre = simpledialog.askstring("Alimento propio", "Nombre del alimento:", parent=self.root)
        if not nombre:
            return None
        v = []
        for m in MACROS:
            x = simpledialog.askfloat("Alimento propio", f"Gramos de {m.lower()} por cada 100 g:",
                                      parent=self.root, minvalue=0.0, maxvalue=100.0)
            if x is None:
                return None
            v.append(x)
        return (nombre.strip(), *v)

    def ejemplo(self):
        for c, a in zip(self.combos, ALIMENTOS[:3]):
            c.set(a[0])
        for i in range(3):
            self.actualizar_info(i)
        for v, x in zip(self.metas, ("40", "60", "15")):
            v.set(x)
        self.previo = [c.get() for c in self.combos]

    # ---------- resolver ----------
    def resolver(self):
        elegidos = [self.buscar(c.get()) for c in self.combos]
        if len({a[0] for a in elegidos}) < 3:
            messagebox.showwarning("Alimentos repetidos", "Elija tres alimentos distintos.")
            return
        try:
            metas = [float(v.get().strip().replace(",", ".")) for v in self.metas]
            if any(m < 0 for m in metas):
                raise ValueError
        except ValueError:
            messagebox.showwarning("Metas no válidas", "Escriba números mayores o iguales a cero en las tres metas.")
            return
        self.res = resolver(elegidos, metas)
        self.idx = 0
        self.mostrar()
        self.mostrar_resultado()

    def mostrar_resultado(self):
        r = self.res
        if r["tipo"] == "determinado":
            partes = [f"{n}: {s * 100:.1f} g" for n, s in zip(r["nombres"], r["sol"])]
            ok = all(s >= 0 for s in r["sol"])
            estado = "Factible" if ok else "NO factible (porciones negativas)"
            txt = "Resultado:   " + "   |   ".join(partes) + f"\n{estado}   |   Energía total: {r['kcal']:.0f} kcal"
            color = "#1f4e79" if ok else "#b00020"
        else:
            txt = ("Resultado: sistema " + r["tipo"].upper() +
                   (" (sin solución)" if r["tipo"] == "incompatible" else " (infinitas soluciones)") +
                   "\nReemplace uno de los alimentos.")
            color = "#b00020"
        self.lbl_res.config(text=txt, fg=color)

    # ---------- pantalla paso a paso ----------
    def mostrar(self):
        if not self.res:
            return
        p = self.res["pasos"][self.idx]
        self.lbl_titulo.config(text=p["titulo"])
        self.lbl_paso.config(text=f"Paso {self.idx + 1} de {len(self.res['pasos'])}")
        for w, t in ((self.txt, p["texto"]),):
            w.config(state="normal")
            w.delete("1.0", "end")
            w.insert("1.0", t)
            w.config(state="disabled")
        self.mat.config(state="normal")
        self.mat.delete("1.0", "end")
        if p["mat"]:
            self.dibujar_matriz(p)
        self.mat.config(state="disabled")
        total = len(self.res["pasos"])
        self.botones["< Anterior"].state(["!disabled"] if self.idx > 0 else ["disabled"])
        self.botones["|< Inicio"].state(["!disabled"] if self.idx > 0 else ["disabled"])
        self.botones["Siguiente >"].state(["!disabled"] if self.idx < total - 1 else ["disabled"])
        self.botones["Resultado >|"].state(["!disabled"] if self.idx < total - 1 else ["disabled"])

    def dibujar_matriz(self, p):
        cab = "  " + "  ".join(f"x{j+1}".center(10) for j in range(3)) + "    " + "B (meta)".center(10) + "\n"
        self.mat.insert("end", cab)
        for i, fila in enumerate(p["mat"]):
            linea = "│ " + "  ".join(f"{v:10.4f}" for v in fila[:3]) + "  │ " + f"{fila[3]:10.4f}" + " │\n"
            self.mat.insert("end", linea)
            ln = i + 2
            if i in p["filas"]:
                self.mat.tag_add(p["filas"][i], f"{ln}.0", f"{ln}.end")
            if p["celda"] and p["celda"][0] == i:
                ini = 2 + p["celda"][1] * 12
                self.mat.tag_add("pivote", f"{ln}.{ini}", f"{ln}.{ini + 10}")

    def ir(self, k):
        if self.res:
            self.idx = max(0, min(len(self.res["pasos"]) - 1, k))
            self.mostrar()

    def anterior(self): self.ir(self.idx - 1)
    def siguiente(self): self.ir(self.idx + 1)
    def inicio(self): self.ir(0)
    def final(self): self.ir(len(self.res["pasos"]) - 1 if self.res else 0)

    # ---------- gráfico 3D ----------
    def grafico(self):
        if not self.res:
            messagebox.showinfo("Gráfico 3D", "Primero resuelva el sistema.")
            return
        try:
            import numpy as np
            from matplotlib.figure import Figure
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
        except ImportError:
            messagebox.showinfo("Falta instalar", "Para ver el gráfico 3D instale:\n\npip install matplotlib numpy")
            return
        datos, sol, nombres = self.res["datos"], self.res["sol"], self.res["nombres"]
        win = tk.Toplevel(self.root)
        win.title("Planos de cada macronutriente y su intersección")
        win.geometry("860x720")
        fig = Figure(figsize=(8, 6.4), dpi=100)
        ax = fig.add_subplot(projection="3d")
        maximo = max([4.0] + [abs(s) for s in (sol or [])]) + 0.5
        minimo = min([0.0] + list(sol or [])) - (0.5 if sol and min(sol) < 0 else 0)
        U, V = np.meshgrid(np.linspace(minimo, maximo, 25), np.linspace(minimo, maximo, 25))
        for fila, nom, col in zip(datos, MACROS, ("teal", "gold", "tomato")):
            coef, d = [float(v) for v in fila[:3]], float(fila[3])
            k = max(range(3), key=lambda j: abs(coef[j]))  # se despeja la variable de mayor coeficiente
            if coef[k] != 0:
                o1, o2 = [j for j in range(3) if j != k]
                W = (d - coef[o1] * U - coef[o2] * V) / coef[k]
                W[(W < minimo - 1) | (W > maximo)] = np.nan
                ejes = {o1: U, o2: V, k: W}
                ax.plot_surface(ejes[0], ejes[1], ejes[2], alpha=0.5, color=col)
            ax.plot([], [], color=col, label=nom)
        if sol:
            ax.scatter(*sol, color="black", s=70, label="Solución")
        ax.set_xlabel(f"x1 ({nombres[0]})")
        ax.set_ylabel(f"x2 ({nombres[1]})")
        ax.set_zlabel(f"x3 ({nombres[2]})")
        ax.legend()
        ax.set_title("Cada plano es un nutriente; la solución es donde se cortan")
        canvas = FigureCanvasTkAgg(fig, master=win)
        NavigationToolbar2Tk(canvas, win)
        canvas.get_tk_widget().pack(fill="both", expand=True)
        canvas.draw()


if __name__ == "__main__":
    ventana = tk.Tk()
    App(ventana)
    ventana.mainloop()
