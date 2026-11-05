"""
NutriGauss - Motor de eliminación de Gauss (backend)
====================================================
Resuelve el sistema 3x3 A·X = B con el método de eliminación de Gauss con
pivoteo parcial, programado por el grupo, y devuelve cada paso explicado.

Es la misma función resolver() del documento del proyecto. La única diferencia
es que cada paso trae, además del texto, sus datos ("info") y la matriz en
fracciones exactas, para que la página web pueda dibujarlo.

    Filas de A    -> macronutrientes (proteína, carbohidratos, grasa)
    Columnas de A -> los tres alimentos (gramos por cada 100 g)
    B             -> las metas de la comida en gramos
    x1, x2, x3    -> porciones de cada alimento en unidades de 100 g

Autores: Sebastian Mantilla Piñeres, Deyner Santiago Higuera Cardenas y
         Jeins Schneider Suarez Godoy. Álgebra Lineal, UDES.
"""
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
KCAL_POR_GRAMO = (4, 4, 9)  # factores generales de Atwater (FAO, 2003)


def fraccion_texto(x):
    """Fracción exacta como texto: '141/5', '-3' o '0'."""
    return str(x.numerator) if x.denominator == 1 else f"{x.numerator}/{x.denominator}"


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

    def snap_exacta():
        return [[fraccion_texto(x) for x in fila] for fila in A]

    def add(titulo, texto, mat=True, filas=None, celda=None, tipo="", info=None):
        pasos.append(dict(titulo=titulo, texto=texto, mat=snap() if mat else None,
                          mat_exacta=snap_exacta() if mat else None,
                          filas=filas or {}, celda=celda, tipo=tipo, info=info or {}))

    # --- Paso 1: planteamiento ---
    variables = "\n".join(f"   x{i+1} = porciones de 100 g de {nombres[i]}" for i in range(n))
    ecuaciones = "\n".join(
        f"   {MACROS[k]:<14}: {datos[k][0]}·x1 + {datos[k][1]}·x2 + {datos[k][2]}·x3 = {datos[k][3]}"
        for k in range(n))
    add("Planteamiento del sistema de ecuaciones",
        f"Sean x1, x2 y x3 las porciones de cada alimento, en unidades de 100 g:\n{variables}\n\n"
        f"Cada alimento aporta los tres nutrientes, así que hay una ecuación por nutriente "
        f"(la suma debe dar la meta):\n{ecuaciones}\n\n"
        f"Matriz aumentada [A | B]: filas = nutrientes, columnas = alimentos, B = metas.",
        tipo="planteamiento", info=dict(nombres=nombres, datos=datos))

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
                f"No se puede eliminar; se pasa a la siguiente columna.",
                tipo="sin_pivote", info=dict(col=col, desde=fila_act))
            continue
        extra = ("Ya está en la fila actual: no hace falta intercambiar."
                 if mejor == fila_act else
                 f"Está en la fila {mejor+1}: se intercambiará con la fila {fila_act+1}.")
        add(f"Columna {col+1}: buscar el pivote",
            f"Pivoteo parcial: se compara el valor absoluto de la columna {col+1}, desde la fila {fila_act+1} hacia abajo.\n"
            f"   {valores}\nEl mayor es {abs(float(A[mejor][col])):.4f} (fila {mejor+1}) y será el pivote.\n{extra}",
            filas={mejor: "piv_fila"}, celda=(mejor, col), tipo="buscar_pivote",
            info=dict(col=col, desde=fila_act, mejor=mejor,
                      valores=[[i, abs(float(A[i][col]))] for i in range(fila_act, n)]))
        if mejor != fila_act:
            A[fila_act], A[mejor] = A[mejor], A[fila_act]
            add(f"Intercambio de filas: F{fila_act+1} <-> F{mejor+1}",
                "Se coloca el pivote de mayor valor absoluto en la posición correcta. "
                "Esto evita dividir por números pequeños y reduce los errores de redondeo.",
                filas={fila_act: "swap_fila", mejor: "swap_fila"}, celda=(fila_act, col),
                tipo="intercambio", info=dict(a=fila_act, b=mejor, col=col))
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
                filas={fila_act: "piv_fila", i: "mod_fila"}, celda=(fila_act, col),
                tipo="eliminacion",
                info=dict(fila=i, fila_pivote=fila_act, col=col,
                          a_i=float(a_i), pivote=float(pivote), m=float(m),
                          a_i_exacta=fraccion_texto(a_i), pivote_exacta=fraccion_texto(pivote),
                          m_exacta=fraccion_texto(m)))
        fila_act += 1

    add("Matriz triangular superior",
        "Todos los elementos debajo de la diagonal son cero. "
        "Ahora las incógnitas se pueden despejar de la última fila hacia la primera.",
        tipo="triangular")

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
    pasos[-1]["tipo"] = "clasificacion"
    pasos[-1]["info"] = dict(rango_a=rango_a, rango_ab=rango_ab, sistema=tipo,
                             filas_nulas_a=[not any(x != 0 for x in f[:3]) for f in A],
                             filas_nulas_ab=[not any(x != 0 for x in f) for f in A])

    sol, kcal = None, 4 * metas[0] + 4 * metas[1] + 9 * metas[2]
    verificacion = None
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
                filas={i: "piv_fila"}, tipo="sustitucion",
                info=dict(i=i, b=float(A[i][3]), a_ii=float(A[i][i]),
                          terminos=[[j, float(A[i][j]), float(x[j])] for j in range(i + 1, 3)],
                          x=float(x[i]), x_exacta=fraccion_texto(x[i]), gramos=float(x[i]) * 100,
                          nombre=nombres[i]))
        sol = [float(v) for v in x]
        # --- Verificación ---
        lineas, verificacion = [], []
        for k in range(n):
            total = sum(Fraction(str(datos[k][j])) * x[j] for j in range(3))
            lineas.append(f"   {MACROS[k]:<14}: obtenido {float(total):8.4f} g    meta {datos[k][3]} g")
            verificacion.append(dict(macro=MACROS[k], obtenido=float(total), meta=float(datos[k][3]),
                                     exacto=total == Fraction(str(datos[k][3]))))
        add("Verificación", "Se reemplazan x1, x2 y x3 en las ecuaciones originales:\n" + "\n".join(lineas),
            mat=False, tipo="verificacion", info=dict(filas=verificacion))

    # --- Resultado final ---
    factible = None
    if tipo == "determinado":
        factible = all(v >= 0 for v in sol)
        porciones = "\n".join(f"   {nombres[i]:<28}{sol[i] * 100:8.1f} g" for i in range(n))
        estado = ("La comida es FACTIBLE: todas las porciones son positivas." if factible else
                  "La comida NO es factible: hay porciones negativas. Cambie algún alimento o las metas.")
        add("Resultado final", f"Cantidad que debe servir de cada alimento:\n{porciones}\n\n{estado}\n"
            f"Energía total: {kcal:.0f} kcal  (4 kcal/g de proteína y carbohidrato, 9 kcal/g de grasa)", mat=False,
            tipo="resultado")
    else:
        add("Resultado final",
            "Las metas no se pueden cumplir de forma única con estos tres alimentos.\n"
            "Sugerencia: reemplace uno de los alimentos por otro con un perfil nutricional distinto.", mat=False,
            tipo="resultado")
    pasos[-1]["info"] = dict(sistema=tipo, factible=factible, kcal=kcal,
                             gramos=[s * 100 for s in sol] if sol else None)
    return dict(pasos=pasos, tipo=tipo, sol=sol, kcal=kcal, datos=datos, nombres=nombres,
                factible=factible, verificacion=verificacion)
