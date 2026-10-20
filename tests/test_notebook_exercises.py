"""
Pruebas automatizadas para los ejercicios manuscritos del cuaderno (Imagen 4):
a) f(x) = x^4 - 3x^2 + 1,  x0 = 1
b) f(x) = x^2 + x + 1,     x0 = 1
c) f(x) = 2x^3 - 3x^2 + 6x + 2, x0 = 1
d) f(x) = -0.5x^2 - 0.3x + 0.9, x0 = 1
"""

import sympy as sp
from taylor_engine import TaylorEngine


def test_ejercicio_a_cuaderno():
    """
    Ejercicio a: f(x) = x^4 - 3x^2 + 1, x0 = 1
    f(1) = -1
    f'(1) = -2  -> término: -2(x - 1)
    f''(1) = 6  -> término: 3(x - 1)^2
    f'''(1) = 24 -> término: 4(x - 1)^3
    f''''(1) = 24 -> término: (x - 1)^4
    Fórmula final: -1 - 2(x - 1) + 3(x - 1)^2 + 4(x - 1)^3 + (x - 1)^4
    """
    engine = TaylorEngine()
    res = engine.compute_series("x^4 - 3*x^2 + 1", x0=1.0, x_min=-3.0, x_max=3.0, max_order=4)

    # Verificación exacta de los valores de las derivadas evaluadas en 1
    assert res.steps[0].derivative_at_x0_val == -1.0
    assert res.steps[1].derivative_at_x0_val == -2.0
    assert res.steps[2].derivative_at_x0_val == 6.0
    assert res.steps[3].derivative_at_x0_val == 24.0
    assert res.steps[4].derivative_at_x0_val == 24.0

    # Coincidencia con la fórmula del cuaderno
    assert "-1 - 2 (x - 1) + 3 (x - 1)^{2} + 4 (x - 1)^{3} + (x - 1)^{4}" in res.constructed_taylor_formula_latex

    # Forma expandida coincide con la función original
    x = sp.Symbol("x", real=True)
    assert sp.simplify(res.steps[4].poly_expanded_sym - (x**4 - 3*x**2 + 1)) == 0


def test_ejercicio_b_cuaderno():
    """
    Ejercicio b: f(x) = x^2 + x + 1, x0 = 1
    f(1) = 3
    f'(1) = 3
    f''(1) = 2
    P_2(x) = 3 + 3(x - 1) + (x - 1)^2
    """
    engine = TaylorEngine()
    res = engine.compute_series("x^2 + x + 1", x0=1.0, x_min=-2.0, x_max=3.0, max_order=2)

    assert res.steps[0].derivative_at_x0_val == 3.0
    assert res.steps[1].derivative_at_x0_val == 3.0
    assert res.steps[2].derivative_at_x0_val == 2.0

    assert "3 + 3 (x - 1) + (x - 1)^{2}" in res.constructed_taylor_formula_latex


def test_ejercicio_c_cuaderno():
    """
    Ejercicio c: f(x) = 2x^3 - 3x^2 + 6x + 2, x0 = 1
    f(1) = 7
    f'(1) = 6
    f''(1) = 6
    f'''(1) = 12
    P_3(x) = 7 + 6(x - 1) + 3(x - 1)^2 + 2(x - 1)^3
    """
    engine = TaylorEngine()
    res = engine.compute_series("2*x^3 - 3*x^2 + 6*x + 2", x0=1.0, x_min=-2.0, x_max=3.0, max_order=3)

    assert res.steps[0].derivative_at_x0_val == 7.0
    assert res.steps[1].derivative_at_x0_val == 6.0
    assert res.steps[2].derivative_at_x0_val == 6.0
    assert res.steps[3].derivative_at_x0_val == 12.0

    assert "7 + 6 (x - 1) + 3 (x - 1)^{2} + 2 (x - 1)^{3}" in res.constructed_taylor_formula_latex


def test_ejercicio_d_cuaderno():
    """
    Ejercicio d: f(x) = -0.5x^2 - 0.3x + 0.9, x0 = 1
    f(1) = 0.1
    f'(1) = -1.3
    f''(1) = -1.0
    P_2(x) = 0.1 - 1.3(x - 1) - 0.5(x - 1)^2
    """
    engine = TaylorEngine()
    res = engine.compute_series("-0.5*x^2 - 0.3*x + 0.9", x0=1.0, x_min=-3.0, x_max=3.0, max_order=2)

    assert abs(res.steps[0].derivative_at_x0_val - 0.1) < 1e-9
    assert abs(res.steps[1].derivative_at_x0_val - (-1.3)) < 1e-9
    assert abs(res.steps[2].derivative_at_x0_val - (-1.0)) < 1e-9
