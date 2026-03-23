"""
Widget karaoké avec rendu par paintEvent.
Chaque ligne occupe une hauteur fixe → pas de saut de layout quand
la ligne active change de taille de police.
"""

from PyQt6.QtCore import Qt, pyqtSignal, QRect, QPoint
from PyQt6.QtGui import QPainter, QColor, QFont, QPen
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QLabel,
    QPushButton, QSizePolicy,
)

# ------------------------------------------------------------------
# Constantes visuelles
# ------------------------------------------------------------------
LINE_HEIGHT      = 52    # hauteur fixe de chaque ligne en px
PADDING_VERT     = 300   # espace avant la 1re ligne et après la dernière
FONT_ACTIVE_PX   = 28    # taille police ligne en cours
FONT_FUTURE_PX   = 17    # lignes à venir
FONT_PAST_PX     = 14    # lignes passées
HIGHLIGHT_OFFSET = 0     # ms d'avance de base (ajustable via set_sync_offset)

COLOR_ACTIVE  = QColor("#00d4ff")
COLOR_FUTURE  = QColor("#8aaabb")
COLOR_PAST    = QColor("#2a3d4a")


# ------------------------------------------------------------------
# Canvas de rendu
# ------------------------------------------------------------------

class _LyricsCanvas(QWidget):
    """Dessine toutes les lignes LRC à positions Y fixes."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._lyrics: list[tuple[int, str]] = []
        self._active: int = -1
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self._font_active = QFont()
        self._font_active.setPixelSize(FONT_ACTIVE_PX)
        self._font_active.setBold(True)

        self._font_future = QFont()
        self._font_future.setPixelSize(FONT_FUTURE_PX)

        self._font_past = QFont()
        self._font_past.setPixelSize(FONT_PAST_PX)

    def set_lyrics(self, lyrics: list[tuple[int, str]]):
        self._lyrics = lyrics
        self._active = -1
        self._update_height()
        self.update()

    def set_active(self, index: int):
        if index != self._active:
            self._active = index
            self.update()

    def line_y_center(self, index: int) -> int:
        """Coordonnée Y du centre de la ligne `index`."""
        return PADDING_VERT + index * LINE_HEIGHT + LINE_HEIGHT // 2

    def _update_height(self):
        h = PADDING_VERT * 2 + len(self._lyrics) * LINE_HEIGHT
        self.setFixedHeight(max(h, 1))

    def paintEvent(self, event):
        if not self._lyrics:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()

        for i, (_, text) in enumerate(self._lyrics):
            y = PADDING_VERT + i * LINE_HEIGHT
            rect = QRect(24, y, w - 48, LINE_HEIGHT)

            if i == self._active:
                painter.setFont(self._font_active)
                painter.setPen(QPen(COLOR_ACTIVE))
            elif i < self._active:
                painter.setFont(self._font_past)
                painter.setPen(QPen(COLOR_PAST))
            else:
                painter.setFont(self._font_future)
                painter.setPen(QPen(COLOR_FUTURE))

            painter.drawText(
                rect,
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
                text if text else "♪",
            )

        painter.end()


# ------------------------------------------------------------------
# Widget public
# ------------------------------------------------------------------

class LyricsWidget(QWidget):
    search_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._lyrics: list[tuple[int, str]] = []
        self._current_index: int = -1
        self._sync_offset_ms: int = 0   # décalage manuel ajustable
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # --- Zone de scroll avec le canvas ---
        self._scroll = QScrollArea()
        self._scroll.setObjectName("lyrics_area")
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self._canvas = _LyricsCanvas()
        self._scroll.setWidget(self._canvas)
        layout.addWidget(self._scroll)

        # --- Zone "aucune parole" ---
        self._empty_widget = QWidget()
        empty_layout = QVBoxLayout(self._empty_widget)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.setSpacing(16)

        lbl = QLabel("Aucune parole disponible")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("font-size: 18px; color: #445566;")

        btn = QPushButton("Rechercher en ligne")
        btn.setMaximumWidth(220)
        btn.clicked.connect(self.search_requested.emit)

        empty_layout.addWidget(lbl)
        empty_layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._empty_widget)

        self._show_empty()

    # ------------------------------------------------------------------
    # API publique
    # ------------------------------------------------------------------

    def set_sync_offset(self, ms: int):
        """Décalage en ms : négatif = avancer les paroles, positif = les retarder."""
        self._sync_offset_ms = ms

    def get_sync_offset(self) -> int:
        return self._sync_offset_ms

    def set_lyrics(self, lyrics: list[tuple[int, str]]):
        self._lyrics = lyrics
        self._current_index = -1
        self._sync_offset_ms = 0
        self._canvas.set_lyrics(lyrics)
        self._scroll.show()
        self._empty_widget.hide()
        # Revenir en haut
        self._scroll.verticalScrollBar().setValue(0)

    def set_plain_text(self, text: str):
        """Affiche un texte USLT non synchronisé."""
        self._lyrics = []
        self._current_index = -1

        # Réutilise le canvas pour afficher chaque ligne
        lines = [(0, line) for line in text.splitlines() if line.strip()]
        self._canvas.set_lyrics(lines)
        # Tout en bleu atténué (pas de ligne active)
        self._canvas.set_active(-1)
        self._scroll.show()
        self._empty_widget.hide()
        self._scroll.verticalScrollBar().setValue(0)

    def clear(self):
        self._lyrics = []
        self._current_index = -1
        self._canvas.set_lyrics([])
        self._show_empty()

    def update_position(self, current_ms: int):
        if not self._lyrics:
            return

        # Appliquer l'offset de synchronisation manuel
        # offset négatif = paroles avancées (highlight plus tôt)
        # offset positif = paroles retardées (highlight plus tard)
        adjusted_ms = current_ms - self._sync_offset_ms + HIGHLIGHT_OFFSET
        new_index = -1
        for i, (ms, _) in enumerate(self._lyrics):
            if ms <= adjusted_ms:
                new_index = i
            else:
                break

        if new_index == self._current_index:
            return

        self._current_index = new_index
        self._canvas.set_active(new_index)
        self._scroll_to_active(new_index)

    # ------------------------------------------------------------------
    # Interne
    # ------------------------------------------------------------------

    def _show_empty(self):
        self._scroll.hide()
        self._empty_widget.show()

    def _scroll_to_active(self, index: int):
        if index < 0:
            return
        # Centrer la ligne active dans la fenêtre de scroll
        scroll_bar = self._scroll.verticalScrollBar()
        visible_height = self._scroll.viewport().height()
        line_center = self._canvas.line_y_center(index)
        target = line_center - visible_height // 2
        scroll_bar.setValue(max(0, target))
