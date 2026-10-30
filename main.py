#!/usr/bin/env python3
"""
Punto de entrada principal para la aplicación de cálculo y análisis visual de Series de Taylor.
"""

import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt


def main():
    # Asegurar renderizado correcto en pantallas de alta densidad
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Serie de Taylor - Calculadora y Análisis Visual")
    app.setOrganizationName("MetodosNumericos")
    app.setApplicationVersion("1.0.0")

    from ui.main_window import MainWindow
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
