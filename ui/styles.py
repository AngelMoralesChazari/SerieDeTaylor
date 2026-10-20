"""
Sistema de estilos visuales modernos inspirados en GeoGebra Suite Calculadora.
Soporta temas Claro y Oscuro con tarjetas limpias, tipografía sobria y acabados profesionales.
"""

def get_application_stylesheet(is_dark: bool = False) -> str:
    """Retorna la hoja de estilos Qt (QSS) para la aplicación completa."""
    if is_dark:
        bg_main = "#0f172a"          # Pizarra profundo
        bg_card = "#1e293b"          # Pizarra medio
        bg_card_hover = "#334155"
        bg_input = "#0f172a"
        border_color = "#334155"
        border_focus = "#38bdf8"
        text_primary = "#f8fafc"
        text_secondary = "#94a3b8"
        text_muted = "#64748b"
        accent = "#38bdf8"
        accent_hover = "#0ea5e9"
        primary_btn_bg = "#2563eb"
        primary_btn_hover = "#1d4ed8"
        btn_bg = "#334155"
        btn_hover = "#475569"
        tab_bg = "#1e293b"
        tab_active_bg = "#0f172a"
        scroll_thumb = "#475569"
    else:
        bg_main = "#f8fafc"          # Blanco suave / pizarra claro
        bg_card = "#ffffff"
        bg_card_hover = "#f1f5f9"
        bg_input = "#ffffff"
        border_color = "#e2e8f0"
        border_focus = "#2563eb"
        text_primary = "#0f172a"
        text_secondary = "#475569"
        text_muted = "#94a3b8"
        accent = "#2563eb"
        accent_hover = "#1d4ed8"
        primary_btn_bg = "#2563eb"
        primary_btn_hover = "#1d4ed8"
        btn_bg = "#f1f5f9"
        btn_hover = "#e2e8f0"
        tab_bg = "#f1f5f9"
        tab_active_bg = "#ffffff"
        scroll_thumb = "#cbd5e1"

    return f"""
    /* Ventana y contenedores generales */
    QMainWindow, QWidget {{
        background-color: {bg_main};
        color: {text_primary};
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        font-size: 13px;
    }}

    QFrame.card {{
        background-color: {bg_card};
        border: 1px solid {border_color};
        border-radius: 8px;
        padding: 10px;
    }}

    /* Barra de herramientas superior */
    QToolBar {{
        background-color: {bg_card};
        border-bottom: 1px solid {border_color};
        padding: 4px 8px;
        spacing: 6px;
    }}

    /* Botones */
    QPushButton {{
        background-color: {btn_bg};
        color: {text_primary};
        border: 1px solid {border_color};
        border-radius: 6px;
        padding: 6px 14px;
        font-weight: 500;
        outline: none;
    }}

    QPushButton:hover {{
        background-color: {btn_hover};
        border-color: {accent};
    }}

    QPushButton:pressed {{
        background-color: {border_color};
    }}

    QPushButton.primary {{
        background-color: {primary_btn_bg};
        color: #ffffff;
        border: none;
        font-weight: 600;
        padding: 8px 18px;
    }}

    QPushButton.primary:hover {{
        background-color: {primary_btn_hover};
    }}

    QPushButton.primary:pressed {{
        background-color: #1e40af;
    }}

    QPushButton.key-btn {{
        background-color: {bg_card};
        color: {text_primary};
        border: 1px solid {border_color};
        border-radius: 5px;
        font-size: 13px;
        font-weight: 500;
        min-width: 38px;
        min-height: 32px;
        padding: 2px 4px;
    }}

    QPushButton.key-btn:hover {{
        background-color: {btn_hover};
        border-color: {accent};
    }}

    QPushButton.key-btn-op {{
        background-color: {btn_bg};
        color: {accent};
        font-weight: 600;
    }}

    QPushButton.key-btn-accent {{
        background-color: {primary_btn_bg};
        color: #ffffff;
        font-weight: 600;
    }}

    /* Campos de entrada */
    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
        background-color: {bg_input};
        color: {text_primary};
        border: 1px solid {border_color};
        border-radius: 6px;
        padding: 6px 10px;
        selection-background-color: {accent};
        selection-color: #ffffff;
    }}

    QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
        border: 1.5px solid {border_focus};
    }}

    /* Pestañas estilo GeoGebra */
    QTabWidget::pane {{
        border: 1px solid {border_color};
        background-color: {bg_card};
        border-radius: 6px;
    }}

    QTabBar::tab {{
        background-color: {tab_bg};
        color: {text_secondary};
        padding: 8px 16px;
        margin-right: 2px;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
        font-weight: 500;
    }}

    QTabBar::tab:selected {{
        background-color: {tab_active_bg};
        color: {accent};
        font-weight: 600;
        border-bottom: 2px solid {accent};
    }}

    QTabBar::tab:hover:!selected {{
        color: {text_primary};
        background-color: {btn_hover};
    }}

    /* Scrollbars */
    QScrollBar:vertical {{
        background-color: transparent;
        width: 8px;
        margin: 0px;
    }}

    QScrollBar::handle:vertical {{
        background-color: {scroll_thumb};
        min-height: 24px;
        border-radius: 4px;
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    QScrollBar:horizontal {{
        background-color: transparent;
        height: 8px;
        margin: 0px;
    }}

    QScrollBar::handle:horizontal {{
        background-color: {scroll_thumb};
        min-width: 24px;
        border-radius: 4px;
    }}

    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}

    /* Tablas */
    QTableWidget {{
        background-color: {bg_card};
        color: {text_primary};
        border: 1px solid {border_color};
        border-radius: 6px;
        gridline-color: {border_color};
        selection-background-color: {accent};
        selection-color: #ffffff;
    }}

    QHeaderView::section {{
        background-color: {tab_bg};
        color: {text_secondary};
        font-weight: 600;
        border: none;
        border-bottom: 1px solid {border_color};
        border-right: 1px solid {border_color};
        padding: 6px;
    }}

    /* Divisores (Splitters) */
    QSplitter::handle {{
        background-color: {border_color};
    }}

    QSplitter::handle:hover {{
        background-color: {accent};
    }}

    /* CheckBoxes */
    QCheckBox {{
        spacing: 6px;
        color: {text_primary};
    }}

    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
        border: 1px solid {border_color};
        border-radius: 4px;
        background-color: {bg_input};
    }}

    QCheckBox::indicator:checked {{
        background-color: {accent};
        border-color: {accent};
        image: none;
    }}

    /* Etiquetas de texto */
    QLabel.secondary {{
        color: {text_secondary};
        font-size: 11px;
    }}

    QLabel.title {{
        font-size: 14px;
        font-weight: 600;
        color: {text_primary};
    }}

    QLabel.badge {{
        background-color: {btn_bg};
        color: {accent};
        border-radius: 4px;
        padding: 2px 6px;
        font-size: 11px;
        font-weight: 600;
    }}
    """
