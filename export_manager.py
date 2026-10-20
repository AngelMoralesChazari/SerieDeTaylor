"""
Módulo de exportación de resultados matemáticos y gráficos.
Permite exportar tablas de datos y métricas a archivos CSV,
y generar reportes tipográficos completos en formato PDF con gráficos y fórmulas embebidos.
"""

from __future__ import annotations

import csv
import io
import base64
from datetime import datetime
from typing import Dict, Optional, List
import numpy as np

from PySide6.QtGui import QTextDocument, QPdfWriter, QPageSize, QPageLayout
from PySide6.QtCore import QSizeF

from taylor_engine import TaylorSeriesResult, TaylorOrderStep
from error_analysis import OrderErrorMetrics, OrderErrorCurves
from latex_renderer import GLOBAL_LATEX_RENDERER


class ExportManager:
    """Gestiona la exportación de resultados a CSV y PDF profesional."""

    @staticmethod
    def export_to_csv(
        filepath: str,
        result: TaylorSeriesResult,
        metrics_map: Dict[int, OrderErrorMetrics],
        num_samples: int = 100
    ) -> None:
        """
        Exporta los metadatos, tabla de errores y muestreo numérico a CSV.
        """
        with open(filepath, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # 1. Metadatos del cálculo
            writer.writerow(["# REPORTE DE CÁLCULO DE SERIE DE TAYLOR"])
            writer.writerow(["# Fecha de generación", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
            writer.writerow(["# Función f(x)", result.func_input])
            writer.writerow(["# Expresión simbólica", str(result.func_sym)])
            writer.writerow(["# Punto de expansión x0", result.x0])
            writer.writerow(["# Intervalo de visualización", f"[{result.x_min}, {result.x_max}]"])
            writer.writerow(["# Orden máximo calculado", result.max_order])
            writer.writerow([])

            # 2. Resumen de polinomios y métricas de error
            writer.writerow(["RESUMEN DE APROXIMACIONES"])
            writer.writerow([
                "Orden (k)",
                "Derivada f^(k)(x0)",
                "Polinomio P_k(x) [Taylor]",
                "Polinomio Expandido"
            ])

            for step in result.steps:
                k = step.order
                writer.writerow([
                    k,
                    f"{step.derivative_at_x0_val:.6g}",
                    step.poly_taylor_latex,
                    str(step.poly_expanded_sym)
                ])

            writer.writerow([])

            # 3. Malla de evaluación numérica detallada
            writer.writerow(["TABLA DETALLADA DE PUNTOS EVALUADOS SOBRE EL INTERVALO"])
            x_pts = np.linspace(result.x_min, result.x_max, num_samples)
            y_f = result.func_eval(x_pts)
            poly_evals = {step.order: step.eval_func(x_pts) for step in result.steps}

            # Cabecera de la tabla
            cols = ["x", "f(x)"]
            for step in result.steps:
                cols.append(f"P_{step.order}(x)")
            for step in result.steps:
                cols.append(f"E_{step.order}(x)")
            writer.writerow(cols)

            # Filas
            for i in range(num_samples):
                row = [f"{x_pts[i]:.6g}"]
                row.append(f"{y_f[i]:.8g}" if np.isfinite(y_f[i]) else "NaN")

                for step in result.steps:
                    p_val = poly_evals[step.order][i]
                    row.append(f"{p_val:.8g}" if np.isfinite(p_val) else "NaN")

                for step in result.steps:
                    p_val = poly_evals[step.order][i]
                    if np.isfinite(y_f[i]) and np.isfinite(p_val):
                        row.append(f"{abs(y_f[i] - p_val):.8e}")
                    else:
                        row.append("NaN")

                writer.writerow(row)

    @staticmethod
    def export_to_pdf(
        filepath: str,
        result: TaylorSeriesResult,
        metrics_map: Dict[int, OrderErrorMetrics],
        main_plot_bytes: Optional[bytes] = None,
        error_plot_bytes: Optional[bytes] = None
    ) -> None:
        """
        Genera un informe en PDF con formato tipográfico, tablas y gráficos.
        """
        doc = QTextDocument()

        # Construir contenido HTML estilizado
        html = []
        html.append("""
        <style>
            body { font-family: Helvetica, Arial, sans-serif; color: #1e293b; font-size: 11pt; line-height: 1.4; }
            h1 { color: #1e40af; font-size: 20pt; margin-bottom: 4px; }
            h2 { color: #2563eb; font-size: 14pt; border-bottom: 1px solid #cbd5e1; padding-bottom: 4px; margin-top: 16px; }
            h3 { color: #334155; font-size: 12pt; margin-top: 12px; }
            .meta-box { background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 10px; margin-bottom: 14px; }
            table { width: 100%; border-collapse: collapse; margin-top: 8px; margin-bottom: 14px; }
            th { background-color: #f1f5f9; color: #334155; font-weight: bold; border: 1px solid #cbd5e1; padding: 6px; font-size: 9pt; }
            td { border: 1px solid #e2e8f0; padding: 6px; font-size: 9pt; }
            .step-box { background-color: #ffffff; border: 1px solid #e2e8f0; border-left: 3px solid #2563eb; padding: 8px; margin-bottom: 10px; }
            .formula { font-family: 'Courier New', monospace; font-weight: bold; color: #0f172a; }
            .explanation { font-style: italic; color: #475569; font-size: 9pt; }
            .plot-img { width: 95%; max-width: 600px; margin: 10px auto; display: block; }
        </style>
        """)

        html.append(f"""
        <h1>Reporte: Serie de Taylor (GeoGebra)</h1>
        <p style="color: #64748b; font-size: 9pt;">Generado automáticamente el {datetime.now().strftime('%d/%m/%Y a las %H:%M:%S')}</p>
        
        <div class="meta-box">
            <b>Parámetros del Cálculo:</b><br/>
            • <b>Función original f(x):</b> {result.func_input}<br/>
            • <b>Punto de expansión (x₀):</b> {result.x0:g}<br/>
            • <b>Intervalo de visualización:</b> [{result.x_min:g}, {result.x_max:g}]<br/>
            • <b>Orden máximo calculado:</b> {result.max_order}
        </div>
        """)

        # Gráfico principal si está disponible
        if main_plot_bytes:
            b64_main = base64.b64encode(main_plot_bytes).decode("utf-8")
            html.append(f"""
            <h2>1. Representación Gráfica (GeoGebra)</h2>
            <p style="text-align: center;"><img class="plot-img" src="data:image/png;base64,{b64_main}" width="550" /></p>
            """)

        # Tabla de Polinomios
        html.append("""
        <h2>2. Resumen de Polinomios de Taylor</h2>
        <table>
            <tr>
                <th>Orden (k)</th>
                <th>f^(k)(x₀)</th>
                <th>Polinomio P_k(x) [Forma de Taylor]</th>
                <th>Polinomio Expandido</th>
            </tr>
        """)

        for step in result.steps:
            k = step.order
            html.append(f"""
            <tr>
                <td style="text-align: center;"><b>P_{k}</b></td>
                <td>{step.derivative_at_x0_val:.6g}</td>
                <td class="formula">{step.poly_taylor_latex}</td>
                <td class="formula">{str(step.poly_expanded_sym)}</td>
            </tr>
            """)

        html.append("</table>")

        # Desarrollo Matemático Paso a Paso
        html.append("<h2>3. Desarrollo Matemático Paso a Paso</h2>")
        for step in result.steps:
            k = step.order
            html.append(f"""
            <div class="step-box">
                <b>Aproximación de Orden {k}:</b><br/>
                • <b>Derivada simbólica:</b> f^({k})(x) = {str(step.derivative_simplified)}<br/>
                • <b>Evaluación en x₀ = {result.x0:g}:</b> f^({k})({result.x0:g}) = {step.derivative_at_x0_val:.6g}<br/>
                • <b>Término añadido:</b> {step.term_taylor_latex}<br/>
                • <b>Polinomio acumulado P_{k}(x):</b> {step.poly_taylor_latex}<br/>
            </div>
            """)

        # Fórmula final construida
        html.append(f"""
        <div style="background-color: #eff6ff; border: 2px solid #2563eb; border-radius: 6px; padding: 10px; margin-top: 14px;">
            <b>Fórmula de Taylor Construida:</b><br/>
            <span class="formula" style="font-size: 11pt; color: #1e40af;">f(x) ≈ {result.constructed_taylor_formula_latex}</span><br/><br/>
            <b>Forma Expandida:</b><br/>
            <span class="formula">{result.expanded_formula_latex}</span>
        </div>
        """)

        doc.setHtml("".join(html))

        writer = QPdfWriter(filepath)
        writer.setPageSize(QPageSize(QPageSize.A4))
        writer.setResolution(150)
        writer.setPageMargins(QPageLayout().margins())

        doc.print_(writer)
