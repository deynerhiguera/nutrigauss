# NutriGauss

Planificador de porciones por macronutrientes mediante el método de eliminación de Gauss.
Proyecto de aula de Álgebra Lineal, Universidad de Santander (UDES).

Sebastian Mantilla Piñeres, Deyner Santiago Higuera Cardenas y Jeins Schneider Suarez Godoy.
Docente: Antonio Balcucho Contreras.

NutriGauss es un sitio web que corre en tu computador. El backend en Python resuelve el
sistema 3x3 con el motor de Gauss del grupo, y la página muestra cada paso de la eliminación,
el resultado y los tres planos en 3D. No necesita internet ni instalar librerías.

## Requisito

Python 3.8 o más reciente. Para comprobarlo, abre la Terminal y escribe `python3 --version`.
Si el Mac pide instalar las "herramientas de línea de comandos", acepta: eso instala Python.
También sirve el instalador de https://www.python.org/downloads/

## Abrirlo en Mac

**Con doble clic.** Haz doble clic en `Abrir NutriGauss.command`. Se abre una ventana de
Terminal con el servidor y el navegador entra solo a http://localhost:8000.

La primera vez, macOS puede decir que no se puede abrir porque es de un desarrollador no
identificado. En ese caso haz clic derecho sobre el archivo, elige **Abrir** y confirma.
Las siguientes veces basta el doble clic.

**Desde la Terminal:**

```
cd ~/Downloads/NutriGauss
python3 servidor.py
```

**Desde Visual Studio Code:** abre la carpeta `NutriGauss`, abre `servidor.py` y pulsa ▶.

Deja abierta la ventana del servidor mientras usas la página. Para detenerlo, ciérrala o
pulsa Ctrl + C. Si el puerto 8000 está ocupado, el servidor usa el siguiente libre y lo dice.

## Abrirlo en Windows

Doble clic en `Abrir NutriGauss (Windows).bat`, o en una terminal: `python servidor.py`.

## Pruebas

```
python3 pruebas.py
```

Son 7 pruebas: el sistema del primer avance (x = 2, y = 3, z = −1), el ejemplo del documento,
un pivote cero, un sistema con infinitas soluciones, uno sin solución, una porción negativa y
la API del servidor.

## Archivos

| Archivo | Qué es |
| --- | --- |
| `motor.py` | Motor de eliminación de Gauss con pivoteo parcial (backend) |
| `servidor.py` | Servidor local: sirve la página y la API `/api/resolver` |
| `web/` | Página web: `index.html`, `estilos.css`, `app.js` y librerías locales |
| `pruebas.py` | Pruebas del motor y del servidor |
| `version_escritorio/nutrigauss.py` | Versión de escritorio (tkinter) que aparece en el documento |

## Cómo se usa

1. **Plantear.** Elige tres alimentos (o "Otro alimento…" para agregar uno propio) y escribe
   las metas en gramos. Pulsa **Resolver con Gauss**.
2. **Paso a paso.** Recorre los pasos con los botones o con las flechas ← →. El interruptor
   de arriba cambia entre decimales y fracciones exactas.
3. **Resultado.** Porciones en gramos, verificación de los nutrientes y energía total.
4. **Planos en 3D.** Los tres planos y su punto de corte. Arrastra para girarlo.

Librerías incluidas en `web/vendor`: KaTeX (fórmulas), Plotly (gráfico 3D) y la fuente
Bricolage Grotesque, todas con licencia libre.

Uso académico. No reemplaza la orientación de un profesional en nutrición.
