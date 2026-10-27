"""
Ventana principal de la aplicación con la distribución y estética oficial de GeoGebra Suite Calculadora (Imagen 2).
- Panel izquierdo delgado (Vista Álgebra con lista de ecuaciones y desarrollo matemático como en la Imagen 4).
- Plano cartesiano central ocupando el 80% de la pantalla (función azul sólida, Taylor punteadas, x0 en rojo).
- Teclado matemático virtual integrado en la parte inferior con botón para expandir/colapsar.
"""

from __future__ import annotations

import io
from typing import Optional, Dict
import numpy as np

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QToolBar, QPushButton, QLabel,
    QFileDialog, QMessageBox, QStatusBar, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QIcon, QKeySequence, QShortcut

from taylor_engine import TaylorEngine, TaylorSeriesResult
from plot_manager import GeoGebraCartesianCanvas, MinimalNavigationToolbar
from ui.sidebar_panel import SidebarPanel
from ui.math_keyboard import GeoGebraVirtualKeyboard
from ui.values_table_dialog import ValuesTableDialog
from ui.styles import get_application_stylesheet
from export_manager import ExportManager


class MainWindow(QMainWindow):
    """
    Ventana principal con distribución GeoGebra Suite.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Serie de Taylor")
        self.resize(1360, 820)
        self.setMinimumSize(960, 600)

        self.is_dark_mode = False
        self.taylor_engine = TaylorEngine()

        self.current_result: Optional[TaylorSeriesResult] = None
        self.selected_order: Optional[int] = None

        self._init_ui()
        self._setup_shortcuts()
        self.apply_theme()

        # Cargar por defecto el ejercicio a) de la libreta (Imagen 4): x^4 - 3x^2 + 1 con x0 = 1
        self.sidebar.set_inputs(
            func_str="x^4 - 3x^2 + 1",
            x0=1.0,
            x_min=-2.5,
            x_max=2.5,
            order=4
        )
        # Desacoplar el cálculo inicial para que la ventana abra de forma inmediata (< 0.5 s)
        QTimer.singleShot(
            30,
            lambda: self.solve_series("x^4 - 3x^2 + 1", x0=1.0, x_min=-2.5, x_max=2.5, max_order=4)
        )

    def _init_ui(self):
        # 1. Contenedor central principal
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Splitter horizontal: Panel Izquierdo (Álgebra) + Panel Central (Gráfica)
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.setHandleWidth(5)

        # Panel Izquierdo: (Vista Álgebra y Paso a Paso) - ocupa toda la altura del lateral izquierdo
        self.sidebar = SidebarPanel(is_dark_mode=self.is_dark_mode)
        self.sidebar.setMinimumWidth(320)
        self.sidebar.setMaximumWidth(1000) # Ancho máximo expandible del panel izquierdo
        self.main_splitter.addWidget(self.sidebar)

        # Panel Central: Barra superior alineada a la derecha, Gráfica protagonista y Teclado
        self.center_graph_panel = QWidget()
        graph_vbox = QVBoxLayout(self.center_graph_panel)
        graph_vbox.setContentsMargins(0, 0, 0, 0)
        graph_vbox.setSpacing(0)

        # Barra superior ubicada exclusivamente sobre el panel derecho, con botones desplazados a la derecha
        self.top_toolbar = self._create_top_toolbar()
        graph_vbox.addWidget(self.top_toolbar)

        # Lienzo Cartesiano Matplotlib puro estilo GeoGebra (con botonera flotante y navegación por arrastre)
        self.canvas = GeoGebraCartesianCanvas(is_dark_mode=self.is_dark_mode)
        self.canvas_toolbar = MinimalNavigationToolbar(self.canvas, self.center_graph_panel)
        self.canvas_toolbar.hide()
        graph_vbox.addWidget(self.canvas, stretch=1)

        # 3. Teclado matemático virtual GeoGebra (ubicado en el panel derecho debajo de la gráfica)
        self.virtual_keyboard = GeoGebraVirtualKeyboard(is_dark_mode=self.is_dark_mode)
        self.virtual_keyboard.set_target_input(self.sidebar.input_fx)
        self.virtual_keyboard.expression_confirmed.connect(self.sidebar._on_solve_clicked)
        self.virtual_keyboard.show()
        graph_vbox.addWidget(self.virtual_keyboard)

        self.main_splitter.addWidget(self.center_graph_panel)
        self.main_splitter.setStretchFactor(0, 0)
        self.main_splitter.setStretchFactor(1, 1)
        self.main_splitter.setSizes([540, 820])

        main_layout.addWidget(self.main_splitter, stretch=1)

        # 4. Barra de estado
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Listo para calcular Series de Taylor.")

        self._connect_signals()

    def _create_top_toolbar(self) -> QToolBar:
        toolbar = QToolBar("Barra GeoGebra")
        toolbar.setIconSize(QSize(18, 18))
        toolbar.setMovable(False)

        # Espaciador para desplazar todas las opciones a la derecha junto a Modo Oscuro
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        toolbar.addWidget(spacer)

        btn_table = QPushButton("📊 Tabla de Valores")
        btn_table.clicked.connect(self._open_values_table)
        toolbar.addWidget(btn_table)

        btn_pdf = QPushButton("📄 Exportar PDF")
        btn_pdf.clicked.connect(self._export_pdf)
        toolbar.addWidget(btn_pdf)

        btn_csv = QPushButton("💾 Exportar CSV")
        btn_csv.clicked.connect(self._export_csv)
        toolbar.addWidget(btn_csv)

        toolbar.addSeparator()

        self.btn_toggle_kbd = QPushButton("⌨ Teclado")
        self.btn_toggle_kbd.setCheckable(True)
        self.btn_toggle_kbd.setChecked(True)
        self.btn_toggle_kbd.clicked.connect(self._toggle_virtual_keyboard)
        toolbar.addWidget(self.btn_toggle_kbd)

        toolbar.addSeparator()

        self.btn_theme = QPushButton("🌙 Modo Oscuro")
        self.btn_theme.clicked.connect(self._toggle_theme)
        toolbar.addWidget(self.btn_theme)

        return toolbar

    def _connect_signals(self):
        self.sidebar.solve_requested.connect(self.solve_series)
        self.sidebar.curve_visibility_changed.connect(self.canvas.set_curve_visibility)
        self.sidebar.func_visibility_changed.connect(self.canvas.set_func_visibility)
        self.sidebar.order_selected.connect(self._on_order_selected)
        self.sidebar.inspect_eval_point_requested.connect(
            lambda x_val: self.canvas.show_exact_intersection_point(x_val)
        )

        self.canvas.point_inspected.connect(self._on_point_inspected)

    def _setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+R"), self, self.sidebar._on_solve_clicked)
        QShortcut(QKeySequence("Ctrl+K"), self, self._toggle_virtual_keyboard)
        QShortcut(QKeySequence("Ctrl+P"), self, self._export_pdf)

    def apply_theme(self):
        self.setStyleSheet(get_application_stylesheet(self.is_dark_mode))
        self.canvas.set_dark_mode(self.is_dark_mode)
        self.sidebar.set_dark_mode(self.is_dark_mode)
        self.btn_theme.setText("☀️ Modo Claro" if self.is_dark_mode else "🌙 Modo Oscuro")

    def _toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        self.apply_theme()

    def _toggle_virtual_keyboard(self):
        is_visible = self.virtual_keyboard.isVisible()
        self.virtual_keyboard.setVisible(not is_visible)
        self.btn_toggle_kbd.setChecked(not is_visible)

    def solve_series(
        self,
        func_str: str,
        x0: float,
        x_min: float,
        x_max: float,
        max_order: int
    ):
        """
        Calcula la serie de Taylor alrededor de x0 para visualizar en [x_min, x_max].
        """
        self.status_bar.showMessage(f"Calculando Serie de Taylor de {func_str} en x₀ = {x0}...")

        try:
            result = self.taylor_engine.compute_series(
                func_expr=func_str,
                x0=x0,
                x_min=x_min,
                x_max=x_max,
                max_order=max_order
            )

            self.current_result = result

            # Actualizar lienzo de Matplotlib
            self.canvas.update_data(result)

            # Actualizar panel lateral (Vista Álgebra y Paso a Paso)
            self.sidebar.display_results(result)

            self.status_bar.showMessage(
                f"✓ Serie calculada con éxito alrededor de x₀ = {x0:g} hasta orden {max_order}.",
                5000
            )

        except Exception as exc:
            self.status_bar.showMessage(f"Error: {str(exc)}", 8000)
            QMessageBox.critical(
                self,
                "Error en el Cálculo",
                f"No se pudo resolver la función ingresada:\n\n{str(exc)}\n\n"
                f"Verifica la sintaxis de la expresión y que sea derivable en x₀ = {x0:g}."
            )

    def _on_order_selected(self, order: int):
        self.selected_order = order if order >= 0 else None
        self.canvas.select_order(self.selected_order)
        self.sidebar.select_order(self.selected_order)
        self.canvas.show_exact_intersection_point()

    def _on_point_inspected(self, x_val: float, y_val: float):
        self.status_bar.showMessage(f"Punto inspeccionado: x = {x_val:.4f}, f(x) = {y_val:.4f}")

    def _open_values_table(self):
        if not self.current_result:
            QMessageBox.information(self, "Sin Datos", "Primero calcula una serie de Taylor.")
            return

        dialog = ValuesTableDialog(
            result=self.current_result,
            error_curves={},
            parent=self,
            is_dark_mode=self.is_dark_mode
        )
        dialog.exec()

    def _export_csv(self):
        if not self.current_result:
            QMessageBox.information(self, "Sin Datos", "Primero calcula una serie de Taylor.")
            return

        filepath, _ = QFileDialog.getSaveFileName(
            self, "Exportar Reporte a CSV", "serie_taylor_reporte.csv", "Archivos CSV (*.csv)"
        )
        if not filepath:
            return

        try:
            ExportManager.export_to_csv(
                filepath=filepath,
                result=self.current_result,
                metrics_map={},
                num_samples=100
            )
            QMessageBox.information(self, "Éxito", f"Archivo CSV guardado en:\n{filepath}")
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"No se pudo exportar a CSV:\n{str(exc)}")

    def _export_pdf(self):
        if not self.current_result:
            QMessageBox.information(self, "Sin Datos", "Primero calcula una serie de Taylor.")
            return

        filepath, _ = QFileDialog.getSaveFileName(
            self, "Exportar Reporte a PDF", "serie_taylor_reporte.pdf", "Archivos PDF (*.pdf)"
        )
        if not filepath:
            return

        try:
            buf = io.BytesIO()
            self.canvas.figure.savefig(buf, format="png", dpi=200, bbox_inches="tight")
            plot_bytes = buf.getvalue()

            ExportManager.export_to_pdf(
                filepath=filepath,
                result=self.current_result,
                metrics_map={},
                main_plot_bytes=plot_bytes,
                error_plot_bytes=None
            )
            QMessageBox.information(self, "Éxito", f"Reporte en PDF generado en:\n{filepath}")
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"No se pudo exportar a PDF:\n{str(exc)}")
