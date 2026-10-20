"""
Diálogo para consultar y exportar la tabla numérica completa de valores y errores.
Incluye columnas para x, f(x), cada aproximación P_k(x) y cada error E_k(x).
"""

from __future__ import annotations

from typing import Optional, Dict
import numpy as np
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QLabel, QSpinBox,
    QFileDialog, QMessageBox, QHeaderView
)
from PySide6.QtCore import Qt

from taylor_engine import TaylorSeriesResult
from error_analysis import OrderErrorCurves


class ValuesTableDialog(QDialog):
    """
    Ventana emergente con la tabla de valores numéricos de las funciones y errores.
    """

    def __init__(
        self,
        result: TaylorSeriesResult,
        error_curves: Dict[int, OrderErrorCurves],
        parent=None,
        is_dark_mode: bool = False
    ):
        super().__init__(parent)
        self.setWindowTitle("Tabla de Valores Numéricos y Errores - Serie de Taylor")
        self.resize(850, 520)

        self.result = result
        self.error_curves = error_curves
        self.is_dark_mode = is_dark_mode

        self._init_ui()
        self._populate_table(num_rows=25)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Barra superior con controles de muestreo
        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel("Filas de muestreo:"))

        self.spin_rows = QSpinBox()
        self.spin_rows.setRange(5, 500)
        self.spin_rows.setValue(25)
        self.spin_rows.valueChanged.connect(self._populate_table)
        top_bar.addWidget(self.spin_rows)

        top_bar.addStretch()

        btn_export = QPushButton("Exportar a CSV...")
        btn_export.setProperty("class", "primary")
        btn_export.clicked.connect(self._export_csv)
        top_bar.addWidget(btn_export)

        layout.addLayout(top_bar)

        # Tabla
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

    def _populate_table(self, num_rows: int):
        res = self.result
        x_pts = np.linspace(res.x_min, res.x_max, num_rows)
        y_f = res.func_eval(x_pts)

        # Preparar encabezados
        headers = ["x", f"f(x)"]
        for step in res.steps:
            headers.append(f"P_{step.order}(x)")
        for step in res.steps:
            headers.append(f"E_{step.order}(x)")

        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(num_rows)

        # Evaluar cada polinomio en x_pts
        poly_evals = {step.order: step.eval_func(x_pts) for step in res.steps}

        for i, x_val in enumerate(x_pts):
            # Col 0: x
            self.table.setItem(i, 0, QTableWidgetItem(f"{x_val:.5g}"))

            # Col 1: f(x)
            f_val = y_f[i]
            self.table.setItem(i, 1, QTableWidgetItem(f"{f_val:.6g}" if np.isfinite(f_val) else "Indefinido"))

            col_idx = 2
            # Polinomios
            for step in res.steps:
                p_val = poly_evals[step.order][i]
                self.table.setItem(i, col_idx, QTableWidgetItem(f"{p_val:.6g}" if np.isfinite(p_val) else "Indefinido"))
                col_idx += 1

            # Errores
            for step in res.steps:
                p_val = poly_evals[step.order][i]
                if np.isfinite(f_val) and np.isfinite(p_val):
                    err_val = abs(f_val - p_val)
                    err_str = f"{err_val:.4e}" if err_val < 1e-3 else f"{err_val:.6g}"
                else:
                    err_str = "—"
                self.table.setItem(i, col_idx, QTableWidgetItem(err_str))
                col_idx += 1

        self.table.resizeColumnsToContents()

    def _export_csv(self):
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Guardar Tabla de Valores como CSV", "serie_taylor_tabla_valores.csv", "Archivos CSV (*.csv)"
        )
        if not filepath:
            return

        try:
            import csv
            with open(filepath, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)

                # Cabecera
                headers = [self.table.horizontalHeaderItem(c).text() for c in range(self.table.columnCount())]
                writer.writerow(headers)

                # Filas
                for r in range(self.table.rowCount()):
                    row_data = [self.table.item(r, c).text() for c in range(self.table.columnCount())]
                    writer.writerow(row_data)

            QMessageBox.information(self, "Exportación Exitosa", f"Archivo CSV guardado correctamente en:\n{filepath}")
        except Exception as exc:
            QMessageBox.critical(self, "Error de Exportación", f"No se pudo guardar el archivo:\n{str(exc)}")
