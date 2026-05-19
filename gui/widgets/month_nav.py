"""年月导航栏 — 月份前后箭头 + 年/月下拉选择器。"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
    QGridLayout, QSizePolicy,
)

from todo_manager.gui.theme import (
    LightColors, FONT_FAMILY, FONT_SIZE_SM, FONT_SIZE_XL,
    RADIUS_MD, RADIUS_LG, RADIUS_SM, qcolor,
)

MIN_YEAR = 2006
MAX_YEAR = 2046
MONTHS = ["1月", "2月", "3月", "4月", "5月", "6月",
          "7月", "8月", "9月", "10月", "11月", "12月"]


class MonthNav(QWidget):
    """年月导航栏。"""

    prev_month = Signal()
    next_month = Signal()
    month_selected = Signal(int)  # 1-12
    year_selected = Signal(int)   # e.g. 2026

    def __init__(self, year: int, month: int, theme_colors=None, parent=None):
        super().__init__(parent)
        self._year = year
        self._month = month
        self._theme = theme_colors or LightColors

        self._build_ui()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addStretch()

        # 上一月
        self._prev_btn = QPushButton("◀")
        self._prev_btn.setFixedSize(36, 36)
        self._prev_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._prev_btn.clicked.connect(self.prev_month)
        layout.addWidget(self._prev_btn)

        # 年份（可点击弹出选择器）
        self._year_btn = QPushButton(f"{self._year}年")
        self._year_btn.setFont(QFont(FONT_FAMILY, FONT_SIZE_XL, QFont.Weight.Bold))
        self._year_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._year_btn.setFlat(True)
        self._year_btn.clicked.connect(self._show_year_picker)
        layout.addWidget(self._year_btn)

        # 月份（可点击弹出选择器）
        self._month_btn = QPushButton(f"{self._month}月")
        self._month_btn.setFont(QFont(FONT_FAMILY, FONT_SIZE_XL, QFont.Weight.Bold))
        self._month_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._month_btn.setFlat(True)
        self._month_btn.clicked.connect(self._show_month_picker)
        layout.addWidget(self._month_btn)

        # 下一月
        self._next_btn = QPushButton("▶")
        self._next_btn.setFixedSize(36, 36)
        self._next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._next_btn.clicked.connect(self.next_month)
        layout.addWidget(self._next_btn)

        layout.addStretch()

        self._apply_style()
        self._update_arrow_state()

    def _apply_style(self):
        c = self._theme
        btn_style = f"""
            QPushButton {{
                background: {c.BG_SURFACE};
                border: 1px solid {c.BORDER};
                border-radius: {RADIUS_MD}px;
                color: {c.TEXT_PRIMARY};
                font-size: 14px;
            }}
            QPushButton:hover {{
                background: {c.BG_HOVER};
            }}
            QPushButton:disabled {{
                opacity: 0.3; color: {c.TEXT_TERTIARY};
            }}
        """
        self._prev_btn.setStyleSheet(btn_style)
        self._next_btn.setStyleSheet(btn_style)

        label_style = f"""
            QPushButton {{
                background: transparent; border: none; color: {c.TEXT_PRIMARY};
                padding: 6px 14px; border-radius: {RADIUS_MD}px;
            }}
            QPushButton:hover {{
                background: {c.BG_HOVER};
            }}
        """
        self._year_btn.setStyleSheet(label_style)
        self._month_btn.setStyleSheet(label_style)

    def _update_arrow_state(self):
        at_min = (self._year == MIN_YEAR and self._month == 1)
        at_max = (self._year == MAX_YEAR and self._month == 12)
        self._prev_btn.setEnabled(not at_min)
        self._next_btn.setEnabled(not at_max)

    def _show_month_picker(self):
        self._close_month_popup()
        popup = QWidget()
        popup.setWindowFlags(Qt.WindowType.Popup)
        popup.setStyleSheet(f"""
            QWidget {{
                background: {self._theme.BG_DROPDOWN};
                border: 1px solid {self._theme.BORDER};
                border-radius: {RADIUS_LG}px;
            }}
        """)

        layout = QGridLayout(popup)
        layout.setSpacing(4)

        for i, m in enumerate(MONTHS):
            btn = QPushButton(m)
            btn.setFont(QFont(FONT_FAMILY, FONT_SIZE_SM))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            is_current = (i + 1) == self._month
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {self._theme.BORDER_FOCUS if is_current else "transparent"};
                    color: {"#FFF" if is_current else self._theme.TEXT_PRIMARY};
                    border: none; border-radius: {RADIUS_SM}px;
                    padding: 8px 12px;
                }}
                QPushButton:hover {{
                    background: {self._theme.BORDER_FOCUS if is_current else self._theme.BG_HOVER};
                    color: {"#FFF" if is_current else self._theme.TEXT_PRIMARY};
                }}
            """)
            m_idx = i + 1
            btn.clicked.connect(lambda checked=False, mi=m_idx: self._on_month_picked(mi, popup))
            layout.addWidget(btn, i // 4, i % 4)

        pos = self._month_btn.mapToGlobal(self._month_btn.rect().bottomLeft())
        popup.move(pos.x() - 50, pos.y() + 6)
        popup.show()
        self._month_popup = popup

    def _close_month_popup(self):
        if hasattr(self, '_month_popup') and self._month_popup:
            self._month_popup.close()
            self._month_popup = None

    def _on_month_picked(self, m: int, popup: QWidget):
        popup.close()
        self._month_popup = None
        self.month_selected.emit(m)

    def _show_year_picker(self):
        self._close_year_popup()
        popup = QWidget()
        popup.setWindowFlags(Qt.WindowType.Popup)
        c = self._theme
        popup.setStyleSheet(f"""
            QWidget {{
                background: {c.BG_DROPDOWN};
                border: 1px solid {c.BORDER};
                border-radius: {RADIUS_LG}px;
            }}
        """)

        layout = QVBoxLayout(popup)
        layout.setSpacing(4)

        # 翻页栏
        nav_layout = QHBoxLayout()
        base_year = ((self._year - MIN_YEAR) // 5) * 5 + MIN_YEAR

        prev_page_btn = QPushButton("◀")
        prev_page_btn.setFixedSize(28, 28)
        prev_page_btn.setEnabled(base_year > MIN_YEAR)
        nav_layout.addWidget(prev_page_btn)

        range_label = QLabel(f"{base_year} — {min(base_year + 4, MAX_YEAR)}")
        range_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_SM, QFont.Weight.Bold))
        range_label.setStyleSheet(f"color: {c.TEXT_SECONDARY}; border: none; background: transparent;")
        range_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav_layout.addWidget(range_label)

        next_page_btn = QPushButton("▶")
        next_page_btn.setFixedSize(28, 28)
        next_page_btn.setEnabled(base_year + 5 <= MAX_YEAR)
        nav_layout.addWidget(next_page_btn)

        layout.addLayout(nav_layout)

        # 年份网格
        year_grid = QGridLayout()
        year_grid.setSpacing(4)

        def _build_year_grid(base):
            # 清空
            while year_grid.count():
                item = year_grid.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            for i in range(5):
                y = base + i
                if y > MAX_YEAR:
                    break
                btn = QPushButton(str(y))
                btn.setFont(QFont(FONT_FAMILY, FONT_SIZE_SM))
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                is_current = y == self._year
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: {c.BORDER_FOCUS if is_current else "transparent"};
                        color: {"#FFF" if is_current else c.TEXT_PRIMARY};
                        border: none; border-radius: {RADIUS_SM}px;
                        padding: 8px 12px;
                    }}
                    QPushButton:hover {{
                        background: {c.BORDER_FOCUS if is_current else c.BG_HOVER};
                        color: {"#FFF" if is_current else c.TEXT_PRIMARY};
                    }}
                """)
                btn.clicked.connect(lambda checked=False, yy=y: self._on_year_picked(yy, popup))
                year_grid.addWidget(btn, i // 3, i % 3)

            # 更新翻页按钮
            prev_page_btn.setEnabled(base > MIN_YEAR)
            next_page_btn.setEnabled(base + 5 <= MAX_YEAR)
            range_label.setText(f"{base} — {min(base + 4, MAX_YEAR)}")

        _build_year_grid(base_year)

        def _prev_page():
            nonlocal base_year
            new_base = base_year - 5
            if new_base >= MIN_YEAR:
                base_year = new_base
                _build_year_grid(base_year)

        def _next_page():
            nonlocal base_year
            new_base = base_year + 5
            if new_base + 4 <= MAX_YEAR:
                base_year = new_base
                _build_year_grid(base_year)

        prev_page_btn.clicked.connect(_prev_page)
        next_page_btn.clicked.connect(_next_page)

        layout.addLayout(year_grid)

        pos = self._year_btn.mapToGlobal(self._year_btn.rect().bottomLeft())
        popup.move(pos.x() - 30, pos.y() + 6)
        popup.show()
        self._year_popup = popup

    def _close_year_popup(self):
        if hasattr(self, '_year_popup') and self._year_popup:
            self._year_popup.close()
            self._year_popup = None

    def _on_year_picked(self, y: int, popup: QWidget):
        popup.close()
        self._year_popup = None
        self.year_selected.emit(y)

    def update_display(self, year: int, month: int):
        """更新显示的年月。"""
        self._year = year
        self._month = month
        self._year_btn.setText(f"{year}年")
        self._month_btn.setText(f"{month}月")
        self._update_arrow_state()

    def refresh_theme(self, theme_colors):
        self._theme = theme_colors
        self._apply_style()
