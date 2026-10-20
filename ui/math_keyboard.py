"""
Teclado matemático virtual diseñado a partir del teclado oficial de GeoGebra Suite Calculadora (Imagen 2).
Organizado con pestañas [123], [f(x)], [ABC], [#&~] y distribución exacta de teclas numéricas y algebraicas.
"""

from __future__ import annotations

from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLineEdit, QTabWidget, QLabel, QFrame,
    QButtonGroup
)
from PySide6.QtCore import Qt, Signal


class GeoGebraVirtualKeyboard(QFrame):
    """
    Teclado virtual idéntico a GeoGebra Suite Calculadora (Imagen 2).
    """
    expression_confirmed = Signal()

    def __init__(self, parent=None, is_dark_mode: bool = False):
        super().__init__(parent)
        self.setObjectName("geogebraVirtualKeyboard")
        self.is_dark_mode = is_dark_mode
        self._target_input: Optional[QLineEdit] = None

        self._init_ui()

    def set_target_input(self, line_edit: Optional[QLineEdit]):
        self._target_input = line_edit

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 4, 6, 6)
        main_layout.setSpacing(4)

        # Barra superior con pestañas GeoGebra: [123] [f(x)] [ABC] [#&~] y botón de cerrar
        top_bar = QHBoxLayout()
        top_bar.setSpacing(4)

        self.btn_tab_123 = QPushButton("123")
        self.btn_tab_123.setCheckable(True)
        self.btn_tab_123.setChecked(True)
        self.btn_tab_123.setStyleSheet("font-weight: 700; padding: 4px 14px; border-radius: 12px;")

        self.btn_tab_fx = QPushButton("f(x)")
        self.btn_tab_fx.setCheckable(True)
        self.btn_tab_fx.setStyleSheet("font-weight: 700; padding: 4px 14px; border-radius: 12px;")

        self.btn_tab_abc = QPushButton("ABC")
        self.btn_tab_abc.setCheckable(True)
        self.btn_tab_abc.setStyleSheet("font-weight: 700; padding: 4px 14px; border-radius: 12px;")

        # Agrupar pestañas
        self.tab_group = QButtonGroup(self)
        self.tab_group.addButton(self.btn_tab_123, 0)
        self.tab_group.addButton(self.btn_tab_fx, 1)
        self.tab_group.addButton(self.btn_tab_abc, 2)
        self.tab_group.idClicked.connect(self._on_tab_switched)

        top_bar.addStretch()
        top_bar.addWidget(self.btn_tab_123)
        top_bar.addWidget(self.btn_tab_fx)
        top_bar.addWidget(self.btn_tab_abc)
        top_bar.addStretch()

        # Botón para colapsar teclado (esquina derecha)
        btn_collapse = QPushButton("✕")
        btn_collapse.setFixedSize(24, 24)
        btn_collapse.setToolTip("Ocultar teclado")
        btn_collapse.setStyleSheet("border: none; font-size: 13px; font-weight: bold; color: #64748b;")
        btn_collapse.clicked.connect(self.hide)
        top_bar.addWidget(btn_collapse)

        main_layout.addLayout(top_bar)

        # Contenedor para las vistas de teclas
        self.tab_container = QWidget()
        self.tab_layout = QVBoxLayout(self.tab_container)
        self.tab_layout.setContentsMargins(0, 0, 0, 0)

        # 1. Panel de Teclas 123 (GeoGebra exacto)
        self.panel_123 = self._create_123_keypad()
        self.tab_layout.addWidget(self.panel_123)

        # 2. Panel de Teclas f(x)
        self.panel_fx = self._create_fx_keypad()
        self.panel_fx.hide()
        self.tab_layout.addWidget(self.panel_fx)

        # 3. Panel de Teclas ABC
        self.panel_abc = self._create_abc_keypad()
        self.panel_abc.hide()
        self.tab_layout.addWidget(self.panel_abc)

        main_layout.addWidget(self.tab_container)

    def _create_123_keypad(self) -> QWidget:
        """Crea el teclado '123' idéntico a la distribución de GeoGebra (Imagen 2)."""
        w = QWidget()
        grid = QGridLayout(w)
        grid.setSpacing(3)
        grid.setContentsMargins(4, 2, 4, 2)

        # Matriz GeoGebra: 5 columnas a la izquierda (álgebra) + 5 columnas a la derecha (numérico)
        # Fila 0
        # x, y, pi, e | 7, 8, 9, *, /
        keys_row0 = [
            ("x", "x"), ("y", "y"), ("π", "pi"), ("e", "E"),
            ("7", "7"), ("8", "8"), ("9", "9"), ("×", "*"), ("÷", "/")
        ]
        # Fila 1
        # x^2, x^n, sqrt, |x| | 4, 5, 6, +, -
        keys_row1 = [
            ("x²", ("^2", "wrap_pow2")), ("xⁿ", ("^", "wrap_pow")),
            ("√", ("sqrt(", "wrap_sqrt")), ("|x|", ("abs(", "wrap_abs")),
            ("4", "4"), ("5", "5"), ("6", "6"), ("+", "+"), ("−", "-")
        ]
        # Fila 2
        # <, >, (, ) | 1, 2, 3, =, backspace
        keys_row2 = [
            ("<", "<"), (">", ">"), ("(", "("), (")", ")"),
            ("1", "1"), ("2", "2"), ("3", "3"), ("=", "="), ("⌫", self._backspace)
        ]
        # Fila 3
        # ans, ,, nroot, frac | 0, ., left, right, enter
        keys_row3 = [
            ("ans", "ans"), (",", ","), ("ⁿ√", ("root(x, 3)", "wrap_nroot")), ("frac", ("/(", "wrap_frac")),
            ("0", "0"), (".", "."), ("←", self._move_left), ("→", self._move_right), ("↵", self._confirm)
        ]

        all_rows = [keys_row0, keys_row1, keys_row2, keys_row3]

        for r_idx, row in enumerate(all_rows):
            for c_idx, (text, action) in enumerate(row):
                btn = QPushButton(text)
                btn.setFixedHeight(34)
                btn.setMinimumWidth(38)

                # Estilos visuales acordes a GeoGebra
                if text in ("7", "8", "9", "4", "5", "6", "1", "2", "3", "0", "."):
                    btn.setStyleSheet("font-size: 14px; font-weight: 600;")
                elif text in ("×", "÷", "+", "−", "="):
                    btn.setStyleSheet("font-size: 15px; font-weight: 700; color: #2563eb;")
                elif text == "↵":
                    btn.setStyleSheet("font-size: 15px; font-weight: 700; background-color: #2563eb; color: #ffffff;")
                elif text == "frac":
                    btn.setText("a/b")
                    btn.setStyleSheet("font-size: 12px; font-weight: 700; color: #2563eb;")
                else:
                    btn.setStyleSheet("font-size: 13px; font-weight: 500;")

                btn.clicked.connect(lambda checked=False, act=action: self._handle_key(act))
                grid.addWidget(btn, r_idx, c_idx)

        return w

    def _create_fx_keypad(self) -> QWidget:
        """Crea el teclado de funciones trascendentes f(x)."""
        w = QWidget()
        grid = QGridLayout(w)
        grid.setSpacing(3)
        grid.setContentsMargins(4, 2, 4, 2)

        funcs = [
            [("sin", "sin("), ("cos", "cos("), ("tan", "tan("), ("exp", "exp("), ("ln", "log(")],
            [("asin", "asin("), ("acos", "acos("), ("atan", "atan("), ("log₁₀", "log10("), ("log₂", "log2(")],
            [("sinh", "sinh("), ("cosh", "cosh("), ("tanh", "tanh("), ("sec", "sec("), ("csc", "csc(")],
            [("cot", "cot("), ("abs", "abs("), ("root", "root("), ("factorial", "factorial("), ("C", self._clear_input)]
        ]

        for r_idx, row in enumerate(funcs):
            for c_idx, (text, action) in enumerate(row):
                btn = QPushButton(text)
                btn.setFixedHeight(34)
                btn.setMinimumWidth(55)
                btn.setStyleSheet("font-size: 12px; font-weight: 600; color: #2563eb;")
                btn.clicked.connect(lambda checked=False, act=action: self._handle_key(act))
                grid.addWidget(btn, r_idx, c_idx)

        return w

    def _create_abc_keypad(self) -> QWidget:
        """Crea el teclado alfabético compacto ABC."""
        w = QWidget()
        grid = QGridLayout(w)
        grid.setSpacing(3)
        grid.setContentsMargins(4, 2, 4, 2)

        letters = [
            ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p"],
            ["a", "s", "d", "f", "g", "h", "j", "k", "l", "ñ"],
            ["z", "x", "c", "v", "b", "n", "m", "_", "(", ")"]
        ]

        for r_idx, row in enumerate(letters):
            for c_idx, char in enumerate(row):
                btn = QPushButton(char)
                btn.setFixedHeight(32)
                btn.setMinimumWidth(32)
                btn.clicked.connect(lambda checked=False, ch=char: self._handle_key(ch))
                grid.addWidget(btn, r_idx, c_idx)

        return w

    def _on_tab_switched(self, tab_id: int):
        self.panel_123.setVisible(tab_id == 0)
        self.panel_fx.setVisible(tab_id == 1)
        self.panel_abc.setVisible(tab_id == 2)

    def _handle_key(self, action):
        if callable(action):
            action()
            return

        target = self._target_input
        if not target:
            return

        target.setFocus()
        selected_text = target.selectedText()
        cursor_pos = target.cursorPosition()

        if isinstance(action, tuple):
            token, behavior = action
            if behavior == "wrap_pow2":
                if selected_text:
                    target.insert(f"({selected_text})^2")
                else:
                    target.insert("^2")
            elif behavior == "wrap_pow":
                if selected_text:
                    target.insert(f"({selected_text})^")
                else:
                    target.insert("^")
            elif behavior == "wrap_sqrt":
                if selected_text:
                    target.insert(f"sqrt({selected_text})")
                else:
                    target.insert("sqrt()")
                    target.setCursorPosition(cursor_pos + 5)
            elif behavior == "wrap_abs":
                if selected_text:
                    target.insert(f"abs({selected_text})")
                else:
                    target.insert("abs()")
                    target.setCursorPosition(cursor_pos + 4)
            elif behavior == "wrap_frac":
                # Botón de fracción a/b
                if selected_text:
                    target.insert(f"({selected_text})/")
                else:
                    target.insert("/")
            elif behavior == "wrap_nroot":
                if selected_text:
                    target.insert(f"root({selected_text}, 3)")
                else:
                    target.insert("root(x, 3)")
        elif isinstance(action, str):
            if action.endswith("("):
                if selected_text:
                    target.insert(f"{action}{selected_text})")
                else:
                    target.insert(f"{action})")
                    target.setCursorPosition(cursor_pos + len(action))
            else:
                target.insert(action)

    def _backspace(self):
        target = self._target_input
        if target:
            target.setFocus()
            target.backspace()

    def _clear_input(self):
        target = self._target_input
        if target:
            target.clear()
            target.setFocus()

    def _move_left(self):
        target = self._target_input
        if target:
            target.setFocus()
            target.setCursorPosition(max(0, target.cursorPosition() - 1))

    def _move_right(self):
        target = self._target_input
        if target:
            target.setFocus()
            target.setCursorPosition(min(len(target.text()), target.cursorPosition() + 1))

    def _confirm(self):
        self.expression_confirmed.emit()


# Alias de compatibilidad
MathVirtualKeyboard = GeoGebraVirtualKeyboard
