# Plataforma Visual e Interactiva para el Cálculo y Análisis de Series de Taylor

Una aplicación de escritorio moderna desarrollada en **Python**, **PySide6 (Qt)**, **SymPy**, **Matplotlib** y **NumPy** para el cálculo simbólico, la representación gráfica interactiva y el análisis riguroso de errores en aproximaciones polinómicas de Taylor.

Inspirada en los principios de diseño y usabilidad de herramientas como **GeoGebra Suite**, la aplicación está concebida como un entorno didáctico y profesional orientado a métodos numéricos, cálculo diferencial e investigación de operaciones.

---

## Características Principales

### 1. Motor Simbólico y Numérico
- **Interpretación matemática flexible:** Admite sintaxis estándar y amigable (`x^2 + 1`, `3x`, `sin(x)`, `cos(x)`, `e^x`, `exp(x)`, `log(x)`, `ln(x)`, `sqrt(x)`, `1/(1+x^2)`, etc.).
- **Validación y seguridad:** Analizador restringido mediante lista blanca de operadores y funciones matemáticas; no ejecuta código arbitrario (`exec`/`eval` prohibidos).
- **Cálculo sistemático:** Derivación simbólica sucesiva, simplificación analítica, evaluación exacta en el punto de expansión $a = x_i$ y construcción acumulada de polinomios $P_n(x)$.
- **Evaluación vectorizada robusta:** Detección de singularidades y discontinuidades verticales (evita conectar asíntotas en funciones como $\tan(x)$ o racionales).

### 2. Interfaz Gráfica Moderna (Estilo GeoGebra)
- **Panel lateral izquierdo:**
  - Configuración del cálculo: función $f(x)$ con renderizado LaTeX dinámico en vivo, punto de expansión $a = x_i$, intervalo $[x_i, h]$, orden máximo $n$ (0 a 15) y resolución de malla.
  - Pestaña **Funciones (Álgebra):** Tarjetas organizadas para la función original $f(x)$ y cada aproximación $P_k(x)$ con indicadores visuales de color, casillas para mostrar/ocultar curvas y botones globales "Mostrar Todas" / "Ocultar Todas".
  - Pestaña **Paso a Paso:** Acordeón interactivo que desglosa para cada orden:
    1. Derivada simbólica $f^{(k)}(x)$.
    2. Evaluación en el punto de expansión $f^{(k)}(a)$.
    3. Sustitución en la fórmula del término de Taylor $\frac{f^{(k)}(a)}{k!}(x-a)^k$.
    4. Polinomio acumulado $P_k(x)$.
    5. Explicación didáctica (significado geométrico de pendiente, concavidad, etc.).
    6. Métricas de error resultantes.
  - Pestaña **Métricas:** Tabla comparativa con Error Máximo estimado, coordenada $x$ del error máximo, Error Medio y RMSE sobre la malla de puntos en $[x_i, h]$, junto con un análisis de convergencia.

### 3. Plano Cartesiano Interactivo Central
- **Gráfica Principal:** Superpone $f(x)$ y todos los polinomios de Taylor activos en un único sistema de coordenadas cartesianas, con ejes destacados, cuadrícula mayor y menor, punto de expansión $(a, f(a))$ etiquetado y franja translúcida del intervalo $[x_i, h]$.
- **Gráfica Independiente de Error:** Pestaña dedicada para estudiar la evolución del error a lo largo del intervalo:
  - Error Absoluto: $E_n(x) = |f(x) - P_n(x)|$.
  - Residuo con Signo: $R_n(x) = f(x) - P_n(x)$ (identifica regiones de sobrestimación y subestimación).
  - Error Relativo Porcentual: $E_{r,n}(x) = \frac{|f(x) - P_n(x)|}{|f(x)|} \times 100\%$ (con protección numérica cuando $f(x) \approx 0$).
  - Selector de escala del eje Y: **Lineal** y **Logarítmica** (ideal para observar tasas de convergencia).
- **Herramientas de navegación:** Zoom suave centrado en el ratón, desplazamiento (pan), reajuste automático de escala (Auto-fit) y restablecimiento de vista.
- **Sincronización total:** Al seleccionar cualquier orden en el panel lateral o en el gráfico, se resalta la curva en ambas vistas, se sincroniza el acordeón de pasos y se actualiza la inspección de valores.

### 4. Exploración Interactiva de Puntos
- Barra interactiva con entrada numérica y control deslizante (slider) para examinar cualquier punto $x = c \in [x_i, h]$.
- Muestra en tiempo real: valor exacto $f(c)$, aproximación $P_n(c)$, error absoluto, residuo con signo y error relativo.
- Admite seleccionar el punto directamente haciendo clic sobre el lienzo cartesiano.

### 5. Teclado Matemático Virtual
- Teclado inferior plegable inspirado en GeoGebra.
- Botones para variables ($x, y$), números (0–9), operadores, potencias ($x^2, x^n$), raíces ($\sqrt{x}, \sqrt[n]{x}$), valor absoluto ($|x|$), exponenciales ($e^x$), logaritmos ($\ln, \log$), trigonométricas ($\sin, \cos, \tan$), constantes ($\pi, e$), flechas de cursor y botón de resolución directa.
- Permite envolver texto seleccionado al pulsar funciones o potencias.

### 6. Exportación de Resultados
- **Exportación a CSV:** Genera un archivo estructurado con metadatos de la sesión, tabla resumen de errores y tabla de muestreo numérico punto a punto de $x, f(x), P_k(x), E_k(x)$.
- **Exportación a PDF:** Genera un informe tipográfico completo con metadatos, gráficos vectoriales/imágenes de alta resolución del plano cartesiano y del error, fórmulas renderizadas, tabla de métricas y desarrollo paso a paso.

---

## Requisitos e Instalación

### Requisitos previos
- **Python 3.10 o superior** (probado y verificado en Python 3.14).
- Sistema operativo: Linux, Windows o macOS.

### Instalación de dependencias

1. Clona o descarga el repositorio:
   ```bash
   git clone https://github.com/AngelMoralesChazari/SerieDeTaylor.git
   cd SerieDeTaylor
   ```

2. (Opcional pero recomendado) Crea y activa un entorno virtual:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # En Linux/macOS
   # venv\Scripts\activate   # En Windows
   ```

3. Instala los requisitos mediante pip:
   ```bash
   pip install -r requirements.txt
   ```

---

## Ejecución de la Aplicación

Para iniciar la aplicación de escritorio:

```bash
python3 main.py
```

La aplicación arrancará con el caso de ejemplo precargado $f(x) = e^x$ en el punto $a = 0$ sobre $[0, 1.5]$ hasta orden 4.

### Accesos directos y atajos de teclado
- **Ctrl + R:** Resolver / recalcular la serie actual.
- **Ctrl + K:** Mostrar / ocultar el teclado matemático virtual.
- **Ctrl + P:** Exportar reporte completo en formato PDF.

---

## Casos de Prueba Matemáticos Obligatorios

La aplicación incluye un selector desplegable en la barra de herramientas para cargar instantáneamente los 4 casos de prueba matemáticos clave:

| Caso | Función $f(x)$ | Punto $a$ | Polinomios esperados | Comportamiento notable |
| :--- | :--- | :---: | :--- | :--- |
| **Caso A: Cuadrática** | $x^2 + 1$ | $0$ | $P_0=1$, $P_1=1$, $P_2=1+x^2$ | El polinomio de orden 2 coincide exactamente con la función original (error = 0). |
| **Caso B: Exponencial** | $e^x$ | $0$ | $P_0=1$, $P_1=1+x$, $P_2=1+x+\frac{x^2}{2}$, $P_3=1+x+\frac{x^2}{2}+\frac{x^3}{6}$ | Convergencia uniforme y error estrictamente decreciente en todo $\mathbb{R}$. |
| **Caso C: Trigonométrica** | $\sin(x)$ | $0$ | $P_0=0$, $P_1=x$, $P_2=x$, $P_3=x-\frac{x^3}{6}$ | Términos pares nulos por simetría impar; $P_1(x) = P_2(x)$. |
| **Caso D: Racional** | $\frac{1}{1+x^2}$ | $0$ | $P_0=1$, $P_1=1$, $P_2=1-x^2$, $P_4=1-x^2+x^4$ | Serie geométrica alterna; radio de convergencia finito $R=1$. |

---

## Ejecución de Pruebas Automatizadas

El proyecto cuenta con una suite completa de pruebas unitarias y de integración que verifica:
1. Parseo matemático y seguridad.
2. Construcción correcta de derivadas y polinomios.
3. Precisión de las curvas y métricas de error.
4. Cumplimiento de los 4 casos obligatorios.
5. Exportación válida a CSV y PDF.

Para ejecutar todas las pruebas:

```bash
python3 -m pytest tests/ -v
```

---

## Arquitectura Modular del Proyecto

```text
SerieTaylor/
├── main.py                 # Punto de entrada de la aplicación de escritorio
├── math_engine.py          # Validación segura, preprocesamiento y lambdificación numérica
├── taylor_engine.py        # Cálculo de derivadas, términos, polinomios y explicaciones pedagógicas
├── error_analysis.py       # Análisis de error absoluto, con signo, relativo y métricas globales
├── latex_renderer.py       # Renderizado tipográfico LaTeX de alta definición a QPixmap
├── plot_manager.py         # Administración de lienzos interactivos de Matplotlib en PySide6
├── export_manager.py       # Exportación de datos a CSV y reportes a PDF
├── requirements.txt        # Especificación de dependencias del proyecto
├── README.md               # Documentación general de instalación y uso
├── ui/
│   ├── __init__.py         # Exportaciones del paquete de interfaz
│   ├── main_window.py      # Ventana principal, barra de herramientas y sincronización
│   ├── sidebar_panel.py    # Panel lateral izquierdo (Álgebra, Paso a Paso, Métricas)
│   ├── math_keyboard.py    # Teclado matemático virtual estilo GeoGebra
│   ├── point_eval_widget.py# Widget de exploración de puntos x = c en tiempo real
│   ├── values_table_dialog.py # Diálogo para tabla numérica de valores y errores
│   └── styles.py           # Hojas de estilo modernas QSS (Tema Claro y Oscuro)
└── tests/
    ├── test_math_engine.py      # Pruebas del motor analítico y seguridad
    ├── test_taylor_engine.py    # Pruebas de construcción de series y derivadas
    ├── test_error_analysis.py   # Pruebas de cálculo de error y salvaguardas
    ├── test_cases_required.py   # Verificación formal de los Casos A, B, C y D
    └── test_exports.py          # Pruebas de generación de CSV y PDF
```

---

## Licencia

Desarrollado con fines académicos y de investigación en métodos numéricos y optimización matemática.
