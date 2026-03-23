"""
Identification acoustique via AcoustID + enrichissement MusicBrainz.
Toutes les opérations réseau sont pensées pour tourner dans un QThread.
"""

import subprocess
import time
from typing import Optional

import acoustid
import musicbrainzngs
import requests


# Rate limiting MusicBrainz : 1 req/sec
_MB_LAST_REQUEST = 0.0
_MB_MIN_INTERVAL = 1.1


def _mb_wait():
    global _MB_LAST_REQUEST
    elapsed = time.monotonic() - _MB_LAST_REQUEST
    if elapsed < _MB_MIN_INTERVAL:
        time.sleep(_MB_MIN_INTERVAL - elapsed)
    _MB_LAST_REQUEST = time.monotonic()


class FingerprintEngine:
    def __init__(self, useragent: str = "KaraTagor/1.0 (contact@example.com)"):
        app, version, contact = "KaraTagor", "1.0", "contact@example.com"
        # Extraire le contact entre parenthèses si fourni
        if "(" in useragent and ")" in useragent:
            contact = useragent.split("(")[1].rstrip(")")
        musicbrainzngs.set_useragent(app, version, contact)

    # ------------------------------------------------------------------
    # Empreinte acoustique
    # ------------------------------------------------------------------

    def generate(self, path: str) -> tuple[float, str]:
        """
        Lance fpcalc et retourne (duration_sec, fingerprint_str).
        Lève RuntimeError si fpcalc est absent ou échoue.
        """
        try:
            result = subprocess.run(
                ["fpcalc", path],
                capture_output=True,
                text=True,
                timeout=30,
            )
        except FileNotFoundError:
            raise RuntimeError(
                "fpcalc introuvable. Installez libchromaprint-tools : "
                "sudo apt install libchromaprint-tools"
            )

        if result.returncode != 0:
            raise RuntimeError(f"fpcalc a échoué : {result.stderr.strip()}")

        lines = result.stdout.strip().splitlines()
        duration = 0.0
        fingerprint = ""
        for line in lines:
            if line.startswith("DURATION="):
                try:
                    duration = float(line.split("=", 1)[1])
                except ValueError:
                    pass
            elif line.startswith("FINGERPRINT="):
                fingerprint = line.split("=", 1)[1]

        if not fingerprint:
            raise RuntimeError("fpcalc n'a pas retourné d'empreinte.")

        return duration, fingerprint

    # ------------------------------------------------------------------
    # Identification AcoustID
    # ------------------------------------------------------------------

    def identify_online(
        self,
        fingerprint: str,
        duration: float,
        acoustid_api_key: str,
    ) -> list[dict]:
        """
        Interroge l'API AcoustID.
        Retourne une liste de candidats :
          [{"recording_id": str, "title": str, "artist": str, "score": float}, ...]
        """
        if not acoustid_api_key:
            raise ValueError(
                "Clé API AcoustID manquante. Obtenez-en une gratuitement sur https://acoustid.org"
            )

        try:
            results = acoustid.lookup(
                acoustid_api_key,
                fingerprint,
                int(duration),
                meta="recordings releasegroups",
            )
        except acoustid.AcoustidError as e:
            raise RuntimeError(f"Erreur AcoustID : {e}")
        except Exception as e:
            raise RuntimeError(f"Erreur réseau AcoustID : {e}")

        candidates = []
        for score, recording_id, title, artist in acoustid.parse_lookup_result(results):
            candidates.append({
                "recording_id": recording_id or "",
                "title": title or "",
                "artist": artist or "",
                "score": round(score, 3),
            })

        # Trier par score décroissant
        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates

    # ------------------------------------------------------------------
    # Enrichissement MusicBrainz
    # ------------------------------------------------------------------

    def fetch_musicbrainz(self, recording_id: str) -> dict:
        """
        Enrichit les métadonnées depuis MusicBrainz.
        Retourne un dict : title, artist, album, year, genre, mbid
        """
        _mb_wait()

        try:
            result = musicbrainzngs.get_recording_by_id(
                recording_id,
                includes=["artists", "releases", "tags"],
            )
        except musicbrainzngs.ResponseError as e:
            raise RuntimeError(f"MusicBrainz : réponse invalide — {e}")
        except musicbrainzngs.NetworkError as e:
            raise RuntimeError(f"MusicBrainz : erreur réseau — {e}")
        except Exception as e:
            raise RuntimeError(f"MusicBrainz : erreur inattendue — {e}")

        rec = result.get("recording", {})

        title = rec.get("title", "")
        artist = ""
        artist_credits = rec.get("artist-credit", [])
        if artist_credits:
            parts = []
            for credit in artist_credits:
                if isinstance(credit, dict) and "artist" in credit:
                    parts.append(credit["artist"].get("name", ""))
                elif isinstance(credit, str):
                    parts.append(credit)
            artist = "".join(parts)

        album = ""
        year = ""
        release_mbid = ""
        releases = rec.get("release-list", [])
        if releases:
            rel = releases[0]
            album = rel.get("title", "")
            date = rel.get("date", "")
            year = date[:4] if date else ""
            release_mbid = rel.get("id", "")

        # Genre depuis les tags MusicBrainz
        genre = ""
        tags = rec.get("tag-list", [])
        if tags:
            tags_sorted = sorted(tags, key=lambda t: int(t.get("count", 0)), reverse=True)
            genre = tags_sorted[0].get("name", "").title() if tags_sorted else ""

        return {
            "title": title,
            "artist": artist,
            "album": album,
            "year": year,
            "genre": genre,
            "mbid": recording_id,
            "release_mbid": release_mbid,
        }

    # ------------------------------------------------------------------
    # Pochette d'album
    # ------------------------------------------------------------------

    def fetch_cover_art(
        self,
        release_mbid: str = "",
        artist: str = "",
        album: str = "",
    ) -> bytes | None:
        """
        Tente de récupérer la pochette d'album.
        1. Cover Art Archive (si release_mbid fourni)
        2. iTunes Search API (fallback artiste + album)
        Retourne les bytes de l'image ou None.
        """
        if release_mbid:
            data = self._fetch_cover_art_archive(release_mbid)
            if data:
                return data

        if artist or album:
            data = self._fetch_cover_itunes(artist, album)
            if data:
                return data

        return None

    def _fetch_cover_art_archive(self, release_mbid: str) -> bytes | None:
        url = f"https://coverartarchive.org/release/{release_mbid}/front"
        try:
            resp = requests.get(url, timeout=10, allow_redirects=True,
                                headers={"User-Agent": "KaraTagor/1.0"})
            if resp.status_code == 200 and resp.content:
                return resp.content
        except requests.RequestException:
            pass
        return None

    def _fetch_cover_itunes(self, artist: str, album: str) -> bytes | None:
        query = f"{artist} {album}".strip()
        if not query:
            return None
        try:
            resp = requests.get(
                "https://itunes.apple.com/search",
                params={"term": query, "entity": "album", "limit": 1},
                timeout=10,
                headers={"User-Agent": "KaraTagor/1.0"},
            )
            if resp.status_code != 200:
                return None
            results = resp.json().get("results", [])
            if not results:
                return None
            art_url = results[0].get("artworkUrl100", "")
            if not art_url:
                return None
            # Demander la version 600x600
            art_url = art_url.replace("100x100bb", "600x600bb")
            img_resp = requests.get(art_url, timeout=10,
                                    headers={"User-Agent": "KaraTagor/1.0"})
            if img_resp.status_code == 200 and img_resp.content:
                return img_resp.content
        except requests.RequestException:
            pass
        return None
