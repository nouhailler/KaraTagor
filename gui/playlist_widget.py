"""
Widget playlist avec drag & drop et navigation.
"""

import os
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal, QMimeData, QUrl
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QIcon
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QAbstractItemView, QSizePolicy,
)


class PlaylistWidget(QWidget):
    track_selected = pyqtSignal(str)    # chemin du fichier
    tracks_added = pyqtSignal(list)     # liste de chemins ajoutés

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tracks: list[str] = []
        self._current_index: int = -1
        self._setup_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        header = QLabel("Playlist")
        header.setStyleSheet("font-weight: bold; color: #00d4ff; font-size: 13px;")
        layout.addWidget(header)

        self._list = QListWidget()
        self._list.setAlternatingRowColors(True)
        self._list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self._list.setAcceptDrops(True)
        self._list.setDragEnabled(True)
        self._list.itemDoubleClicked.connect(self._on_double_click)
        self._list.setToolTip("Double-clic pour jouer — Glissez des MP3 ici")
        layout.addWidget(self._list)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(4)

        self._btn_clear = QPushButton("Vider")
        self._btn_clear.setMaximumHeight(28)
        self._btn_clear.clicked.connect(self.clear_playlist)

        self._btn_remove = QPushButton("Retirer")
        self._btn_remove.setMaximumHeight(28)
        self._btn_remove.clicked.connect(self._remove_selected)

        btn_layout.addWidget(self._btn_remove)
        btn_layout.addWidget(self._btn_clear)
        layout.addLayout(btn_layout)

        self.setAcceptDrops(True)

    # ------------------------------------------------------------------
    # API publique
    # ------------------------------------------------------------------

    def add_tracks(self, paths: list[str]):
        new = []
        for path in paths:
            if path not in self._tracks:
                self._tracks.append(path)
                name = Path(path).stem
                item = QListWidgetItem(name)
                item.setData(Qt.ItemDataRole.UserRole, path)
                item.setToolTip(path)
                self._list.addItem(item)
                new.append(path)
        if new:
            self.tracks_added.emit(new)

    def current_track(self) -> str | None:
        if 0 <= self._current_index < len(self._tracks):
            return self._tracks[self._current_index]
        return None

    def set_current_index(self, index: int):
        self._current_index = index
        self._highlight_current()

    def next_track(self) -> str | None:
        if not self._tracks:
            return None
        next_idx = self._current_index + 1
        if next_idx >= len(self._tracks):
            return None
        self._current_index = next_idx
        self._highlight_current()
        return self._tracks[self._current_index]

    def prev_track(self) -> str | None:
        if not self._tracks:
            return None
        prev_idx = self._current_index - 1
        if prev_idx < 0:
            return None
        self._current_index = prev_idx
        self._highlight_current()
        return self._tracks[self._current_index]

    def clear_playlist(self):
        self._tracks.clear()
        self._current_index = -1
        self._list.clear()

    def get_tracks(self) -> list[str]:
        return list(self._tracks)

    # ------------------------------------------------------------------
    # Drag & Drop
    # ------------------------------------------------------------------

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        paths = []
        for url in urls:
            path = url.toLocalFile()
            if path.lower().endswith(".mp3"):
                paths.append(path)
        if paths:
            self.add_tracks(paths)
            event.acceptProposedAction()

    # ------------------------------------------------------------------
    # Interne
    # ------------------------------------------------------------------

    def _on_double_click(self, item: QListWidgetItem):
        path = item.data(Qt.ItemDataRole.UserRole)
        if path in self._tracks:
            self._current_index = self._tracks.index(path)
            self._highlight_current()
            self.track_selected.emit(path)

    def _remove_selected(self):
        selected = self._list.selectedItems()
        for item in selected:
            path = item.data(Qt.ItemDataRole.UserRole)
            row = self._list.row(item)
            self._list.takeItem(row)
            if path in self._tracks:
                idx = self._tracks.index(path)
                self._tracks.pop(idx)
                if self._current_index >= idx:
                    self._current_index = max(-1, self._current_index - 1)

    def _highlight_current(self):
        for i in range(self._list.count()):
            item = self._list.item(i)
            if i == self._current_index:
                item.setForeground(Qt.GlobalColor.cyan)
            else:
                item.setForeground(Qt.GlobalColor.white)
        if 0 <= self._current_index < self._list.count():
            self._list.scrollToItem(self._list.item(self._current_index))
