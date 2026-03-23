# KaraTagor — Contexte de session

## Architecture

### Fichiers

**Racine**
- `main.py` — Point d'entrée : initialise QApplication, charge le stylesheet, instancie MainWindow, gère l'argument MP3 en ligne de commande
- `requirements.txt` — Dépendances pip avec versions réelles installées
- `install.sh` — Script d'installation apt + pip pour Debian/Ubuntu
- `README.md` — Documentation utilisateur
- `CLAUDE.md` — Instructions de développement pour Claude Code

**core/**
- `core/__init__.py` — Module vide
- `core/audio_engine.py` — Classe `AudioEngine` : wrapper python-vlc, play/pause/stop/seek/volume, égaliseur, signaux `position_changed(ms)`, `track_ended`, `state_changed`, `duration_changed` via QTimer 100ms
- `core/tagger.py` — Classe `Tagger` : lecture/écriture tags ID3v2 via mutagen (TIT2, TPE1, TALB, TDRC, TRCK, TCON, COMM, APIC, USLT, SYLT), backup automatique .bak, offset de sync via TXXX custom ("KaraTagor_sync_offset")
- `core/fingerprint.py` — Classe `FingerprintEngine` : génération empreinte via fpcalc, identification AcoustID, enrichissement MusicBrainz (rate-limiting 1 req/s), récupération pochette Cover Art Archive + iTunes fallback
- `core/lyrics_fetcher.py` — Classe `LyricsFetcher` : appels LRCLIB (fetch_synced, fetch_plain), parser LRC (formats [mm:ss.xx], [mm:ss:xx], [mm:ss], support [offset:N]), chargement fichier .lrc adjacent
- `core/config.py` — Classe `Config` : fichier INI dans ~/.config/karatagor/config.ini, clés acoustid_api_key, default_music_folder, theme, backup_enabled, musicbrainz_useragent
- `core/library.py` — Classe `Library` : historique des pistes (play_count, last_played, favorite) en JSON, gestion playlists nommées en JSON dans ~/.config/karatagor/playlists/

**gui/**
- `gui/__init__.py` — Module vide
- `gui/main_window.py` — `MainWindow` : layout 3 colonnes (FileBrowser+PlaylistTree | LyricsWidget | TagEditorPanel), barre de contrôle bas (cover miniature, seekbar, Play/Pause/Stop/Prev/Next, volume, sync offset), menus, drag & drop MP3, vue bibliothèque basculable, worker LyricsWorker en QThread (753 lignes)
- `gui/lyrics_widget.py` — `LyricsWidget` + `_LyricsCanvas` : affichage karaoké avec scroll automatique, surbrillance ligne active (QPainter custom), support sync offset en ms, fallback texte statique (231 lignes)
- `gui/tag_editor.py` — `TagEditorPanel` : panel latéral avec champs Title/Artist/Album/Year/Track/Genre/Comment, `CoverLabel` cliquable/drag-drop, boutons Identifier/Sauvegarder/Intégrer Paroles, workers en QThread (FingerprintWorker, MusicBrainzWorker, CoverArtWorker), dialog CandidateDialog (607 lignes)
- `gui/playlist_widget.py` — `PlaylistWidget` : liste de pistes avec drag & drop, double-clic pour jouer, suppression, navigation prev/next (172 lignes)
- `gui/playlist_tree_widget.py` — `PlaylistTreeWidget` : arborescence playlists (nœud "En cours" + playlists nommées), gestion sauvegarde/chargement via Library, menu contextuel (320 lignes)
- `gui/file_browser.py` — `FileBrowser` : explorateur de dossiers via QFileSystemModel, filtré sur .mp3, signal file_selected (93 lignes)
- `gui/library_widget.py` — `LibraryWidget` : vue bibliothèque en grille avec covers, filtrage texte, favoris (étoile), chargement covers asynchrone (_CoverLoader en QThread), tri favoris/date (234 lignes)
- `gui/playlist_manager.py` — `PlaylistManagerDialog` : dialog de gestion des playlists sauvegardées (chargement, suppression) (130 lignes)
- `gui/help_dialog.py` — `HelpDialog` : fenêtre d'aide HTML complète (336 lignes)

**assets/**
- `assets/style.qss` — Thème sombre (fond #1a1a2e, accent cyan #00d4ff/#4fc3f7), scrollbars custom, boutons arrondis
- `assets/icons/` — Icônes SVG : play, pause, stop, prev, next, volume, search, folder, music, star, star_filled

### Dépendances clés

| Rôle | Bibliothèque | Version installée |
|---|---|---|
| GUI | PyQt6 | 6.9.0 |
| Audio | python-vlc | 3.0.21203 |
| Tags ID3v2 | mutagen | 1.47.0 |
| Empreinte acoustique | pyacoustid | 1.3.0 |
| API identification | musicbrainzngs | 0.7.1 |
| Paroles | LRCLIB (HTTP REST) | — |
| Normalisation | pyloudnorm | 0.2.0 |
| HTTP | requests | 2.32.3 |

---

## Fonctionnalités implémentées

- **Lecture audio** : play/pause/stop/seek, volume, égaliseur bass/treble via VLC
- **Tags ID3v2** : lecture et écriture complète (titre, artiste, album, année, piste, genre, commentaire, cover art APIC, paroles USLT/SYLT), backup .bak automatique
- **Karaoké** : affichage des paroles synchronisées avec défilement automatique et surbrillance, rendu custom par QPainter, offset de synchronisation ajustable au runtime (±100ms, ±1000ms) et persisté en tag TXXX
- **Paroles** : chargement depuis fichier .lrc adjacent, tag USLT embarqué, ou recherche en ligne LRCLIB ; parser LRC complet (3 formats de timestamp + [offset:N])
- **Identification acoustique** : génération empreinte via fpcalc, appel API AcoustID, enrichissement MusicBrainz, récupération pochette Cover Art Archive + iTunes fallback — tout en QThread
- **Bibliothèque musicale** : historique des lectures (play_count, last_played), favoris, tri favoris/date, vue grille avec covers asynchrones
- **Playlists** : playlist en cours (PlaylistWidget + PlaylistTreeWidget), playlists nommées sauvegardées en JSON, dialog de gestion
- **Explorateur de fichiers** : arborescence dossiers filtrée .mp3 (QFileSystemModel)
- **Drag & Drop** : sur la fenêtre principale et sur la playlist
- **Interface** : thème sombre complet, layout 3 colonnes, barre de contrôle seekable, titre de fenêtre dynamique, menus Fichier/Affichage/Aide, fenêtre d'aide HTML
- **Configuration** : fichier INI persistant, clé AcoustID avec prompt si absente
- **Rate limiting** : MusicBrainz 1 req/sec respecté, timeout réseau 10s

---

## Derniers travaux (session actuelle)

- Bibliothèque musicale (`core/library.py`, `gui/library_widget.py`) : historique des lectures, favoris, vue grille avec covers asynchrones, filtrage textuel
- Playlists nommées : `PlaylistTreeWidget` remplaçant `PlaylistWidget` comme widget principal de gauche (arborescence playlists + piste en cours), `PlaylistManagerDialog`
- Offset de synchronisation des paroles : ajustement ±100ms/±1000ms dans la barre de contrôle, persisté via `Tagger.write_sync_offset()` dans tag TXXX
- Seekbar : barre de progression cliquable et draggable
- Packaging Debian : création du .deb v1.0.0 (cette session)

---

## Bugs connus / Points d'attention

- **Backup .bak dupliqué** : `write_sync_offset()` ne fait pas de backup (intentionnel), mais `write_tags()` crée un .bak à chaque sauvegarde — si l'utilisateur sauvegarde fréquemment, les .bak s'accumulent (un seul .bak est conservé, le plus récent écrase le précédent, ce qui est correct)
- **VLC et thread** : `_on_end_reached` est appelé depuis le thread interne VLC — l'émission du signal `track_ended` via `pyqtSignal` est thread-safe en PyQt6 (connexion auto), pas de problème attendu
- **Library.all_tracks() : triple tri redondant** — la méthode trie trois fois (deux fois redondant) avant le tri final favoris/date. Fonctionnel mais inefficace sur grande bibliothèque
- **PlaylistTreeWidget vs PlaylistWidget** : les deux classes existent, `PlaylistTreeWidget` est utilisé dans `MainWindow` mais `PlaylistWidget` est conservé (potentiellement inutilisé dans l'UI actuelle)
- **Genre combobox** : le panel tags affiche une combobox de genres ID3 standards, mais si le genre lu depuis le fichier n'est pas dans la liste, il peut ne pas être sélectionné correctement
- **fpcalc absent** : si `libchromaprint-tools` n'est pas installé, l'identification AcoustID échoue avec un message clair — mais l'erreur n'est pas testée à l'ouverture de l'app
- **LRC offset global** : le tag `[offset:N]` du fichier LRC est appliqué au parsing, mais l'offset custom KaraTagor (TXXX) est appliqué séparément dans `LyricsWidget.update_position()` — les deux coexistent sans conflit

---

## Packaging et release (session 2026-03-23)

### Ce qui a été fait

- **requirements.txt** mis à jour avec les versions réellement installées (PyQt6 6.9.0, python-vlc 3.0.21203, mutagen 1.47.0, pyacoustid 1.3.0, pyloudnorm 0.2.0, requests 2.32.3)
- **CONTEXT.md** créé pour tracer l'état du projet entre sessions
- **Packaging Debian** créé dans `packaging/karatagor_1.0.0_all/` :
  - `DEBIAN/control` : métadonnées du paquet
  - `DEBIAN/postinst` : installation automatique des dépendances pip
  - `usr/bin/karatagor` : script shell de lancement
  - `usr/share/applications/karatagor.desktop` : entrée menu FreeDesktop
  - `usr/share/icons/hicolor/256x256/apps/karatagor.png` : icône PNG 256x256 générée (cercle #1a1a2e + texte "KT" cyan #00d4ff)
  - `usr/share/karatagor/` : copie de toutes les sources Python (main.py, core/, gui/, assets/)
- **`packaging/karatagor_1.0.0_all.deb`** : paquet Debian construit (91 Ko)
- **Git tag v1.0.0** créé et poussé
- **GitHub Release v1.0.0** créée avec le .deb en asset : https://github.com/nouhailler/KaraTagor/releases/tag/v1.0.0

### Pour installer le paquet

```bash
sudo dpkg -i karatagor_1.0.0_all.deb
sudo apt-get install -f
```

---

## Points de reprise suggérés

- **Tests** : aucun test unitaire existant — ajouter des tests pour `parse_lrc()`, `read_tags()`/`write_tags()`, `Library`
- **Export M3U** : fonctionnalité hors scope Phase 1, simple à ajouter depuis `PlaylistTreeWidget`
- **Normalisation ReplayGain** : pyloudnorm est installé mais non utilisé (hors scope Phase 1)
- **Tap to Sync** : création manuelle de fichier .lrc en temps réel (hors scope Phase 1)
- **Mise à jour dynamique de la bibliothèque** : actuellement nécessite un refresh manuel après ajout de fichiers
- **Packaging** : .deb créé en v1.0.0, à maintenir lors de futures versions
