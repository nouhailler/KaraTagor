"""
Dialog de gestion des playlists nommées.
Permet de sauvegarder la playlist courante et de charger des playlists existantes.
"""

from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QLineEdit, QMessageBox, QInputDialog, QWidget,
)


class PlaylistManagerDialog(QDialog):
    playlist_load_requested = pyqtSignal(list)   # liste de chemins à charger

    def __init__(self, library, current_tracks: list[str], parent=None):
        super().__init__(parent)
        self._library = library
        self._current_tracks = current_tracks
        self.setWindowTitle("Gestionnaire de playlists")
        self.setMinimumSize(460, 380)
        self._setup_ui()
        self._refresh_list()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # En-tête
        header = QLabel("Playlists sauvegardées")
        header.setStyleSheet("font-size:14px; font-weight:bold; color:#00d4ff;")
        layout.addWidget(header)

        # Liste des playlists
        self._list = QListWidget()
        self._list.setAlternatingRowColors(True)
        self._list.itemDoubleClicked.connect(self._load_selected)
        layout.addWidget(self._list)

        # Boutons
        btn_layout = QHBoxLayout()

        self._btn_save = QPushButton("Sauvegarder la playlist courante…")
        self._btn_save.clicked.connect(self._save_current)
        self._btn_save.setEnabled(bool(self._current_tracks))

        self._btn_load = QPushButton("Charger")
        self._btn_load.clicked.connect(self._load_selected)

        self._btn_delete = QPushButton("Supprimer")
        self._btn_delete.clicked.connect(self._delete_selected)
        self._btn_delete.setStyleSheet("color:#ff5252;")

        btn_layout.addWidget(self._btn_save)
        btn_layout.addStretch()
        btn_layout.addWidget(self._btn_load)
        btn_layout.addWidget(self._btn_delete)
        layout.addLayout(btn_layout)

        # Barre fermeture
        close_layout = QHBoxLayout()
        btn_close = QPushButton("Fermer")
        btn_close.setMaximumWidth(90)
        btn_close.clicked.connect(self.accept)
        close_layout.addStretch()
        close_layout.addWidget(btn_close)
        layout.addLayout(close_layout)

    def _refresh_list(self):
        self._list.clear()
        for name in self._library.list_playlists():
            tracks = self._library.load_playlist(name)
            item = QListWidgetItem(f"  {name}  ({len(tracks)} titre{'s' if len(tracks) != 1 else ''})")
            item.setData(Qt.ItemDataRole.UserRole, name)
            self._list.addItem(item)
        self._btn_load.setEnabled(self._list.count() > 0)
        self._btn_delete.setEnabled(self._list.count() > 0)

    def _save_current(self):
        name, ok = QInputDialog.getText(
            self, "Nom de la playlist",
            "Donnez un nom à cette playlist :",
            text="Ma playlist",
        )
        if not ok or not name.strip():
            return

        # Vérifier écrasement
        existing = self._library.list_playlists()
        safe = "".join(c for c in name if c.isalnum() or c in " _-").strip()
        if safe in existing:
            reply = QMessageBox.question(
                self, "Écraser ?",
                f"La playlist « {name} » existe déjà. L'écraser ?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        self._library.save_playlist(name.strip(), self._current_tracks)
        self._refresh_list()

    def _load_selected(self):
        item = self._list.currentItem()
        if not item:
            return
        name = item.data(Qt.ItemDataRole.UserRole)
        tracks = self._library.load_playlist(name)
        if not tracks:
            QMessageBox.warning(self, "Playlist vide",
                                "Aucun fichier valide trouvé dans cette playlist.")
            return
        self.playlist_load_requested.emit(tracks)
        self.accept()

    def _delete_selected(self):
        item = self._list.currentItem()
        if not item:
            return
        name = item.data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(
            self, "Supprimer",
            f"Supprimer la playlist « {name} » ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._library.delete_playlist(name)
            self._refresh_list()
