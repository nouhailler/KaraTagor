"""
Récupération et parsing des paroles depuis LRCLIB.
"""

import re
from pathlib import Path
from typing import Optional

import requests


LRCLIB_BASE = "https://lrclib.net/api"
TIMEOUT = 10  # secondes

# Patterns LRC supportés :
#   [mm:ss.xx]  [mm:ss:xx]  [mm:ss]
_LRC_LINE_RE = re.compile(
    r"\[(\d{1,3}):(\d{2})(?:[.:](\d{1,3}))?\](.*)"
)

# Tags de métadonnées LRC à ignorer (ex: [ar:Artist])
_LRC_META_RE  = re.compile(r"\[[a-zA-Z]+:.*\]")
_LRC_OFFSET_RE = re.compile(r"\[offset:\s*([+-]?\d+)\s*\]", re.IGNORECASE)


class LyricsFetcher:

    # ------------------------------------------------------------------
    # Récupération en ligne
    # ------------------------------------------------------------------

    def fetch_synced(
        self,
        artist: str,
        title: str,
        album: str = "",
        duration_sec: float = 0.0,
    ) -> Optional[list[tuple[int, str]]]:
        """
        Tente de récupérer des paroles synchronisées (LRC) depuis LRCLIB.
        Retourne une liste de (timestamp_ms, texte) ou None si indisponible.
        """
        params = {"artist_name": artist, "track_name": title}
        if album:
            params["album_name"] = album
        if duration_sec > 0:
            params["duration"] = int(duration_sec)

        try:
            resp = requests.get(
                f"{LRCLIB_BASE}/get",
                params=params,
                timeout=TIMEOUT,
                headers={"User-Agent": "KaraTagor/1.0"},
            )
        except requests.RequestException as e:
            raise RuntimeError(f"Erreur réseau LRCLIB : {e}")

        if resp.status_code == 404:
            return None
        if resp.status_code != 200:
            raise RuntimeError(f"LRCLIB a retourné HTTP {resp.status_code}")

        data = resp.json()

        synced_lrc = data.get("syncedLyrics", "")
        if synced_lrc:
            parsed = self.parse_lrc(synced_lrc)
            if parsed:
                return parsed

        return None

    def fetch_plain(self, artist: str, title: str) -> Optional[str]:
        """
        Récupère les paroles non synchronisées depuis LRCLIB.
        Retourne le texte brut ou None.
        """
        params = {"artist_name": artist, "track_name": title}

        try:
            resp = requests.get(
                f"{LRCLIB_BASE}/get",
                params=params,
                timeout=TIMEOUT,
                headers={"User-Agent": "KaraTagor/1.0"},
            )
        except requests.RequestException as e:
            raise RuntimeError(f"Erreur réseau LRCLIB : {e}")

        if resp.status_code == 404:
            return None
        if resp.status_code != 200:
            raise RuntimeError(f"LRCLIB a retourné HTTP {resp.status_code}")

        data = resp.json()
        return data.get("plainLyrics") or None

    # ------------------------------------------------------------------
    # Parsing LRC
    # ------------------------------------------------------------------

    def parse_lrc(self, lrc_string: str) -> list[tuple[int, str]]:
        """
        Parse un fichier LRC et retourne une liste triée de (timestamp_ms, texte).
        Supporte les formats [mm:ss.xx], [mm:ss:xx] et [mm:ss].
        Applique le tag [offset:N] (en ms) s'il est présent.
        """
        # --- Passe 1 : extraire l'offset global ---
        offset_ms = 0
        for raw_line in lrc_string.splitlines():
            m = _LRC_OFFSET_RE.fullmatch(raw_line.strip())
            if m:
                offset_ms = int(m.group(1))
                break

        # --- Passe 2 : parser les lignes de paroles ---
        result = []

        for raw_line in lrc_string.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if _LRC_META_RE.fullmatch(line):
                continue

            # Une ligne peut avoir plusieurs timestamps : [00:10.00][00:11.00]texte
            timestamps = []
            remaining = line

            while True:
                m = _LRC_LINE_RE.match(remaining)
                if not m:
                    break
                minutes  = int(m.group(1))
                seconds  = int(m.group(2))
                frac_str = m.group(3) or "0"
                text_part = m.group(4)

                # Normaliser centièmes/millièmes en ms
                if len(frac_str) <= 2:
                    frac_ms = int(frac_str) * 10
                else:
                    frac_ms = int(frac_str[:3])

                ms = (minutes * 60 + seconds) * 1000 + frac_ms + offset_ms
                timestamps.append(max(0, ms))
                remaining = text_part

            text = remaining.strip()
            for ms in timestamps:
                result.append((ms, text))

        result.sort(key=lambda x: x[0])
        return result

    # ------------------------------------------------------------------
    # Fichier .lrc local
    # ------------------------------------------------------------------

    def load_lrc_file(self, mp3_path: str) -> Optional[list[tuple[int, str]]]:
        """
        Cherche et charge le fichier .lrc adjacent au MP3.
        Retourne None si introuvable ou si le fichier ne contient aucune ligne synchronisée.
        """
        lrc_path = Path(mp3_path).with_suffix(".lrc")
        if not lrc_path.exists():
            return None

        try:
            content = lrc_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None

        parsed = self.parse_lrc(content)
        return parsed if parsed else None
