"""
Renderizador tipográfico de fórmulas matemáticas en LaTeX a QPixmap / QImage.
Utiliza el motor mathtext de Matplotlib sin requerir la instalación de un compilador TeX externo.
Incluye caché en memoria para renderizado ultra rápido y soporte para temas claro y oscuro.
"""

from __future__ import annotations

import io
from typing import Dict, Tuple, Optional
import matplotlib
# Configurar backend agg seguro
matplotlib.use("Agg")
# Configurar tipografía matemática Computer Modern idéntica a LaTeX clásico (Imagen 2)
matplotlib.rcParams["mathtext.fontset"] = "cm"
matplotlib.rcParams["font.family"] = "serif"
import matplotlib.pyplot as plt
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt


class LaTeXRenderer:
    """
    Renderiza expresiones LaTeX en mapas de píxeles QPixmap de alta resolución.
    """

    def __init__(self, default_dpi: int = 150):
        self.default_dpi = default_dpi
        # Caché de pixmaps: clave -> ((latex_str, font_size, color_hex, dpi), QPixmap)
        self._pixmap_cache: Dict[Tuple[str, int, str, int], QPixmap] = {}
        # Caché de bytes de imagen (PNG)
        self._bytes_cache: Dict[Tuple[str, int, str, int], bytes] = {}

    def clean_latex_string(self, latex_str: str) -> str:
        """
        Limpia y envuelve la expresión LaTeX para el motor mathtext de Matplotlib.
        """
        s = latex_str.strip()
        # Eliminar signos $ si ya los tiene
        if s.startswith("$") and s.endswith("$") and len(s) >= 2:
            s = s[1:-1].strip()

        # Reemplazar comandos de LaTeX no soportados o conflictivos en mathtext
        replacements = {
            r"\left(": "(",
            r"\right)": ")",
            r"\left[": "[",
            r"\right]": "]",
            r"\left\{": r"\{",
            r"\right\}": r"\}",
            r"\left|": "|",
            r"\right|": "|",
            r"\text{": r"\mathrm{",
            r"\operatorname{": r"\mathrm{",
        }
        for orig, rep in replacements.items():
            s = s.replace(orig, rep)

        # Envolver en entorno matemático mathtext
        return f"${s}$"

    def render_to_bytes(
        self,
        latex_str: str,
        font_size: int = 14,
        color_hex: str = "#1e293b",
        dpi: Optional[int] = None
    ) -> bytes:
        """
        Renderiza la fórmula LaTeX a bytes PNG.
        """
        dpi = dpi or self.default_dpi
        key = (latex_str, font_size, color_hex, dpi)
        if key in self._bytes_cache:
            return self._bytes_cache[key]

        cleaned = self.clean_latex_string(latex_str)

        fig = plt.figure(figsize=(0.1, 0.1), dpi=dpi)
        fig.patch.set_alpha(0.0)

        # Añadir texto en el centro
        text = fig.text(
            0.5, 0.5,
            cleaned,
            fontsize=font_size,
            color=color_hex,
            ha="center",
            va="center"
        )

        buf = io.BytesIO()
        try:
            fig.savefig(
                buf,
                format="png",
                dpi=dpi,
                bbox_inches="tight",
                pad_inches=0.04,
                transparent=True
            )
            data = buf.getvalue()
        finally:
            plt.close(fig)

        self._bytes_cache[key] = data
        return data

    def render_to_pixmap(
        self,
        latex_str: str,
        font_size: int = 14,
        color_hex: str = "#1e293b",
        dpi: Optional[int] = None
    ) -> QPixmap:
        """
        Renderiza una expresión LaTeX directamente a un objeto QPixmap para interfaces Qt.
        """
        dpi = dpi or self.default_dpi
        key = (latex_str, font_size, color_hex, dpi)
        if key in self._pixmap_cache:
            return self._pixmap_cache[key]

        png_bytes = self.render_to_bytes(latex_str, font_size, color_hex, dpi)
        qimg = QImage()
        qimg.loadFromData(png_bytes)
        pixmap = QPixmap.fromImage(qimg)

        self._pixmap_cache[key] = pixmap
        return pixmap

    def clear_cache(self) -> None:
        """Limpia los cachés en memoria."""
        self._pixmap_cache.clear()
        self._bytes_cache.clear()


# Instancia singleton para uso en toda la aplicación
GLOBAL_LATEX_RENDERER = LaTeXRenderer()
