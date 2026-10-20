"""
Módulo de cálculo y análisis exhaustivo del error en aproximaciones de Taylor.
Incluye error absoluto, con signo, relativo, métricas globales (máximo, medio, RMSE),
evaluación puntual y comparación entre órdenes consecutivos.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple, List
import numpy as np


@dataclass
class OrderErrorMetrics:
    """Métricas numéricas de error para un orden específico sobre el intervalo de evaluación."""
    order: int
    max_abs_error: float                     # Máximo error absoluto estimado en la malla
    max_abs_error_x: float                   # Coordenada x donde ocurre el error máximo
    mean_abs_error: float                    # Error absoluto medio estimado en la malla
    rmse: float                              # Raíz del error cuadrático medio (RMSE)
    is_exact: bool                           # True si el error es despreciable (< 1e-12) en todo el intervalo
    
    # Métricas puntuales en un punto de consulta x = c
    eval_c: Optional[float] = None
    eval_f_c: Optional[float] = None
    eval_p_c: Optional[float] = None
    eval_abs_error: Optional[float] = None
    eval_signed_error: Optional[float] = None
    eval_rel_error_pct: Optional[float] = None
    eval_rel_error_reliable: bool = True

    # Comparación con el orden anterior (k - 1)
    diff_max_error: Optional[float] = None   # max_error(k) - max_error(k-1)
    improved_globally: Optional[bool] = None # True si el error máximo disminuyó


@dataclass
class OrderErrorCurves:
    """Curvas numéricas de error calculadas sobre la malla de puntos."""
    order: int
    x: np.ndarray
    abs_error: np.ndarray                    # |f(x) - P_n(x)|
    signed_error: np.ndarray                 # f(x) - P_n(x)
    rel_error_pct: np.ndarray                # (|f(x) - P_n(x)| / |f(x)|) * 100%
    rel_error_mask: np.ndarray               # True donde el error relativo es numéricamente fiable


class ErrorAnalyzer:
    """
    Analizador de errores numéricos para series de Taylor.
    """

    def __init__(self, zero_threshold: float = 1e-10):
        self.zero_threshold = zero_threshold

    def compute_curves(
        self,
        order: int,
        x: np.ndarray,
        y_true: np.ndarray,
        y_pred: np.ndarray
    ) -> OrderErrorCurves:
        """
        Calcula las curvas de error absoluto, con signo y relativo para un orden dado.
        """
        signed_error = y_true - y_pred
        abs_error = np.abs(signed_error)

        # Para el error relativo: |f(x) - P_n(x)| / |f(x)|
        denom = np.abs(y_true)
        # Es fiable si |f(x)| no está cerca de 0 y y_true es finito
        reliable_mask = (denom > self.zero_threshold) & np.isfinite(denom) & np.isfinite(abs_error)

        with np.errstate(divide="ignore", invalid="ignore"):
            rel_error = np.where(
                reliable_mask,
                (abs_error / denom) * 100.0,
                np.nan
            )

        return OrderErrorCurves(
            order=order,
            x=x,
            abs_error=abs_error,
            signed_error=signed_error,
            rel_error_pct=rel_error,
            rel_error_mask=reliable_mask
        )

    def compute_metrics(
        self,
        order: int,
        x: np.ndarray,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        c: Optional[float] = None,
        f_c: Optional[float] = None,
        p_c: Optional[float] = None,
        prev_metrics: Optional[OrderErrorMetrics] = None
    ) -> OrderErrorMetrics:
        """
        Calcula las métricas de error globales (máximo, promedio, RMSE) y puntuales en x = c.
        """
        abs_err = np.abs(y_true - y_pred)
        valid_mask = np.isfinite(abs_err)

        if not np.any(valid_mask):
            return OrderErrorMetrics(
                order=order,
                max_abs_error=np.nan,
                max_abs_error_x=np.nan,
                mean_abs_error=np.nan,
                rmse=np.nan,
                is_exact=False
            )

        valid_abs_err = abs_err[valid_mask]
        valid_x = x[valid_mask]

        max_idx = np.argmax(valid_abs_err)
        max_abs = float(valid_abs_err[max_idx])
        max_x = float(valid_x[max_idx])
        mean_abs = float(np.mean(valid_abs_err))
        rmse = float(np.sqrt(np.mean(valid_abs_err ** 2)))

        is_exact = max_abs < 1e-11

        # Métricas puntuales en c
        eval_abs = None
        eval_signed = None
        eval_rel_pct = None
        eval_reliable = True

        if c is not None and f_c is not None and p_c is not None:
            if np.isfinite(f_c) and np.isfinite(p_c):
                eval_signed = float(f_c - p_c)
                eval_abs = abs(eval_signed)
                if abs(f_c) > self.zero_threshold:
                    eval_rel_pct = float((eval_abs / abs(f_c)) * 100.0)
                    eval_reliable = True
                else:
                    eval_rel_pct = None
                    eval_reliable = False

        diff_max = None
        improved = None
        if prev_metrics is not None and np.isfinite(prev_metrics.max_abs_error) and np.isfinite(max_abs):
            diff_max = max_abs - prev_metrics.max_abs_error
            improved = max_abs <= prev_metrics.max_abs_error + 1e-12

        return OrderErrorMetrics(
            order=order,
            max_abs_error=max_abs,
            max_abs_error_x=max_x,
            mean_abs_error=mean_abs,
            rmse=rmse,
            is_exact=is_exact,
            eval_c=c,
            eval_f_c=f_c,
            eval_p_c=p_c,
            eval_abs_error=eval_abs,
            eval_signed_error=eval_signed,
            eval_rel_error_pct=eval_rel_pct,
            eval_rel_error_reliable=eval_reliable,
            diff_max_error=diff_max,
            improved_globally=improved
        )

    def analyze_order_comparison(
        self,
        curr_curves: OrderErrorCurves,
        prev_curves: OrderErrorCurves
    ) -> Dict[str, Any]:
        """
        Compara punto a punto los errores de dos órdenes consecutivos E_{n}(x) y E_{n+1}(x).
        Identifica el porcentaje de la malla donde el nuevo orden mejora la aproximación.
        """
        valid = np.isfinite(curr_curves.abs_error) & np.isfinite(prev_curves.abs_error)
        if not np.any(valid):
            return {
                "improvement_ratio": 0.0,
                "summary": "No hay suficientes datos válidos para comparar."
            }

        curr_valid = curr_curves.abs_error[valid]
        prev_valid = prev_curves.abs_error[valid]

        improved_points = curr_valid < prev_valid
        improvement_ratio = float(np.mean(improved_points)) * 100.0

        if improvement_ratio > 95.0:
            summary = f"El orden {curr_curves.order} mejora la aproximación en prácticamente todo el intervalo ({improvement_ratio:.1f}%)."
        elif improvement_ratio > 50.0:
            summary = f"El orden {curr_curves.order} mejora la aproximación en la mayor parte del intervalo ({improvement_ratio:.1f}%), aunque empeora en los extremos."
        elif improvement_ratio < 10.0:
            summary = f"El orden {curr_curves.order} empeora la aproximación en la mayor parte del intervalo ({100 - improvement_ratio:.1f}%). Esto ocurre típicamente fuera del radio de convergencia."
        else:
            summary = f"El orden {curr_curves.order} mejora en el {improvement_ratio:.1f}% del intervalo y empeora en el restante."

        return {
            "improvement_ratio": improvement_ratio,
            "summary": summary
        }
