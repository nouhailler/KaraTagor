"""
Panneau de playlists sous forme d'arborescence.
- Nœud "En cours" : piste courante en lecture
- Un nœud par playlist sauvegardée avec ses chansons en enfants
Clic sur une chanson → lance la playlist depuis cette chanson.
"""

from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QLabel, QMenu, QInputDialog, QMessageBox, QSizePolicy,
)

ASSETS_DIR = Path(__file__).parent.parent / "assets" / "icons"

_NODE_CURRENT   = "__current__"
_ROLE_PATH      = Qt.ItemDataRole.UserRole
_ROLE_NODE_TYPE = Qt.ItemDataRole.UserRole + 1   # "playlist" | "track"


def _icon(name: str) -> QIcon:
    p = ASSETS_DIR / f"{name}.svg"
    return QIcon(str(p)) if p.exists() else QIcon()


class PlaylistTreeWidget(QWidget):
    # Signaux publics (mêmes que l'ancien PlaylistWidget)
    track_selected  = pyqtSignal(str)          # chemin à jouer
    tracks_added    = pyqtSignal(list)         # nouveaux fichiers ajoutés
    playlist_loaded = pyqtSignal(list, int)    # (chemins, index_de_départ)

    def __init__(self, library, parent=None):
        super().__init__(parent)
        self._library = library
        self._current_tracks: list[str] = []
        self._current_index: int = -1
        self._setup_ui()
        self.refresh_playlists()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        header = QLabel("Playlists")
        header.setStyleSheet("font-weight:bold; color:#00d4ff; font-size:13px;")
        layout.addWidget(header)

        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setAnimated(True)
        self._tree.setIndentation(14)
        self._tree.setAlternatingRowColors(True)
        self._tree.setAcceptDrops(True)
        self._tree.itemClicked.connect(self._on_item_clicked)
        self._tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._on_context_menu)
        layout.addWidget(self._tree)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(4)

        self._btn_save = QPushButton("Sauvegarder")
        self._btn_save.setMaximumHeight(26)
        self._btn_save.setToolTip("Sauvegarder la playlist en cours sous un nom")
        self._btn_save.clicked.connect(self._save_current_playlist)

        self._btn_clear = QPushButton("Vider")
        self._btn_clear.setMaximumHeight(26)
        self._btn_clear.clicked.connect(self._clear_current)

        btn_row.addWidget(self._btn_save)
        btn_row.addWidget(self._btn_clear)
        layout.addLayout(btn_row)

        self.setAcceptDrops(True)

    # ------------------------------------------------------------------
    # API publique (compatibilité avec l'ancien PlaylistWidget)
    # ------------------------------------------------------------------

    def add_tracks(self, paths: list[str]):
        new = [p for p in paths if p not in self._current_tracks]
        self._current_tracks.extend(new)
        self._rebuild_current_node()
        if new:
            self.tracks_added.emit(new)

    def get_tracks(self) -> list[str]:
        return list(self._current_tracks)

    def current_track(self) -> str | None:
        if 0 <= self._current_index < len(self._current_tracks):
            return self._current_tracks[self._current_index]
        return None

    def set_current_by_path(self, path: str):
        if path in self._current_tracks:
            self._current_index = self._current_tracks.index(path)
            self._highlight_current()

    def next_track(self) -> str | None:
        if not self._current_tracks:
            return None
        nxt = self._current_index + 1
        if nxt >= len(self._current_tracks):
            return None
        self._current_index = nxt
        self._highlight_current()
        return self._current_tracks[nxt]

    def prev_track(self) -> str | None:
        if not self._current_tracks:
            return None
        prv = self._current_index - 1
        if prv < 0:
            return None
        self._current_index = prv
        self._highlight_current()
        return self._current_tracks[prv]

    def clear_playlist(self):
        self._current_tracks.clear()
        self._current_index = -1
        self._rebuild_current_node()

    def refresh_playlists(self):
        """Reconstruit l'arbre complet depuis la bibliothèque."""
        self._tree.clear()

        # Nœud "En cours"
        self._current_node = self._make_playlist_node("▶  En cours", _NODE_CURRENT)
        self._tree.addTopLevelItem(self._current_node)
        self._current_node.setExpanded(True)
        self._rebuild_current_node()

        # Playlists sauvegardées
        for name in self._library.list_playlists():
            tracks = self._library.load_playlist(name)
            node = self._make_playlist_node(f"☰  {name}", name)
            for path in tracks:
                node.addChild(self._make_track_item(path))
            self._tree.addTopLevelItem(node)

    # ------------------------------------------------------------------
    # Drag & drop
    # ------------------------------------------------------------------

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            if any(u.toLocalFile().lower().endswith(".mp3")
                   for u in event.mimeData().urls()):
                event.acceptProposedAction()
                return
        event.ignore()

    def dropEvent(self, event):
        paths = [u.toLocalFile() for u in event.mimeData().urls()
                 if u.toLocalFile().lower().endswith(".mp3")]
        if paths:
            self.add_tracks(paths)
            event.acceptProposedAction()

    # ------------------------------------------------------------------
    # Interne
    # ------------------------------------------------------------------

    def _make_playlist_node(self, label: str, node_id: str) -> QTreeWidgetItem:
        item = QTreeWidgetItem([label])
        item.setData(0, _ROLE_NODE_TYPE, "playlist")
        item.setData(0, _ROLE_PATH, node_id)
        font = item.font(0)
        font.setBold(True)
        item.setFont(0, font)
        item.setForeground(0, Qt.GlobalColor.cyan)
        return item

    def _make_track_item(self, path: str) -> QTreeWidgetItem:
        name = Path(path).stem
        item = QTreeWidgetItem([f"  {name}"])
        item.setData(0, _ROLE_NODE_TYPE, "track")
        item.setData(0, _ROLE_PATH, path)
        item.setToolTip(0, path)
        return item

    def _rebuild_current_node(self):
        if not hasattr(self, "_current_node"):
            return
        self._current_node.takeChildren()
        for path in self._current_tracks:
            self._current_node.addChild(self._make_track_item(path))
        count = len(self._current_tracks)
        self._current_node.setText(
            0, f"▶  En cours  ({count} titre{'s' if count != 1 else ''})"
        )
        self._highlight_current()

    def _highlight_current(self):
        if not hasattr(self, "_current_node"):
            return
        for i in range(self._current_node.childCount()):
            child = self._current_node.child(i)
            is_active = (i == self._current_index)
            font = child.font(0)
            font.setBold(is_active)
            child.setFont(0, font)
            child.setForeground(
                0,
                Qt.GlobalColor.cyan if is_active else Qt.GlobalColor.white,
            )

    def _on_item_clicked(self, item: QTreeWidgetItem, col: int):
        node_type = item.data(0, _ROLE_NODE_TYPE)
        if node_type != "track":
            return

        path = item.data(0, _ROLE_PATH)
        parent = item.parent()
        if parent is None:
            return

        parent_id = parent.data(0, _ROLE_PATH)

        if parent_id == _NODE_CURRENT:
            # Chanson de la playlist en cours
            if path in self._current_tracks:
                self._current_index = self._current_tracks.index(path)
                self._highlight_current()
                self.track_selected.emit(path)
        else:
            # Chanson d'une playlist sauvegardée → charger la playlist
            tracks = self._library.load_playlist(parent_id)
            if not tracks:
                return
            start_index = tracks.index(path) if path in tracks else 0
            # Remplacer la playlist en cours
            self._current_tracks = list(tracks)
            self._current_index = start_index
            self._rebuild_current_node()
            self._current_node.setExpanded(True)
            self.playlist_loaded.emit(tracks, start_index)

    def _save_current_playlist(self):
        if not self._current_tracks:
            return
        name, ok = QInputDialog.getText(
            self, "Sauvegarder la playlist",
            "Nom de la playlist :",
            text="Ma playlist",
        )
        if not ok or not name.strip():
            return
        self._library.save_playlist(name.strip(), self._current_tracks)
        self.refresh_playlists()

    def _clear_current(self):
        self.clear_playlist()

    def _on_context_menu(self, pos):
        item = self._tree.itemAt(pos)
        if not item:
            return

        node_type = item.data(0, _ROLE_NODE_TYPE)
        menu = QMenu(self)

        if node_type == "track":
            parent = item.parent()
            if parent and parent.data(0, _ROLE_PATH) == _NODE_CURRENT:
                act_remove = menu.addAction("Retirer de la playlist")
                act_remove.triggered.connect(lambda: self._remove_track(item))

        elif node_type == "playlist":
            pid = item.data(0, _ROLE_PATH)
            if pid != _NODE_CURRENT:
                act_load = menu.addAction("Charger cette playlist")
                act_load.triggered.connect(lambda: self._load_playlist(pid))
                act_del = menu.addAction("Supprimer")
                act_del.setForeground(Qt.GlobalColor.red)
                act_del.triggered.connect(lambda: self._delete_playlist(pid, item))

        if not menu.isEmpty():
            menu.exec(self._tree.viewport().mapToGlobal(pos))

    def _remove_track(self, item: QTreeWidgetItem):
        path = item.data(0, _ROLE_PATH)
        if path in self._current_tracks:
            idx = self._current_tracks.index(path)
            self._current_tracks.pop(idx)
            if self._current_index >= idx:
                self._current_index = max(-1, self._current_index - 1)
        self._rebuild_current_node()

    def _load_playlist(self, name: str):
        tracks = self._library.load_playlist(name)
        if not tracks:
            return
        self._current_tracks = list(tracks)
        self._current_index = 0
        self._rebuild_current_node()
        self._current_node.setExpanded(True)
        self.playlist_loaded.emit(tracks, 0)

    def _delete_playlist(self, name: str, item: QTreeWidgetItem):
        reply = QMessageBox.question(
            self, "Supprimer",
            f"Supprimer la playlist « {name} » ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._library.delete_playlist(name)
            root = self._tree.invisibleRootItem()
            root.removeChild(item)
