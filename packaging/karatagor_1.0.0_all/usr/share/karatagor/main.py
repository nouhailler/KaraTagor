#!/usr/bin/env python3
"""
KaraTagor — Point d'entrée.
"""

import sys
import os
from pathlib import Path

# S'assurer que le répertoire racine est dans sys.path
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from core.config import Config
from gui.main_window import MainWindow


def load_stylesheet(app: QApplication):
    qss_path = ROOT_DIR / "assets" / "style.qss"
    if qss_path.exists():
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())


def main():
    # Nécessaire sur certains systèmes Linux pour que VLC fonctionne correctement
    os.environ.setdefault("QT_QPA_PLATFORM", "xcb")

    app = QApplication(sys.argv)
    app.setApplicationName("KaraTagor")
    app.setOrganizationName("KaraTagor")
    app.setApplicationVersion("1.0")

    config = Config()
    load_stylesheet(app)

    window = MainWindow(config)
    window.show()

    # Si un fichier MP3 est passé en argument
    if len(sys.argv) > 1:
        path = sys.argv[1]
        if path.lower().endswith(".mp3") and Path(path).exists():
            window._playlist.add_tracks([path])
            window._load_file(path)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
