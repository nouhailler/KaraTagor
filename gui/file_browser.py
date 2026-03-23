"""
Arborescence de dossiers musicaux avec filtre MP3.
"""

from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal, QDir
from PyQt6.QtGui import QFileSystemModel
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeView,
    QPushButton, QLabel, QFileDialog, QSizePolicy,
)


class FileBrowser(QWidget):
    file_activated = pyqtSignal(str)     # double-clic sur un MP3
    folder_loaded = pyqtSignal(str)      # nouveau dossier racine

    def __init__(self, root_path: str = "", parent=None):
        super().__init__(parent)
        self._setup_ui()
        if root_path:
            self.set_root(root_path)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # En-tête
        header_layout = QHBoxLayout()
        header = QLabel("Fichiers")
        header.setStyleSheet("font-weight: bold; color: #00d4ff; font-size: 13px;")
        self._btn_browse = QPushButton("...")
        self._btn_browse.setMaximumWidth(32)
        self._btn_browse.setMaximumHeight(24)
        self._btn_browse.setToolTip("Choisir un dossier musical")
        self._btn_browse.clicked.connect(self._choose_folder)
        header_layout.addWidget(header)
        header_layout.addStretch()
        header_layout.addWidget(self._btn_browse)
        layout.addLayout(header_layout)

        # Modèle de système de fichiers
        self._model = QFileSystemModel()
        self._model.setNameFilters(["*.mp3"])
        self._model.setNameFilterDisables(False)
        self._model.setFilter(
            QDir.Filter.AllDirs | QDir.Filter.NoDotAndDotDot | QDir.Filter.Files
        )

        self._tree = QTreeView()
        self._tree.setModel(self._model)
        self._tree.setRootIsDecorated(True)
        self._tree.setAnimated(True)
        self._tree.setIndentation(16)
        # Masquer les colonnes Size/Type/Date
        self._tree.setColumnHidden(1, True)
        self._tree.setColumnHidden(2, True)
        self._tree.setColumnHidden(3, True)
        self._tree.header().hide()
        self._tree.activated.connect(self._on_activated)
        self._tree.doubleClicked.connect(self._on_activated)

        layout.addWidget(self._tree)

    # ------------------------------------------------------------------
    # API publique
    # ------------------------------------------------------------------

    def set_root(self, path: str):
        index = self._model.setRootPath(path)
        self._tree.setRootIndex(index)
        self.folder_loaded.emit(path)

    # ------------------------------------------------------------------
    # Interne
    # ------------------------------------------------------------------

    def _choose_folder(self):
        path = QFileDialog.getExistingDirectory(
            self,
            "Choisir le dossier musical",
            str(Path.home() / "Music"),
            QFileDialog.Option.ShowDirsOnly,
        )
        if path:
            self.set_root(path)

    def _on_activated(self, index):
        path = self._model.filePath(index)
        if path.lower().endswith(".mp3"):
            self.file_activated.emit(path)
