"""
Motor matemático para validación, análisis simbólico y evaluación numérica de funciones.
Utiliza SymPy para análisis simbólico y transformaciones seguras, y NumPy para evaluación vectorial.
"""

from __future__ import annotations

import re
import math
from typing import Callable, Any, Dict, Optional, Tuple, Set
import sympy as sp
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
    convert_xor,
)
import numpy as np


class MathParsingError(ValueError):
    """Excepción para errores de sintaxis o seguridad en expresiones matemáticas."""
    pass


# Lista blanca de nombres permitidos en la evaluación simbólica
ALLOWED_NAMES: Dict[str, Any] = {
    # Variables y constantes
    "x": sp.Symbol("x", real=True),
    "pi": sp.pi,
    "E": sp.E,
    "e": sp.E,
    "oo": sp.oo,
    # Funciones algebraicas
    "sqrt": sp.sqrt,
    "cbrt": sp.cbrt,
    "root": sp.root,
    "Abs": sp.Abs,
    "abs": sp.Abs,
    # Funciones exponenciales y logarítmicas
    "exp": sp.exp,
    "log": sp.log,
    "ln": sp.log,
    "log10": lambda arg: sp.log(arg, 10),
    "log2": lambda arg: sp.log(arg, 2),
    # Funciones trigonométricas directas
    "sin": sp.sin,
    "cos": sp.cos,
    "tan": sp.tan,
    "sec": sp.sec,
    "csc": sp.csc,
    "cot": sp.cot,
    # Funciones trigonométricas inversas
    "asin": sp.asin,
    "acos": sp.acos,
    "atan": sp.atan,
    "asec": sp.asec,
    "acsc": sp.acsc,
    "acot": sp.acot,
    # Funciones hiperbólicas directas
    "sinh": sp.sinh,
    "cosh": sp.cosh,
    "tanh": sp.tanh,
    "sech": sp.sech,
    "csch": sp.csch,
    "coth": sp.coth,
    # Funciones hiperbólicas inversas
    "asinh": sp.asinh,
    "acosh": sp.acosh,
    "atanh": sp.atanh,
    # Funciones especiales comunes
    "gamma": sp.gamma,
    "factorial": sp.factorial,
}

# Palabras clave prohibidas que no deben aparecer bajo ninguna circunstancia
FORBIDDEN_KEYWORDS: Set[str] = {
    "import", "exec", "eval", "compile", "open", "file", "builtins",
    "globals", "locals", "__", "lambda", "def", "class", "sys", "os",
    "subprocess", "shutil", "socket", "urllib", "requests"
}


def preprocess_expression_string(expr_str: str) -> str:
    """
    Normaliza y limpia la cadena introducida por el usuario:
    - Convierte símbolos matemáticos visuales (π, √, ·, :, etc.).
    - Convierte notación e^x o e^(...) a exp(...).
    - Convierte |x| a Abs(x).
    - Convierte potencias con ^ a **.
    - Maneja multiplicaciones implícitas comunes y espacios.
    """
    if not expr_str or not expr_str.strip():
        raise MathParsingError("La expresión no puede estar vacía.")

    s = expr_str.strip()

    # Reemplazo de caracteres Unicode comunes
    unicode_replacements = {
        "π": "pi",
        "·": "*",
        "×": "*",
        "÷": "/",
        ":": "/",
        "−": "-",
        "–": "-",
        "²": "**2",
        "³": "**3",
        "⁴": "**4",
        "⁵": "**5",
    }
    for char, rep in unicode_replacements.items():
        s = s.replace(char, rep)

    # Manejo de valor absoluto en formato |algo| -> Abs(algo)
    # Reemplaza pares de barras |...|
    bar_pattern = re.compile(r"\|([^|]+)\|")
    while bar_pattern.search(s):
        s = bar_pattern.sub(r"Abs(\1)", s)

    # Reemplazar raíces cuadradas tipográficas: √(algo) o √x
    s = re.sub(r"√\(([^)]+)\)", r"sqrt(\1)", s)
    s = re.sub(r"√([a-zA-Z0-9]+)", r"sqrt(\1)", s)

    # Manejar notación e^u -> exp(u)
    # Caso 1: e^(...)
    s = re.sub(r"(?<![a-zA-Z0-9_])e\^\(([^)]+)\)", r"exp(\1)", s)
    s = re.sub(r"(?<![a-zA-Z0-9_])e\*\*(\([^)]+\))", r"exp\1", s)
    # Caso 2: e^x o e^2x etc
    s = re.sub(r"(?<![a-zA-Z0-9_])e\^([a-zA-Z0-9]+)", r"exp(\1)", s)

    # Convertir ^ a **
    s = s.replace("^", "**")

    return s


def validate_expression_tokens(expr_str: str) -> None:
    """
    Verifica que la cadena no contenga elementos no autorizados o maliciosos.
    """
    # Extraer todos los identificadores (palabras)
    tokens = re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", expr_str)
    for token in tokens:
        token_lower = token.lower()
        if token_lower in FORBIDDEN_KEYWORDS or token.startswith("__"):
            raise MathParsingError(f"Término o instrucción no permitida: '{token}'")
        if token not in ALLOWED_NAMES:
            raise MathParsingError(
                f"Símbolo o función no reconocida: '{token}'. "
                f"Funciones válidas incluyen: sin, cos, tan, exp, log, ln, sqrt, etc."
            )


def parse_math_expression(expr_str: str) -> sp.Expr:
    """
    Analiza de forma segura una expresión matemática y retorna un objeto SymPy.
    Acepta sintaxis estándar y amigable.
    """
    cleaned = preprocess_expression_string(expr_str)
    validate_expression_tokens(cleaned)

    transformations = standard_transformations + (
        implicit_multiplication_application,
        convert_xor,
    )

    try:
        sym_expr = parse_expr(
            cleaned,
            local_dict=ALLOWED_NAMES,
            transformations=transformations,
            evaluate=True
        )
    except Exception as exc:
        raise MathParsingError(f"Error al interpretar la expresión: {str(exc)}")

    # Verificar que las únicas variables libres sean 'x'
    free_vars = {str(sym) for sym in sym_expr.free_symbols}
    invalid_vars = free_vars - {"x"}
    if invalid_vars:
        raise MathParsingError(
            f"Variables no permitidas encontradas: {', '.join(invalid_vars)}. "
            f"Solo se permite la variable 'x'."
        )

    return sym_expr


def safe_lambdify(
    sym_expr: sp.Expr,
    var: sp.Symbol = sp.Symbol("x", real=True)
) -> Callable[[np.ndarray | float], np.ndarray]:
    """
    Crea una función NumPy vectorizada y robusta a partir de una expresión SymPy.
    Maneja divisiones por cero, funciones constantes, valores complejos y singularidades.
    """
    # Si la expresión es constante (no depende de x)
    if var not in sym_expr.free_symbols:
        try:
            val = float(sym_expr.evalf())
        except Exception:
            val = np.nan

        def constant_func(x_in: np.ndarray | float) -> np.ndarray:
            x_arr = np.asarray(x_in, dtype=float)
            return np.full_like(x_arr, val, dtype=float)

        return constant_func

    # Crear función lambdificada con NumPy
    try:
        raw_func = sp.lambdify(
            var,
            sym_expr,
            modules=[
                {
                    "log": lambda z: np.where(z > 0, np.log(np.maximum(z, 1e-300)), np.nan),
                    "sqrt": lambda z: np.where(z >= 0, np.sqrt(np.maximum(z, 0)), np.nan),
                },
                "numpy"
            ]
        )
    except Exception:
        # Fallback a sympy evalf punto a punto
        def fallback_eval(x_in: np.ndarray | float) -> np.ndarray:
            x_arr = np.asarray(x_in, dtype=float)
            res = np.empty_like(x_arr, dtype=float)
            for idx, val in np.ndenumerate(x_arr):
                try:
                    num_val = complex(sym_expr.subs(var, val).evalf())
                    if abs(num_val.imag) < 1e-10 and np.isfinite(num_val.real):
                        res[idx] = num_val.real
                    else:
                        res[idx] = np.nan
                except Exception:
                    res[idx] = np.nan
            return res

        return fallback_eval

    def vectorized_safe_func(x_in: np.ndarray | float) -> np.ndarray:
        x_arr = np.asarray(x_in, dtype=float)
        # Ignorar advertencias de numpy temporales de división o log(<=0)
        with np.errstate(all="ignore"):
            try:
                y = raw_func(x_arr)
            except Exception:
                # Si falló la vectorización, evaluar elemento a elemento
                y = np.empty_like(x_arr, dtype=float)
                for idx, val in np.ndenumerate(x_arr):
                    try:
                        res = raw_func(val)
                        if isinstance(res, (complex, np.complexfloating)):
                            y[idx] = res.real if abs(res.imag) < 1e-9 else np.nan
                        elif np.isfinite(res):
                            y[idx] = float(res)
                        else:
                            y[idx] = np.nan
                    except Exception:
                        y[idx] = np.nan
                return y

            # Convertir a array de floats reales
            y_arr = np.asarray(y)

            # Si el resultado es un escalar (ocurrió que numpy no expandió a array)
            if y_arr.ndim == 0:
                y_arr = np.full_like(x_arr, float(y_arr))

            # Si contiene números complejos
            if np.iscomplexobj(y_arr):
                # Descartar partes con componente imaginaria significativa
                real_part = np.real(y_arr)
                imag_part = np.imag(y_arr)
                y_arr = np.where(np.abs(imag_part) < 1e-9, real_part, np.nan)

            # Reemplazar valores no finitos con NaN
            y_arr = np.where(np.isfinite(y_arr), y_arr, np.nan)

            return y_arr.astype(float)

    return vectorized_safe_func


def clean_asymptotes(x: np.ndarray, y: np.ndarray, max_derivative_jump: float = 80.0) -> np.ndarray:
    """
    Detecta saltos hiperbólicos o asíntotas verticales (p. ej. en tan(x), 1/(x-1))
    e inserta NaN para que Matplotlib no conecte puntos a través de discontinuidades.
    """
    y_clean = np.copy(y)
    if len(y_clean) < 3:
        return y_clean

    with np.errstate(all="ignore"):
        dx = np.diff(x)
        dy = np.diff(y_clean)
        # Aproximación de la pendiente entre puntos contiguos
        slopes = np.abs(dy / np.where(dx == 0, 1e-12, dx))

        # Detectar cambios bruscos de signo con pendientes muy altas
        sign_change = (y_clean[:-1] * y_clean[1:]) < 0
        huge_jump = slopes > max_derivative_jump

        jump_indices = np.where(sign_change & huge_jump)[0]
        for idx in jump_indices:
            y_clean[idx] = np.nan
            y_clean[idx + 1] = np.nan

    return y_clean


def expr_to_latex(expr: sp.Expr) -> str:
    """
    Convierte una expresión SymPy a formato LaTeX legible.
    """
    try:
        return sp.latex(expr)
    except Exception:
        return str(expr)
