"""
Pruebas automatizadas para el administrador del lienzo cartesiano (plot_manager.py).
Verifica:
1. Escala geométrica óptima: evita que polinomios divergentes aplanen la curva f(x).
2. Funcionalidades de zoom, desplazamiento (pan) y centrado.
3. Botonera flotante y márgenes reducidos estilo GeoGebra.
"""

import pytest
import numpy as np
from PySide6.QtWidgets import QApplication

from taylor_engine import TaylorEngine
from plot_manager import GeoGebraCartesianCanvas, GraphFloatingNavWidget


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_autofit_view_curves_visible(qapp):
    """
    Verifica que la función f(x) = x^4 - 3x^2 + 1 en [-2.5, 2.5] no resulte aplanada.
    Los límites de Y deben enmarcar adecuadamente los mínimos en -1.25 y el pico en 1.0,
    con una altura total de Y moderada (~6 a 12 unidades), en lugar de cientos.
    """
    engine = TaylorEngine()
    res = engine.compute_series("x^4 - 3*x^2 + 1", x0=1.0, x_min=-2.5, x_max=2.5, max_order=4)

    canvas = GeoGebraCartesianCanvas()
    canvas.update_data(res)

    ylim = canvas.ax.get_ylim()
    y_min, y_max = ylim[0], ylim[1]
    y_span = y_max - y_min

    # El mínimo de f(x) es -1.25, por lo que y_min debe estar ligeramente por debajo de -1.25
    assert y_min <= -1.25, f"y_min ({y_min}) debe contener el fondo del pozo -1.25"
    assert y_min > -6.0, f"y_min ({y_min}) no debe estar aplastado por polinomios divergentes"

    # La altura total de la vista debe ser razonable para que la forma de 'W' sea prominente
    assert 4.0 <= y_span <= 18.0, f"El rango vertical ({y_span}) debe permitir que las curvas se noten claramente"


def test_pan_and_zoom_methods(qapp):
    """Verifica que zoom y pan modifiquen los límites de la gráfica correctamente."""
    engine = TaylorEngine()
    res = engine.compute_series("x^2 + 1", x0=0.0, x_min=-2.0, x_max=2.0, max_order=2)

    canvas = GeoGebraCartesianCanvas()
    canvas.update_data(res)

    init_xlim = canvas.ax.get_xlim()
    init_ylim = canvas.ax.get_ylim()

    # Desplazar a la derecha (pan_by positivo en X)
    canvas.pan_by(0.2, 0.0)
    pan_xlim = canvas.ax.get_xlim()
    assert pan_xlim[0] > init_xlim[0]
    assert pan_xlim[1] > init_xlim[1]

    # Aplicar zoom in (factor < 1 reduce la anchura del intervalo)
    canvas.zoom(0.5)
    zoom_xlim = canvas.ax.get_xlim()
    assert (zoom_xlim[1] - zoom_xlim[0]) < (pan_xlim[1] - pan_xlim[0])

    # Centrar en x0 (x0 = 0.0)
    canvas.center_on_x0()
    cx_xlim = canvas.ax.get_xlim()
    center_x = (cx_xlim[0] + cx_xlim[1]) / 2.0
    assert abs(center_x - 0.0) < 1e-4


def test_floating_nav_widget_exists(qapp):
    """Verifica que la botonera flotante esté presente y conectada."""
    canvas = GeoGebraCartesianCanvas()
    assert hasattr(canvas, "floating_nav")
    assert isinstance(canvas.floating_nav, GraphFloatingNavWidget)
    assert canvas.floating_nav.btn_zoom_in is not None
    assert canvas.floating_nav.btn_zoom_out is not None
    assert canvas.floating_nav.btn_home is not None
    assert canvas.floating_nav.btn_x0 is not None
    assert hasattr(canvas.floating_nav, "btn_error")


def test_show_exact_intersection_point(qapp):
    """
    Verifica que el botón de intersección en la botonera flotante traslade la vista
    exactamente a x0 = 1.0 y despliegue el globo de error sin desviación de clic (Imagen 2).
    """
    engine = TaylorEngine()
    res = engine.compute_series("x^4 - 3*x^2 + 1", x0=1.0, x_min=-2.5, x_max=2.5, max_order=4)

    canvas = GeoGebraCartesianCanvas()
    canvas.update_data(res)

    # Invocar el traslado exacto a la intersección
    canvas.floating_nav.btn_error.click()

    # Comprobar que la vista quedó centrada exactamente en x0 = 1.0
    xlim = canvas.ax.get_xlim()
    cx = (xlim[0] + xlim[1]) / 2.0
    assert abs(cx - 1.0) < 1e-4

    # Comprobar que el tooltip explicativo (Imagen 2) se creó y contiene el error matemático
    assert canvas.tooltip_annotation is not None
    text = canvas.tooltip_annotation.get_text()
    assert "x = 1" in text
    assert "f(x) = -1" in text
    assert "P_4(x) = -1" in text
    assert "Error = 0" in text or "0.00" in text

