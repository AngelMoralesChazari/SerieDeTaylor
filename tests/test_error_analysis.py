"""
Pruebas para el módulo de análisis de error.
"""

import numpy as np
from error_analysis import ErrorAnalyzer


def test_error_curves_and_metrics():
    analyzer = ErrorAnalyzer()
    x = np.linspace(0.0, 1.0, 101)
    y_true = np.exp(x)
    y_pred = 1.0 + x  # Aproximación P_1(x)

    curves = analyzer.compute_curves(order=1, x=x, y_true=y_true, y_pred=y_pred)
    assert curves.abs_error.shape == x.shape
    assert curves.signed_error.shape == x.shape
    assert np.all(curves.abs_error >= 0)

    metrics = analyzer.compute_metrics(order=1, x=x, y_true=y_true, y_pred=y_pred)
    assert np.isfinite(metrics.max_abs_error)
    assert metrics.max_abs_error > 0
    # En x = 0, e^0 - (1+0) = 0
    # En x = 1, e^1 - 2 = 0.71828...
    np.testing.assert_allclose(metrics.max_abs_error, np.e - 2.0, rtol=1e-2)
    assert not metrics.is_exact


def test_relative_error_safeguard():
    analyzer = ErrorAnalyzer(zero_threshold=1e-10)
    x = np.array([0.0, 1.0])
    y_true = np.array([0.0, 2.0])  # y_true[0] es 0
    y_pred = np.array([0.1, 1.8])

    curves = analyzer.compute_curves(order=1, x=x, y_true=y_true, y_pred=y_pred)
    # En x = 0, el error relativo debe ser NaN (no fiable)
    assert np.isnan(curves.rel_error_pct[0])
    # En x = 1, |2 - 1.8| / 2 * 100 = 10%
    np.testing.assert_allclose(curves.rel_error_pct[1], 10.0, rtol=1e-3)


def test_exact_polynomial_error():
    analyzer = ErrorAnalyzer()
    x = np.linspace(0.0, 2.0, 50)
    y_true = x**2 + 1.0
    y_pred = x**2 + 1.0  # Exacto

    metrics = analyzer.compute_metrics(order=2, x=x, y_true=y_true, y_pred=y_pred)
    assert metrics.is_exact
    assert metrics.max_abs_error < 1e-11
