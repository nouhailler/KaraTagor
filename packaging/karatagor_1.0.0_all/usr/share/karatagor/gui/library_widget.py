"""
Vue Bibliothèque musicale — affichage en grille d'images (pochettes).
"""

from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal, QSize, QThread, QObject
from PyQt6.QtGui import QPixmap, QIcon, QColor, QPainter, QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QLabel, QPushButton, QLineEdit, QSizePolicy, QAbstractItemView,
)

ASSETS_DIR = Path(__file__).parent.parent / "assets" / "icons"
CARD_SIZE  = 150   # px de côté pour chaque carte
COVER_SIZE = 130   # px pour la pochette dans la carte


def _icon(name: str) -> QIcon:
    p = ASSETS_DIR / f"{name}.svg"
    return QIcon(str(p)) if p.exists() else QIcon()


def _placeholder_pixmap(size: int) -> QPixmap:
    """Génère une pochette placeholder avec une note de musique."""
    px = QPixmap(size, size)
    px.fill(QColor("#1e1e3a"))
    painter = QPainter(px)
    painter.setPen(QColor("#3a3a6a"))
    painter.setBrush(QColor("#2a2a4a"))
    painter.drawRoundedRect(2, 2, size - 4, size - 4, 8, 8)
    font = QFont()
    font.setPixelSize(size // 2)
    painter.setFont(font)
    painter.setPen(QColor("#445566"))
    painter.drawText(px.rect(), Qt.AlignmentFlag.AlignCenter, "♪")
    painter.end()
    return px


# ------------------------------------------------------------------
# Worker de chargement des pochettes
# ------------------------------------------------------------------

class _CoverLoader(QObject):
    # Émet les bytes bruts — QPixmap créé dans le thread principal (règle Qt)
    cover_loaded = pyqtSignal(str, bytes)
    finished     = pyqtSignal()

    def __init__(self, tracks: list[dict]):
        super().__init__()
        self._tracks = tracks

    def run(self):
        from mutagen.id3 import ID3, ID3NoHeaderError
        for track in self._tracks:
            path = track["path"]
            data = b""
            try:
                tags = ID3(path)
                apic = tags.getall("APIC")
                if apic:
                    data = apic[0].data
            except Exception:
                pass
            self.cover_loaded.emit(path, data)
        self.finished.emit()


# ------------------------------------------------------------------
# Widget principal
# ------------------------------------------------------------------

class LibraryWidget(QWidget):
    track_requested  = pyqtSignal(str)
    favorite_toggled = pyqtSignal(str, bool)

    def __init__(self, library, parent=None):
        super().__init__(parent)
        self._library = library
        self._all_tracks: list[dict] = []
        self._covers: dict[str, QPixmap] = {}
        self._cover_thread: QThread | None = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # En-tête
        header = QHBoxLayout()
        title_lbl = QLabel("Bibliothèque")
        title_lbl.setStyleSheet("font-size:15px; font-weight:bold; color:#00d4ff;")
        self._count_lbl = QLabel("")
        self._count_lbl.setStyleSheet("font-size:11px; color:#556677;")
        header.addWidget(title_lbl)
        header.addStretch()
        header.addWidget(self._count_lbl)
        layout.addLayout(header)

        # Barre de recherche
        self._search = QLineEdit()
        self._search.setPlaceholderText("Rechercher…")
        self._search.textChanged.connect(self._filter)
        self._search.setStyleSheet("padding:4px 8px;")
        layout.addWidget(self._search)

        # Grille (IconMode)
        self._grid = QListWidget()
        self._grid.setViewMode(QListWidget.ViewMode.IconMode)
        self._grid.setIconSize(QSize(COVER_SIZE, COVER_SIZE))
        self._grid.setGridSize(QSize(CARD_SIZE + 10, CARD_SIZE + 40))
        self._grid.setResizeMode(QListWidget.ResizeMode.Adjust)
        self._grid.setMovement(QListWidget.Movement.Static)
        self._grid.setWordWrap(True)
        self._grid.setSpacing(6)
        self._grid.setStyleSheet(
            "QListWidget { background:#12122a; border:none; }"
            "QListWidget::item { background:#1e1e3a; border-radius:8px; "
            "  color:#c8d8e8; padding:4px; }"
            "QListWidget::item:selected { background:#00d4ff33; "
            "  border:1px solid #00d4ff; }"
            "QListWidget::item:hover { background:#00d4ff15; }"
        )
        self._grid.itemDoubleClicked.connect(self._on_double_click)
        layout.addWidget(self._grid)

        # Barre du bas
        bottom = QHBoxLayout()
        self._btn_refresh = QPushButton("Actualiser")
        self._btn_refresh.setMaximumWidth(90)
        self._btn_refresh.setMaximumHeight(26)
        self._btn_refresh.clicked.connect(self.refresh)
        bottom.addStretch()
        bottom.addWidget(self._btn_refresh)
        layout.addLayout(bottom)

    # ------------------------------------------------------------------
    # API publique
    # ------------------------------------------------------------------

    def refresh(self):
        self._all_tracks = self._library.all_tracks()
        self._covers.clear()
        self._grid.clear()
        self._filter(self._search.text())
        self._load_covers_async()

    # ------------------------------------------------------------------
    # Interne
    # ------------------------------------------------------------------

    def _filter(self, text: str):
        query = text.lower().strip()
        self._grid.clear()
        shown = 0
        placeholder = _placeholder_pixmap(COVER_SIZE)
        for track in self._all_tracks:
            if query and not any(
                query in (track.get(k) or "").lower()
                for k in ("title", "artist", "album", "path")
            ):
                continue
            path    = track["path"]
            title   = track.get("title") or Path(path).stem
            artist  = track.get("artist", "")
            fav     = track.get("favorite", False)

            # Ligne de texte : étoile + titre (tronqué) + artiste
            star   = "★ " if fav else ""
            label  = f"{star}{title}"
            if artist:
                label += f"\n{artist}"

            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, track)
            item.setIcon(
                QIcon(self._covers[path]) if path in self._covers
                else QIcon(placeholder)
            )
            item.setTextAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom)
            item.setSizeHint(QSize(CARD_SIZE, CARD_SIZE + 36))
            item.setToolTip(f"{title}\n{artist}")
            self._grid.addItem(item)
            shown += 1

        total = len(self._all_tracks)
        self._count_lbl.setText(f"{shown}/{total} titre{'s' if total != 1 else ''}")

    def _load_covers_async(self):
        if self._cover_thread and self._cover_thread.isRunning():
            return
        if not self._all_tracks:
            return

        self._loader = _CoverLoader(self._all_tracks)
        self._cover_thread = QThread(self)
        self._loader.moveToThread(self._cover_thread)
        self._cover_thread.started.connect(self._loader.run)
        self._loader.cover_loaded.connect(self._on_cover_loaded)
        self._loader.finished.connect(self._cover_thread.quit)
        self._cover_thread.start()

    def _on_cover_loaded(self, path: str, data: bytes):
        # QPixmap construit ici dans le thread principal
        placeholder = _placeholder_pixmap(COVER_SIZE)
        if data:
            px = QPixmap()
            px.loadFromData(data)
            if not px.isNull():
                px = px.scaled(
                    COVER_SIZE, COVER_SIZE,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self._covers[path] = px
            else:
                self._covers[path] = placeholder
        else:
            self._covers[path] = placeholder

        # Mettre à jour l'icône de l'item correspondant dans la grille
        pixmap = self._covers[path]
        for i in range(self._grid.count()):
            item = self._grid.item(i)
            if item and item.data(Qt.ItemDataRole.UserRole).get("path") == path:
                item.setIcon(QIcon(pixmap))
                break

    def _on_double_click(self, item: QListWidgetItem):
        track = item.data(Qt.ItemDataRole.UserRole)
        if track:
            self.track_requested.emit(track["path"])
