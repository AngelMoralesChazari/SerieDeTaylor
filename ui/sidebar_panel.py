"""
Panel lateral izquierdo ("Vista Álgebra" estilo GeoGebra).
Contiene la configuración compacta (f(x), x0, intervalo [x_min, x_max], orden n),
la lista de funciones con botones circulares de color para activar/desactivar curvas
y el desglose analítico paso a paso idéntico al cuaderno de ejercicios (Imagen 4).
"""

from __future__ import annotations

from typing import Optional, Dict, List, Any
import numpy as np
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QDoubleSpinBox, QSpinBox, QPushButton, QTabWidget,
    QScrollArea, QFrame, QCheckBox, QMessageBox, QGridLayout, QComboBox,
    QDialog
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


class WhiteboardConvergenceWidget(QFrame):
    """
    Despliegue visual de la Parte b) del Pizarrón:
    - Evaluación iterativa de Taylor en x_eval (ej. ln(1.25))
    - Sustitución término a término idéntica al pizarrón:
      ln(1.25) = (1.25 - 1) = 0.25
      ln(1.25) = 0.25 - 1/2(0.25)^2 = 0.21875
      ln(1.25) = 0.21875 + 1/3(0.25)^3 = 0.223958
      ln(1.25) = 0.223958 - 1/4(0.25)^4 = 0.222981  <-- Condición de error cumplida (Δ = 0.000977 < 10^-3)
      ln(1.25) = 0.222981 + 1/5(0.25)^5 = 0.223177
      ln(1.25) = 0.223177 - 1/6(0.25)^6 = 0.223136
    - Columna de diferencias Δ_k entre órdenes sucesivos
    - Resaltado en verde esmeralda del orden exacto que cumple con la condición de error
    - Comparación con el valor exacto de la Calculadora: ln(1.25) = 0.223143
    - Botón interactivo para trasladar la gráfica al punto x_eval
    """
    inspect_eval_point_requested = Signal(float)

    def __init__(self, is_dark_mode: bool = False, parent=None):
        super().__init__(parent)
        self.is_dark_mode = is_dark_mode
        self.eval_data: Optional[Dict[str, Any]] = None
        self._setup_ui()

    def _setup_ui(self):
        self.layout_main = QVBoxLayout(self)
        self.layout_main.setContentsMargins(6, 6, 6, 6)
        self.layout_main.setSpacing(6)
        self.update_style()

    def update_style(self):
        bg = "#182234" if self.is_dark_mode else "#f0fdf4"
        border = "#059669" if self.is_dark_mode else "#10b981"
        self.setStyleSheet(
            f"WhiteboardConvergenceWidget {{"
            f"  background-color: {bg};"
            f"  border: 1.5px solid {border};"
            f"  border-radius: 8px;"
            f"}}"
        )

    def update_data(self, eval_data: Dict[str, Any]):
        self.eval_data = eval_data
        # Limpiar layout previo
        while self.layout_main.count() > 0:
            item = self.layout_main.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                sub = item.layout()
                while sub.count() > 0:
                    si = sub.takeAt(0)
                    if si.widget():
                        si.widget().deleteLater()

        x_eval = eval_data["x_eval"]
        x0 = eval_data["x0"]
        dx = eval_data["dx"]
        f_val = eval_data["f_val"]
        func_prefix = eval_data["func_prefix"]
        tol = eval_data["tolerance"]
        iterations = eval_data["iterations"]
        best_order = eval_data["best_order"]

        txt_color = "#f8fafc" if self.is_dark_mode else "#0f172a"
        muted_color = "#94a3b8" if self.is_dark_mode else "#64748b"

        # 1. Encabezado de la Parte b
        header_box = QFrame()
        h_layout = QVBoxLayout(header_box)
        h_layout.setContentsMargins(4, 4, 4, 4)
        h_layout.setSpacing(2)

        clean_prefix = func_prefix.replace("\\", "")
        title_lbl = QLabel(f"Parte b) Evaluación de {clean_prefix} e Iteraciones de Error")
        title_lbl.setStyleSheet("font-weight: 800; font-size: 11.5px; color: #10b981;")
        h_layout.addWidget(title_lbl)

        tol_str = f"{tol:g}" if tol is not None else "Sin límite"
        if tol == 0.001:
            tol_str = "10⁻³ (0.001)"
        elif tol == 0.0001:
            tol_str = "10⁻⁴ (0.0001)"
        elif tol == 0.01:
            tol_str = "10⁻² (0.01)"

        sub_lbl = QLabel(
            f"Sustitución en potencias: (x - x₀) = ({x_eval:g} - {x0:g}) = {dx:g}  |  "
            f"Tolerancia: < {tol_str}"
        )
        sub_lbl.setStyleSheet(f"font-size: 9.5px; color: {muted_color}; font-weight: 600;")
        h_layout.addWidget(sub_lbl)
        self.layout_main.addWidget(header_box)

        # 2. Contenedor de iteraciones paso a paso
        for it in iterations:
            k = it["order"]
            p_val = it["p_val"]
            prev_val = it.get("prev_val", 0.0)
            diff_term = it["diff_term"]
            abs_diff = it["abs_diff"]
            formula_ltx = it["formula_latex"]
            is_best = (k == best_order)

            card = QFrame()
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(8, 8, 8, 8)
            card_layout.setSpacing(5)

            # Estilo: si es el orden donde se cumple la condición de error -> borde verde y fondo sutil
            if is_best:
                c_bg = "#064e3b" if self.is_dark_mode else "#dcfce7"
                c_border = "#10b981"
                card.setStyleSheet(
                    f"QFrame {{ background-color: {c_bg}; border: 2px solid {c_border}; border-radius: 6px; }}"
                )
            else:
                c_bg = "#1e293b" if self.is_dark_mode else "#ffffff"
                c_border = "#334155" if self.is_dark_mode else "#e2e8f0"
                card.setStyleSheet(
                    f"QFrame {{ background-color: {c_bg}; border: 1px solid {c_border}; border-radius: 6px; }}"
                )

            # Fila superior de la tarjeta: Badge de Orden y si cumple, badge verde
            top_row = QHBoxLayout()
            lbl_k = QLabel(f" Orden {k} ")
            lbl_k.setStyleSheet(
                "background-color: #3b82f6; color: #ffffff; font-weight: bold; font-size: 10px; border-radius: 3px; padding: 2px 6px;"
            )
            top_row.addWidget(lbl_k)

            if is_best:
                lbl_badge_ok = QLabel(f" ✓ Condición Cumplida: |Resta| < {tol_str} ")
                lbl_badge_ok.setStyleSheet(
                    "background-color: #10b981; color: #ffffff; font-weight: bold; font-size: 10px; border-radius: 3px; padding: 2px 6px;"
                )
                top_row.addWidget(lbl_badge_ok)

            top_row.addStretch()
            card_layout.addLayout(top_row)

            # Render de la fórmula de sustitución en LaTeX
            lbl_math = QLabel()
            try:
                px = GLOBAL_LATEX_RENDERER.render_to_pixmap(formula_ltx, font_size=9.5, color_hex=txt_color)
                if not px.isNull():
                    lbl_math.setPixmap(px)
                else:
                    lbl_math.setText(formula_ltx)
            except Exception:
                lbl_math.setText(formula_ltx)
            lbl_math.setToolTip(formula_ltx)
            card_layout.addWidget(lbl_math)

            # Fila prominente con el resultado visual de la resta
            sub_frame = QFrame()
            if k == 1:
                sub_bg = "#334155" if self.is_dark_mode else "#f1f5f9"
                sub_border = "#475569" if self.is_dark_mode else "#e2e8f0"
                sub_fg = txt_color
                resta_text = f"Valor base: P₁({x_eval:g}) = {p_val:.6g}"
            else:
                if is_best:
                    sub_bg = "#047857" if self.is_dark_mode else "#bbf7d0"
                    sub_border = "#10b981"
                    sub_fg = "#ffffff" if self.is_dark_mode else "#14532d"
                    resta_text = f"Resta: |{p_val:.6g} - {prev_val:.6g}| = {abs_diff:.6g}   (< {tol_str}  ✓ ¡Cumple condición!)"
                else:
                    sub_bg = "#1e293b" if self.is_dark_mode else "#f8fafc"
                    sub_border = "#475569" if self.is_dark_mode else "#cbd5e1"
                    sub_fg = "#cbd5e1" if self.is_dark_mode else "#334155"
                    resta_text = f"Resta: |{p_val:.6g} - {prev_val:.6g}| = {abs_diff:.6g}"

            sub_frame.setStyleSheet(
                f"background-color: {sub_bg}; border: 1px solid {sub_border}; border-radius: 4px;"
            )
            sub_layout = QHBoxLayout(sub_frame)
            sub_layout.setContentsMargins(8, 4, 8, 4)
            lbl_sub = QLabel(resta_text)
            lbl_sub.setStyleSheet(f"font-size: 10.5px; font-weight: 700; color: {sub_fg};")
            sub_layout.addWidget(lbl_sub)
            card_layout.addWidget(sub_frame)

            self.layout_main.addWidget(card)

        # Botón para trasladar la vista de la gráfica al punto inspeccionado
        btn_inspect = QPushButton(f"🎯 Ver punto x = {x_eval:g} en la Gráfica")
        btn_inspect.setStyleSheet(
            "QPushButton { background-color: #2563eb; color: #ffffff; border-radius: 5px; padding: 6px 12px; font-weight: 700; font-size: 11px; margin-top: 4px; }"
            "QPushButton:hover { background-color: #1d4ed8; }"
        )
        btn_inspect.clicked.connect(lambda: self.inspect_eval_point_requested.emit(x_eval))
        self.layout_main.addWidget(btn_inspect)


class TaylorOptionsDialog(QDialog):
    """
    Diálogo modal pop-up estilo GeoGebra para configurar los parámetros de la Serie de Taylor:
    - Punto de expansión x0 (a)
    - Orden máximo n
    - Intervalo de graficación [x_min, x_max]
    - Opciones adicionales (Evaluar en x puntual, Tolerancia de error)
    """
    options_applied = Signal()

    def __init__(self, parent=None, is_dark_mode: bool = False):
        super().__init__(parent)
        self.is_dark_mode = is_dark_mode
        self.setWindowTitle("Configuración de Parámetros")
        self.setModal(True)
        self.setMinimumWidth(380)
        self._setup_ui()
        self.apply_theme(self.is_dark_mode)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        lbl_head = QLabel("⚙ Parámetros de la Serie de Taylor")
        lbl_head.setStyleSheet("font-size: 14px; font-weight: 700; color: #2563eb;")
        layout.addWidget(lbl_head)

        lbl_sub = QLabel("Configura los valores del desarrollo y el rango del plano cartesiano:")
        lbl_sub.setStyleSheet("font-size: 11px; color: #64748b;")
        lbl_sub.setWordWrap(True)
        layout.addWidget(lbl_sub)

        # 1. Parámetros Principales
        box_main = QFrame()
        box_main.setObjectName("optionsGroup")
        lay_main = QVBoxLayout(box_main)
        lay_main.setContentsMargins(12, 12, 12, 12)
        lay_main.setSpacing(8)

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)

        grid.addWidget(QLabel("Punto x₀ (a):"), 0, 0)
        self.spin_x0 = QDoubleSpinBox()
        self.spin_x0.setRange(-1000.0, 1000.0)
        self.spin_x0.setDecimals(2)
        self.spin_x0.setValue(1.0)
        grid.addWidget(self.spin_x0, 0, 1)

        grid.addWidget(QLabel("Orden máx (n):"), 0, 2)
        self.spin_order = QSpinBox()
        self.spin_order.setRange(0, 12)
        self.spin_order.setValue(4)
        grid.addWidget(self.spin_order, 0, 3)

        grid.addWidget(QLabel("Intervalo de:"), 1, 0)
        self.spin_xmin = QDoubleSpinBox()
        self.spin_xmin.setRange(-1000.0, 1000.0)
        self.spin_xmin.setDecimals(2)
        self.spin_xmin.setValue(-2.5)
        grid.addWidget(self.spin_xmin, 1, 1)

        grid.addWidget(QLabel("hasta:"), 1, 2)
        self.spin_xmax = QDoubleSpinBox()
        self.spin_xmax.setRange(-1000.0, 1000.0)
        self.spin_xmax.setDecimals(2)
        self.spin_xmax.setValue(2.5)
        grid.addWidget(self.spin_xmax, 1, 3)

        lay_main.addLayout(grid)
        layout.addWidget(box_main)

        # 2. Opciones Adicionales (Punto b y tolerancia)
        box_adv = QFrame()
        box_adv.setObjectName("optionsGroup")
        lay_adv = QVBoxLayout(box_adv)
        lay_adv.setContentsMargins(12, 12, 12, 12)
        lay_adv.setSpacing(6)

        self.chk_advanced = QCheckBox("Opciones adicionales (Evaluación y Tolerancia)")
        self.chk_advanced.setChecked(False)
        self.chk_advanced.setCursor(Qt.PointingHandCursor)
        self.chk_advanced.setStyleSheet("font-size: 11px; font-weight: 600; color: #2563eb;")
        self.chk_advanced.toggled.connect(self._on_adv_toggled)
        lay_adv.addWidget(self.chk_advanced)

        self.advanced_container = QWidget()
        lay_adv_grid = QGridLayout(self.advanced_container)
        lay_adv_grid.setContentsMargins(0, 4, 0, 0)
        lay_adv_grid.setHorizontalSpacing(10)
        lay_adv_grid.setVerticalSpacing(8)

        lay_adv_grid.addWidget(QLabel("Evaluar en x:"), 0, 0)
        self.spin_x_eval = QDoubleSpinBox()
        self.spin_x_eval.setRange(-1000.0, 1000.0)
        self.spin_x_eval.setDecimals(3)
        self.spin_x_eval.setSingleStep(0.05)
        self.spin_x_eval.setValue(1.25)
        lay_adv_grid.addWidget(self.spin_x_eval, 0, 1)

        lay_adv_grid.addWidget(QLabel("Tolerancia error:"), 1, 0)
        self.combo_tolerance = QComboBox()
        self.combo_tolerance.addItem("10⁻³ (0.001) [Pizarrón]", 0.001)
        self.combo_tolerance.addItem("10⁻⁴ (0.0001) [Pizarrón]", 0.0001)
        self.combo_tolerance.addItem("10⁻² (0.01)", 0.01)
        self.combo_tolerance.addItem("10⁻⁵ (0.00001)", 0.00001)
        self.combo_tolerance.addItem("Sin límite", None)
        lay_adv_grid.addWidget(self.combo_tolerance, 1, 1)

        self.advanced_container.setVisible(False)
        lay_adv.addWidget(self.advanced_container)
        layout.addWidget(box_adv)

        # Botones inferiores: Cancelar y Aplicar
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.addStretch()

        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setFixedSize(90, 32)
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        self.btn_apply = QPushButton("✓ Aplicar")
        self.btn_apply.setFixedSize(110, 32)
        self.btn_apply.setProperty("class", "primary")
        self.btn_apply.clicked.connect(self._on_apply_clicked)
        btn_layout.addWidget(self.btn_apply)

        layout.addLayout(btn_layout)

    def _on_adv_toggled(self, checked: bool):
        self.advanced_container.setVisible(checked)

    def open_dialog(self):
        self._backup = {
            "x0": self.spin_x0.value(),
            "order": self.spin_order.value(),
            "xmin": self.spin_xmin.value(),
            "xmax": self.spin_xmax.value(),
            "adv": self.chk_advanced.isChecked(),
            "x_eval": self.spin_x_eval.value(),
            "tol_idx": self.combo_tolerance.currentIndex(),
        }
        self.exec()

    def reject(self):
        if hasattr(self, "_backup"):
            self.spin_x0.setValue(self._backup["x0"])
            self.spin_order.setValue(self._backup["order"])
            self.spin_xmin.setValue(self._backup["xmin"])
            self.spin_xmax.setValue(self._backup["xmax"])
            self.chk_advanced.setChecked(self._backup["adv"])
            self.spin_x_eval.setValue(self._backup["x_eval"])
            self.combo_tolerance.setCurrentIndex(self._backup["tol_idx"])
        super().reject()

    def _on_apply_clicked(self):
        x_min = self.spin_xmin.value()
        x_max = self.spin_xmax.value()
        if x_min >= x_max:
            QMessageBox.warning(
                self, "Intervalo Inválido",
                f"El límite inferior ({x_min:g}) debe ser menor que el límite superior ({x_max:g})."
            )
            return
        self.accept()
        self.options_applied.emit()

    def apply_theme(self, is_dark: bool):
        self.is_dark_mode = is_dark
        bg = "#18181b" if is_dark else "#ffffff"
        text = "#f4f4f5" if is_dark else "#0f172a"
        card_bg = "#27272a" if is_dark else "#f8fafc"
        border = "#3f3f46" if is_dark else "#cbd5e1"
        btn_bg = "#3f3f46" if is_dark else "#e2e8f0"
        btn_text = "#f4f4f5" if is_dark else "#0f172a"

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {bg};
                color: {text};
            }}
            QFrame#optionsGroup {{
                background-color: {card_bg};
                border: 1px solid {border};
                border-radius: 8px;
            }}
            QLabel {{
                color: {text};
            }}
            QDoubleSpinBox, QSpinBox, QComboBox {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 4px;
                padding: 3px 6px;
                color: {text};
            }}
            QPushButton {{
                background-color: {btn_bg};
                color: {btn_text};
                border: 1px solid {border};
                border-radius: 6px;
                font-weight: 600;
                padding: 4px 12px;
            }}
            QPushButton:hover {{
                border-color: #3b82f6;
            }}
            QPushButton[class="primary"] {{
                background-color: #2563eb;
                color: #ffffff;
                border: none;
            }}
            QPushButton[class="primary"]:hover {{
                background-color: #1d4ed8;
            }}
        """)


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
    inspect_eval_point_requested = Signal(float)

    def __init__(self, parent=None, is_dark_mode: bool = False):
        super().__init__(parent)
        self.is_dark_mode = is_dark_mode
        self.result: Optional[TaylorSeriesResult] = None

        self.cards_map: Dict[int, GeoGebraAlgebraCard] = {}
        self.selected_order: Optional[int] = None

        # Pop-up modal de configuración de parámetros estilo GeoGebra
        self.options_dialog = TaylorOptionsDialog(self, is_dark_mode=self.is_dark_mode)
        self.spin_x0 = self.options_dialog.spin_x0
        self.spin_order = self.options_dialog.spin_order
        self.spin_xmin = self.options_dialog.spin_xmin
        self.spin_xmax = self.options_dialog.spin_xmax
        self.spin_x_eval = self.options_dialog.spin_x_eval
        self.combo_tolerance = self.options_dialog.combo_tolerance
        self.chk_advanced = self.options_dialog.chk_advanced
        self.advanced_container = self.options_dialog.advanced_container

        self.options_dialog.options_applied.connect(self._on_options_applied)
        self.chk_advanced.toggled.connect(self._on_advanced_toggled)

        self._init_ui()

    def sizeHint(self):
        from PySide6.QtCore import QSize
        return QSize(540, 800)

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

        # Fila compacta de Opciones y Resumen de Parámetros (Abre pop-up modal para ahorrar espacio vertical)
        opts_row = QHBoxLayout()
        opts_row.setContentsMargins(0, 2, 0, 2)
        opts_row.setSpacing(6)

        self.btn_options = QPushButton("⚙ Opciones...")
        self.btn_options.setToolTip("Abrir ventana modal para configurar punto x₀, orden n, intervalo y opciones avanzadas")
        self.btn_options.setFixedHeight(28)
        self.btn_options.setCursor(Qt.PointingHandCursor)
        self.btn_options.clicked.connect(self._open_options_dialog)
        opts_row.addWidget(self.btn_options)

        self.lbl_options_summary = QLabel()
        self.lbl_options_summary.setStyleSheet("font-size: 11px; font-weight: 600; color: #2563eb; padding-left: 4px;")
        self._update_options_summary()
        opts_row.addWidget(self.lbl_options_summary, stretch=1)

        in_layout.addLayout(opts_row)

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

        # Pestaña 2: Desarrollo Paso a Paso (como en la libreta y pizarrón, Parte a + Parte b)
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
        self.steps_list_layout.setContentsMargins(0, 0, 0, 24)
        self.steps_list_layout.setSpacing(8)

        # Sub-layout exclusivo para los widgets de cada orden de derivación (Parte a)
        self.steps_items_layout = QVBoxLayout()
        self.steps_items_layout.setContentsMargins(0, 0, 0, 0)
        self.steps_items_layout.setSpacing(6)
        self.steps_list_layout.addLayout(self.steps_items_layout)

        # Caja para la fórmula final construida (con scroll horizontal independiente)
        self.final_formula_box = QFrame()
        self.final_formula_box.setStyleSheet(
            "background-color: #2563eb12; border: 1.5px solid #2563eb; border-radius: 6px; padding: 4px;"
        )
        self.final_formula_box.setMinimumWidth(380)
        self.final_formula_box.setMaximumHeight(170)

        f_box_layout = QVBoxLayout(self.final_formula_box)
        f_box_layout.setContentsMargins(6, 6, 6, 6)
        f_box_layout.setSpacing(4)

        #lbl_f_title = QLabel("Fórmula de Taylor Construida:")
        #lbl_f_title.setStyleSheet("font-weight: 700; font-size: 11px; color: #2563eb;")
        #f_box_layout.addWidget(lbl_f_title)

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

        self.steps_list_layout.addWidget(self.final_formula_box)

        self.steps_list_layout.addStretch()
        self.scroll_steps.setWidget(self.steps_container)
        steps_layout.addWidget(self.scroll_steps)

        self.tabs.addTab(self.tab_steps, "Paso a Paso")

        # Pestaña 3: Vista dedicada exclusiva de Evaluación y Convergencia (Parte b)
        self.tab_eval = QWidget()
        eval_layout = QVBoxLayout(self.tab_eval)
        eval_layout.setContentsMargins(4, 4, 4, 4)

        self.scroll_eval = QScrollArea()
        self.scroll_eval.setWidgetResizable(True)
        self.scroll_eval.setFrameShape(QFrame.NoFrame)
        self.scroll_eval.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_eval.setStyleSheet(slim_scroll_style)

        eval_container = QWidget()
        eval_container_layout = QVBoxLayout(eval_container)
        eval_container_layout.setContentsMargins(0, 0, 0, 20)
        eval_container_layout.setSpacing(6)

        self.whiteboard_widget_tab = WhiteboardConvergenceWidget(is_dark_mode=self.is_dark_mode)
        self.whiteboard_widget_tab.inspect_eval_point_requested.connect(self.inspect_eval_point_requested.emit)
        eval_container_layout.addWidget(self.whiteboard_widget_tab)
        eval_container_layout.addStretch()

        self.scroll_eval.setWidget(eval_container)
        eval_layout.addWidget(self.scroll_eval)

        self.tabs.addTab(self.tab_eval, "Evaluación (Parte b)")

        # Ocultar pestaña de Evaluación a primera vista hasta activar "Opciones adicionales"
        if hasattr(self.tabs, "setTabVisible"):
            self.tabs.setTabVisible(2, False)

        main_layout.addWidget(self.tabs, stretch=1)

    def set_dark_mode(self, is_dark: bool):
        self.is_dark_mode = is_dark
        if hasattr(self, "options_dialog"):
            self.options_dialog.apply_theme(is_dark)
        self._update_options_summary()
        self._update_fx_preview(self.input_fx.text())
        if hasattr(self, "whiteboard_widget_tab"):
            self.whiteboard_widget_tab.is_dark_mode = is_dark
            self.whiteboard_widget_tab.update_style()
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

    def get_selected_tolerance(self) -> Optional[float]:
        return self.combo_tolerance.currentData()

    def set_tolerance(self, tol: Optional[float]):
        if tol is None:
            self.combo_tolerance.setCurrentIndex(self.combo_tolerance.count() - 1)
            return
        for idx in range(self.combo_tolerance.count()):
            val = self.combo_tolerance.itemData(idx)
            if val is not None and abs(val - tol) < 1e-9:
                self.combo_tolerance.setCurrentIndex(idx)
                return

    def _open_options_dialog(self):
        self.options_dialog.open_dialog()

    def _on_options_applied(self):
        self._update_options_summary()
        self._on_advanced_toggled(self.chk_advanced.isChecked())

    def _update_options_summary(self):
        if not hasattr(self, "spin_x0") or not hasattr(self, "lbl_options_summary"):
            return
        x0 = self.spin_x0.value()
        order = self.spin_order.value()
        xmin = self.spin_xmin.value()
        xmax = self.spin_xmax.value()
        adv = self.chk_advanced.isChecked()
        color = "#60a5fa" if self.is_dark_mode else "#2563eb"
        self.lbl_options_summary.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {color}; padding-left: 4px;")
        summary = f"x₀={x0:g} | n={order} | [{xmin:g}, {xmax:g}]"
        if adv:
            summary += f" | x*={self.spin_x_eval.value():g}"
        self.lbl_options_summary.setText(summary)

    def _on_eval_param_changed(self):
        self._update_evaluation_views()

    def _on_advanced_toggled(self, checked: bool):
        if hasattr(self, "tabs") and hasattr(self.tabs, "setTabVisible"):
            self.tabs.setTabVisible(2, checked)
        if checked and self.result is not None:
            self._update_evaluation_views()

    def _update_evaluation_views(self):
        if self.result is None:
            return
        x_eval = self.spin_x_eval.value()
        tol = self.get_selected_tolerance()
        eval_data = self.result.evaluate_point_iterations(x_eval, tolerance=tol)
        if hasattr(self, "whiteboard_widget_tab"):
            self.whiteboard_widget_tab.update_data(eval_data)

    def _clear_lists(self):
        while self.alg_list_layout.count() > 1:
            item = self.alg_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.cards_map.clear()

        while self.steps_items_layout.count() > 0:
            item = self.steps_items_layout.takeAt(0)
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

        # 2. Tarjetas para cada polinomio P_k(x) en la Vista Álgebra y Paso a Paso
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
            self.steps_items_layout.addWidget(step_widget)

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

        # 4. Actualizar visualización de la Parte b en su pestaña de Evaluación
        self._update_evaluation_views()
        is_adv = self.chk_advanced.isChecked()
        if hasattr(self, "tabs") and hasattr(self.tabs, "setTabVisible"):
            self.tabs.setTabVisible(2, is_adv)

    def select_order(self, order: Optional[int]):
        self.selected_order = order
        for k, card in self.cards_map.items():
            card.set_selected(k == order)

    def _on_card_clicked(self, order: int):
        self.select_order(order)
        self.order_selected.emit(order)

    def set_inputs(
        self,
        func_str: str,
        x0: float,
        x_min: float,
        x_max: float,
        order: int,
        x_eval: Optional[float] = None,
        tolerance: Optional[float] = None
    ):
        self.input_fx.setText(func_str)
        self.spin_x0.setValue(x0)
        self.spin_xmin.setValue(x_min)
        self.spin_xmax.setValue(x_max)
        self.spin_order.setValue(order)
        if x_eval is not None:
            self.spin_x_eval.setValue(x_eval)
        if tolerance is not None:
            self.set_tolerance(tolerance)
        if x_eval is not None or tolerance is not None:
            self.chk_advanced.setChecked(True)
        else:
            self.chk_advanced.setChecked(False)
        self._update_options_summary()
        self._on_advanced_toggled(self.chk_advanced.isChecked())
