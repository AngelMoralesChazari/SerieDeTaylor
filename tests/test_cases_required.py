"""
Pruebas matemáticas obligatorias especificadas en el requerimiento del proyecto:
- Caso A: Función cuadrática f(x) = x^2 + 1, a = 0
- Caso B: Función exponencial f(x) = e^x, a = 0
- Caso C: Función trigonométrica f(x) = sin(x), a = 0
- Caso D: Función racional f(x) = 1/(1+x^2), a = 0
"""

import sympy as sp
import numpy as np
from taylor_engine import TaylorEngine
from error_analysis import ErrorAnalyzer


def test_caso_a_cuadratica():
    """
    Caso A: función cuadrática
    f(x) = x^2 + 1
    a = 0
    Resultados esperados:
    P_0(x) = 1
    P_1(x) = 1
    P_2(x) = 1 + x^2
    La aproximación de orden 2 debe coincidir exactamente con la función original.
    """
    engine = TaylorEngine()
    res = engine.compute_series("x^2 + 1", a=0.0, x_min=0.0, x_max=2.0, max_order=2)
    x = sp.Symbol("x", real=True)

    # Verificación de polinomios
    assert sp.simplify(res.steps[0].poly_expanded - 1) == 0
    assert sp.simplify(res.steps[1].poly_expanded - 1) == 0
    assert sp.simplify(res.steps[2].poly_expanded - (1 + x**2)) == 0

    # Coincidencia exacta con la función original en orden 2
    assert sp.simplify(res.steps[2].poly_expanded - res.func_sym) == 0

    # Verificación de error numérico exacto
    analyzer = ErrorAnalyzer()
    x_mesh = np.linspace(0.0, 2.0, 100)
    y_true = res.func_eval(x_mesh)
    y_p2 = res.steps[2].eval_func(x_mesh)
    metrics_p2 = analyzer.compute_metrics(order=2, x=x_mesh, y_true=y_true, y_pred=y_p2)

    assert metrics_p2.is_exact
    assert metrics_p2.max_abs_error < 1e-12


def test_caso_b_exponencial():
    """
    Caso B: función exponencial
    f(x) = e^x
    a = 0
    Resultados esperados:
    P_0(x) = 1
    P_1(x) = 1 + x
    P_2(x) = 1 + x + x^2/2
    P_3(x) = 1 + x + x^2/2 + x^3/6
    """
    engine = TaylorEngine()
    res = engine.compute_series("exp(x)", a=0.0, x_min=0.0, x_max=1.0, max_order=3)
    x = sp.Symbol("x", real=True)

    # Verificación de polinomios
    assert sp.simplify(res.steps[0].poly_expanded - 1) == 0
    assert sp.simplify(res.steps[1].poly_expanded - (1 + x)) == 0
    assert sp.simplify(res.steps[2].poly_expanded - (1 + x + x**2 / 2)) == 0
    assert sp.simplify(res.steps[3].poly_expanded - (1 + x + x**2 / 2 + x**3 / 6)) == 0

    # Verificación de error monótonamente decreciente en [0, 1]
    analyzer = ErrorAnalyzer()
    x_mesh = np.linspace(0.0, 1.0, 100)
    y_true = res.func_eval(x_mesh)

    max_errors = []
    for step in res.steps:
        y_p = step.eval_func(x_mesh)
        m = analyzer.compute_metrics(order=step.order, x=x_mesh, y_true=y_true, y_pred=y_p)
        max_errors.append(m.max_abs_error)

    # El error debe disminuir estrictamente en cada orden adicional
    for i in range(len(max_errors) - 1):
        assert max_errors[i + 1] < max_errors[i]


def test_caso_c_trigonometrica():
    """
    Caso C: función trigonométrica
    f(x) = sin(x)
    a = 0
    Resultados esperados:
    P_0(x) = 0
    P_1(x) = x
    P_2(x) = x
    P_3(x) = x - x^3/6
    """
    engine = TaylorEngine()
    res = engine.compute_series("sin(x)", a=0.0, x_min=-2.0, x_max=2.0, max_order=3)
    x = sp.Symbol("x", real=True)

    # Verificación de polinomios
    assert sp.simplify(res.steps[0].poly_expanded - 0) == 0
    assert sp.simplify(res.steps[1].poly_expanded - x) == 0
    assert sp.simplify(res.steps[2].poly_expanded - x) == 0
    assert sp.simplify(res.steps[3].poly_expanded - (x - x**3 / 6)) == 0


def test_caso_d_racional():
    """
    Caso D: función racional
    f(x) = 1/(1+x^2)
    a = 0
    Resultados esperados:
    P_0(x) = 1
    P_1(x) = 1
    P_2(x) = 1 - x^2
    P_4(x) = 1 - x^2 + x^4
    """
    engine = TaylorEngine()
    res = engine.compute_series("1/(1+x^2)", a=0.0, x_min=-0.8, x_max=0.8, max_order=4)
    x = sp.Symbol("x", real=True)

    # Verificación de polinomios
    assert sp.simplify(res.steps[0].poly_expanded - 1) == 0
    assert sp.simplify(res.steps[1].poly_expanded - 1) == 0
    assert sp.simplify(res.steps[2].poly_expanded - (1 - x**2)) == 0
    assert sp.simplify(res.steps[4].poly_expanded - (1 - x**2 + x**4)) == 0
