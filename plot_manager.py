"""
Administrador del lienzo cartesiano interactivo de Matplotlib integrado en PySide6.
Diseñado con la estética minimalista y limpia de GeoGebra:
- Función original f(x) en línea azul gruesa continua.
- Polinomios de Taylor P_k(x) en líneas punteadas/a trazos con colores distintivos.
- Punto de expansión x0 marcado con un punto rojo prominente.
- Tooltip flotante interactivo al hacer clic sobre el gráfico (sin barras inferiores invasivas).
- Auto-ajuste y zoom centrado en el cursor.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import matplotlib
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.ticker import MultipleLocator, AutoLocator

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QSizePolicy
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from taylor_engine import TaylorSeriesResult, TaylorOrderStep
from math_engine import clean_asymptotes


# Paleta armoniosa y distintiva para los polinomios de Taylor (estilo GeoGebra)
TAYLOR_PALETTE = [
    "#f59e0b",  # P0: Ámbar / Naranja dorado
    "#10b981",  # P1: Verde esmeralda
    "#e11d48",  # P2: Carmesí / Rosa
    "#8b5cf6",  # P3: Violeta moderno
    "#06b6d4",  # P4: Cian brillante
    "#ea580c",  # P5: Naranja quemado
    "#6366f1",  # P6: Índigo
    "#14b8a6",  # P7: Turquesa
    "#d946ef",  # P8: Fucsia
    "#84cc16",  # P9: Lima
    "#64748b",  # P10: Gris pizarra
]

# Color azul constante para la función original f(x)
FUNC_COLOR = "#1a73e8"  # Azul real GeoGebra


class MinimalNavigationToolbar(NavigationToolbar2QT):
    """Barra de herramientas compacta de navegación para Matplotlib."""
    toolitems = [
        t for t in NavigationToolbar2QT.toolitems
        if t[0] in ("Home", "Pan", "Zoom", "Save")
    ]


class GraphFloatingNavWidget(QFrame):
    """
    Botonera flotante minimalista estilo GeoGebra para zoom y navegación rápida.
    Aparece sobre la esquina superior derecha del lienzo sin consumir espacio en el layout.
    """
    def __init__(self, canvas: "GeoGebraCartesianCanvas", is_dark_mode: bool = False, parent=None):
        super().__init__(parent or canvas)
        self.canvas = canvas
        self.is_dark_mode = is_dark_mode
        self._setup_ui()
        self.update_style()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Botón Zoom In (+)
        self.btn_zoom_in = QPushButton("+")
        self.btn_zoom_in.setFixedSize(30, 30)
        self.btn_zoom_in.setToolTip("Acercar (Zoom +)")
        self.btn_zoom_in.clicked.connect(lambda: self.canvas.zoom(0.82))
        layout.addWidget(self.btn_zoom_in)

        # Botón Zoom Out (-)
        self.btn_zoom_out = QPushButton("−")
        self.btn_zoom_out.setFixedSize(30, 30)
        self.btn_zoom_out.setToolTip("Alejar (Zoom -)")
        self.btn_zoom_out.clicked.connect(lambda: self.canvas.zoom(1.22))
        layout.addWidget(self.btn_zoom_out)

        # Botón Reajustar vista óptima (Home / Auto-fit)
        self.btn_home = QPushButton("⌂")
        self.btn_home.setFixedSize(30, 30)
        self.btn_home.setToolTip("Restablecer vista a la curvatura de f(x) (Home)")
        self.btn_home.clicked.connect(self.canvas.auto_fit_view)
        layout.addWidget(self.btn_home)

        # Botón Ir al Punto de Error / Intersección Exacta (Imagen 2)
        self.btn_error = QPushButton("🎯")
        self.btn_error.setFixedSize(30, 30)
        self.btn_error.setToolTip("🎯 Ir a la intersección y punto de error exacto (sin error de clic)")
        self.btn_error.clicked.connect(lambda: self.canvas.show_exact_intersection_point())
        self.btn_x0 = self.btn_error
        layout.addWidget(self.btn_error)

    def update_style(self):
        bg = "rgba(24, 24, 27, 0.94)" if self.is_dark_mode else "rgba(255, 255, 255, 0.96)"
        border = "#3f3f46" if self.is_dark_mode else "#cbd5e1"
        btn_bg = "#27272a" if self.is_dark_mode else "#f8fafc"
        btn_hover = "#3f3f46" if self.is_dark_mode else "#e2e8f0"
        btn_fg = "#f4f4f5" if self.is_dark_mode else "#0f172a"

        self.setStyleSheet(
            f"GraphFloatingNavWidget {{"
            f"  background-color: {bg};"
            f"  border: 1.5px solid {border};"
            f"  border-radius: 8px;"
            f"}}"
            f"GraphFloatingNavWidget QPushButton {{"
            f"  background-color: {btn_bg};"
            f"  color: {btn_fg} !important;"
            f"  border: 1px solid {border};"
            f"  border-radius: 6px;"
            f"  font-size: 14px;"
            f"  font-weight: 700;"
            f"  padding: 0px !important;"
            f"  margin: 0px !important;"
            f"  text-align: center;"
            f"}}"
            f"GraphFloatingNavWidget QPushButton:hover {{"
            f"  background-color: {btn_hover};"
            f"  border-color: #3b82f6;"
            f"}}"
            f"GraphFloatingNavWidget QPushButton:pressed {{"
            f"  background-color: #2563eb;"
            f"  color: #ffffff !important;"
            f"}}"
        )


class GeoGebraCartesianCanvas(FigureCanvasQTAgg):
    """
    Lienzo cartesiano interactivo que replica la estética y comportamiento de GeoGebra:
    - Desplazamiento natural (pan) arrastrando con el ratón.
    - Zoom fluido centrado en la posición del puntero.
    - Cuadrícula amplia con márgenes mínimos.
    - Escala vertical adaptativa que resalta la curvatura real de las funciones.
    - Botonera flotante estilo GeoGebra para acciones rápidas.
    """
    point_inspected = Signal(float, float)  # (x, y) inspeccionado

    def __init__(self, parent=None, is_dark_mode: bool = False):
        self.figure = Figure(figsize=(8, 6), dpi=100)
        super().__init__(self.figure)
        self.setParent(parent)
        self.setFocusPolicy(Qt.StrongFocus)

        self.ax = self.figure.add_subplot(111)
        self.is_dark_mode = is_dark_mode

        self.taylor_result: Optional[TaylorSeriesResult] = None
        self.x_grid: Optional[np.ndarray] = None
        self.y_true: Optional[np.ndarray] = None
        self.visibility_map: Dict[int, bool] = {}
        self.func_visible: bool = True
        self.selected_order: Optional[int] = None

        self.line_func: Optional[Line2D] = None
        self.lines_poly: Dict[int, Line2D] = {}
        self.x0_marker = None
        self.x0_line = None
        self.tooltip_annotation = None

        # Variables de control para arrastre fluido (pan) y extensión dinámica estilo GeoGebra
        self._is_panning = False
        self._press_coord: Optional[Tuple[float, float]] = None
        self._press_xlim: Optional[Tuple[float, float]] = None
        self._press_ylim: Optional[Tuple[float, float]] = None
        self._has_dragged = False
        self._updating_curves = False

        self._setup_style()
        self._xlim_cid = self.ax.callbacks.connect("xlim_changed", self._on_xlim_changed)
        self._ylim_cid = self.ax.callbacks.connect("ylim_changed", self._on_ylim_changed)

        # Botonera flotante en la esquina superior derecha
        self.floating_nav = GraphFloatingNavWidget(self, is_dark_mode=self.is_dark_mode, parent=self)
        self.floating_nav.show()

        # Cursor de mano abierta estilo GeoGebra
        self.setCursor(Qt.OpenHandCursor)

    def _setup_style(self):
        """Aplica la estética limpia de GeoGebra con cuadrícula suave y márgenes mínimos."""
        bg_color = "#18181b" if self.is_dark_mode else "#ffffff"
        fg_color = "#f4f4f5" if self.is_dark_mode else "#334155"
        grid_major = "#3f3f46" if self.is_dark_mode else "#e2e8f0"
        grid_minor = "#27272a" if self.is_dark_mode else "#f8fafc"
        axis_color = "#71717a" if self.is_dark_mode else "#94a3b8"

        self.figure.patch.set_facecolor(bg_color)
        self.ax.set_facecolor(bg_color)

        # Márgenes mínimos para que la cuadrícula ocupe prácticamente todo el panel disponible
        self.figure.subplots_adjust(left=0.038, right=0.988, top=0.985, bottom=0.045)

        self.ax.tick_params(colors=fg_color, which="both", labelsize=9)
        self.ax.xaxis.label.set_color(fg_color)
        self.ax.yaxis.label.set_color(fg_color)

        for spine in self.ax.spines.values():
            spine.set_color(axis_color)
            spine.set_linewidth(1.0)

        # Cuadrícula principal y secundaria GeoGebra
        self.ax.grid(True, which="major", color=grid_major, linestyle="-", linewidth=0.8, alpha=0.9)
        self.ax.grid(True, which="minor", color=grid_minor, linestyle=":", linewidth=0.5, alpha=0.7)
        self.ax.minorticks_on()

        # Ejes X e Y en el origen
        self.ax.axhline(0, color=axis_color, linewidth=1.2, alpha=0.85)
        self.ax.axvline(0, color=axis_color, linewidth=1.2, alpha=0.85)

        # Configurar vista centrada en (0, 0) con unidades de 1 en 1
        self.ax.set_xlim(-3.8, 3.8)
        self.ax.set_ylim(-3.5, 4.8)
        self._update_locators()

    def set_dark_mode(self, is_dark: bool):
        self.is_dark_mode = is_dark
        self._setup_style()
        if hasattr(self, "floating_nav") and self.floating_nav:
            self.floating_nav.is_dark_mode = is_dark
            self.floating_nav.update_style()
        self.rebuild_plot()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "floating_nav") and self.floating_nav:
            fw = self.floating_nav.sizeHint().width()
            self.floating_nav.move(max(self.width() - fw - 14, 10), 14)

    def update_data(self, result: TaylorSeriesResult, resolution: int = 600):
        """Actualiza los datos matemáticos y renderiza las curvas."""
        self.taylor_result = result
        self.selected_order = None

        # Intervalo para la malla: cubrir ampliamente [x_min, x_max] y x0
        x_start = min(result.x_min, result.x0 - 2.0)
        x_end = max(result.x_max, result.x0 + 2.0)
        span = x_end - x_start
        x_pad = max(span * 0.25, 1.0)

        self.x_grid = np.linspace(x_start - x_pad, x_end + x_pad, resolution)
        raw_y = result.func_eval(self.x_grid)
        self.y_true = clean_asymptotes(self.x_grid, raw_y)

        # Visibilidad por defecto: todos activos
        self.visibility_map = {step.order: True for step in result.steps}
        self.func_visible = True

        self.rebuild_plot()

    def rebuild_plot(self):
        """Redibuja completamente el plano cartesiano."""
        self.ax.clear()
        self._setup_style()
        self._xlim_cid = self.ax.callbacks.connect("xlim_changed", self._on_xlim_changed)
        self.lines_poly.clear()
        self.line_func = None
        self.tooltip_annotation = None

        if self.taylor_result is None or self.x_grid is None or self.y_true is None:
            self.draw()
            return

        res = self.taylor_result

        # 1. Función original f(x): LÍNEA AZUL CONTINUA PROMINENTE
        line_f, = self.ax.plot(
            self.x_grid, self.y_true,
            color=FUNC_COLOR,
            linewidth=2.8,
            linestyle="-",
            label=f"$f(x) = {res.func_input}$",
            zorder=4,
            visible=self.func_visible
        )
        self.line_func = line_f

        # 2. Polinomios de Taylor P_k(x): LÍNEAS A TRAZOS / PUNTEADAS CON COLORES DISTINTIVOS
        for step in res.steps:
            k = step.order
            color = TAYLOR_PALETTE[k % len(TAYLOR_PALETTE)]
            raw_y_p = step.eval_func(self.x_grid)
            y_p = clean_asymptotes(self.x_grid, raw_y_p)

            is_selected = (self.selected_order == k)
            lw = 3.4 if is_selected else 2.2
            alpha = 1.0 if is_selected else (0.85 if self.selected_order is None else 0.35)
            zorder = 5 if is_selected else (3 + k * 0.05)

            # Estilo a trazos / punteado
            line_style = "--" if k % 2 == 0 else "-."

            line, = self.ax.plot(
                self.x_grid, y_p,
                color=color,
                linewidth=lw,
                linestyle=line_style,
                alpha=alpha,
                label=f"$P_{{{k}}}(x)$",
                zorder=zorder,
                visible=self.visibility_map.get(k, True)
            )
            self.lines_poly[k] = line

        # 3. Punto de expansión x0 con un punto rojo prominente y línea guía
        try:
            f_x0 = float(res.func_eval(res.x0))
            if np.isfinite(f_x0):
                self.x0_line = self.ax.axvline(
                    res.x0,
                    color="#ef4444",
                    linestyle=":",
                    linewidth=1.3,
                    alpha=0.85,
                    label=f"$x_0 = {res.x0:g}$"
                )
                self.x0_marker = self.ax.plot(
                    [res.x0], [f_x0],
                    marker="o",
                    markersize=8,
                    color="#ef4444",
                    markeredgecolor="#ffffff" if not self.is_dark_mode else "#18181b",
                    markeredgewidth=1.8,
                    zorder=7
                )
        except Exception:
            pass

        # 4. Ajustar vista al intervalo especificado [x_min, x_max] con escala geométrica que resalta las curvas
        self.auto_fit_view()

        # 5. Leyenda sobria en upper left para evitar colisión con la botonera flotante
        legend = self.ax.legend(
            loc="upper left",
            frameon=True,
            facecolor="#18181b" if self.is_dark_mode else "#ffffff",
            edgecolor="#3f3f46" if self.is_dark_mode else "#e2e8f0",
            fontsize=9
        )
        if legend:
            for text in legend.get_texts():
                text.set_color("#f4f4f5" if self.is_dark_mode else "#0f172a")

        self._refresh_curve_data(force=True)
        self.draw()

    def auto_fit_view(self):
        """
        Ajusta la vista para que el plano cartesiano salga centrado en (0, 0)
        con unidades de 1 en 1 como en GeoGebra, abarcando el intervalo de estudio
        y manteniendo una proporción geométrica equilibrada que permite al usuario
        explorar con zoom in y zoom out con total naturalidad.
        """
        if self.taylor_result is None:
            self.ax.set_xlim(-3.8, 3.8)
            self.ax.set_ylim(-3.5, 4.8)
            self._update_locators()
            self.draw_idle()
            return

        res = self.taylor_result

        # 1. Centrado en X: simétrico alrededor de x=0 para que el plano cartesiano salga centrado
        if res.x_min <= 0 <= res.x_max:
            half_x = max(abs(res.x_min), abs(res.x_max)) + 1.3
            half_x = max(half_x, 3.8)
            self.ax.set_xlim(-half_x, half_x)
        else:
            cx = (res.x_min + res.x_max) / 2.0
            span_x = max(res.x_max - res.x_min, 3.0) + 2.0
            self.ax.set_xlim(cx - span_x / 2.0, cx + span_x / 2.0)

        # 2. Centrado en Y con unidades de 1 en 1
        cur_xlim = self.ax.get_xlim()
        span_x = abs(cur_xlim[1] - cur_xlim[0])

        mask = (self.x_grid >= cur_xlim[0]) & (self.x_grid <= cur_xlim[1]) if self.x_grid is not None else None
        if self.y_true is not None and mask is not None:
            valid_f = self.y_true[mask & np.isfinite(self.y_true)]
        else:
            valid_f = np.array([])

        target_h = max(span_x * 1.05, 8.3)
        if len(valid_f) > 0:
            f_min = float(np.min(valid_f))
            f_max = float(np.max(valid_f))
            y_min = min(-3.5, f_min - 1.0)
            y_max = max(4.8, y_min + target_h)
            if y_min < -15.0 or y_max > 25.0:
                y_min = -max(abs(f_min), 3.5) * 1.2
                y_max = max(abs(f_max), 4.8) * 1.2
        else:
            y_min = -3.5
            y_max = 4.8

        self.ax.set_ylim(y_min, y_max)
        self._update_locators()
        self._refresh_curve_data(force=True)
        self.draw_idle()

    def _update_locators(self):
        """
        Mantiene los ejes y la cuadrícula en unidades de 1 en 1 sin saltos de 2, 4 o 5,
        exactamente como en GeoGebra, adaptándose suavemente si el usuario hace zoom extremo.
        """
        cur_xlim = self.ax.get_xlim()
        cur_ylim = self.ax.get_ylim()
        sx = abs(cur_xlim[1] - cur_xlim[0])
        sy = abs(cur_ylim[1] - cur_ylim[0])

        # Eje X: en escalas estándar (hasta ~35 unidades visibles) estrictamente de 1 en 1
        if sx > 70:
            self.ax.xaxis.set_major_locator(AutoLocator())
        elif sx > 35:
            self.ax.xaxis.set_major_locator(MultipleLocator(2.0))
            self.ax.xaxis.set_minor_locator(MultipleLocator(0.5))
        elif sx < 2.0:
            self.ax.xaxis.set_major_locator(MultipleLocator(0.2))
            self.ax.xaxis.set_minor_locator(MultipleLocator(0.05))
        elif sx < 4.0:
            self.ax.xaxis.set_major_locator(MultipleLocator(0.5))
            self.ax.xaxis.set_minor_locator(MultipleLocator(0.1))
        else:
            self.ax.xaxis.set_major_locator(MultipleLocator(1.0))
            self.ax.xaxis.set_minor_locator(MultipleLocator(0.2))

        # Eje Y: en escalas estándar estrictamente de 1 en 1
        if sy > 70:
            self.ax.yaxis.set_major_locator(AutoLocator())
        elif sy > 35:
            self.ax.yaxis.set_major_locator(MultipleLocator(2.0))
            self.ax.yaxis.set_minor_locator(MultipleLocator(0.5))
        elif sy < 2.0:
            self.ax.yaxis.set_major_locator(MultipleLocator(0.2))
            self.ax.yaxis.set_minor_locator(MultipleLocator(0.05))
        elif sy < 4.0:
            self.ax.yaxis.set_major_locator(MultipleLocator(0.5))
            self.ax.yaxis.set_minor_locator(MultipleLocator(0.1))
        else:
            self.ax.yaxis.set_major_locator(MultipleLocator(1.0))
            self.ax.yaxis.set_minor_locator(MultipleLocator(0.2))

    def _on_xlim_changed(self, event_ax=None):
        """Callback invocado por Matplotlib cuando cambian los límites horizontales (zoom, pan, etc.)."""
        if self._updating_curves:
            return
        self._update_locators()
        if self.taylor_result is not None:
            self._refresh_curve_data()

    def _on_ylim_changed(self, event_ax=None):
        """Callback invocado por Matplotlib cuando cambian los límites verticales."""
        if self._updating_curves:
            return
        self._update_locators()

    def _refresh_curve_data(self, force: bool = False):
        """
        Evalúa y extiende dinámicamente las curvas sobre el viewport visible actual (más margen).
        Comportamiento idéntico a GeoGebra:
        - Al hacer zoom out, las curvas no se cortan y continúan dibujándose en todo el rango visible.
        - Al hacer zoom in, se recalculan para mantener una resolución suave y continua.
        - Al desplazarse (pan), el margen pre-calculado evita parpadeos o cortes en los bordes.
        """
        if self.taylor_result is None or self._updating_curves:
            return

        cur_xlim = self.ax.get_xlim()
        x_vis_min = float(min(cur_xlim[0], cur_xlim[1]))
        x_vis_max = float(max(cur_xlim[0], cur_xlim[1]))
        span = x_vis_max - x_vis_min
        if not np.isfinite(span) or span <= 1e-9:
            return

        # Comprobar si la malla actual ya cubre ampliamente la vista con buena resolución
        if not force and self.x_grid is not None and len(self.x_grid) >= 300:
            grid_min = float(self.x_grid[0])
            grid_max = float(self.x_grid[-1])
            # Si el área visible está bien cubierta con al menos 20% de margen a cada lado
            if grid_min <= (x_vis_min - 0.20 * span) and grid_max >= (x_vis_max + 0.20 * span):
                pts_in_view = int(np.count_nonzero((self.x_grid >= x_vis_min) & (self.x_grid <= x_vis_max)))
                # Y tiene entre 250 y 1500 puntos en pantalla para garantizar suavidad sin exceso
                if 250 <= pts_in_view <= 1500:
                    return

        self._updating_curves = True
        try:
            # Margen del 80% fuera de la pantalla para permitir arrastres fluidos sin ver cortes
            pad = max(span * 0.8, 1.0)
            x_start = x_vis_min - pad
            x_end = x_vis_max + pad

            resolution = 1000
            new_x = np.linspace(x_start, x_end, resolution)
            res = self.taylor_result

            try:
                raw_y = res.func_eval(new_x)
                new_y = clean_asymptotes(new_x, raw_y)
            except Exception:
                new_y = np.full_like(new_x, np.nan)

            self.x_grid = new_x
            self.y_true = new_y

            if self.line_func is not None:
                self.line_func.set_data(new_x, new_y)

            for k, line in self.lines_poly.items():
                step = res.get_step(k)
                if step is not None:
                    try:
                        raw_yp = step.eval_func(new_x)
                        yp = clean_asymptotes(new_x, raw_yp)
                    except Exception:
                        yp = np.full_like(new_x, np.nan)
                    line.set_data(new_x, yp)
        finally:
            self._updating_curves = False

    def zoom(self, factor: float):
        """Aplica zoom centrado en el centro del viewport actual."""
        cur_xlim = self.ax.get_xlim()
        cur_ylim = self.ax.get_ylim()
        cx = (cur_xlim[0] + cur_xlim[1]) / 2.0
        cy = (cur_ylim[0] + cur_ylim[1]) / 2.0
        new_w = (cur_xlim[1] - cur_xlim[0]) * factor
        new_h = (cur_ylim[1] - cur_ylim[0]) * factor
        self.ax.set_xlim(cx - new_w / 2.0, cx + new_w / 2.0)
        self.ax.set_ylim(cy - new_h / 2.0, cy + new_h / 2.0)
        self._refresh_curve_data()
        self.draw_idle()

    def show_exact_intersection_point(self, x_val: Optional[Union[float, bool]] = None):
        """
        Traslada la vista directamente al punto de intersección / expansión x0 (o x_val)
        y despliega el cuadro explicativo con el valor exacto de f(x), P_k(x) y el error,
        eliminando cualquier desviación o duda de 1px por clic manual (Imagen 2).
        """
        if self.taylor_result is None:
            return

        res = self.taylor_result
        if x_val is None or isinstance(x_val, bool):
            target_x = float(res.x0)
        else:
            target_x = float(x_val)

        try:
            yf = float(res.func_eval(target_x))
            if not np.isfinite(yf):
                yf = 0.0
        except Exception:
            yf = 0.0

        # Centrar suavemente los límites de los ejes en el punto exacto
        cur_xlim = self.ax.get_xlim()
        cur_ylim = self.ax.get_ylim()
        w = cur_xlim[1] - cur_xlim[0]
        h = cur_ylim[1] - cur_ylim[0]
        self.ax.set_xlim(target_x - w / 2.0, target_x + w / 2.0)
        self.ax.set_ylim(yf - h / 2.0, yf + h / 2.0)
        self._refresh_curve_data()

        # Mostrar el globo de error idéntico a la Imagen 2 en las coordenadas exactas
        self._show_click_tooltip_coords(target_x, yf)
        self.draw_idle()

    def center_on_x0(self):
        """Centra la vista en el punto de expansión x0 y muestra el error exacto."""
        self.show_exact_intersection_point()

    def pan_by(self, dx_ratio: float, dy_ratio: float):
        """Desplaza la vista por una fracción del tamaño visible."""
        cur_xlim = self.ax.get_xlim()
        cur_ylim = self.ax.get_ylim()
        dx = (cur_xlim[1] - cur_xlim[0]) * dx_ratio
        dy = (cur_ylim[1] - cur_ylim[0]) * dy_ratio
        self.ax.set_xlim(cur_xlim[0] + dx, cur_xlim[1] + dx)
        self.ax.set_ylim(cur_ylim[0] + dy, cur_ylim[1] + dy)
        self._refresh_curve_data()
        self.draw_idle()

    # --- INTERACCIÓN DIRECTA CON EL RATÓN: PAN (ARRASTRE) Y ZOOM ---

    def mousePressEvent(self, event):
        """Inicia el desplazamiento fluido (pan) al presionar cualquier botón del ratón."""
        if event.button() in (Qt.LeftButton, Qt.MiddleButton, Qt.RightButton):
            self._is_panning = True
            self._has_dragged = False
            pos = event.position() if hasattr(event, "position") else event.pos()
            self._press_coord = (pos.x(), pos.y())
            self._press_xlim = self.ax.get_xlim()
            self._press_ylim = self.ax.get_ylim()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Desplaza en tiempo real los ejes de la gráfica al arrastrar el ratón."""
        if self._is_panning and self._press_coord is not None and self._press_xlim is not None and self._press_ylim is not None:
            pos = event.position() if hasattr(event, "position") else event.pos()
            dx_pixels = pos.x() - self._press_coord[0]
            dy_pixels = pos.y() - self._press_coord[1]

            if abs(dx_pixels) > 2 or abs(dy_pixels) > 2:
                self._has_dragged = True

            bbox = self.ax.bbox
            x_span = self._press_xlim[1] - self._press_xlim[0]
            y_span = self._press_ylim[1] - self._press_ylim[0]

            dx_data = dx_pixels * (x_span / max(bbox.width, 1.0))
            dy_data = dy_pixels * (y_span / max(bbox.height, 1.0))

            # En Qt, pos.y() crece hacia abajo. Por tanto, arrastrar hacia abajo (dy_pixels > 0)
            # incrementa los límites en Y (+ dy_data)
            self.ax.set_xlim(self._press_xlim[0] - dx_data, self._press_xlim[1] - dx_data)
            self.ax.set_ylim(self._press_ylim[0] + dy_data, self._press_ylim[1] + dy_data)
            self._refresh_curve_data()
            self.draw_idle()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Finaliza el arrastre y, si fue un clic puro sin desplazamiento, muestra el tooltip del punto."""
        self.setCursor(Qt.OpenHandCursor)
        if self._is_panning:
            self._is_panning = False
            if self._has_dragged:
                self._refresh_curve_data(force=True)
                self.draw_idle()
            else:
                # Clic sin arrastre: convertir a coordenadas matemáticas e inspeccionar
                pos = event.position() if hasattr(event, "position") else event.pos()
                inv = self.ax.transData.inverted()
                mpl_x = pos.x()
                mpl_y = self.figure.bbox.height - pos.y()
                try:
                    xdata, ydata = inv.transform((mpl_x, mpl_y))
                    self._show_click_tooltip_coords(float(xdata), float(ydata))
                except Exception:
                    pass
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        """Zoom fluido centrado exactamente en la posición del puntero del ratón."""
        angle = event.angleDelta().y()
        if angle == 0:
            return
        scale = 0.85 if angle > 0 else 1.18

        pos = event.position() if hasattr(event, "position") else event.pos()
        inv = self.ax.transData.inverted()
        mpl_x = pos.x()
        mpl_y = self.figure.bbox.height - pos.y()
        try:
            xdata, ydata = inv.transform((mpl_x, mpl_y))
        except Exception:
            cur_xlim = self.ax.get_xlim()
            cur_ylim = self.ax.get_ylim()
            xdata = (cur_xlim[0] + cur_xlim[1]) / 2.0
            ydata = (cur_ylim[0] + cur_ylim[1]) / 2.0

        cur_xlim = self.ax.get_xlim()
        cur_ylim = self.ax.get_ylim()

        new_w = (cur_xlim[1] - cur_xlim[0]) * scale
        new_h = (cur_ylim[1] - cur_ylim[0]) * scale

        relx = (cur_xlim[1] - xdata) / max(cur_xlim[1] - cur_xlim[0], 1e-9)
        rely = (cur_ylim[1] - ydata) / max(cur_ylim[1] - cur_ylim[0], 1e-9)

        self.ax.set_xlim([xdata - new_w * (1 - relx), xdata + new_w * relx])
        self.ax.set_ylim([ydata - new_h * (1 - rely), ydata + new_h * rely])
        self._refresh_curve_data()
        self.draw_idle()
        event.accept()

    def keyPressEvent(self, event):
        """Permite desplazarse con las flechas del teclado y zoom con teclas +/-."""
        step = 0.1
        if event.key() == Qt.Key_Left:
            self.pan_by(-step, 0.0)
            event.accept()
        elif event.key() == Qt.Key_Right:
            self.pan_by(step, 0.0)
            event.accept()
        elif event.key() == Qt.Key_Up:
            self.pan_by(0.0, step)
            event.accept()
        elif event.key() == Qt.Key_Down:
            self.pan_by(0.0, -step)
            event.accept()
        elif event.key() in (Qt.Key_Plus, Qt.Key_Equal):
            self.zoom(0.85)
            event.accept()
        elif event.key() in (Qt.Key_Minus, Qt.Key_Underscore):
            self.zoom(1.18)
            event.accept()
        elif event.key() == Qt.Key_Home:
            self.auto_fit_view()
            event.accept()
        else:
            super().keyPressEvent(event)

    def _show_click_tooltip_coords(self, cx: float, cy: float):
        """Muestra un tooltip con información matemática del punto clicado."""
        if self.taylor_result is None:
            return

        res = self.taylor_result
        try:
            fc_val = float(res.func_eval(cx))
        except Exception:
            fc_val = np.nan

        active_order = self.selected_order if self.selected_order is not None else res.max_order
        step = res.get_step(active_order)
        try:
            pc_val = float(step.eval_func(cx)) if step else np.nan
        except Exception:
            pc_val = np.nan

        err_val = abs(fc_val - pc_val) if (np.isfinite(fc_val) and np.isfinite(pc_val)) else np.nan

        lines = [f"x = {cx:.4g}"]
        if np.isfinite(fc_val):
            lines.append(f"f(x) = {fc_val:.4g}")
        if np.isfinite(pc_val):
            lines.append(f"P_{active_order}(x) = {pc_val:.4g}")
        if np.isfinite(err_val):
            lines.append(f"Error = {err_val:.2e}" if err_val < 1e-3 else f"Error = {err_val:.4g}")

        text = "\n".join(lines)

        if self.tooltip_annotation:
            try:
                self.tooltip_annotation.remove()
            except Exception:
                pass

        box_bg = "#18181b" if self.is_dark_mode else "#ffffff"
        box_edge = "#3b82f6"
        txt_color = "#f4f4f5" if self.is_dark_mode else "#0f172a"

        self.tooltip_annotation = self.ax.annotate(
            text,
            xy=(cx, fc_val if np.isfinite(fc_val) else cy),
            xytext=(15, 15),
            textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.5", fc=box_bg, ec=box_edge, lw=1.2, alpha=0.92),
            arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0.2", color=box_edge, lw=1.2),
            fontsize=8.5,
            color=txt_color,
            zorder=8
        )

        self.draw_idle()
        self.point_inspected.emit(cx, fc_val if np.isfinite(fc_val) else cy)

    def set_curve_visibility(self, order: int, visible: bool):
        self.visibility_map[order] = visible
        if order in self.lines_poly:
            self.lines_poly[order].set_visible(visible)
        self.draw_idle()

    def set_func_visibility(self, visible: bool):
        self.func_visible = visible
        if self.line_func:
            self.line_func.set_visible(visible)
        self.draw_idle()

    def set_all_visibility(self, visible: bool):
        for k in self.visibility_map:
            self.visibility_map[k] = visible
        for line in self.lines_poly.values():
            line.set_visible(visible)
        self.draw_idle()

    def select_order(self, order: Optional[int]):
        self.selected_order = order
        for k, line in self.lines_poly.items():
            is_sel = (k == order)
            line.set_linewidth(3.4 if is_sel else 2.2)
            line.set_alpha(1.0 if is_sel else (0.85 if order is None else 0.35))
            line.set_zorder(5 if is_sel else (3 + k * 0.05))
        self.draw_idle()
