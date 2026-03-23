# KaraTagor — Prompt de Réalisation pour Claude Code

## Contexte et objectif

Crée une application de bureau Python complète appelée **KaraTagor**, tournant sous Linux (Debian/Ubuntu), permettant :
1. La lecture de fichiers MP3 en mode Karaoké (paroles synchronisées)
2. L'identification automatique et l'édition des tags ID3v2
3. La gestion d'une playlist avec explorateur de fichiers

L'environnement cible est Debian Linux avec PyQt6 disponible en natif.

---

## Stack technique imposée

| Besoin | Bibliothèque | Notes |
|---|---|---|
| GUI | PyQt6 | Pas PySide6 |
| Lecture audio | python-vlc | Wrapper VLC |
| Tags ID3v2 | mutagen | Lecture + écriture |
| Empreinte acoustique | pyacoustid | Nécessite `fpcalc` système |
| API identification | musicbrainzngs | + AcoustID |
| API paroles | LRCLIB (HTTP REST) | lrclib.net, gratuit, sans clé |
| Normalisation audio | pyloudnorm | Optionnel, Phase 2 |

---

## Architecture des fichiers à créer

```
/karatagor/
    main.py                    # Point d'entrée
    requirements.txt           # Dépendances pip
    install.sh                 # Script d'installation système (apt + pip)
    /assets/
        style.qss              # Thème sombre PyQt6
        /icons/                # Icônes SVG (play, pause, stop, etc.)
    /core/
        __init__.py
        audio_engine.py        # Wrapper python-vlc : play/pause/stop/seek/volume/equalizer
        tagger.py              # Wrapper mutagen : lecture/écriture tags ID3v2 + cover art
        fingerprint.py         # Wrapper pyacoustid : génération empreinte + appel AcoustID
        lyrics_fetcher.py      # Appels HTTP LRCLIB + parsing format .LRC
        config.py              # Gestion config (clé AcoustID, chemins, préférences)
    /gui/
        __init__.py
        main_window.py         # Fenêtre principale
        lyrics_widget.py       # Widget karaoké avec défilement et surbrillance
        tag_editor.py          # Panel/Dialog édition tags
        playlist_widget.py     # Widget playlist drag & drop
        file_browser.py        # Arborescence dossiers musicaux
```

---

## Spécifications module par module

### 1. `core/audio_engine.py`

- Classe `AudioEngine` encapsulant `python-vlc`
- Méthodes : `load(path)`, `play()`, `pause()`, `stop()`, `seek(ms)`, `set_volume(0-100)`, `get_position_ms()` (polling ou callback)
- Égaliseur : `set_equalizer(bass, treble)` via l'API VLC native
- Signal PyQt `position_changed(ms)` émis toutes les 100ms (QTimer)
- Signal `track_ended` pour passer au suivant dans la playlist

### 2. `core/tagger.py`

- Classe `Tagger` encapsulant mutagen
- Lecture : `read_tags(path)` → dict avec title, artist, album, year, genre, track, comment, cover_bytes, lyrics_uslt
- Écriture : `write_tags(path, tag_dict)` avec backup automatique (`.bak`) avant toute écriture
- Cover art : lecture APIC → QPixmap, écriture bytes → APIC
- Lyrics embedded : lecture USLT + SYLT, écriture USLT (texte non synchronisé) et création fichier `.lrc` adjacent

### 3. `core/fingerprint.py`

- Classe `FingerprintEngine`
- `generate(path)` → appel `fpcalc` via subprocess, retourne `(duration, fingerprint_str)`
- `identify_online(fingerprint, duration, acoustid_api_key)` → appel API AcoustID → retourne liste de candidats avec `recording_id` MusicBrainz
- `fetch_musicbrainz(recording_id)` → appel `musicbrainzngs` → retourne dict enrichi (title, artist, album, year, genre, mbid)
- Gestion des erreurs réseau (timeout, rate limiting MusicBrainz : respecter 1 req/sec)

### 4. `core/lyrics_fetcher.py`

- Classe `LyricsFetcher`
- `fetch_synced(artist, title, album, duration_sec)` → appel GET `https://lrclib.net/api/get` → retourne liste de tuples `[(timestamp_ms, line_text), ...]`
- `fetch_plain(artist, title)` → fallback texte non synchronisé
- `parse_lrc(lrc_string)` → parser format LRC : `[mm:ss.xx]texte`
- `load_lrc_file(path)` → charge un fichier `.lrc` adjacent au MP3

### 5. `core/config.py`

- Fichier de config : `~/.config/karatagor/config.ini`
- Clés : `acoustid_api_key`, `default_music_folder`, `theme`, `backup_enabled`
- Créé automatiquement au premier lancement avec valeurs par défaut

---

### 6. `gui/lyrics_widget.py` — Le widget karaoké

C'est le composant le plus critique visuellement.

- Hérite de `QWidget`
- Affiche les lignes LRC dans un scroll area
- Ligne active : grande taille, couleur primaire (ex: cyan/blanc), centrée
- Lignes passées : petites, grisées
- Lignes à venir : taille intermédiaire, blanches atténuées
- Défilement **automatique et animé** (`QPropertyAnimation` ou `QScrollArea.ensureWidgetVisible`)
- Méthode `set_lyrics([(ms, text), ...])`
- Méthode `update_position(current_ms)` appelée depuis le timer de `AudioEngine`
- Si pas de paroles synchronisées : afficher le texte USLT statique centré
- Si aucune parole : afficher un message "Aucune parole disponible" avec bouton "Rechercher en ligne"

### 7. `gui/tag_editor.py`

- Panel latéral (pas une dialog modale) intégré dans la fenêtre principale
- Champs : Title, Artist, Album, Year, Track, Genre (combobox avec genres ID3 standards), Comment
- Cover art : `QLabel` cliquable pour importer une image locale, affichage 200x200px
- Bouton **"Identifier (AcoustID)"** : lance `FingerprintEngine` dans un `QThread`, affiche `QProgressDialog`, propose les résultats dans une liste sélectionnable
- Bouton **"Sauvegarder Tags"** : appelle `Tagger.write_tags()`, feedback visuel (vert/rouge)
- Bouton **"Intégrer Paroles"** : écrit les paroles dans USLT ET crée le `.lrc` adjacent

### 8. `gui/main_window.py`

- Layout : 3 colonnes
  - **Gauche** : `file_browser.py` (arborescence) + `playlist_widget.py`
  - **Centre** : `lyrics_widget.py` (zone principale, prend le maximum d'espace)
  - **Droite** : `tag_editor.py` (panel tags)
- Barre de contrôle en bas : cover art miniature, titre/artiste, barre de progression (seekable), boutons Play/Pause/Stop/Prev/Next, volume slider
- Drag & Drop sur la fenêtre entière : `dragEnterEvent` + `dropEvent` acceptant les `.mp3`
- Menu bar : Fichier (Ouvrir, Ouvrir dossier, Quitter), Affichage (Thème, Panels), Aide (À propos)
- Titre de fenêtre dynamique : `"KaraTagor — {Artiste} - {Titre}"`

### 9. `assets/style.qss`

- Thème sombre complet (fond `#1a1a2e` ou similaire)
- Accent color : cyan/bleu électrique (`#00d4ff` ou `#4fc3f7`)
- Polices : titre lyrics en grande taille (24-32px), contrôles standard
- Scrollbar custom, boutons arrondis, panels avec bordures subtiles

---

## Comportement au lancement d'un fichier MP3

Quand l'utilisateur charge un MP3 (drag/drop ou double-clic dans l'explorateur) :

1. `Tagger.read_tags()` → peupler le panel tags et afficher la cover
2. Chercher un fichier `.lrc` adjacent (même nom, extension `.lrc`)
3. Si pas de `.lrc` : lire le tag USLT dans le fichier
4. Si ni l'un ni l'autre : afficher bouton "Rechercher paroles en ligne"
5. `AudioEngine.load()` → prêt à jouer
6. Mise à jour titre de fenêtre

---

## Fonctionnalité "Rechercher en ligne" (workflow complet)

Quand l'utilisateur clique **"Identifier (AcoustID)"** :

1. `FingerprintEngine.generate(path)` dans un QThread
2. `FingerprintEngine.identify_online()` → AcoustID API
3. Si résultats : afficher liste de candidats (titre, artiste, score de confiance)
4. L'utilisateur sélectionne le bon résultat
5. `FingerprintEngine.fetch_musicbrainz(mbid)` → enrichir les tags
6. `LyricsFetcher.fetch_synced()` → tenter LRCLIB avec les infos MusicBrainz
7. Si paroles trouvées : charger dans `LyricsWidget`, proposer "Intégrer dans le fichier"
8. Peupler le formulaire tag_editor avec les données récupérées (non sauvegardées automatiquement)

---

## Dépendances

### `requirements.txt`

```
PyQt6>=6.4.0
python-vlc>=3.0.0
mutagen>=1.46.0
pyacoustid>=1.2.0
musicbrainzngs>=0.7.1
pyloudnorm>=0.1.1
requests>=2.28.0
```

### `install.sh`

```bash
#!/bin/bash
sudo apt update
sudo apt install -y python3-pip python3-pyqt6 vlc libchromaprint-tools libvlc-dev
pip3 install --break-system-packages -r requirements.txt
```

---

## Contraintes et points d'attention pour l'implémentation

1. **Threading obligatoire** : Toute opération réseau (AcoustID, MusicBrainz, LRCLIB) et toute analyse audio (fpcalc) doivent tourner dans un `QThread` ou `QThreadPool` avec signaux de retour. Ne jamais bloquer le thread principal Qt.

2. **Rate limiting MusicBrainz** : L'API MusicBrainz impose 1 requête/seconde. Implémenter un délai ou une queue dans `fingerprint.py`. Toujours définir un `User-Agent` de la forme `KaraTagor/1.0 (contact@example.com)`.

3. **Clé AcoustID** : Lire depuis `config.ini`. Si absente, afficher une dialog d'information expliquant comment en obtenir une gratuitement sur acoustid.org, avec un champ de saisie pour la stocker.

4. **Backup avant écriture** : Dans `tagger.py`, toujours copier le fichier original en `filename.mp3.bak` avant d'écrire les tags, sauf si l'utilisateur a désactivé l'option dans les préférences.

5. **Gestion d'erreurs réseau** : Timeout à 10 secondes, messages d'erreur clairs dans l'interface (pas de crash silencieux).

6. **Format LRC** : Le parser doit gérer les variantes `[mm:ss.xx]`, `[mm:ss:xx]` et `[mm:ss]` (sans centièmes).

---

## Hors scope Phase 1 (à ne pas implémenter maintenant)

- Fonctionnalité "Tap to Sync" (création manuelle de LRC en temps réel)
- Export playlist `.m3u`
- Pitch shifting / réglage de tonalité
- Normalisation ReplayGain (pyloudnorm)
