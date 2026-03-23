"""
Lecture et écriture des tags ID3v2 via mutagen.
Gestion de la cover art, des paroles USLT/SYLT et du backup automatique.
"""

import shutil
from pathlib import Path
from typing import Optional

from mutagen.id3 import (
    ID3, ID3NoHeaderError,
    TIT2, TPE1, TALB, TDRC, TRCK, TCON, COMM,
    APIC, USLT, SYLT, TXXX,
    error as ID3Error,
)
from mutagen.mp3 import MP3


class Tagger:
    def __init__(self, backup_enabled: bool = True):
        self.backup_enabled = backup_enabled

    # ------------------------------------------------------------------
    # Lecture
    # ------------------------------------------------------------------

    def read_tags(self, path: str) -> dict:
        """
        Retourne un dict :
          title, artist, album, year, track, genre, comment,
          cover_bytes (bytes | None), lyrics_uslt (str | None),
          lyrics_sylt (list[(str, int)] | None), duration_sec (float)
        """
        result = {
            "title": "",
            "artist": "",
            "album": "",
            "year": "",
            "track": "",
            "genre": "",
            "comment": "",
            "cover_bytes": None,
            "lyrics_uslt": None,
            "lyrics_sylt": None,
            "duration_sec": 0.0,
        }

        try:
            audio = MP3(path)
            result["duration_sec"] = audio.info.length
        except Exception:
            pass

        try:
            tags = ID3(path)
        except ID3NoHeaderError:
            return result
        except Exception:
            return result

        def _first(frame_id):
            frames = tags.getall(frame_id)
            if frames:
                return str(frames[0])
            return ""

        result["title"] = _first("TIT2")
        result["artist"] = _first("TPE1")
        result["album"] = _first("TALB")
        result["year"] = _first("TDRC")
        result["track"] = _first("TRCK")
        result["genre"] = _first("TCON")

        comm_frames = tags.getall("COMM")
        if comm_frames:
            result["comment"] = str(comm_frames[0].text[0]) if comm_frames[0].text else ""

        apic_frames = tags.getall("APIC")
        if apic_frames:
            result["cover_bytes"] = apic_frames[0].data

        uslt_frames = tags.getall("USLT")
        if uslt_frames:
            result["lyrics_uslt"] = uslt_frames[0].text

        sylt_frames = tags.getall("SYLT")
        if sylt_frames:
            result["lyrics_sylt"] = sylt_frames[0].text  # list of (text, timestamp_ms)

        return result

    # ------------------------------------------------------------------
    # Écriture
    # ------------------------------------------------------------------

    def write_tags(self, path: str, tag_dict: dict):
        """
        Écrit les tags dans le fichier MP3.
        Crée un backup .bak si backup_enabled.
        tag_dict peut contenir n'importe quel sous-ensemble des clés.
        """
        if self.backup_enabled:
            self._make_backup(path)

        try:
            tags = ID3(path)
        except ID3NoHeaderError:
            tags = ID3()

        if "title" in tag_dict and tag_dict["title"] is not None:
            tags.delall("TIT2")
            tags.add(TIT2(encoding=3, text=tag_dict["title"]))

        if "artist" in tag_dict and tag_dict["artist"] is not None:
            tags.delall("TPE1")
            tags.add(TPE1(encoding=3, text=tag_dict["artist"]))

        if "album" in tag_dict and tag_dict["album"] is not None:
            tags.delall("TALB")
            tags.add(TALB(encoding=3, text=tag_dict["album"]))

        if "year" in tag_dict and tag_dict["year"] is not None:
            tags.delall("TDRC")
            tags.add(TDRC(encoding=3, text=str(tag_dict["year"])))

        if "track" in tag_dict and tag_dict["track"] is not None:
            tags.delall("TRCK")
            tags.add(TRCK(encoding=3, text=str(tag_dict["track"])))

        if "genre" in tag_dict and tag_dict["genre"] is not None:
            tags.delall("TCON")
            tags.add(TCON(encoding=3, text=tag_dict["genre"]))

        if "comment" in tag_dict and tag_dict["comment"] is not None:
            tags.delall("COMM")
            tags.add(COMM(encoding=3, lang="fra", desc="", text=tag_dict["comment"]))

        if "cover_bytes" in tag_dict and tag_dict["cover_bytes"] is not None:
            mime = self._detect_image_mime(tag_dict["cover_bytes"])
            tags.delall("APIC")
            tags.add(APIC(
                encoding=3,
                mime=mime,
                type=3,  # Cover (front)
                desc="Cover",
                data=tag_dict["cover_bytes"],
            ))

        if "lyrics_uslt" in tag_dict and tag_dict["lyrics_uslt"] is not None:
            tags.delall("USLT")
            tags.add(USLT(encoding=3, lang="fra", desc="", text=tag_dict["lyrics_uslt"]))

        tags.save(path, v2_version=3)

    def write_lyrics_and_lrc(self, path: str, lyrics_text: str, synced_lyrics: Optional[list] = None):
        """
        Écrit les paroles en USLT et crée le fichier .lrc adjacent.
        synced_lyrics : liste de (timestamp_ms, text)
        """
        self.write_tags(path, {"lyrics_uslt": lyrics_text})

        lrc_path = Path(path).with_suffix(".lrc")
        if synced_lyrics:
            lrc_content = self._build_lrc(synced_lyrics)
        else:
            lrc_content = lyrics_text

        lrc_path.write_text(lrc_content, encoding="utf-8")

    # ------------------------------------------------------------------
    # Offset de synchronisation paroles (tag TXXX custom)
    # ------------------------------------------------------------------

    _SYNC_TAG_DESC = "KaraTagor_sync_offset"

    def read_sync_offset(self, path: str) -> int:
        """Lit l'offset de synchronisation (ms) stocké dans le tag TXXX custom. Retourne 0 si absent."""
        try:
            tags = ID3(path)
            frames = tags.getall(f"TXXX:{self._SYNC_TAG_DESC}")
            if frames:
                return int(frames[0].text[0])
        except Exception:
            pass
        return 0

    def write_sync_offset(self, path: str, offset_ms: int):
        """Écrit l'offset de synchronisation dans le tag TXXX (sans backup, opération légère)."""
        try:
            try:
                tags = ID3(path)
            except ID3NoHeaderError:
                tags = ID3()
            tags.delall(f"TXXX:{self._SYNC_TAG_DESC}")
            if offset_ms != 0:
                tags.add(TXXX(encoding=3, desc=self._SYNC_TAG_DESC, text=[str(offset_ms)]))
            tags.save(path, v2_version=3)
        except Exception:
            pass   # Ne pas bloquer l'UI pour un tag optionnel

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _make_backup(self, path: str):
        backup = path + ".bak"
        shutil.copy2(path, backup)

    def _detect_image_mime(self, data: bytes) -> str:
        if data[:3] == b"\xff\xd8\xff":
            return "image/jpeg"
        if data[:8] == b"\x89PNG\r\n\x1a\n":
            return "image/png"
        return "image/jpeg"

    def _build_lrc(self, synced_lyrics: list) -> str:
        lines = []
        for ms, text in synced_lyrics:
            total_sec = ms // 1000
            centis = (ms % 1000) // 10
            minutes = total_sec // 60
            seconds = total_sec % 60
            lines.append(f"[{minutes:02d}:{seconds:02d}.{centis:02d}]{text}")
        return "\n".join(lines)
