"""
Motor para el cálculo sistemático de Series de Taylor y construcción paso a paso.
Genera derivadas sucesivas, evaluación en el punto de expansión x0,
construcción del polinomio en potencias de (x - x0) (idéntico a la resolución matemática formal)
y la fórmula final de Taylor simplificada y expandida.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, List, Dict, Any, Optional, Union
import sympy as sp
import numpy as np

from math_engine import parse_math_expression, safe_lambdify, expr_to_latex, MathParsingError


@dataclass
class TaylorOrderStep:
    """Representa el cálculo completo correspondiente a un orden k de la Serie de Taylor."""
    order: int
    derivative_sym: sp.Expr                  # f^(k)(x)
    derivative_simplified: sp.Expr           # f^(k)(x) simplificada
    derivative_latex: str                    # LaTeX de f^(k)(x)
    derivative_at_x0_sym: sp.Expr            # f^(k)(x0) exacto
    derivative_at_x0_val: float              # f^(k)(x0) float
    derivative_at_x0_latex: str              # LaTeX de f^(k)(x0)
    factorial_k: int                         # k!
    coeff_sym: sp.Expr                       # c_k = f^(k)(x0) / k!
    coeff_latex: str                         # LaTeX de c_k
    unsimplified_term_latex: str             # [f^(k)(x0) / k!] * (x - x0)^k
    term_taylor_latex: str                   # c_k * (x - x0)^k
    poly_taylor_latex: str                   # P_k(x) en potencias de (x - x0)
    poly_expanded_sym: sp.Expr               # P_k(x) expandido
    poly_expanded_latex: str                 # P_k(x) en forma expandida
    explanation: str                         # Explicación didáctica
    eval_func: Callable[[np.ndarray | float], np.ndarray] = field(repr=False)

    @property
    def poly_expanded(self) -> sp.Expr:
        return self.poly_expanded_sym

    @property
    def poly_sym(self) -> sp.Expr:
        return self.poly_expanded_sym

    @property
    def derivative_at_a_sym(self) -> sp.Expr:
        return self.derivative_at_x0_sym

    @property
    def derivative_at_a_val(self) -> float:
        return self.derivative_at_x0_val

    @property
    def derivative_at_a_latex(self) -> str:
        return self.derivative_at_x0_latex


@dataclass
class TaylorSeriesResult:
    """Resultado global del cálculo de la Serie de Taylor hasta un orden máximo dado."""
    func_input: str
    func_sym: sp.Expr
    func_latex: str
    func_eval: Callable[[np.ndarray | float], np.ndarray] = field(repr=False)
    x0: float                                # Punto de expansión (x0)
    x0_sym: sp.Expr                          # Punto de expansión simbólico
    x_min: float                             # Límite inferior del intervalo de visualización
    x_max: float                             # Límite superior del intervalo de visualización
    max_order: int                           # Orden máximo calculado
    steps: List[TaylorOrderStep] = field(default_factory=list)
    constructed_taylor_formula_latex: str = "" # P_n(x) en potencias de (x - x0)
    expanded_formula_latex: str = ""           # P_n(x) expandido

    def get_step(self, order: int) -> Optional[TaylorOrderStep]:
        for s in self.steps:
            if s.order == order:
                return s
        return None

    @property
    def a(self) -> float:
        return self.x0

    @property
    def poly_expanded(self) -> sp.Expr:
        if self.steps:
            return self.steps[-1].poly_expanded_sym
        return sp.Integer(0)


def format_term_latex(coeff: sp.Expr, k: int, x0_sym: sp.Expr) -> str:
    """
    Formatea el término en potencias de (x - x0) de manera elegante en LaTeX.
    Ejemplo: para c_k = -2, k = 1, x0 = 1 -> -2 (x - 1)
    """
    if coeff == 0:
        return "0"

    x = sp.Symbol("x", real=True)
    if k == 0:
        return expr_to_latex(coeff)

    # Factor (x - x0)
    if x0_sym == 0:
        factor_str = "x" if k == 1 else f"x^{{{k}}}"
    else:
        diff_expr = x - x0_sym
        factor_str = f"({expr_to_latex(diff_expr)})" if k == 1 else f"({expr_to_latex(diff_expr)})^{{{k}}}"

    if coeff == 1:
        return factor_str
    elif coeff == -1:
        return f"-{factor_str}"
    else:
        c_ltx = expr_to_latex(coeff)
        # Si c_ltx es una suma o resta compleja, encerrar entre paréntesis
        if "+" in c_ltx or "-" in c_ltx.lstrip("-"):
            return f"\\left({c_ltx}\\right) {factor_str}"
        return f"{c_ltx} {factor_str}"


def build_taylor_polynomial_latex(coeffs: List[sp.Expr], x0_sym: sp.Expr) -> str:
    """
    Construye la expresión en LaTeX del polinomio acumulado en potencias de (x - x0).
    Ejemplo: -1 - 2(x - 1) + 3(x - 1)^2 + 4(x - 1)^3 + (x - 1)^4
    """
    non_zero = []
    for k, c in enumerate(coeffs):
        if c != 0 or k == 0:
            non_zero.append((k, c))

    if not non_zero:
        return "0"

    # Si todos son cero excepto que la lista esté vacía
    if len(non_zero) == 1 and non_zero[0][1] == 0:
        return "0"

    # Filtrar ceros reales para el resultado si hay otros términos
    active = [(k, c) for k, c in non_zero if c != 0]
    if not active:
        return "0"

    parts = []
    for idx, (k, c) in enumerate(active):
        term_str = format_term_latex(c, k, x0_sym)
        if idx == 0:
            parts.append(term_str)
        else:
            if term_str.startswith("-"):
                parts.append(f"- {term_str[1:].strip()}")
            else:
                parts.append(f"+ {term_str.strip()}")

    return " ".join(parts)


class TaylorEngine:
    """
    Motor encargado de calcular paso a paso las derivadas y la serie de Taylor formal.
    """

    def __init__(self):
        self.x = sp.Symbol("x", real=True)

    def compute_series(
        self,
        func_expr: Union[str, sp.Expr],
        x0: Optional[float] = None,
        x_min: float = -5.0,
        x_max: float = 5.0,
        max_order: int = 4,
        a: Optional[float] = None
    ) -> TaylorSeriesResult:
        """
        Calcula la serie de Taylor de f(x) alrededor del punto de expansión x0 (o a)
        para ser graficada sobre el intervalo [x_min, x_max].
        """
        if x0 is None:
            x0 = a if a is not None else 0.0

        if max_order < 0 or max_order > 15:
            raise ValueError("El orden máximo debe estar comprendido entre 0 y 15.")

        if x_min >= x_max:
            raise ValueError(f"El límite inferior x_min ({x_min:g}) debe ser estrictamente menor que x_max ({x_max:g}).")

        # Parsear expresión
        if isinstance(func_expr, str):
            f_sym = parse_math_expression(func_expr)
            func_input_str = func_expr
        else:
            f_sym = func_expr
            func_input_str = str(func_expr)

        # Representación simbólica del punto x0
        try:
            x0_sym = sp.Rational(str(x0))
        except Exception:
            x0_sym = sp.Float(x0)

        f_latex = expr_to_latex(f_sym)
        f_eval = safe_lambdify(f_sym, self.x)

        result = TaylorSeriesResult(
            func_input=func_input_str,
            func_sym=f_sym,
            func_latex=f_latex,
            func_eval=f_eval,
            x0=float(x0),
            x0_sym=x0_sym,
            x_min=float(x_min),
            x_max=float(x_max),
            max_order=max_order,
            steps=[]
        )

        current_deriv = f_sym
        cumulative_poly_expanded = sp.Integer(0)
        coeffs_list: List[sp.Expr] = []

        for k in range(max_order + 1):
            if k == 0:
                current_deriv = f_sym
            else:
                current_deriv = sp.diff(current_deriv, self.x)

            deriv_simplified = sp.simplify(current_deriv)
            deriv_latex = expr_to_latex(deriv_simplified)

            # Evaluar en x = x0
            try:
                eval_at_x0 = deriv_simplified.subs(self.x, x0_sym)
                if eval_at_x0.has(sp.nan, sp.zoo, sp.oo, -sp.oo):
                    eval_at_x0 = sp.limit(deriv_simplified, self.x, x0_sym)
            except Exception:
                try:
                    eval_at_x0 = sp.limit(deriv_simplified, self.x, x0_sym)
                except Exception as exc:
                    raise MathParsingError(
                        f"No fue posible evaluar la derivada de orden {k} en x = {x0}: {str(exc)}"
                    )

            if eval_at_x0.has(sp.nan, sp.zoo, sp.oo, -sp.oo):
                raise MathParsingError(
                    f"La derivada de orden {k} no existe o diverge en el punto de expansión x₀ = {x0}."
                )

            eval_at_x0_sym = sp.simplify(eval_at_x0)
            try:
                eval_at_x0_val = float(eval_at_x0_sym.evalf())
            except Exception:
                eval_at_x0_val = float(eval_at_x0_sym)

            eval_at_x0_latex = expr_to_latex(eval_at_x0_sym)

            # Factorial k!
            k_fact = math.factorial(k)

            # Coeficiente c_k = f^(k)(x0) / k!
            coeff_sym = sp.simplify(eval_at_x0_sym / sp.Integer(k_fact))
            coeff_latex = expr_to_latex(coeff_sym)
            coeffs_list.append(coeff_sym)

            # Término no simplificado para visualización didáctica: \frac{f^(k)(x0)}{k!}(x - x0)^k
            if k == 0:
                unsimplified_term_latex = eval_at_x0_latex
            elif k == 1:
                diff_str = f"(x - {expr_to_latex(x0_sym)})" if x0_sym != 0 else "x"
                unsimplified_term_latex = f"\\frac{{{eval_at_x0_latex}}}{{1!}} {diff_str}"
            else:
                diff_str = f"(x - {expr_to_latex(x0_sym)})^{{{k}}}" if x0_sym != 0 else f"x^{{{k}}}"
                unsimplified_term_latex = f"\\frac{{{eval_at_x0_latex}}}{{{k}!}} {diff_str}"

            # Término simplificado en potencias de (x - x0)
            term_taylor_latex = format_term_latex(coeff_sym, k, x0_sym)

            # Polinomio acumulado en potencias de (x - x0)
            poly_taylor_latex = build_taylor_polynomial_latex(coeffs_list, x0_sym)

            # Término simbólico para evaluar
            if k == 0:
                term_sym = coeff_sym
            else:
                term_sym = coeff_sym * ((self.x - x0_sym) ** k)

            cumulative_poly_expanded = sp.expand(cumulative_poly_expanded + term_sym)
            poly_expanded_latex = expr_to_latex(cumulative_poly_expanded)

            # Función numérica vectorizada para graficar
            poly_eval = safe_lambdify(cumulative_poly_expanded, self.x)

            # Explicación pedagógica
            if k == 0:
                explanation = f"P₀(x) = f({x0:g}) fija la altura base de la función en el punto x₀ = {x0:g}."
            elif k == 1:
                explanation = f"P₁(x) añade la primera derivada (recta tangente) en x₀ = {x0:g}."
            elif k == 2:
                explanation = f"P₂(x) incorpora la curvatura y concavidad (parábola osculadora) en x₀ = {x0:g}."
            elif k == 3:
                explanation = f"P₃(x) modela la tasa de cambio de curvatura y puntos de inflexión."
            else:
                explanation = f"P_{k}(x) refina el ajuste polinómico en un entorno más amplio de x₀ = {x0:g}."

            step = TaylorOrderStep(
                order=k,
                derivative_sym=current_deriv,
                derivative_simplified=deriv_simplified,
                derivative_latex=deriv_latex,
                derivative_at_x0_sym=eval_at_x0_sym,
                derivative_at_x0_val=eval_at_x0_val,
                derivative_at_x0_latex=eval_at_x0_latex,
                factorial_k=k_fact,
                coeff_sym=coeff_sym,
                coeff_latex=coeff_latex,
                unsimplified_term_latex=unsimplified_term_latex,
                term_taylor_latex=term_taylor_latex,
                poly_taylor_latex=poly_taylor_latex,
                poly_expanded_sym=cumulative_poly_expanded,
                poly_expanded_latex=poly_expanded_latex,
                explanation=explanation,
                eval_func=poly_eval
            )
            result.steps.append(step)

        # Fórmula final construida
        result.constructed_taylor_formula_latex = build_taylor_polynomial_latex(coeffs_list, x0_sym)
        result.expanded_formula_latex = expr_to_latex(cumulative_poly_expanded)

        return result
