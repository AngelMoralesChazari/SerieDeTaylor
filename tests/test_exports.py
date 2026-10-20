"""
Pruebas automatizadas para los módulos de exportación a CSV y PDF.
"""

import os
import tempfile
import numpy as np
from PySide6.QtWidgets import QApplication

from taylor_engine import TaylorEngine
from error_analysis import ErrorAnalyzer
from export_manager import ExportManager


def test_export_csv_and_pdf():
    # Inicializar QApplication si no existe
    app = QApplication.instance() or QApplication([])

    engine = TaylorEngine()
    analyzer = ErrorAnalyzer()

    res = engine.compute_series("exp(x)", a=0.0, x_min=0.0, x_max=1.0, max_order=2)
    x_mesh = np.linspace(0.0, 1.0, 50)
    y_true = res.func_eval(x_mesh)

    metrics_map = {}
    for step in res.steps:
        y_p = step.eval_func(x_mesh)
        metrics_map[step.order] = analyzer.compute_metrics(
            order=step.order, x=x_mesh, y_true=y_true, y_pred=y_p
        )

    # 1. Probar exportación a CSV
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f_csv:
        csv_path = f_csv.name

    try:
        ExportManager.export_to_csv(csv_path, res, metrics_map, num_samples=20)
        assert os.path.exists(csv_path)
        assert os.path.getsize(csv_path) > 100

        with open(csv_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert "REPORTE DE CÁLCULO DE SERIE DE TAYLOR" in content
            assert "exp(x)" in content
            assert "P_0" in content
    finally:
        if os.path.exists(csv_path):
            os.remove(csv_path)

    # 2. Probar exportación a PDF
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f_pdf:
        pdf_path = f_pdf.name

    try:
        ExportManager.export_to_pdf(pdf_path, res, metrics_map)
        assert os.path.exists(pdf_path)
        assert os.path.getsize(pdf_path) > 500
    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
