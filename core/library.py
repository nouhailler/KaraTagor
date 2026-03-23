"""
Gestion de la bibliothèque musicale et des playlists nommées.
Stockage : ~/.config/karatagor/library.json
            ~/.config/karatagor/playlists/<nom>.json
"""

import json
from datetime import datetime
from pathlib import Path


CONFIG_DIR   = Path.home() / ".config" / "karatagor"
LIBRARY_FILE = CONFIG_DIR / "library.json"
PLAYLISTS_DIR = CONFIG_DIR / "playlists"


class Library:
    """Historique des pistes écoutées avec compteur et date de dernière lecture."""

    def __init__(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        PLAYLISTS_DIR.mkdir(parents=True, exist_ok=True)
        self._data: dict[str, dict] = {}
        self._load()

    # ------------------------------------------------------------------
    # Historique
    # ------------------------------------------------------------------

    def record_play(self, path: str, meta: dict):
        """Enregistre une lecture. meta = {title, artist, album, duration_sec}."""
        entry = self._data.get(path, {
            "title":      meta.get("title", Path(path).stem),
            "artist":     meta.get("artist", ""),
            "album":      meta.get("album", ""),
            "duration":   meta.get("duration_sec", 0.0),
            "play_count": 0,
            "last_played": "",
        })
        entry["play_count"]  = entry.get("play_count", 0) + 1
        entry["last_played"] = datetime.now().isoformat(timespec="seconds")
        # Mettre à jour les méta si elles ont changé
        for k in ("title", "artist", "album", "duration"):
            key = k if k != "duration" else "duration"
            src = "duration_sec" if k == "duration" else k
            if meta.get(src):
                entry[key if k != "duration" else "duration"] = meta[src]
        self._data[path] = entry
        self._save()

    def all_tracks(self) -> list[dict]:
        """Retourne toutes les pistes triées : favoris en premier, puis par date."""
        result = []
        for path, info in self._data.items():
            result.append({"path": path, **info})
        result.sort(
            key=lambda t: (
                not t.get("favorite", False),   # favoris d'abord
                t.get("last_played", ""),        # puis plus récent d'abord
            ),
            reverse=False,
        )
        # inverser last_played
        result.sort(key=lambda t: (
            0 if t.get("favorite", False) else 1,
            "" if not t.get("last_played") else t["last_played"],
        ), reverse=False)
        # On refait proprement
        favorites = [t for t in result if t.get("favorite", False)]
        others    = [t for t in result if not t.get("favorite", False)]
        favorites.sort(key=lambda t: t.get("last_played", ""), reverse=True)
        others.sort(   key=lambda t: t.get("last_played", ""), reverse=True)
        return favorites + others

    def set_favorite(self, path: str, value: bool):
        if path in self._data:
            self._data[path]["favorite"] = value
            self._save()

    def is_favorite(self, path: str) -> bool:
        return self._data.get(path, {}).get("favorite", False)

    def remove(self, path: str):
        if path in self._data:
            del self._data[path]
            self._save()

    # ------------------------------------------------------------------
    # Playlists nommées
    # ------------------------------------------------------------------

    def save_playlist(self, name: str, paths: list[str]):
        """Sauvegarde une playlist nommée (liste de chemins)."""
        safe_name = "".join(c for c in name if c.isalnum() or c in " _-").strip()
        if not safe_name:
            safe_name = "playlist"
        dest = PLAYLISTS_DIR / f"{safe_name}.json"
        with open(dest, "w", encoding="utf-8") as f:
            json.dump({"name": name, "tracks": paths}, f, ensure_ascii=False, indent=2)
        return safe_name

    def load_playlist(self, name: str) -> list[str]:
        """Charge une playlist par nom (sans extension). Retourne les chemins."""
        path = PLAYLISTS_DIR / f"{name}.json"
        if not path.exists():
            return []
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return [p for p in data.get("tracks", []) if Path(p).exists()]

    def list_playlists(self) -> list[str]:
        """Retourne les noms des playlists sauvegardées (sans extension)."""
        return sorted(p.stem for p in PLAYLISTS_DIR.glob("*.json"))

    def delete_playlist(self, name: str):
        path = PLAYLISTS_DIR / f"{name}.json"
        if path.exists():
            path.unlink()

    # ------------------------------------------------------------------
    # Persistance
    # ------------------------------------------------------------------

    def _load(self):
        if not LIBRARY_FILE.exists():
            self._data = {}
            return
        try:
            with open(LIBRARY_FILE, encoding="utf-8") as f:
                self._data = json.load(f)
        except Exception:
            self._data = {}

    def _save(self):
        with open(LIBRARY_FILE, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)
