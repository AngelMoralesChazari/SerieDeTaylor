#!/usr/bin/env python3
"""
Punto de entrada principal para la aplicación de cálculo y análisis visual de Series de Taylor.
"""

import sys
import os
from PySide6.QtWidgets import QApplication, QSplashScreen
from PySide6.QtGui import QPixmap, QPainter, QColor
from PySide6.QtCore import Qt, QRectF


def main():
    # Asegurar renderizado correcto en pantallas de alta densidad
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Serie de Taylor - Calculadora y Análisis Visual")
    app.setOrganizationName("MetodosNumericos")
    app.setApplicationVersion("1.0.0")

    # Pantalla de carga inmediata (Feedback instantáneo < 100 ms al hacer doble clic)
    pixmap = QPixmap(360, 180)
    pixmap.fill(QColor("#18181b"))
    painter = QPainter(pixmap)
    painter.setPen(QColor("#3b82f6"))
    font_title = painter.font()
    font_title.setPointSize(14)
    font_title.setBold(True)
    painter.setFont(font_title)
    painter.drawText(QRectF(0, 45, 360, 35), Qt.AlignCenter, "Serie de Taylor")

    painter.setPen(QColor("#a1a1aa"))
    font_sub = painter.font()
    font_sub.setPointSize(9)
    font_sub.setBold(False)
    painter.setFont(font_sub)
    painter.drawText(QRectF(0, 85, 360, 25), Qt.AlignCenter, "Iniciando entorno gráfico y matemático...")
    painter.end()

    splash = QSplashScreen(pixmap, Qt.WindowStaysOnTopHint)
    splash.show()
    app.processEvents()

    from ui.main_window import MainWindow
    window = MainWindow()
    window.show()
    splash.finish(window)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
