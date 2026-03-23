"""
Moteur audio basé sur python-vlc.
Fournit play/pause/stop/seek/volume et un égaliseur basique.
Émet des signaux PyQt toutes les 100ms via QTimer.
"""

import vlc
from PyQt6.QtCore import QObject, QTimer, pyqtSignal


class AudioEngine(QObject):
    position_changed = pyqtSignal(int)   # ms
    track_ended = pyqtSignal()
    state_changed = pyqtSignal(str)      # "playing" | "paused" | "stopped"
    duration_changed = pyqtSignal(int)   # ms, émis à la première position valide

    def __init__(self, parent=None):
        super().__init__(parent)
        self._instance = vlc.Instance("--no-xlib")
        self._player = self._instance.media_player_new()
        self._equalizer = vlc.AudioEqualizer()
        self._player.set_equalizer(self._equalizer)

        self._duration_reported = False
        self._current_path: str | None = None

        # Attacher le callback de fin de piste
        em = self._player.event_manager()
        em.event_attach(vlc.EventType.MediaPlayerEndReached, self._on_end_reached)

        self._timer = QTimer(self)
        self._timer.setInterval(100)
        self._timer.timeout.connect(self._poll_position)

    # ------------------------------------------------------------------
    # Contrôles principaux
    # ------------------------------------------------------------------

    def load(self, path: str):
        self._current_path = path
        self._duration_reported = False
        media = self._instance.media_new(path)
        self._player.set_media(media)

    def play(self):
        self._player.play()
        self._timer.start()
        self.state_changed.emit("playing")

    def pause(self):
        if self._player.is_playing():
            self._player.pause()
            self._timer.stop()
            self.state_changed.emit("paused")
        elif self._player.get_state() == vlc.State.Paused:
            self._player.pause()
            self._timer.start()
            self.state_changed.emit("playing")

    def stop(self):
        self._player.stop()
        self._timer.stop()
        self._duration_reported = False
        self.state_changed.emit("stopped")
        self.position_changed.emit(0)

    def seek(self, ms: int):
        duration = self._player.get_length()
        if duration > 0:
            self._player.set_time(max(0, min(ms, duration)))

    def set_volume(self, volume: int):
        """Volume de 0 à 100."""
        self._player.audio_set_volume(max(0, min(100, volume)))

    def get_position_ms(self) -> int:
        t = self._player.get_time()
        return t if t >= 0 else 0

    def get_duration_ms(self) -> int:
        d = self._player.get_length()
        return d if d > 0 else 0

    def is_playing(self) -> bool:
        return self._player.is_playing()

    # ------------------------------------------------------------------
    # Égaliseur
    # ------------------------------------------------------------------

    def set_equalizer(self, bass: float, treble: float):
        """
        Réglage simplifié : bass en dB (bandes 0-3), treble en dB (bandes 7-9).
        Valeurs typiques : -12.0 à +12.0 dB.
        """
        for band in range(0, 4):
            self._equalizer.set_amp_at_index(bass, band)
        for band in range(7, 10):
            self._equalizer.set_amp_at_index(treble, band)
        self._player.set_equalizer(self._equalizer)

    # ------------------------------------------------------------------
    # Interne
    # ------------------------------------------------------------------

    def _poll_position(self):
        state = self._player.get_state()
        if state in (vlc.State.Ended, vlc.State.Stopped, vlc.State.Error):
            self._timer.stop()
            return

        pos_ms = self.get_position_ms()
        self.position_changed.emit(pos_ms)

        if not self._duration_reported:
            dur = self.get_duration_ms()
            if dur > 0:
                self._duration_reported = True
                self.duration_changed.emit(dur)

    def _on_end_reached(self, event):
        self._timer.stop()
        self.state_changed.emit("stopped")
        self.track_ended.emit()
