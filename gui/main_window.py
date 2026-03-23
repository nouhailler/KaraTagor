"""
Fenêtre principale de KaraTagor.
Layout 3 colonnes : FileBrowser+Playlist | LyricsWidget | TagEditorPanel
Barre de contrôle en bas.
"""

import os
from pathlib import Path

from PyQt6.QtCore import Qt, QThread, QObject, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QPixmap, QAction, QIcon, QDragEnterEvent, QDropEvent
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QPushButton, QSlider, QLabel, QStatusBar, QMenuBar, QMenu,
    QFileDialog, QMessageBox, QDialog, QScrollArea, QSizePolicy,
    QProgressDialog,
)

from core.audio_engine import AudioEngine
from core.tagger import Tagger
from core.config import Config
from core.lyrics_fetcher import LyricsFetcher
from gui.lyrics_widget import LyricsWidget
from gui.tag_editor import TagEditorPanel
from gui.playlist_widget import PlaylistWidget
from gui.file_browser import FileBrowser


# ------------------------------------------------------------------
# Worker de recherche de paroles
# ------------------------------------------------------------------

class LyricsWorker(QObject):
    synced_found = pyqtSignal(list)
    plain_found = pyqtSignal(str)
    not_found = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, artist: str, title: str, album: str = "", duration: float = 0.0):
        super().__init__()
        self._artist = artist
        self._title = title
        self._album = album
        self._duration = duration

    def run(self):
        try:
            fetcher = LyricsFetcher()
            synced = fetcher.fetch_synced(self._artist, self._title, self._album, self._duration)
            if synced:
                self.synced_found.emit(synced)
                return
            plain = fetcher.fetch_plain(self._artist, self._title)
            if plain:
                self.plain_found.emit(plain)
            else:
                self.not_found.emit()
        except Exception as e:
            self.error.emit(str(e))


# ------------------------------------------------------------------
# Fenêtre principale
# ------------------------------------------------------------------

ASSETS_DIR = Path(__file__).parent.parent / "assets"
ICONS_DIR = ASSETS_DIR / "icons"


def _icon(name: str) -> QIcon:
    path = ICONS_DIR / f"{name}.svg"
    if path.exists():
        return QIcon(str(path))
    return QIcon()


class MainWindow(QMainWindow):
    def __init__(self, config: Config):
        super().__init__()
        self._config = config
        self._tagger = Tagger(backup_enabled=config.backup_enabled)
        self._audio = AudioEngine(self)
        self._lyrics_fetcher = LyricsFetcher()
        self._current_path: str | None = None
        self._current_duration_ms: int = 0
        self._current_synced_lyrics: list | None = None
        self._seeking = False
        self._lyrics_thread: QThread | None = None

        self._build_ui()
        self._connect_signals()
        self._setup_menu()
        self.setAcceptDrops(True)
        self.setMinimumSize(1100, 680)
        self.setWindowTitle("KaraTagor")

    # ------------------------------------------------------------------
    # Construction UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(6, 6, 6, 0)
        root_layout.setSpacing(0)

        # Splitter principal (3 colonnes)
        self._splitter = QSplitter(Qt.Orientation.Horizontal)

        # --- Colonne gauche : browser + playlist ---
        left = QWidget()
        left.setMaximumWidth(280)
        left.setMinimumWidth(180)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(4)

        self._file_browser = FileBrowser(
            self._config.default_music_folder
        )
        self._playlist = PlaylistWidget()

        left_vsplit = QSplitter(Qt.Orientation.Vertical)
        left_vsplit.addWidget(self._file_browser)
        left_vsplit.addWidget(self._playlist)
        left_vsplit.setSizes([300, 200])
        left_layout.addWidget(left_vsplit)

        # --- Colonne centrale : paroles ---
        self._lyrics_widget = LyricsWidget()
        self._lyrics_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        # --- Colonne droite : tag editor ---
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        right_scroll.setMinimumWidth(240)
        right_scroll.setMaximumWidth(320)
        self._tag_editor = TagEditorPanel(self._config, self._tagger)
        right_scroll.setWidget(self._tag_editor)

        self._splitter.addWidget(left)
        self._splitter.addWidget(self._lyrics_widget)
        self._splitter.addWidget(right_scroll)
        self._splitter.setSizes([240, 620, 280])

        root_layout.addWidget(self._splitter, 1)

        # --- Barre de contrôle ---
        root_layout.addWidget(self._build_control_bar())

        self.setStatusBar(QStatusBar())

    def _build_control_bar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(90)
        bar.setStyleSheet("background-color: #12122a; border-top: 1px solid #2a2a4a;")
        layout = QVBoxLayout(bar)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(4)

        # Seekbar
        seek_layout = QHBoxLayout()
        self._lbl_pos = QLabel("0:00")
        self._lbl_pos.setObjectName("lbl_time")
        self._lbl_pos.setMinimumWidth(40)
        self._lbl_dur = QLabel("0:00")
        self._lbl_dur.setObjectName("lbl_time")
        self._lbl_dur.setMinimumWidth(40)

        self._seek_slider = QSlider(Qt.Orientation.Horizontal)
        self._seek_slider.setObjectName("seek_slider")
        self._seek_slider.setRange(0, 1000)
        self._seek_slider.setSingleStep(1)
        self._seek_slider.setTracking(False)
        self._seek_slider.sliderPressed.connect(lambda: setattr(self, "_seeking", True))
        self._seek_slider.sliderReleased.connect(self._on_seek)

        seek_layout.addWidget(self._lbl_pos)
        seek_layout.addWidget(self._seek_slider)
        seek_layout.addWidget(self._lbl_dur)
        layout.addLayout(seek_layout)

        # Contrôles principaux
        ctrl_layout = QHBoxLayout()
        ctrl_layout.setSpacing(8)

        # Mini cover + infos
        self._mini_cover = QLabel()
        self._mini_cover.setFixedSize(48, 48)
        self._mini_cover.setStyleSheet(
            "border: 1px solid #2a2a4a; border-radius: 4px; background: #1e1e3a;"
        )
        self._mini_cover.setAlignment(Qt.AlignmentFlag.AlignCenter)

        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)
        self._lbl_track_title = QLabel("—")
        self._lbl_track_title.setObjectName("lbl_title")
        self._lbl_track_artist = QLabel("")
        self._lbl_track_artist.setObjectName("lbl_artist")
        info_layout.addWidget(self._lbl_track_title)
        info_layout.addWidget(self._lbl_track_artist)

        # Boutons transport
        self._btn_prev = QPushButton()
        self._btn_prev.setObjectName("btn_prev")
        self._btn_prev.setIcon(_icon("prev"))
        self._btn_prev.setIconSize(QSize(20, 20))
        self._btn_prev.setToolTip("Précédent")

        self._btn_play = QPushButton()
        self._btn_play.setObjectName("btn_play")
        self._btn_play.setIcon(_icon("play"))
        self._btn_play.setIconSize(QSize(24, 24))
        self._btn_play.setToolTip("Lecture / Pause")

        self._btn_stop = QPushButton()
        self._btn_stop.setObjectName("btn_stop")
        self._btn_stop.setIcon(_icon("stop"))
        self._btn_stop.setIconSize(QSize(20, 20))
        self._btn_stop.setToolTip("Stop")

        self._btn_next = QPushButton()
        self._btn_next.setObjectName("btn_next")
        self._btn_next.setIcon(_icon("next"))
        self._btn_next.setIconSize(QSize(20, 20))
        self._btn_next.setToolTip("Suivant")

        # Volume
        vol_icon = QLabel()
        vol_icon.setPixmap(_icon("volume").pixmap(QSize(18, 18)))

        self._vol_slider = QSlider(Qt.Orientation.Horizontal)
        self._vol_slider.setRange(0, 100)
        self._vol_slider.setValue(80)
        self._vol_slider.setMaximumWidth(100)
        self._vol_slider.setToolTip("Volume")
        self._audio.set_volume(80)

        ctrl_layout.addWidget(self._mini_cover)
        ctrl_layout.addWidget(info_widget)
        ctrl_layout.addStretch()
        ctrl_layout.addWidget(self._btn_prev)
        ctrl_layout.addWidget(self._btn_play)
        ctrl_layout.addWidget(self._btn_stop)
        ctrl_layout.addWidget(self._btn_next)
        ctrl_layout.addStretch()
        ctrl_layout.addWidget(vol_icon)
        ctrl_layout.addWidget(self._vol_slider)
        layout.addLayout(ctrl_layout)

        return bar

    def _setup_menu(self):
        menubar = self.menuBar()

        # Fichier
        file_menu = menubar.addMenu("Fichier")
        act_open = QAction("Ouvrir un fichier MP3…", self)
        act_open.setShortcut("Ctrl+O")
        act_open.triggered.connect(self._open_file_dialog)
        act_folder = QAction("Ouvrir un dossier…", self)
        act_folder.triggered.connect(self._open_folder_dialog)
        act_quit = QAction("Quitter", self)
        act_quit.setShortcut("Ctrl+Q")
        act_quit.triggered.connect(self.close)
        file_menu.addAction(act_open)
        file_menu.addAction(act_folder)
        file_menu.addSeparator()
        file_menu.addAction(act_quit)

        # Affichage
        view_menu = menubar.addMenu("Affichage")
        act_toggle_left = QAction("Panneau gauche", self, checkable=True, checked=True)
        act_toggle_left.triggered.connect(
            lambda c: self._splitter.widget(0).setVisible(c)
        )
        act_toggle_right = QAction("Panneau tags", self, checkable=True, checked=True)
        act_toggle_right.triggered.connect(
            lambda c: self._splitter.widget(2).setVisible(c)
        )
        view_menu.addAction(act_toggle_left)
        view_menu.addAction(act_toggle_right)

        # Aide
        help_menu = menubar.addMenu("Aide")
        act_about = QAction("À propos…", self)
        act_about.triggered.connect(self._show_about)
        help_menu.addAction(act_about)

    # ------------------------------------------------------------------
    # Connexions signaux
    # ------------------------------------------------------------------

    def _connect_signals(self):
        # Audio
        self._audio.position_changed.connect(self._on_position)
        self._audio.duration_changed.connect(self._on_duration)
        self._audio.track_ended.connect(self._on_track_ended)
        self._audio.state_changed.connect(self._on_state_changed)

        # Contrôles
        self._btn_play.clicked.connect(self._toggle_play)
        self._btn_stop.clicked.connect(self._stop)
        self._btn_prev.clicked.connect(self._prev_track)
        self._btn_next.clicked.connect(self._next_track)
        self._vol_slider.valueChanged.connect(self._audio.set_volume)

        # Explorateur + Playlist
        self._file_browser.file_activated.connect(self._load_file)
        self._playlist.track_selected.connect(self._load_file)
        self._file_browser.file_activated.connect(
            lambda p: self._playlist.add_tracks([p])
        )

        # Paroles
        self._lyrics_widget.search_requested.connect(self._search_lyrics_online)

        # Tag editor
        self._tag_editor.lyrics_fetched.connect(self._on_lyrics_search_from_mb)

    # ------------------------------------------------------------------
    # Chargement d'un fichier
    # ------------------------------------------------------------------

    def _load_file(self, path: str):
        self._current_path = path
        self._current_synced_lyrics = None

        # Tags
        tags = self._tagger.read_tags(path)
        self._tag_editor.load_file(path)

        title = tags.get("title") or Path(path).stem
        artist = tags.get("artist", "")
        album = tags.get("album", "")
        duration = tags.get("duration_sec", 0.0)

        self._lbl_track_title.setText(title)
        self._lbl_track_artist.setText(artist)
        self.setWindowTitle(
            f"KaraTagor — {artist + ' - ' if artist else ''}{title}"
        )

        # Mini cover
        cover = tags.get("cover_bytes")
        if cover:
            px = QPixmap()
            px.loadFromData(cover)
            self._mini_cover.setPixmap(
                px.scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio,
                          Qt.TransformationMode.SmoothTransformation)
            )
        else:
            self._mini_cover.setPixmap(QPixmap())

        # Paroles : priorité .lrc > USLT > aucune
        fetcher = LyricsFetcher()
        synced = fetcher.load_lrc_file(path)
        if synced:
            self._current_synced_lyrics = synced
            self._lyrics_widget.set_lyrics(synced)
            self.statusBar().showMessage("Paroles synchronisées chargées depuis .lrc")
        elif tags.get("lyrics_uslt"):
            self._lyrics_widget.set_plain_text(tags["lyrics_uslt"])
            self.statusBar().showMessage("Paroles non synchronisées (USLT)")
        else:
            self._lyrics_widget.clear()
            self.statusBar().showMessage("Aucune parole — cliquez 'Rechercher en ligne'")

        # Audio
        self._audio.load(path)
        self._current_duration_ms = 0
        self._seek_slider.setValue(0)
        self._lbl_pos.setText("0:00")
        self._lbl_dur.setText("0:00")

    # ------------------------------------------------------------------
    # Contrôles audio
    # ------------------------------------------------------------------

    def _toggle_play(self):
        if self._current_path is None:
            self._open_file_dialog()
            return
        self._audio.pause() if self._audio.is_playing() else self._audio.play()

    def _stop(self):
        self._audio.stop()

    def _prev_track(self):
        path = self._playlist.prev_track()
        if path:
            self._load_file(path)
            self._audio.play()

    def _next_track(self):
        path = self._playlist.next_track()
        if path:
            self._load_file(path)
            self._audio.play()

    def _on_seek(self):
        self._seeking = False
        if self._current_duration_ms > 0:
            pos = int(self._seek_slider.value() / 1000.0 * self._current_duration_ms)
            self._audio.seek(pos)

    # ------------------------------------------------------------------
    # Slots audio
    # ------------------------------------------------------------------

    def _on_position(self, ms: int):
        if self._seeking:
            return
        self._lyrics_widget.update_position(ms)
        if self._current_duration_ms > 0:
            self._seek_slider.blockSignals(True)
            self._seek_slider.setValue(int(ms / self._current_duration_ms * 1000))
            self._seek_slider.blockSignals(False)
        self._lbl_pos.setText(self._ms_to_str(ms))

    def _on_duration(self, ms: int):
        self._current_duration_ms = ms
        self._lbl_dur.setText(self._ms_to_str(ms))

    def _on_track_ended(self):
        self._next_track()

    def _on_state_changed(self, state: str):
        if state == "playing":
            self._btn_play.setIcon(_icon("pause"))
            self._btn_play.setToolTip("Pause")
        else:
            self._btn_play.setIcon(_icon("play"))
            self._btn_play.setToolTip("Lecture")

    # ------------------------------------------------------------------
    # Recherche de paroles
    # ------------------------------------------------------------------

    def _search_lyrics_online(self):
        if not self._current_path:
            return
        tags = self._tagger.read_tags(self._current_path)
        artist = tags.get("artist", "")
        title = tags.get("title", "") or Path(self._current_path).stem
        duration = tags.get("duration_sec", 0.0)
        album = tags.get("album", "")
        self._start_lyrics_search(artist, title, album, duration)

    def _on_lyrics_search_from_mb(self, artist: str, title: str):
        """Déclenché après identification MusicBrainz."""
        duration = 0.0
        if self._current_path:
            tags = self._tagger.read_tags(self._current_path)
            duration = tags.get("duration_sec", 0.0)
        self._start_lyrics_search(artist, title, "", duration)

    def _start_lyrics_search(self, artist: str, title: str, album: str, duration: float):
        progress = QProgressDialog("Recherche des paroles…", "Annuler", 0, 0, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()

        self._lyr_worker = LyricsWorker(artist, title, album, duration)
        self._lyrics_thread = QThread(self)
        self._lyr_worker.moveToThread(self._lyrics_thread)
        self._lyrics_thread.started.connect(self._lyr_worker.run)

        self._lyr_worker.synced_found.connect(progress.close)
        self._lyr_worker.synced_found.connect(self._on_synced_lyrics)
        self._lyr_worker.plain_found.connect(progress.close)
        self._lyr_worker.plain_found.connect(self._on_plain_lyrics)
        self._lyr_worker.not_found.connect(progress.close)
        self._lyr_worker.not_found.connect(
            lambda: self.statusBar().showMessage("Aucune parole trouvée sur LRCLIB.")
        )
        self._lyr_worker.error.connect(progress.close)
        self._lyr_worker.error.connect(
            lambda msg: self.statusBar().showMessage(f"Erreur paroles : {msg}")
        )

        for sig in (self._lyr_worker.synced_found, self._lyr_worker.plain_found,
                    self._lyr_worker.not_found, self._lyr_worker.error):
            sig.connect(self._lyrics_thread.quit)

        progress.canceled.connect(self._lyrics_thread.requestInterruption)
        self._lyrics_thread.start()

    def _on_synced_lyrics(self, synced: list):
        self._current_synced_lyrics = synced
        self._lyrics_widget.set_lyrics(synced)

        # Préparer pour intégration
        plain = "\n".join(text for _, text in synced)
        self._tag_editor.set_lyrics_for_embed(plain, synced)
        self.statusBar().showMessage("Paroles synchronisées trouvées !")

    def _on_plain_lyrics(self, text: str):
        self._lyrics_widget.set_plain_text(text)
        self._tag_editor.set_lyrics_for_embed(text, None)
        self.statusBar().showMessage("Paroles (non synchronisées) trouvées.")

    # ------------------------------------------------------------------
    # Drag & Drop fenêtre entière
    # ------------------------------------------------------------------

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            mp3s = [
                u.toLocalFile() for u in event.mimeData().urls()
                if u.toLocalFile().lower().endswith(".mp3")
            ]
            if mp3s:
                event.acceptProposedAction()
                return
        event.ignore()

    def dropEvent(self, event: QDropEvent):
        mp3s = [
            u.toLocalFile() for u in event.mimeData().urls()
            if u.toLocalFile().lower().endswith(".mp3")
        ]
        if mp3s:
            self._playlist.add_tracks(mp3s)
            self._load_file(mp3s[0])
            event.acceptProposedAction()

    # ------------------------------------------------------------------
    # Menus
    # ------------------------------------------------------------------

    def _open_file_dialog(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Ouvrir un fichier MP3",
            self._config.default_music_folder,
            "Fichiers MP3 (*.mp3)",
        )
        if path:
            self._playlist.add_tracks([path])
            self._load_file(path)

    def _open_folder_dialog(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Ouvrir un dossier",
            self._config.default_music_folder,
        )
        if folder:
            self._config.default_music_folder = folder
            self._file_browser.set_root(folder)

    def _show_about(self):
        QMessageBox.about(
            self, "À propos de KaraTagor",
            "<h2>KaraTagor</h2>"
            "<p>Lecteur karaoké avec gestion des tags ID3v2.</p>"
            "<p><b>Technologies :</b> PyQt6, python-vlc, mutagen, "
            "pyacoustid, musicbrainzngs, LRCLIB</p>"
            "<p>Version 1.0</p>",
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _ms_to_str(ms: int) -> str:
        total_sec = ms // 1000
        m = total_sec // 60
        s = total_sec % 60
        return f"{m}:{s:02d}"
