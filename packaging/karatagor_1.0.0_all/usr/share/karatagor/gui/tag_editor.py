"""
Panel latéral d'édition des tags ID3v2 avec identification AcoustID.
"""

import os
from pathlib import Path

from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt6.QtGui import QPixmap, QImage, QDragEnterEvent, QDropEvent
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QComboBox, QLabel, QPushButton, QFileDialog,
    QProgressDialog, QListWidget, QListWidgetItem, QDialog,
    QDialogButtonBox, QMessageBox, QSizePolicy, QScrollArea,
    QFrame,
)

from core.tagger import Tagger
from core.fingerprint import FingerprintEngine
from core.config import Config


# Genres ID3 standards (liste raccourcie)
ID3_GENRES = [
    "", "Blues", "Classic Rock", "Country", "Dance", "Disco", "Funk", "Grunge",
    "Hip-Hop", "Jazz", "Metal", "New Age", "Oldies", "Other", "Pop", "R&B",
    "Rap", "Reggae", "Rock", "Techno", "Industrial", "Alternative", "Ska",
    "Death Metal", "Pranks", "Soundtrack", "Euro-Techno", "Ambient",
    "Trip-Hop", "Vocal", "Jazz+Funk", "Fusion", "Trance", "Classical",
    "Instrumental", "Acid", "House", "Game", "Sound Clip", "Gospel",
    "Noise", "AlternRock", "Bass", "Soul", "Punk", "Space", "Meditative",
    "Instrumental Pop", "Instrumental Rock", "Ethnic", "Gothic",
    "Darkwave", "Techno-Industrial", "Electronic", "Pop-Folk",
    "Eurodance", "Dream", "Southern Rock", "Comedy", "Cult", "Gangsta",
    "Top 40", "Christian Rap", "Pop/Funk", "Jungle", "Native American",
    "Cabaret", "New Wave", "Psychadelic", "Rave", "Showtunes", "Trailer",
    "Lo-Fi", "Tribal", "Acid Punk", "Acid Jazz", "Polka", "Retro",
    "Musical", "Rock & Roll", "Hard Rock",
]


# ------------------------------------------------------------------
# Worker threads
# ------------------------------------------------------------------

class FingerprintWorker(QObject):
    finished = pyqtSignal(list)   # liste de candidats
    error = pyqtSignal(str)

    def __init__(self, path: str, api_key: str, useragent: str):
        super().__init__()
        self._path = path
        self._api_key = api_key
        self._useragent = useragent

    def run(self):
        try:
            engine = FingerprintEngine(self._useragent)
            duration, fingerprint = engine.generate(self._path)
            candidates = engine.identify_online(fingerprint, duration, self._api_key)
            self.finished.emit(candidates)
        except Exception as e:
            self.error.emit(str(e))


class MusicBrainzWorker(QObject):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, recording_id: str, useragent: str):
        super().__init__()
        self._recording_id = recording_id
        self._useragent = useragent

    def run(self):
        try:
            engine = FingerprintEngine(self._useragent)
            data = engine.fetch_musicbrainz(self._recording_id)
            self.finished.emit(data)
        except Exception as e:
            self.error.emit(str(e))


class CoverArtWorker(QObject):
    finished = pyqtSignal(bytes)   # données image
    not_found = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, release_mbid: str, artist: str, album: str, useragent: str):
        super().__init__()
        self._release_mbid = release_mbid
        self._artist = artist
        self._album = album
        self._useragent = useragent

    def run(self):
        try:
            engine = FingerprintEngine(self._useragent)
            data = engine.fetch_cover_art(self._release_mbid, self._artist, self._album)
            if data:
                self.finished.emit(data)
            else:
                self.not_found.emit()
        except Exception as e:
            self.error.emit(str(e))


# ------------------------------------------------------------------
# Dialog de sélection des candidats
# ------------------------------------------------------------------

class CandidateDialog(QDialog):
    def __init__(self, candidates: list[dict], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Résultats AcoustID")
        self.setMinimumWidth(480)
        self._selected = None

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Sélectionnez le résultat correspondant :"))

        self._list = QListWidget()
        for c in candidates:
            score_pct = int(c["score"] * 100)
            label = f"{c['title']} — {c['artist']}  [{score_pct}%]"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, c)
            self._list.addItem(item)
        if self._list.count() > 0:
            self._list.setCurrentRow(0)

        layout.addWidget(self._list)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_accept(self):
        item = self._list.currentItem()
        if item:
            self._selected = item.data(Qt.ItemDataRole.UserRole)
        self.accept()

    def selected_candidate(self) -> dict | None:
        return self._selected


# ------------------------------------------------------------------
# Widget cover art (clic + drag & drop)
# ------------------------------------------------------------------

class CoverLabel(QLabel):
    image_changed = pyqtSignal(bytes)   # données brutes de l'image

    _PLACEHOLDER = "Cliquez ou\nglissez une image"
    _PLACEHOLDER_STYLE = (
        "border: 2px dashed #3a3a5a; border-radius: 6px; "
        "color: #556677; font-size: 11px; background: #12122a;"
    )
    _HOVER_STYLE = (
        "border: 2px dashed #00d4ff; border-radius: 6px; "
        "color: #00d4ff; font-size: 11px; background: #001a2a;"
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("cover_art")
        self.setFixedSize(200, 200)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._reset()

    def _reset(self):
        self.setPixmap(QPixmap())
        self.setText(self._PLACEHOLDER)
        self.setStyleSheet(self._PLACEHOLDER_STYLE)

    def set_image_data(self, data: bytes | None):
        if not data:
            self._reset()
            return
        px = QPixmap()
        px.loadFromData(data)
        if px.isNull():
            self._reset()
            return
        self.setText("")
        self.setStyleSheet("border: 2px solid #3a3a5a; border-radius: 6px;")
        self.setPixmap(
            px.scaled(200, 200,
                      Qt.AspectRatioMode.KeepAspectRatio,
                      Qt.TransformationMode.SmoothTransformation)
        )

    # --- Clic → dialog fichier ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._open_file_dialog()

    def _open_file_dialog(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Importer une image",
            str(Path.home()),
            "Images (*.jpg *.jpeg *.png *.webp *.bmp)",
        )
        if path:
            self._load_from_path(path)

    # --- Drag & drop ---
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls() or event.mimeData().hasImage():
            urls = event.mimeData().urls()
            if not urls or any(
                u.toLocalFile().lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".bmp"))
                for u in urls
            ):
                self.setStyleSheet(self._HOVER_STYLE)
                event.acceptProposedAction()
                return
        event.ignore()

    def dragLeaveEvent(self, event):
        # Restaurer le style selon qu'une image est affichée ou non
        if self.pixmap() and not self.pixmap().isNull():
            self.setStyleSheet("border: 2px solid #3a3a5a; border-radius: 6px;")
        else:
            self.setStyleSheet(self._PLACEHOLDER_STYLE)

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if path.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".bmp")):
                self._load_from_path(path)
                event.acceptProposedAction()
                return
        event.ignore()

    def _load_from_path(self, path: str):
        try:
            with open(path, "rb") as f:
                data = f.read()
            self.set_image_data(data)
            self.image_changed.emit(data)
        except OSError as e:
            QMessageBox.warning(self, "Erreur", f"Impossible de lire l'image :\n{e}")


# ------------------------------------------------------------------
# Panel principal
# ------------------------------------------------------------------

class TagEditorPanel(QWidget):
    tags_saved = pyqtSignal(str)          # chemin du fichier sauvegardé
    lyrics_fetched = pyqtSignal(str, str) # (artist, title) pour LyricsFetcher

    def __init__(self, config: Config, tagger: Tagger, parent=None):
        super().__init__(parent)
        self._config = config
        self._tagger = tagger
        self._current_path: str | None = None
        self._cover_bytes: bytes | None = None
        self._fp_thread: QThread | None = None
        self._mb_thread: QThread | None = None
        self._cover_thread: QThread | None = None
        self._last_release_mbid: str = ""
        self._setup_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(8)

        header = QLabel("Tags ID3")
        header.setStyleSheet("font-weight: bold; color: #00d4ff; font-size: 13px;")
        main_layout.addWidget(header)

        # Cover art
        self._cover_label = CoverLabel()
        self._cover_label.image_changed.connect(self._on_cover_changed)
        main_layout.addWidget(self._cover_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Formulaire
        form = QFormLayout()
        form.setSpacing(6)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._field_title = QLineEdit()
        self._field_artist = QLineEdit()
        self._field_album = QLineEdit()
        self._field_year = QLineEdit()
        self._field_year.setMaximumWidth(80)
        self._field_track = QLineEdit()
        self._field_track.setMaximumWidth(60)
        self._field_genre = QComboBox()
        self._field_genre.addItems(sorted(ID3_GENRES))
        self._field_genre.setEditable(True)
        self._field_comment = QLineEdit()

        form.addRow("Titre :", self._field_title)
        form.addRow("Artiste :", self._field_artist)
        form.addRow("Album :", self._field_album)
        form.addRow("Année :", self._field_year)
        form.addRow("Piste :", self._field_track)
        form.addRow("Genre :", self._field_genre)
        form.addRow("Commentaire :", self._field_comment)

        main_layout.addLayout(form)

        # Boutons
        self._btn_identify = QPushButton("Identifier (AcoustID)")
        self._btn_identify.setObjectName("btn_identify")
        self._btn_identify.clicked.connect(self._identify)
        self._btn_identify.setEnabled(False)

        self._btn_save = QPushButton("Sauvegarder Tags")
        self._btn_save.setObjectName("btn_save_tags")
        self._btn_save.clicked.connect(self._save_tags)
        self._btn_save.setEnabled(False)

        self._btn_embed = QPushButton("Intégrer Paroles")
        self._btn_embed.setObjectName("btn_embed_lyrics")
        self._btn_embed.clicked.connect(self._embed_lyrics)
        self._btn_embed.setEnabled(False)

        self._btn_cover = QPushButton("Récupérer la pochette")
        self._btn_cover.setToolTip(
            "Cherche la pochette sur Cover Art Archive puis iTunes"
        )
        self._btn_cover.clicked.connect(self._fetch_cover_online)
        self._btn_cover.setEnabled(False)

        main_layout.addWidget(self._btn_identify)
        main_layout.addWidget(self._btn_cover)
        main_layout.addWidget(self._btn_save)
        main_layout.addWidget(self._btn_embed)
        main_layout.addStretch()

        self._status_label = QLabel("")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self._status_label)

    # ------------------------------------------------------------------
    # API publique
    # ------------------------------------------------------------------

    def load_file(self, path: str):
        self._current_path = path
        tags = self._tagger.read_tags(path)

        self._field_title.setText(tags.get("title", ""))
        self._field_artist.setText(tags.get("artist", ""))
        self._field_album.setText(tags.get("album", ""))
        self._field_year.setText(tags.get("year", ""))
        self._field_track.setText(tags.get("track", ""))

        genre = tags.get("genre", "")
        idx = self._field_genre.findText(genre, Qt.MatchFlag.MatchFixedString)
        if idx >= 0:
            self._field_genre.setCurrentIndex(idx)
        else:
            self._field_genre.setCurrentText(genre)

        self._field_comment.setText(tags.get("comment", ""))

        # Cover art
        cover = tags.get("cover_bytes")
        self._cover_bytes = cover
        self._update_cover_display(cover)

        self._btn_identify.setEnabled(True)
        self._btn_cover.setEnabled(True)
        self._btn_save.setEnabled(True)
        self._btn_embed.setEnabled(True)
        self._set_status("")

    def populate_from_mb(self, data: dict):
        """Pré-remplit les champs depuis MusicBrainz (sans sauvegarder)."""
        if data.get("title"):
            self._field_title.setText(data["title"])
        if data.get("artist"):
            self._field_artist.setText(data["artist"])
        if data.get("album"):
            self._field_album.setText(data["album"])
        if data.get("year"):
            self._field_year.setText(data["year"])
        if data.get("genre"):
            self._field_genre.setCurrentText(data["genre"])
        # Mémoriser le release_mbid pour la récupération de pochette
        self._last_release_mbid = data.get("release_mbid", "")

    def get_current_tags(self) -> dict:
        return {
            "title": self._field_title.text(),
            "artist": self._field_artist.text(),
            "album": self._field_album.text(),
            "year": self._field_year.text(),
            "track": self._field_track.text(),
            "genre": self._field_genre.currentText(),
            "comment": self._field_comment.text(),
            "cover_bytes": self._cover_bytes,
        }

    def set_lyrics_for_embed(self, lyrics_text: str, synced: list | None = None):
        """Mémorise les paroles à intégrer lors du prochain clic "Intégrer Paroles"."""
        self._pending_lyrics_text = lyrics_text
        self._pending_lyrics_synced = synced

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_cover_changed(self, data: bytes):
        self._cover_bytes = data

    def _save_tags(self):
        if not self._current_path:
            return
        try:
            tags = self.get_current_tags()
            self._tagger.write_tags(self._current_path, tags)
            self._set_status("✓ Tags sauvegardés", success=True)
            self.tags_saved.emit(self._current_path)
        except Exception as e:
            self._set_status(f"✗ Erreur : {e}", success=False)
            QMessageBox.critical(self, "Erreur sauvegarde", str(e))

    def _embed_lyrics(self):
        if not self._current_path:
            return
        lyrics_text = getattr(self, "_pending_lyrics_text", "")
        synced = getattr(self, "_pending_lyrics_synced", None)
        if not lyrics_text:
            QMessageBox.information(
                self, "Intégrer Paroles",
                "Aucune parole à intégrer. Recherchez d'abord les paroles en ligne."
            )
            return
        try:
            self._tagger.write_lyrics_and_lrc(self._current_path, lyrics_text, synced)
            self._set_status("✓ Paroles intégrées", success=True)
        except Exception as e:
            self._set_status(f"✗ Erreur : {e}", success=False)
            QMessageBox.critical(self, "Erreur", str(e))

    def _identify(self):
        if not self._current_path:
            return

        api_key = self._config.acoustid_api_key
        if not api_key:
            api_key = self._prompt_api_key()
            if not api_key:
                return

        progress = QProgressDialog(
            "Analyse de l'empreinte acoustique…", "Annuler", 0, 0, self
        )
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()

        self._fp_worker = FingerprintWorker(
            self._current_path, api_key, self._config.musicbrainz_useragent
        )
        self._fp_thread = QThread(self)
        self._fp_worker.moveToThread(self._fp_thread)
        self._fp_thread.started.connect(self._fp_worker.run)
        self._fp_worker.finished.connect(progress.close)
        self._fp_worker.finished.connect(self._on_candidates_received)
        self._fp_worker.error.connect(progress.close)
        self._fp_worker.error.connect(
            lambda msg: QMessageBox.warning(self, "Erreur AcoustID", msg)
        )
        self._fp_worker.finished.connect(self._fp_thread.quit)
        self._fp_worker.error.connect(self._fp_thread.quit)
        progress.canceled.connect(self._fp_thread.requestInterruption)
        self._fp_thread.start()

    def _on_candidates_received(self, candidates: list):
        if not candidates:
            QMessageBox.information(self, "AcoustID", "Aucun résultat trouvé.")
            return

        dlg = CandidateDialog(candidates, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        candidate = dlg.selected_candidate()
        if not candidate or not candidate.get("recording_id"):
            return

        self._fetch_musicbrainz(candidate["recording_id"])

    def _fetch_musicbrainz(self, recording_id: str):
        progress = QProgressDialog(
            "Récupération MusicBrainz…", None, 0, 0, self
        )
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()

        self._mb_worker = MusicBrainzWorker(
            recording_id, self._config.musicbrainz_useragent
        )
        self._mb_thread = QThread(self)
        self._mb_worker.moveToThread(self._mb_thread)
        self._mb_thread.started.connect(self._mb_worker.run)
        self._mb_worker.finished.connect(progress.close)
        self._mb_worker.finished.connect(self._on_mb_data)
        self._mb_worker.error.connect(progress.close)
        self._mb_worker.error.connect(
            lambda msg: QMessageBox.warning(self, "Erreur MusicBrainz", msg)
        )
        self._mb_worker.finished.connect(self._mb_thread.quit)
        self._mb_worker.error.connect(self._mb_thread.quit)
        self._mb_thread.start()

    def _on_mb_data(self, data: dict):
        self.populate_from_mb(data)
        self._set_status("✓ Données MusicBrainz chargées", success=True)
        # Déclencher la recherche de paroles
        artist = data.get("artist", "")
        title = data.get("title", "")
        if artist and title:
            self.lyrics_fetched.emit(artist, title)
        # Récupérer la pochette automatiquement
        self._start_cover_fetch(
            release_mbid=data.get("release_mbid", ""),
            artist=artist,
            album=data.get("album", ""),
        )

    def _fetch_cover_online(self):
        """Bouton manuel : récupérer la pochette avec les infos des champs."""
        self._start_cover_fetch(
            release_mbid=self._last_release_mbid,
            artist=self._field_artist.text(),
            album=self._field_album.text(),
        )

    def _start_cover_fetch(self, release_mbid: str, artist: str, album: str):
        if not release_mbid and not artist and not album:
            self._set_status("Renseignez artiste/album pour chercher la pochette.")
            return

        self._set_status("Recherche de la pochette…")

        self._cover_worker = CoverArtWorker(
            release_mbid, artist, album, self._config.musicbrainz_useragent
        )
        self._cover_thread = QThread(self)
        self._cover_worker.moveToThread(self._cover_thread)
        self._cover_thread.started.connect(self._cover_worker.run)
        self._cover_worker.finished.connect(self._on_cover_fetched)
        self._cover_worker.not_found.connect(
            lambda: self._set_status("Aucune pochette trouvée en ligne.")
        )
        self._cover_worker.error.connect(
            lambda msg: self._set_status(f"Erreur pochette : {msg}", success=False)
        )
        self._cover_worker.finished.connect(self._cover_thread.quit)
        self._cover_worker.not_found.connect(self._cover_thread.quit)
        self._cover_worker.error.connect(self._cover_thread.quit)
        self._cover_thread.start()

    def _on_cover_fetched(self, data: bytes):
        self._cover_bytes = data
        self._cover_label.set_image_data(data)
        self._set_status("✓ Pochette récupérée", success=True)

    def _prompt_api_key(self) -> str:
        from PyQt6.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(
            self,
            "Clé API AcoustID",
            "Obtenez une clé gratuite sur https://acoustid.org/login\n\nClé API :",
        )
        if ok and text.strip():
            self._config.acoustid_api_key = text.strip()
            return text.strip()
        return ""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _update_cover_display(self, data: bytes | None):
        self._cover_label.set_image_data(data)

    def _set_status(self, msg: str, success: bool | None = None):
        if success is True:
            color = "#00e676"
        elif success is False:
            color = "#ff5252"
        else:
            color = "#a0a0c0"
        self._status_label.setStyleSheet(f"color: {color}; font-size: 12px;")
        self._status_label.setText(msg)
