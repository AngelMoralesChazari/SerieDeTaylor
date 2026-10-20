"""
Pruebas para el motor de cálculo de series de Taylor.
"""

import pytest
import sympy as sp
import numpy as np

from taylor_engine import TaylorEngine


def test_taylor_order_construction():
    engine = TaylorEngine()
    res = engine.compute_series("exp(x)", a=0.0, x_min=0.0, x_max=1.0, max_order=3)

    assert len(res.steps) == 4  # 0, 1, 2, 3
    x = sp.Symbol("x", real=True)

    # Orden 0: 1
    assert sp.simplify(res.steps[0].poly_expanded - 1) == 0
    # Orden 1: 1 + x
    assert sp.simplify(res.steps[1].poly_expanded - (1 + x)) == 0
    # Orden 2: 1 + x + x^2 / 2
    assert sp.simplify(res.steps[2].poly_expanded - (1 + x + x**2 / 2)) == 0
    # Orden 3: 1 + x + x^2 / 2 + x^3 / 6
    assert sp.simplify(res.steps[3].poly_expanded - (1 + x + x**2 / 2 + x**3 / 6)) == 0


def test_expansion_point_nonzero():
    engine = TaylorEngine()
    # f(x) = x^2 en a = 1
    # f(1) = 1, f'(1) = 2, f''(1) = 2
    # P_0 = 1
    # P_1 = 1 + 2(x-1) = 2x - 1
    # P_2 = 1 + 2(x-1) + (x-1)^2 = x^2
    res = engine.compute_series("x^2", a=1.0, x_min=0.0, x_max=2.0, max_order=2)
    x = sp.Symbol("x", real=True)

    assert sp.simplify(res.steps[0].poly_expanded - 1) == 0
    assert sp.simplify(res.steps[1].poly_expanded - (2 * x - 1)) == 0
    assert sp.simplify(res.steps[2].poly_expanded - (x**2)) == 0


def test_invalid_orders_and_intervals():
    engine = TaylorEngine()
    with pytest.raises(ValueError):
        engine.compute_series("x", a=0.0, x_min=2.0, x_max=1.0, max_order=3)

    with pytest.raises(ValueError):
        engine.compute_series("x", a=0.0, x_min=0.0, x_max=1.0, max_order=-1)
