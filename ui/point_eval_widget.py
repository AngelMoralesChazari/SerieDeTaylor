"""
Widget de exploración interactiva de puntos sobre el plano cartesiano.
Permite evaluar cualquier x = c en el intervalo, mostrando f(c), P_n(c),
error absoluto, error con signo y error relativo, comparando órdenes.
"""

from __future__ import annotations

from typing import Optional, Dict
import numpy as np
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QDoubleSpinBox,
    QSlider, QComboBox, QFrame, QGridLayout, QPushButton
)
from PySide6.QtCore import Qt, Signal

from taylor_engine import TaylorSeriesResult, TaylorOrderStep


class PointEvaluationWidget(QFrame):
    """
    Barra interactiva para consultar y evaluar puntos x = c en tiempo real.
    """
    point_value_changed = Signal(float)       # Emite c cuando cambia
    order_changed = Signal(int)               # Emite orden seleccionado

    def __init__(self, parent=None, is_dark_mode: bool = False):
        super().__init__(parent)
        self.setObjectName("pointEvalWidget")
        self.setProperty("class", "card")

        self.is_dark_mode = is_dark_mode
        self.result: Optional[TaylorSeriesResult] = None
        self.current_order: int = 0
        self.is_updating_ui: bool = False

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        # Fila 1: Controles de entrada (c y orden)
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(12)

        lbl_title = QLabel("Exploración Puntual:")
        lbl_title.setStyleSheet("font-weight: 700; color: #2563eb;")
        controls_layout.addWidget(lbl_title)

        controls_layout.addWidget(QLabel("x ="))
        self.spin_c = QDoubleSpinBox()
        self.spin_c.setRange(-1000.0, 1000.0)
        self.spin_c.setDecimals(4)
        self.spin_c.setSingleStep(0.05)
        self.spin_c.setValue(0.5)
        self.spin_c.valueChanged.connect(self._on_spin_changed)
        controls_layout.addWidget(self.spin_c)

        # Slider para barrido continuo suave
        self.slider_c = QSlider(Qt.Horizontal)
        self.slider_c.setRange(0, 1000)
        self.slider_c.setValue(500)
        self.slider_c.valueChanged.connect(self._on_slider_changed)
        controls_layout.addWidget(self.slider_c, stretch=1)

        controls_layout.addWidget(QLabel("Comparar con:"))
        self.combo_order = QComboBox()
        self.combo_order.currentIndexChanged.connect(self._on_order_combo_changed)
        controls_layout.addWidget(self.combo_order)

        layout.addLayout(controls_layout)

        # Fila 2: Tarjetas de métricas de resultados
        results_grid = QGridLayout()
        results_grid.setSpacing(8)

        # Caja Real f(c)
        self.box_fc = self._create_value_box("Valor Real f(c)", "#2563eb")
        results_grid.addWidget(self.box_fc["frame"], 0, 0)

        # Caja Aproximado P_n(c)
        self.box_pc = self._create_value_box("Aproximación Pₙ(c)", "#10b981")
        results_grid.addWidget(self.box_pc["frame"], 0, 1)

        # Caja Error Absoluto
        self.box_err_abs = self._create_value_box("Error Absoluto |f - Pₙ|", "#f59e0b")
        results_grid.addWidget(self.box_err_abs["frame"], 0, 2)

        # Caja Error con Signo (Residuo)
        self.box_err_signed = self._create_value_box("Residuo f(c) - Pₙ(c)", "#8b5cf6")
        results_grid.addWidget(self.box_err_signed["frame"], 0, 3)

        # Caja Error Relativo
        self.box_err_rel = self._create_value_box("Error Relativo %", "#06b6d4")
        results_grid.addWidget(self.box_err_rel["frame"], 0, 4)

        layout.addLayout(results_grid)

    def _create_value_box(self, title: str, accent_color: str) -> dict:
        frame = QFrame()
        frame.setStyleSheet(
            f"background-color: transparent; border: 1px solid {accent_color}44; "
            f"border-left: 3px solid {accent_color}; border-radius: 4px; padding: 4px 8px;"
        )
        l = QVBoxLayout(frame)
        l.setContentsMargins(4, 2, 4, 2)
        l.setSpacing(1)

        lbl_t = QLabel(title)
        lbl_t.setStyleSheet("font-size: 10px; color: #64748b; font-weight: 600;")
        l.addWidget(lbl_t)

        lbl_v = QLabel("—")
        lbl_v.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {accent_color};")
        l.addWidget(lbl_v)

        return {"frame": frame, "title_lbl": lbl_t, "val_lbl": lbl_v}

    def set_dark_mode(self, is_dark: bool):
        self.is_dark_mode = is_dark

    def update_data(self, result: TaylorSeriesResult, current_order: Optional[int] = None):
        self.result = result
        self.is_updating_ui = True

        # Configurar límites del slider y spinbox
        self.spin_c.setRange(result.x_min - 10.0, result.x_max + 10.0)

        # Actualizar opciones del combo box
        self.combo_order.clear()
        for step in result.steps:
            self.combo_order.addItem(f"Orden {step.order} (P_{step.order})", step.order)

        if current_order is not None and 0 <= current_order < len(result.steps):
            self.combo_order.setCurrentIndex(current_order)
            self.current_order = current_order
        elif result.steps:
            # Seleccionar por defecto el orden más alto
            self.combo_order.setCurrentIndex(len(result.steps) - 1)
            self.current_order = result.steps[-1].order

        # Inicializar punto c por defecto en el punto medio del intervalo o en x_max
        c_default = (result.x_min + result.x_max) / 2.0
        self.spin_c.setValue(c_default)
        self._sync_slider_from_value(c_default)

        self.is_updating_ui = False
        self.evaluate_point(c_default)

    def set_selected_order(self, order: int):
        idx = self.combo_order.findData(order)
        if idx >= 0:
            self.combo_order.setCurrentIndex(idx)

    def set_point_c(self, c: float):
        self.spin_c.setValue(c)

    def evaluate_point(self, c: float):
        """Calcula f(c), P_n(c) y las métricas de error correspondientes."""
        if self.result is None:
            return

        res = self.result
        order = self.combo_order.currentData()
        if order is None:
            order = self.current_order

        step = res.get_step(order)
        if not step:
            return

        # Evaluar f(c)
        try:
            fc_val = float(res.func_eval(c))
        except Exception:
            fc_val = np.nan

        # Evaluar P_n(c)
        try:
            pc_val = float(step.eval_func(c))
        except Exception:
            pc_val = np.nan

        # Mostrar f(c)
        if np.isfinite(fc_val):
            self.box_fc["val_lbl"].setText(f"{fc_val:.6g}")
        else:
            self.box_fc["val_lbl"].setText("Indefinido")

        # Mostrar P_n(c)
        self.box_pc["title_lbl"].setText(f"Aproximación P_{order}(c)")
        if np.isfinite(pc_val):
            self.box_pc["val_lbl"].setText(f"{pc_val:.6g}")
        else:
            self.box_pc["val_lbl"].setText("Indefinido")

        # Errores
        if np.isfinite(fc_val) and np.isfinite(pc_val):
            signed_err = fc_val - pc_val
            abs_err = abs(signed_err)

            self.box_err_abs["val_lbl"].setText(f"{abs_err:.6e}" if abs_err < 1e-4 else f"{abs_err:.6g}")
            self.box_err_signed["val_lbl"].setText(f"{signed_err:+.6e}" if abs(signed_err) < 1e-4 else f"{signed_err:+.6g}")

            # Error relativo
            if abs(fc_val) > 1e-10:
                rel_pct = (abs_err / abs(fc_val)) * 100.0
                self.box_err_rel["val_lbl"].setText(f"{rel_pct:.4g} %")
                self.box_err_rel["val_lbl"].setStyleSheet("font-size: 13px; font-weight: 700; color: #06b6d4;")
            else:
                self.box_err_rel["val_lbl"].setText("f(c) ≈ 0 (No fiable)")
                self.box_err_rel["val_lbl"].setStyleSheet("font-size: 11px; font-weight: 600; color: #94a3b8;")
        else:
            self.box_err_abs["val_lbl"].setText("—")
            self.box_err_signed["val_lbl"].setText("—")
            self.box_err_rel["val_lbl"].setText("—")

        self.point_value_changed.emit(c)

    def _on_spin_changed(self, val: float):
        if not self.is_updating_ui:
            self._sync_slider_from_value(val)
            self.evaluate_point(val)

    def _on_slider_changed(self, slider_val: int):
        if not self.is_updating_ui and self.result is not None:
            # Mapear de 0-1000 a [x_min, x_max]
            res = self.result
            val = res.x_min + (slider_val / 1000.0) * (res.x_max - res.x_min)
            self.is_updating_ui = True
            self.spin_c.setValue(val)
            self.is_updating_ui = False
            self.evaluate_point(val)

    def _sync_slider_from_value(self, val: float):
        if self.result is None:
            return
        res = self.result
        span = res.x_max - res.x_min
        if span > 0:
            ratio = (val - res.x_min) / span
            slider_pos = int(np.clip(ratio, 0.0, 1.0) * 1000)
            self.is_updating_ui = True
            self.slider_c.setValue(slider_pos)
            self.is_updating_ui = False

    def _on_order_combo_changed(self, idx: int):
        if not self.is_updating_ui:
            order = self.combo_order.currentData()
            if order is not None:
                self.current_order = order
                self.order_changed.emit(order)
                self.evaluate_point(self.spin_c.value())
