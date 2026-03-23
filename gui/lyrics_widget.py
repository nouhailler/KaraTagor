"""
Widget karaoké avec défilement automatique et surbrillance de la ligne active.
"""

from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QLabel,
    QPushButton, QSizePolicy, QFrame,
)


class LyricsWidget(QWidget):
    search_requested = pyqtSignal()   # émis quand l'utilisateur clique "Rechercher en ligne"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._lyrics: list[tuple[int, str]] = []   # [(ms, text), ...]
        self._plain_text: str = ""
        self._current_index: int = -1
        self._labels: list[QLabel] = []
        self._setup_ui()

    # ------------------------------------------------------------------
    # Construction UI
    # ------------------------------------------------------------------

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._scroll = QScrollArea()
        self._scroll.setObjectName("lyrics_area")
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self._container = QWidget()
        self._container.setObjectName("lyrics_area")
        self._container_layout = QVBoxLayout(self._container)
        self._container_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self._container_layout.setSpacing(8)
        self._container_layout.setContentsMargins(20, 40, 20, 40)

        self._scroll.setWidget(self._container)
        layout.addWidget(self._scroll)

        # Zone "aucune parole"
        self._empty_widget = QWidget()
        empty_layout = QVBoxLayout(self._empty_widget)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._empty_label = QLabel("Aucune parole disponible")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet("font-size: 18px; color: #445566;")

        self._search_btn = QPushButton("Rechercher en ligne")
        self._search_btn.setMaximumWidth(220)
        self._search_btn.clicked.connect(self.search_requested.emit)

        empty_layout.addWidget(self._empty_label)
        empty_layout.addSpacing(16)
        empty_layout.addWidget(self._search_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self._empty_widget)
        self._empty_widget.hide()

        self._show_empty()

    # ------------------------------------------------------------------
    # API publique
    # ------------------------------------------------------------------

    def set_lyrics(self, lyrics: list[tuple[int, str]]):
        """Charge des paroles synchronisées [(ms, text), ...]."""
        self._lyrics = lyrics
        self._plain_text = ""
        self._current_index = -1
        self._rebuild_labels()
        self._scroll.show()
        self._empty_widget.hide()

    def set_plain_text(self, text: str):
        """Affiche un texte non synchronisé (USLT)."""
        self._lyrics = []
        self._plain_text = text
        self._current_index = -1
        self._clear_labels()

        label = QLabel(text)
        label.setObjectName("lyric_plain")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._container_layout.addWidget(label)
        self._labels = [label]

        self._scroll.show()
        self._empty_widget.hide()

    def clear(self):
        self._lyrics = []
        self._plain_text = ""
        self._current_index = -1
        self._clear_labels()
        self._show_empty()

    def update_position(self, current_ms: int):
        """Appelé depuis le timer AudioEngine toutes les 100ms."""
        if not self._lyrics:
            return

        new_index = self._find_active_index(current_ms)
        if new_index == self._current_index:
            return

        self._current_index = new_index
        self._refresh_styles()
        self._scroll_to_active()

    # ------------------------------------------------------------------
    # Interne
    # ------------------------------------------------------------------

    def _show_empty(self):
        self._scroll.hide()
        self._empty_widget.show()

    def _clear_labels(self):
        for lbl in self._labels:
            self._container_layout.removeWidget(lbl)
            lbl.deleteLater()
        self._labels = []

    def _rebuild_labels(self):
        self._clear_labels()
        for ms, text in self._lyrics:
            lbl = QLabel(text if text else "♪")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setWordWrap(True)
            lbl.setObjectName("lyric_future")
            self._container_layout.addWidget(lbl)
            self._labels.append(lbl)
        self._refresh_styles()

    def _find_active_index(self, current_ms: int) -> int:
        """Retourne l'index de la ligne active (dernière ligne dont ms <= current_ms)."""
        active = -1
        for i, (ms, _) in enumerate(self._lyrics):
            if ms <= current_ms:
                active = i
            else:
                break
        return active

    def _refresh_styles(self):
        for i, lbl in enumerate(self._labels):
            if i < self._current_index:
                lbl.setObjectName("lyric_past")
                lbl.setStyleSheet("font-size: 13px; color: #334455; text-align: center;")
            elif i == self._current_index:
                lbl.setObjectName("lyric_active")
                lbl.setStyleSheet(
                    "font-size: 28px; font-weight: bold; color: #00d4ff; "
                    "text-align: center; padding: 8px 0;"
                )
            else:
                lbl.setObjectName("lyric_future")
                lbl.setStyleSheet("font-size: 16px; color: #7090a0; text-align: center;")

    def _scroll_to_active(self):
        if self._current_index < 0 or self._current_index >= len(self._labels):
            return

        target_label = self._labels[self._current_index]
        # Utiliser ensureWidgetVisible pour centrer
        self._scroll.ensureWidgetVisible(target_label, 0, self._scroll.height() // 3)
