"""
Pruebas automatizadas para el motor de análisis y evaluación matemática.
"""

import pytest
import numpy as np
import sympy as sp

from math_engine import (
    parse_math_expression,
    preprocess_expression_string,
    safe_lambdify,
    clean_asymptotes,
    MathParsingError
)


def test_preprocess_syntax():
    assert preprocess_expression_string("x^2 + 1") == "x**2 + 1"
    assert "exp(x)" in preprocess_expression_string("e^x")
    assert "pi" in preprocess_expression_string("π * x")
    assert "sqrt(x)" in preprocess_expression_string("√x")
    assert "Abs(x)" in preprocess_expression_string("|x|")


def test_valid_expressions():
    exprs = [
        "x**2 + 3*x + 2",
        "sin(x)",
        "cos(x)",
        "exp(x)",
        "log(x)",
        "ln(x)",
        "sqrt(x)",
        "1/(1+x**2)",
        "x^3 - 2*x + 1",
        "3x^2 + 2x + 1",
        "2sin(x) + cos(2x)"
    ]
    for expr_str in exprs:
        sym = parse_math_expression(expr_str)
        assert isinstance(sym, sp.Expr)


def test_forbidden_keywords_and_security():
    malicious = [
        "import os",
        "__import__('os').system('ls')",
        "eval('2+2')",
        "open('/etc/passwd')",
        "subprocess.run()",
        "lambda x: x",
        "class Foo: pass"
    ]
    for bad in malicious:
        with pytest.raises(MathParsingError):
            parse_math_expression(bad)


def test_disallowed_variables():
    with pytest.raises(MathParsingError):
        parse_math_expression("x + y + z")


def test_safe_lambdify_eval():
    sym = parse_math_expression("x^2 + 1")
    fn = safe_lambdify(sym)
    arr = np.array([-1.0, 0.0, 1.0, 2.0])
    res = fn(arr)
    np.testing.assert_allclose(res, [2.0, 1.0, 2.0, 5.0])


def test_safe_lambdify_constant():
    # Polinomio P_0 = 1
    sym = sp.Integer(1)
    fn = safe_lambdify(sym)
    arr = np.array([-2.0, 0.0, 3.0])
    res = fn(arr)
    assert res.shape == arr.shape
    np.testing.assert_allclose(res, [1.0, 1.0, 1.0])


def test_safe_lambdify_singularity():
    # 1/x at x = 0 should return NaN without crash
    sym = parse_math_expression("1/x")
    fn = safe_lambdify(sym)
    res = fn(np.array([0.0]))
    assert np.isnan(res[0])


def test_clean_asymptotes():
    # tan(x) has a huge jump around pi/2
    x = np.linspace(1.5, 1.64, 50)
    y = np.tan(x)
    cleaned = clean_asymptotes(x, y, max_derivative_jump=50.0)
    assert np.any(np.isnan(cleaned))
