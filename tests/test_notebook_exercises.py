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


def test_ejercicio_pizarron_logaritmo():
    """
    Ejercicio del pizarrón:
    a) Serie de Taylor de f(x) = ln(x) alrededor de x0 = 1
    b) Calcular ln(1.25) con error menor que 10^-3 = 0.001
       P_1(1.25) = 0.25
       P_2(1.25) = 0.21875     (diff = 0.03125)
       P_3(1.25) = 0.223958... (diff = -0.005208)
       P_4(1.25) = 0.222981... (diff = 0.000977 < 10^-3 -> Cumple condición)
       P_5(1.25) = 0.223177... (diff = 0.000196)
       P_6(1.25) = 0.223136... (diff = 0.000041)
       Calculadora: ln(1.25) = 0.22314355...
    """
    engine = TaylorEngine()
    res = engine.compute_series("ln(x)", x0=1.0, x_min=0.2, x_max=2.5, max_order=6)

    # Derivadas en x0 = 1
    assert res.steps[0].derivative_at_x0_val == 0.0
    assert res.steps[1].derivative_at_x0_val == 1.0
    assert res.steps[2].derivative_at_x0_val == -1.0
    assert res.steps[3].derivative_at_x0_val == 2.0
    assert res.steps[4].derivative_at_x0_val == -6.0
    assert res.steps[5].derivative_at_x0_val == 24.0

    # Evaluación iterativa de la Parte b en x = 1.25 con tolerancia 10^-3
    eval_res = res.evaluate_point_iterations(1.25, tolerance=0.001)
    iterations = eval_res["iterations"]

    # Orden 1: ln(1.25) = (1.25 - 1) = 0.25
    assert abs(iterations[0]["p_val"] - 0.25) < 1e-6

    # Orden 2: 0.21875, diff = -0.03125
    assert abs(iterations[1]["p_val"] - 0.21875) < 1e-6
    assert abs(iterations[1]["abs_diff"] - 0.03125) < 1e-6

    # Orden 3: ≈ 0.223958, diff = 0.005208
    assert abs(iterations[2]["p_val"] - 0.22395833) < 1e-5
    assert abs(iterations[2]["abs_diff"] - 0.00520833) < 1e-5

    # Orden 4: ≈ 0.222981, diff = 0.000977 (< 10^-3)
    assert abs(iterations[3]["p_val"] - 0.22298177) < 1e-5
    assert abs(iterations[3]["abs_diff"] - 0.00097656) < 1e-5
    assert iterations[3]["meets_tolerance_delta"] is True
    assert eval_res["best_order"] == 4

    # Orden 5: ≈ 0.223177, diff = 0.000196
    assert abs(iterations[4]["p_val"] - 0.22317708) < 1e-5

    # Orden 6: ≈ 0.223136, diff = 0.000041
    assert abs(iterations[5]["p_val"] - 0.22313638) < 1e-5


def test_whiteboard_ui_integration():
    """
    Verifica que SidebarPanel y WhiteboardConvergenceWidget rendericen
    correctamente la Parte b del pizarrón y detecten las tolerancias 10^-3 y 10^-4.
    También verifica que 'Opciones adicionales' oculte y muestre las entradas según el checkbox.
    """
    from PySide6.QtWidgets import QApplication
    from ui.sidebar_panel import SidebarPanel

    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    panel = SidebarPanel()

    # A primera vista: el checkbox de opciones adicionales está desmarcado y las opciones ocultas
    assert panel.chk_advanced.isChecked() is False
    assert panel.advanced_container.isHidden() is True

    # Al marcar el checkbox, se hacen visibles
    panel.chk_advanced.setChecked(True)
    assert panel.advanced_container.isHidden() is False

    panel.set_inputs("ln(x)", 1.0, 0.2, 2.5, 6, x_eval=1.25, tolerance=0.001)
    assert panel.chk_advanced.isChecked() is True
    assert panel.advanced_container.isHidden() is False

    engine = TaylorEngine()
    res = engine.compute_series("ln(x)", x0=1.0, x_min=0.2, x_max=2.5, max_order=6)
    panel.display_results(res)

    # Comprobar que el widget en la Pestaña 3 (Evaluación) recibió los datos
    assert panel.whiteboard_widget_tab.eval_data is not None
    assert panel.whiteboard_widget_tab.eval_data["best_order"] == 4

    # Cambiar tolerancia a 10^-4 (0.0001) como anotó el profesor en el pizarrón
    panel.set_tolerance(0.0001)
    panel._on_eval_param_changed()

    assert panel.whiteboard_widget_tab.eval_data["best_order"] == 6

    # Al desmarcar el checkbox de opciones adicionales, se oculta el contenedor
    panel.chk_advanced.setChecked(False)
    assert panel.advanced_container.isHidden() is True


def test_taylor_options_dialog_popup():
    """
    Verifica que el diálogo modal pop-up TaylorOptionsDialog permita configurar
    x0, orden n, intervalo y opciones adicionales, actualizando el resumen en SidebarPanel.
    """
    from PySide6.QtWidgets import QApplication
    from ui.sidebar_panel import SidebarPanel

    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    panel = SidebarPanel()

    # Comprobar que el botón de opciones existe y el resumen inicial es correcto
    assert panel.btn_options is not None
    assert "x₀=1" in panel.lbl_options_summary.text()
    assert "n=4" in panel.lbl_options_summary.text()

    # Modificar valores en el diálogo
    panel.options_dialog.spin_x0.setValue(2.0)
    panel.options_dialog.spin_order.setValue(5)
    panel.options_dialog.spin_xmin.setValue(-4.0)
    panel.options_dialog.spin_xmax.setValue(4.0)
    panel.options_dialog.chk_advanced.setChecked(True)
    panel.options_dialog.spin_x_eval.setValue(1.75)

    # Aplicar
    panel.options_dialog._on_apply_clicked()

    # Comprobar que se reflejan en el resumen del panel
    text = panel.lbl_options_summary.text()
    assert "x₀=2" in text
    assert "n=5" in text
    assert "[-4, 4]" in text
    assert "x*=1.75" in text


def test_independent_eval_and_tolerance_checkboxes():
    """
    Verifica que las casillas de evaluación en x y tolerancia de error operen de forma independiente:
    1. Evaluar en x activado pero Tolerancia desactivada:
       - No aplica criterio de parada (best_order es None).
       - spin_tolerance está deshabilitado.
    2. Tolerancia activada:
       - Aplica criterio y calcula best_order.
    3. Evaluar en x desactivado:
       - Deshabilita tanto el punto x como la tolerancia.
    """
    from PySide6.QtWidgets import QApplication
    from ui.sidebar_panel import SidebarPanel
    from taylor_engine import TaylorEngine

    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    panel = SidebarPanel()
    engine = TaylorEngine()
    res = engine.compute_series("ln(x)", x0=1.0, x_min=0.2, x_max=2.5, max_order=6)

    # 1. Activar opciones avanzadas, pero solo Evaluar en x (Tolerancia desactivada)
    panel.chk_advanced.setChecked(True)
    panel.chk_eval_x.setChecked(True)
    panel.chk_tolerance.setChecked(False)
    panel.spin_x_eval.setValue(1.25)
    panel.display_results(res)

    assert panel.is_eval_point_enabled() is True
    assert panel.get_selected_tolerance() is None
    assert panel.spin_tolerance.isEnabled() is False
    assert panel.whiteboard_widget_tab.eval_data["best_order"] is None

    # 2. Activar tolerancia de error a 0.001
    panel.chk_tolerance.setChecked(True)
    panel.spin_tolerance.setValue(0.001)
    panel._on_eval_param_changed()

    assert panel.spin_tolerance.isEnabled() is True
    assert panel.get_selected_tolerance() == 0.001
    assert panel.whiteboard_widget_tab.eval_data["best_order"] == 4

    # 3. Desactivar evaluar en x pero mantener tolerancia activada
    panel.chk_eval_x.setChecked(False)
    panel._on_eval_param_changed()

    # chk_tolerance y spin_tolerance deben seguir habilitados y activos directamente
    assert panel.chk_tolerance.isEnabled() is True
    assert panel.spin_tolerance.isEnabled() is True
    assert panel.get_selected_tolerance() == 0.001
    assert panel.is_eval_point_enabled() is True
    assert panel.spin_x_eval.isEnabled() is False

    # 4. Desactivar tolerancia también
    panel.chk_tolerance.setChecked(False)
    panel._on_eval_param_changed()
    assert panel.get_selected_tolerance() is None
    assert panel.spin_tolerance.isEnabled() is False
    assert panel.is_eval_point_enabled() is False




