"""
Gestion de la configuration de KaraTagor.
Fichier : ~/.config/karatagor/config.ini
"""

import os
import configparser
from pathlib import Path


CONFIG_DIR = Path.home() / ".config" / "karatagor"
CONFIG_FILE = CONFIG_DIR / "config.ini"

DEFAULTS = {
    "acoustid_api_key": "",
    "default_music_folder": str(Path.home() / "Music"),
    "theme": "dark",
    "backup_enabled": "true",
    "musicbrainz_useragent": "KaraTagor/1.0 (contact@example.com)",
}


class Config:
    def __init__(self):
        self._parser = configparser.ConfigParser()
        self._ensure_config()

    def _ensure_config(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        if not CONFIG_FILE.exists():
            self._write_defaults()
        else:
            self._parser.read(CONFIG_FILE, encoding="utf-8")
            # Ensure all default keys exist
            changed = False
            if not self._parser.has_section("karatagor"):
                self._parser.add_section("karatagor")
                changed = True
            for key, value in DEFAULTS.items():
                if not self._parser.has_option("karatagor", key):
                    self._parser.set("karatagor", key, value)
                    changed = True
            if changed:
                self._save()

    def _write_defaults(self):
        self._parser.add_section("karatagor")
        for key, value in DEFAULTS.items():
            self._parser.set("karatagor", key, value)
        self._save()

    def _save(self):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            self._parser.write(f)

    def get(self, key: str, fallback: str = "") -> str:
        return self._parser.get("karatagor", key, fallback=fallback)

    def set(self, key: str, value: str):
        if not self._parser.has_section("karatagor"):
            self._parser.add_section("karatagor")
        self._parser.set("karatagor", key, value)
        self._save()

    @property
    def acoustid_api_key(self) -> str:
        return self.get("acoustid_api_key")

    @acoustid_api_key.setter
    def acoustid_api_key(self, value: str):
        self.set("acoustid_api_key", value)

    @property
    def default_music_folder(self) -> str:
        return self.get("default_music_folder", str(Path.home() / "Music"))

    @default_music_folder.setter
    def default_music_folder(self, value: str):
        self.set("default_music_folder", value)

    @property
    def backup_enabled(self) -> bool:
        return self.get("backup_enabled", "true").lower() == "true"

    @backup_enabled.setter
    def backup_enabled(self, value: bool):
        self.set("backup_enabled", "true" if value else "false")

    @property
    def musicbrainz_useragent(self) -> str:
        return self.get("musicbrainz_useragent", DEFAULTS["musicbrainz_useragent"])
