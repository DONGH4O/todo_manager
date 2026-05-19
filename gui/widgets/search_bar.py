"""Search bar with Tool-window dropdown — Design doc Sections 1 & 2.

Uses Qt.Tool (frameless, no focus-steal) for reliable z-order and rendering,
positioned 44px below search-container top, width-matched to input.
"""

from PySide6.QtCore import Qt, Signal, QTimer, QSize, QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QGraphicsDropShadowEffect,
    QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QPushButton, QVBoxLayout, QWidget,
)

from todo_manager.gui.theme import (
    LightColors, FONT_FAMILY,
    FONT_SIZE_BASE, FONT_SIZE_SM, FONT_SIZE_XS,
    RADIUS_MD, RADIUS_LG, qcolor,
)
from todo_manager.engine.task_manager import search_tasks


class SearchBar(QWidget):

    result_selected = Signal(str, str)
    overlay_toggled = Signal(bool)

    def __init__(self, theme_colors=None, parent=None):
        super().__init__(parent)
        self._theme = theme_colors or LightColors
        self._debounce_timer = QTimer(singleShot=True, interval=200,
                                       timeout=self._do_search)
        self._anim_pos = None
        self._build_ui()
        self._create_dropdown()

    # ── Construction ────────────────────────────────────

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._input = QLineEdit()
        self._input.setPlaceholderText("搜索任务...")
        self._input.setFont(QFont(FONT_FAMILY, FONT_SIZE_BASE))
        self._input.setFixedHeight(40)
        self._input.textChanged.connect(self._on_text_changed)
        self._input.returnPressed.connect(self._do_search)
        layout.addWidget(self._input)

        self._search_btn = QPushButton("🔍")
        self._search_btn.setFixedSize(36, 36)
        self._search_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._search_btn.clicked.connect(self._do_search)
        layout.addWidget(self._search_btn)

        self._apply_input_style()

    def _create_dropdown(self):
        self._dropdown = QListWidget()
        self._dropdown.setWindowFlags(
            Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint
        )
        self._dropdown.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self._dropdown.setFont(QFont(FONT_FAMILY, FONT_SIZE_SM))
        self._dropdown.itemClicked.connect(self._on_item_clicked)

        self._shadow = QGraphicsDropShadowEffect(self._dropdown)
        self._shadow.setBlurRadius(25)
        self._shadow.setOffset(0, 5)
        self._shadow.setColor(qcolor("rgba(0,0,0,0.25)"))
        self._dropdown.setGraphicsEffect(self._shadow)

        self._apply_dropdown_style()

    # ── Stylesheets ─────────────────────────────────────

    def _apply_input_style(self):
        c = self._theme
        self._input.setStyleSheet(f"""
            QLineEdit {{
                background: {c.BG_SURFACE};
                border: 1px solid {c.BORDER};
                border-radius: {RADIUS_MD}px;
                padding: 0 12px;
                color: {c.TEXT_PRIMARY};
            }}
            QLineEdit:focus {{ border-color: {c.BORDER_FOCUS}; }}
        """)
        self._search_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; border: none;
                color: {c.TEXT_TERTIARY}; font-size: 14px;
            }}
            QPushButton:hover {{
                background: {c.BG_HOVER}; border-radius: 8px;
                color: {c.TEXT_PRIMARY};
            }}
        """)

    def _apply_dropdown_style(self):
        c = self._theme
        self._dropdown.setStyleSheet(f"""
            QListWidget {{
                background: {c.BG_DROPDOWN};
                border: 1px solid {c.BORDER};
                border-radius: {RADIUS_LG}px;
                color: {c.TEXT_PRIMARY};
                padding: 4px;
            }}
            QListWidget::item {{
                padding: 12px 16px;
                border-bottom: 1px solid {c.BORDER_LIGHT};
            }}
            QListWidget::item:hover {{ background: {c.BG_HOVER}; }}
            QListWidget::item:last {{ border-bottom: none; }}
        """)

    # ── Search Logic ────────────────────────────────────

    def _on_text_changed(self):
        self._debounce_timer.start()

    def _do_search(self):
        keyword = self._input.text().strip()
        if len(keyword) < 2:
            self._hide_dropdown()
            return

        results = search_tasks(keyword)
        self._dropdown.clear()

        if not results:
            no_item = QListWidgetItem("无匹配结果")
            no_item.setFont(QFont(FONT_FAMILY, FONT_SIZE_SM))
            no_item.setFlags(Qt.ItemFlag.NoItemFlags)
            no_item.setForeground(qcolor(self._theme.TEXT_TERTIARY))
            self._dropdown.addItem(no_item)
            self._show_dropdown()
            return

        for t in results[:50]:
            item = QListWidgetItem()
            is_sub = t.get("is_sub", False)
            parent_id = t.get("parent_id")
            parent_title = t.get("parent_title", "")
            item.setData(Qt.ItemDataRole.UserRole, (t["id"], t["start_date"], is_sub, parent_id))

            w = QWidget()
            w.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
            lay = QVBoxLayout(w)
            lay.setContentsMargins(0, 0, 0, 0)
            lay.setSpacing(2)

            lay.addStretch()

            title_row = QHBoxLayout()
            title_row.setSpacing(8)

            title_lbl = QLabel(t["title"])
            if is_sub:
                title_lbl.setFont(QFont(FONT_FAMILY, FONT_SIZE_BASE, QFont.Weight.Bold))
                title_lbl.setStyleSheet(
                    f"color: {self._theme.TEXT_PRIMARY}; font-style: italic; border: none; background: transparent;")
            else:
                title_lbl.setFont(QFont(FONT_FAMILY, FONT_SIZE_BASE, QFont.Weight.Bold))
                title_lbl.setStyleSheet(
                    f"color: {self._theme.TEXT_PRIMARY}; border: none; background: transparent;")
            title_lbl.setWordWrap(True)
            title_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
            title_row.addWidget(title_lbl)

            date_lbl = QLabel(t["start_date"])
            date_lbl.setFont(QFont(FONT_FAMILY, FONT_SIZE_XS))
            date_lbl.setStyleSheet(
                f"color: {self._theme.TEXT_TERTIARY}; border: none; background: transparent;")
            date_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
            title_row.addWidget(date_lbl)
            title_row.addStretch()
            lay.addLayout(title_row)

            # Subtask parent indicator
            if is_sub and parent_title:
                parent_lbl = QLabel(f"└─ 所属: {parent_title}")
                parent_lbl.setFont(QFont(FONT_FAMILY, FONT_SIZE_XS))
                parent_lbl.setStyleSheet(
                    f"color: {self._theme.TEXT_LINK}; border: none; background: transparent;")
                parent_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
                lay.addWidget(parent_lbl)

            bg = (t.get("background") or "")
            if len(bg) > 60:
                bg = bg[:60] + "…"
            if bg:
                bg_lbl = QLabel(bg)
                bg_lbl.setFont(QFont(FONT_FAMILY, FONT_SIZE_XS))
                bg_lbl.setStyleSheet(
                    f"color: {self._theme.TEXT_SECONDARY}; border: none; background: transparent;")
                bg_lbl.setWordWrap(True)
                bg_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
                lay.addWidget(bg_lbl)

            # Bottom stretch: balances top stretch to center content vertically
            lay.addStretch()

            min_h = 72 if is_sub else 56
            w.setMinimumHeight(min_h)
            w.adjustSize()
            sh = w.sizeHint()
            item.setSizeHint(QSize(max(sh.width(), 400), max(sh.height(), min_h)))
            self._dropdown.addItem(item)
            self._dropdown.setItemWidget(item, w)

        total_item = QListWidgetItem(f"共 {len(results)} 条结果")
        total_item.setFont(QFont(FONT_FAMILY, FONT_SIZE_XS))
        total_item.setFlags(Qt.ItemFlag.NoItemFlags)
        total_item.setForeground(qcolor(self._theme.TEXT_TERTIARY))
        self._dropdown.addItem(total_item)

        self._show_dropdown()

    # ── Show / Hide ─────────────────────────────────────

    def _show_dropdown(self):
        # Use global coordinates for Tool window positioning
        input_global_pos = self._input.mapToGlobal(self._input.rect().bottomLeft())
        target_pos = QPoint(input_global_pos.x(), input_global_pos.y() + 4)

        self._dropdown.setFixedWidth(self._input.width())
        self._dropdown.setMaximumHeight(360)

        if self._dropdown.isVisible():
            self._dropdown.move(target_pos)
            return

        if self._anim_pos:
            self._anim_pos.stop()
            self._anim_pos = None

        start_pos = QPoint(target_pos.x(), target_pos.y() - 10)
        self._dropdown.move(start_pos)
        self._dropdown.show()

        self._anim_pos = QPropertyAnimation(self._dropdown, b"pos")
        self._anim_pos.setDuration(200)
        self._anim_pos.setStartValue(start_pos)
        self._anim_pos.setEndValue(target_pos)
        self._anim_pos.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim_pos.start()

        # Return keyboard focus to input
        self._input.setFocus()
        self.overlay_toggled.emit(True)

    def _hide_dropdown(self):
        if self._anim_pos:
            self._anim_pos.stop()
            self._anim_pos = None
        self._dropdown.hide()
        self.overlay_toggled.emit(False)

    # ── Events ──────────────────────────────────────────

    def _on_item_clicked(self, item: QListWidgetItem):
        data = item.data(Qt.ItemDataRole.UserRole)
        if data and len(data) >= 2:
            task_id = data[0]
            start_date = data[1]
            is_sub = data[2] if len(data) > 2 else False
            parent_id = data[3] if len(data) > 3 else None
            self._input.clear()
            self._hide_dropdown()
            self.result_selected.emit(task_id, start_date)

    def focus_input(self):
        self._input.setFocus()
        self._input.selectAll()

    def hide_dropdown(self):
        self._hide_dropdown()

    def is_dropdown_visible(self) -> bool:
        return self._dropdown.isVisible()

    def dropdown_global_rect(self):
        r = self._dropdown.rect()
        tl = self._dropdown.mapToGlobal(r.topLeft())
        br = self._dropdown.mapToGlobal(r.bottomRight())
        from PySide6.QtCore import QRect
        return QRect(tl, br)

    def refresh_theme(self, theme_colors):
        self._theme = theme_colors
        self._apply_input_style()
        self._apply_dropdown_style()
