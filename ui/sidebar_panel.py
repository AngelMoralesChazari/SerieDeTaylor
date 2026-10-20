"""
Panel lateral izquierdo ("Vista Álgebra" estilo GeoGebra).
Contiene la configuración compacta (f(x), x0, intervalo [x_min, x_max], orden n),
la lista de funciones con botones circulares de color para activar/desactivar curvas
y el desglose analítico paso a paso idéntico al cuaderno de ejercicios (Imagen 4).
"""

from __future__ import annotations

from typing import Optional, Dict, List
import numpy as np
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QDoubleSpinBox, QSpinBox, QPushButton, QTabWidget,
    QScrollArea, QFrame, QCheckBox, QMessageBox, QGridLayout
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPixmap

from taylor_engine import TaylorSeriesResult, TaylorOrderStep
from latex_renderer import GLOBAL_LATEX_RENDERER
from plot_manager import TAYLOR_PALETTE, FUNC_COLOR


class GeoGebraAlgebraCard(QFrame):
    """
    Tarjeta de ecuación individual estilo GeoGebra (círculo de color a la izquierda + fórmula LaTeX).
    """
    clicked = Signal(int)
    visibility_toggled = Signal(int, bool)

    def __init__(
        self,
        order: int,
        title: str,
        latex_str: str,
        color_hex: str,
        is_dark_mode: bool = False,
        parent=None
    ):
        super().__init__(parent)
        self.order = order
        self.color_hex = color_hex
        self.is_dark_mode = is_dark_mode
        self.is_visible_curve = True
        self.is_selected = False

        self._setup_ui(title, latex_str)

    def _setup_ui(self, title: str, latex_str: str):
        self.setCursor(Qt.PointingHandCursor)
        self.update_style()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(8)

        # Botón circular de color estilo GeoGebra que conmuta visibilidad
        self.btn_circle = QPushButton()
        self.btn_circle.setFixedSize(18, 18)
        self.btn_circle.setCursor(Qt.PointingHandCursor)
        self.btn_circle.setToolTip("Mostrar / Ocultar en la gráfica")
        self._update_circle_style()
        self.btn_circle.clicked.connect(self._toggle_visibility)
        layout.addWidget(self.btn_circle)

        # Contenedor de título y fórmula
        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("font-weight: 700; font-size: 11px; color: #64748b;")
        text_layout.addWidget(lbl_title)

        self.lbl_latex = QLabel()
        self.update_latex(latex_str)
        text_layout.addWidget(self.lbl_latex)

        layout.addLayout(text_layout, stretch=1)

    def _toggle_visibility(self):
        self.is_visible_curve = not self.is_visible_curve
        self._update_circle_style()
        self.visibility_toggled.emit(self.order, self.is_visible_curve)

    def _update_circle_style(self):
        if self.is_visible_curve:
            # Relleno de color completo
            self.btn_circle.setStyleSheet(
                f"QPushButton {{ background-color: {self.color_hex}; border-radius: 9px; border: 1.5px solid {self.color_hex}; }}"
                f"QPushButton:hover {{ border-color: #ffffff; }}"
            )
        else:
            # Hueco / solo contorno
            self.btn_circle.setStyleSheet(
                f"QPushButton {{ background-color: transparent; border-radius: 9px; border: 2px solid {self.color_hex}; }}"
                f"QPushButton:hover {{ background-color: {self.color_hex}33; }}"
            )

    def update_latex(self, latex_str: str):
        color = "#f8fafc" if self.is_dark_mode else "#0f172a"
        try:
            px = GLOBAL_LATEX_RENDERER.render_to_pixmap(latex_str, font_size=9.5, color_hex=color)
            if not px.isNull():
                self.lbl_latex.setPixmap(px)
            else:
                self.lbl_latex.setText(latex_str)
        except Exception:
            self.lbl_latex.setText(latex_str)
        self.lbl_latex.setToolTip(latex_str)

    def set_selected(self, selected: bool):
        self.is_selected = selected
        self.update_style()

    def update_style(self):
        bg = "#1e293b" if self.is_dark_mode else "#ffffff"
        border = self.color_hex if self.is_selected else ("#334155" if self.is_dark_mode else "#e2e8f0")
        border_width = "2px" if self.is_selected else "1px"
        bg_active = "#293548" if self.is_dark_mode else "#f8fafc"
        cur_bg = bg_active if self.is_selected else bg

        self.setStyleSheet(
            f"QFrame {{"
            f"  background-color: {cur_bg};"
            f"  border: {border_width} solid {border};"
            f"  border-radius: 6px;"
            f"}}"
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.order)
        super().mousePressEvent(event)


class NotebookStepWidget(QFrame):
    """
    Desarrollo matemático paso a paso con el formato exacto de la libreta (Imagen 4).
    """

    def __init__(self, step: TaylorOrderStep, x0_val: float, is_dark_mode: bool = False, parent=None):
        super().__init__(parent)
        self.step = step
        self.x0_val = x0_val
        self.is_dark_mode = is_dark_mode

        self._setup_ui()

    def _setup_ui(self):
        k = self.step.order
        color_hex = TAYLOR_PALETTE[k % len(TAYLOR_PALETTE)]

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 8)
        layout.setSpacing(4)

        bg = "#1e293b" if self.is_dark_mode else "#ffffff"
        border = "#334155" if self.is_dark_mode else "#e2e8f0"
        self.setStyleSheet(
            f"QFrame {{ background-color: {bg}; border: 1px solid {border}; "
            f"border-left: 3px solid {color_hex}; border-radius: 4px; }}"
        )

        # Encabezado del orden
        header = QHBoxLayout()
        lbl_badge = QLabel(f" Orden {k} ")
        lbl_badge.setStyleSheet(
            f"background-color: {color_hex}; color: #ffffff; font-weight: bold; "
            f"font-size: 10px; border-radius: 3px; padding: 1px 4px;"
        )
        header.addWidget(lbl_badge)
        header.addStretch()
        layout.addLayout(header)

        txt_color = "#f8fafc" if self.is_dark_mode else "#0f172a"

        # Formato de la libreta (Imagen 4):
        if k == 0:
            # f(x) y evaluación f(x0)
            row_eval = f"f({self.x0_val:g}) = {self.step.derivative_at_x0_latex}"
            self._add_math_line(layout, "Función y Evaluación Base:", row_eval, txt_color)

            row_poly = f"P_{{0}}(x) = {self.step.poly_taylor_latex}"
            self._add_math_line(layout, "Polinomio Inicial:", row_poly, txt_color)
        else:
            # Derivada simbólica: f^(k)(x) = ...
            deriv_name = "f'(x)" if k == 1 else ("f''(x)" if k == 2 else ("f'''(x)" if k == 3 else f"f^{{({k})}}(x)"))
            row_deriv = f"{deriv_name} = {self.step.derivative_latex}"
            self._add_math_line(layout, f"Derivada {k}:", row_deriv, txt_color)

            # Evaluación en x0: f^(k)(x0) = ...
            deriv_eval_name = f"f'({self.x0_val:g})" if k == 1 else (f"f''({self.x0_val:g})" if k == 2 else (f"f'''({self.x0_val:g})" if k == 3 else f"f^{{({k})}}({self.x0_val:g})"))
            row_eval = f"{deriv_eval_name} = {self.step.derivative_at_x0_latex}"
            self._add_math_line(layout, f"Evaluación en x₀ = {self.x0_val:g}:", row_eval, txt_color)

            # Término de Taylor: término no simplificado -> término simplificado
            row_term = f"\\text{{Término: }} {self.step.unsimplified_term_latex} \\rightarrow {self.step.term_taylor_latex}"
            self._add_math_line(layout, "Sustitución en la Fórmula:", row_term, txt_color)

            # Polinomio acumulado P_k(x)
            row_poly = f"P_{{{k}}}(x) = {self.step.poly_taylor_latex}"
            self._add_math_line(layout, f"Polinomio Acumulado P_{k}(x):", row_poly, txt_color)

    def _add_math_line(self, parent_layout: QVBoxLayout, label_text: str, latex_str: str, text_color: str):
        lbl_desc = QLabel(label_text)
        lbl_desc.setStyleSheet("font-size: 10px; color: #64748b; font-weight: 600;")
        parent_layout.addWidget(lbl_desc)

        lbl_img = QLabel()
        try:
            px = GLOBAL_LATEX_RENDERER.render_to_pixmap(latex_str, font_size=9.5, color_hex=text_color)
            if not px.isNull():
                lbl_img.setPixmap(px)
            else:
                lbl_img.setText(latex_str)
        except Exception:
            lbl_img.setText(latex_str)
        lbl_img.setToolTip(latex_str)

        parent_layout.addWidget(lbl_img)


class SidebarPanel(QWidget):
    """
    Panel lateral ("Vista Álgebra"):
    - Entrada compacta de parámetros (f(x), x0, [x_min, x_max], orden n)
    - Pestaña 'Álgebra': lista limpia de ecuaciones con círculos GeoGebra
    - Pestaña 'Paso a Paso': desarrollo matemático como en la libreta (Imagen 4) y fórmula final
    """
    solve_requested = Signal(str, float, float, float, int)  # func, x0, x_min, x_max, order
    curve_visibility_changed = Signal(int, bool)
    func_visibility_changed = Signal(bool)
    order_selected = Signal(int)

    def __init__(self, parent=None, is_dark_mode: bool = False):
        super().__init__(parent)
        self.is_dark_mode = is_dark_mode
        self.result: Optional[TaylorSeriesResult] = None

        self.cards_map: Dict[int, GeoGebraAlgebraCard] = {}
        self.selected_order: Optional[int] = None

        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(6)

        # 1. Panel de Entrada Compacto (Estilo GeoGebra "+ Entrada")
        input_box = QFrame()
        input_box.setProperty("class", "card")
        in_layout = QVBoxLayout(input_box)
        in_layout.setContentsMargins(8, 8, 8, 8)
        in_layout.setSpacing(6)

        lbl_title = QLabel("Entrada Matemática")
        lbl_title.setStyleSheet("font-weight: 700; font-size: 12px; color: #2563eb;")
        in_layout.addWidget(lbl_title)

        # Entrada de f(x)
        in_layout.addWidget(QLabel("Función f(x):"))
        self.input_fx = QLineEdit("x^4 - 3x^2 + 1")
        self.input_fx.setPlaceholderText("Ej: x^4 - 3x^2 + 1, exp(x), sin(x)")
        self.input_fx.textChanged.connect(self._on_fx_text_changed)
        self.input_fx.returnPressed.connect(self._on_solve_clicked)
        in_layout.addWidget(self.input_fx)

        # Previsualización LaTeX inmediata (Imagen 5)
        self.lbl_preview_fx = QLabel()
        self.lbl_preview_fx.setStyleSheet("min-height: 26px; padding: 2px;")
        in_layout.addWidget(self.lbl_preview_fx)
        self._update_fx_preview("x^4 - 3x^2 + 1")

        # Configuración de x0, intervalo [x_min, x_max] y orden n
        grid_cfg = QGridLayout()
        grid_cfg.setSpacing(4)

        # Punto de expansión x0 (Punto a)
        grid_cfg.addWidget(QLabel("Punto x₀ (a):"), 0, 0)
        self.spin_x0 = QDoubleSpinBox()
        self.spin_x0.setRange(-1000.0, 1000.0)
        self.spin_x0.setDecimals(2)
        self.spin_x0.setValue(1.0)
        grid_cfg.addWidget(self.spin_x0, 0, 1)

        # Orden máximo n
        grid_cfg.addWidget(QLabel("Orden máx (n):"), 0, 2)
        self.spin_order = QSpinBox()
        self.spin_order.setRange(0, 12)
        self.spin_order.setValue(4)
        grid_cfg.addWidget(self.spin_order, 0, 3)

        # Intervalo [x_min, x_max]
        grid_cfg.addWidget(QLabel("Intervalo de:"), 1, 0)
        self.spin_xmin = QDoubleSpinBox()
        self.spin_xmin.setRange(-1000.0, 1000.0)
        self.spin_xmin.setDecimals(2)
        self.spin_xmin.setValue(-3.0)
        grid_cfg.addWidget(self.spin_xmin, 1, 1)

        grid_cfg.addWidget(QLabel("hasta:"), 1, 2)
        self.spin_xmax = QDoubleSpinBox()
        self.spin_xmax.setRange(-1000.0, 1000.0)
        self.spin_xmax.setDecimals(2)
        self.spin_xmax.setValue(3.0)
        grid_cfg.addWidget(self.spin_xmax, 1, 3)

        in_layout.addLayout(grid_cfg)

        # Botón Resolver
        self.btn_solve = QPushButton("▶ Resolver Serie de Taylor")
        self.btn_solve.setProperty("class", "primary")
        self.btn_solve.setFixedHeight(32)
        self.btn_solve.clicked.connect(self._on_solve_clicked)
        in_layout.addWidget(self.btn_solve)

        main_layout.addWidget(input_box)

        # 2. Pestañas de la Vista Álgebra
        self.tabs = QTabWidget()

        # Pestaña 1: Vista Álgebra (Lista de Ecuaciones)
        self.tab_algebra = QWidget()
        alg_layout = QVBoxLayout(self.tab_algebra)
        alg_layout.setContentsMargins(4, 4, 4, 4)

        # Estilo sobrio y delgado para barras de desplazamiento horizontales
        slim_scroll_style = """
            QScrollArea { background: transparent; border: none; }
            QScrollBar:horizontal {
                height: 6px;
                background: rgba(0,0,0,0.05);
                border-radius: 3px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: #94a3b8;
                border-radius: 3px;
                min-width: 25px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #64748b;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
        """

        self.scroll_alg = QScrollArea()
        self.scroll_alg.setWidgetResizable(True)
        self.scroll_alg.setFrameShape(QFrame.NoFrame)
        self.scroll_alg.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_alg.setStyleSheet(slim_scroll_style)
        self.alg_container = QWidget()
        self.alg_list_layout = QVBoxLayout(self.alg_container)
        self.alg_list_layout.setContentsMargins(0, 0, 0, 16)
        self.alg_list_layout.setSpacing(4)
        self.alg_list_layout.addStretch()
        self.scroll_alg.setWidget(self.alg_container)
        alg_layout.addWidget(self.scroll_alg)

        self.tabs.addTab(self.tab_algebra, "Álgebra")

        # Pestaña 2: Desarrollo Paso a Paso (como en la libreta, Imagen 4)
        self.tab_steps = QWidget()
        steps_layout = QVBoxLayout(self.tab_steps)
        steps_layout.setContentsMargins(4, 4, 4, 4)

        self.scroll_steps = QScrollArea()
        self.scroll_steps.setWidgetResizable(True)
        self.scroll_steps.setFrameShape(QFrame.NoFrame)
        self.scroll_steps.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_steps.setStyleSheet(slim_scroll_style)
        self.steps_container = QWidget()
        self.steps_list_layout = QVBoxLayout(self.steps_container)
        # Padding inferior de 20px para que el scroll horizontal nunca tape el último paso
        self.steps_list_layout.setContentsMargins(0, 0, 0, 20)
        self.steps_list_layout.setSpacing(6)
        self.steps_list_layout.addStretch()
        self.scroll_steps.setWidget(self.steps_container)
        steps_layout.addWidget(self.scroll_steps)

        # Caja para la fórmula final construida (con scroll horizontal independiente para visualizarla completa)
        self.final_formula_box = QFrame()
        self.final_formula_box.setStyleSheet(
            "background-color: #2563eb12; border: 1.5px solid #2563eb; border-radius: 6px; padding: 4px;"
        )

        # --- AJUSTE DEL TAMAÑO DEL RECUADRO ---
        # Modifica este valor para cambiar el ancho (ej. 350 para menos ancho, 450 para más ancho):
        self.final_formula_box.setMinimumWidth(380)
        # Modifica este valor para cambiar la altura vertical (ej. 110 más compacto, 140 más alto):
        self.final_formula_box.setMaximumHeight(170)

        f_box_layout = QVBoxLayout(self.final_formula_box)
        f_box_layout.setContentsMargins(6, 6, 6, 6)
        f_box_layout.setSpacing(4)

        lbl_f_title = QLabel("Fórmula de Taylor Construida:")
        lbl_f_title.setStyleSheet("font-weight: 700; font-size: 11px; color: #2563eb;")
        f_box_layout.addWidget(lbl_f_title)

        self.scroll_final = QScrollArea()
        self.scroll_final.setWidgetResizable(True)
        self.scroll_final.setFrameShape(QFrame.NoFrame)
        self.scroll_final.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_final.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_final.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:horizontal {
                height: 6px;
                background: rgba(0,0,0,0.06);
                border-radius: 3px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: #3b82f6;
                border-radius: 3px;
                min-width: 25px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #2563eb;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
        """)

        final_inner = QWidget()
        final_inner_layout = QVBoxLayout(final_inner)
        final_inner_layout.setContentsMargins(0, 0, 0, 8)
        final_inner_layout.setSpacing(4)

        self.lbl_final_taylor = QLabel()
        self.lbl_final_taylor.setTextInteractionFlags(Qt.TextSelectableByMouse)
        final_inner_layout.addWidget(self.lbl_final_taylor)

        self.lbl_final_expanded = QLabel()
        self.lbl_final_expanded.setTextInteractionFlags(Qt.TextSelectableByMouse)
        final_inner_layout.addWidget(self.lbl_final_expanded)

        self.scroll_final.setWidget(final_inner)
        f_box_layout.addWidget(self.scroll_final)

        steps_layout.addWidget(self.final_formula_box)

        self.tabs.addTab(self.tab_steps, "Paso a Paso")

        main_layout.addWidget(self.tabs, stretch=1)

    def set_dark_mode(self, is_dark: bool):
        self.is_dark_mode = is_dark
        self._update_fx_preview(self.input_fx.text())
        if self.result:
            self.display_results(self.result)

    def _on_fx_text_changed(self, text: str):
        self._update_fx_preview(text)

    def _update_fx_preview(self, text: str):
        if not text.strip():
            self.lbl_preview_fx.clear()
            return
        color = "#f8fafc" if self.is_dark_mode else "#0f172a"
        try:
            from math_engine import parse_math_expression, expr_to_latex
            expr = parse_math_expression(text)
            ltx = f"f(x) = {expr_to_latex(expr)}"
            px = GLOBAL_LATEX_RENDERER.render_to_pixmap(ltx, font_size=11, color_hex=color)
            if not px.isNull():
                self.lbl_preview_fx.setPixmap(px)
        except Exception:
            self.lbl_preview_fx.setText(text)

    def _on_solve_clicked(self):
        func_str = self.input_fx.text().strip()
        if not func_str:
            QMessageBox.warning(self, "Campo Vacío", "Por favor ingresa una función matemática.")
            return

        x0 = self.spin_x0.value()
        x_min = self.spin_xmin.value()
        x_max = self.spin_xmax.value()
        order = self.spin_order.value()

        if x_min >= x_max:
            QMessageBox.warning(
                self, "Intervalo Inválido",
                f"El límite inferior ({x_min:g}) debe ser menor que el límite superior ({x_max:g})."
            )
            return

        self.solve_requested.emit(func_str, x0, x_min, x_max, order)

    def _clear_lists(self):
        while self.alg_list_layout.count() > 1:
            item = self.alg_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.cards_map.clear()

        while self.steps_list_layout.count() > 1:
            item = self.steps_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.lbl_final_taylor.clear()
        self.lbl_final_expanded.clear()

    def display_results(self, result: TaylorSeriesResult):
        self.result = result
        self._clear_lists()

        # 1. Tarjeta para la función original f(x)
        card_f = GeoGebraAlgebraCard(
            order=-1,
            title="Función Original",
            latex_str=f"f(x) = {result.func_latex}",
            color_hex=FUNC_COLOR,
            is_dark_mode=self.is_dark_mode
        )
        card_f.visibility_toggled.connect(lambda ord, v: self.func_visibility_changed.emit(v))
        card_f.clicked.connect(self._on_card_clicked)
        self.cards_map[-1] = card_f
        self.alg_list_layout.insertWidget(0, card_f)

        # 2. Tarjetas para cada polinomio P_k(x) en la Vista Álgebra
        for idx, step in enumerate(result.steps):
            k = step.order
            color_hex = TAYLOR_PALETTE[k % len(TAYLOR_PALETTE)]

            # Polinomio en potencias de (x - x0)
            card_p = GeoGebraAlgebraCard(
                order=k,
                title=f"Aproximación P_{k}(x)",
                latex_str=f"P_{{{k}}}(x) = {step.poly_taylor_latex}",
                color_hex=color_hex,
                is_dark_mode=self.is_dark_mode
            )
            card_p.visibility_toggled.connect(self.curve_visibility_changed.emit)
            card_p.clicked.connect(self._on_card_clicked)
            self.cards_map[k] = card_p
            self.alg_list_layout.insertWidget(idx + 1, card_p)

            # Tarjeta de paso matemático como en la libreta (Imagen 4)
            step_widget = NotebookStepWidget(
                step=step,
                x0_val=result.x0,
                is_dark_mode=self.is_dark_mode
            )
            self.steps_list_layout.insertWidget(idx, step_widget)

        # 3. Mostrar la fórmula final construida (idéntica al final de la Imagen 4)
        txt_color = "#f8fafc" if self.is_dark_mode else "#0f172a"

        ltx_taylor = f"f(x) \\approx {result.constructed_taylor_formula_latex}"
        px_t = GLOBAL_LATEX_RENDERER.render_to_pixmap(ltx_taylor, font_size=9.5, color_hex=txt_color)
        if not px_t.isNull():
            self.lbl_final_taylor.setPixmap(px_t)
        else:
            self.lbl_final_taylor.setText(ltx_taylor)
        self.lbl_final_taylor.setToolTip(ltx_taylor)

        ltx_exp = f"\\text{{Expandida: }} P_{{{result.max_order}}}(x) = {result.expanded_formula_latex}"
        px_e = GLOBAL_LATEX_RENDERER.render_to_pixmap(ltx_exp, font_size=9.0, color_hex="#64748b")
        if not px_e.isNull():
            self.lbl_final_expanded.setPixmap(px_e)
        else:
            self.lbl_final_expanded.setText(ltx_exp)
        self.lbl_final_expanded.setToolTip(ltx_exp)

    def select_order(self, order: Optional[int]):
        self.selected_order = order
        for k, card in self.cards_map.items():
            card.set_selected(k == order)

    def _on_card_clicked(self, order: int):
        self.select_order(order)
        self.order_selected.emit(order)

    def set_inputs(self, func_str: str, x0: float, x_min: float, x_max: float, order: int):
        self.input_fx.setText(func_str)
        self.spin_x0.setValue(x0)
        self.spin_xmin.setValue(x_min)
        self.spin_xmax.setValue(x_max)
        self.spin_order.setValue(order)
