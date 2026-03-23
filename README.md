# KaraTagor

Lecteur karaoké de bureau pour Linux avec gestion des tags ID3v2, bibliothèque musicale et identification acoustique automatique.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![PyQt6](https://img.shields.io/badge/PyQt6-6.4+-green)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## Fonctionnalités

### Lecture karaoké
- Affichage synchronisé des paroles (format LRC) avec surbrillance de la ligne en cours
- Défilement automatique centré sur la ligne active
- Réglage manuel du décalage de synchronisation (±0,5 s par clic), sauvegardé dans le fichier MP3
- Récupération automatique des paroles depuis [LRCLIB](https://lrclib.net) (gratuit, sans clé API)
- Intégration des paroles dans le tag USLT et création du fichier `.lrc` adjacent

### Bibliothèque musicale
- Grille d'albums avec pochettes chargées en arrière-plan
- Favoris (étoile ★) affichés en tête de liste
- Historique d'écoute avec compteur et date de dernière lecture
- Recherche en temps réel par titre, artiste ou album

### Playlists
- Arborescence dans le panneau gauche : **En cours** + playlists sauvegardées
- Clic sur une chanson d'une playlist sauvegardée → charge la playlist et démarre depuis cette chanson
- Sauvegarde / chargement / suppression de playlists nommées

### Gestion des tags ID3v2
- Lecture et écriture : titre, artiste, album, année, piste, genre, commentaire
- Pochette d'album : import par clic ou glisser-déposer, récupération automatique depuis [Cover Art Archive](https://coverartarchive.org) et iTunes
- Backup automatique `.bak` avant toute écriture

### Identification acoustique
- Empreinte acoustique via `fpcalc` (Chromaprint)
- Identification via [AcoustID](https://acoustid.org) avec liste de candidats et score de confiance
- Enrichissement des métadonnées via [MusicBrainz](https://musicbrainz.org)
- Récupération automatique de la pochette et des paroles après identification

---

## Installation

### Prérequis système (Debian/Ubuntu)

```bash
sudo apt install python3-pip python3-pyqt6 vlc libchromaprint-tools libvlc-dev
```

### Installation automatique

```bash
git clone https://github.com/nouhailler/KaraTagor.git
cd KaraTagor
bash install.sh
```

### Installation manuelle

```bash
pip3 install --break-system-packages -r requirements.txt
```

---

## Lancement

```bash
python3 main.py
# ou avec un fichier directement
python3 main.py /chemin/vers/chanson.mp3
```

---

## Clé API AcoustID

L'identification acoustique nécessite une clé API gratuite :

1. Créez un compte sur [acoustid.org](https://acoustid.org/login)
2. Enregistrez une nouvelle application en indiquant `https://github.com/nouhailler/KaraTagor` comme URL
3. Au premier clic sur **Identifier (AcoustID)**, KaraTagor vous demandera votre clé et la sauvegardera

---

## Structure du projet

```
karatagor/
├── main.py                    # Point d'entrée
├── requirements.txt
├── install.sh
├── assets/
│   ├── style.qss              # Thème sombre
│   └── icons/                 # Icônes SVG
├── core/
│   ├── audio_engine.py        # Lecture audio (python-vlc)
│   ├── tagger.py              # Tags ID3v2 (mutagen)
│   ├── fingerprint.py         # AcoustID + MusicBrainz + Cover Art Archive
│   ├── lyrics_fetcher.py      # LRCLIB + parser LRC
│   ├── library.py             # Bibliothèque et playlists (JSON)
│   └── config.py              # Configuration (~/.config/karatagor/)
└── gui/
    ├── main_window.py         # Fenêtre principale
    ├── lyrics_widget.py       # Vue karaoké
    ├── library_widget.py      # Bibliothèque en grille
    ├── playlist_tree_widget.py # Arbre de playlists
    ├── tag_editor.py          # Panneau tags
    ├── file_browser.py        # Explorateur de fichiers
    ├── playlist_manager.py    # Dialog gestionnaire de playlists
    └── help_dialog.py         # Aide intégrée
```

---

## Données utilisateur

| Fichier | Contenu |
|---|---|
| `~/.config/karatagor/config.ini` | Clé AcoustID, dossier par défaut, préférences |
| `~/.config/karatagor/library.json` | Historique d'écoute et favoris |
| `~/.config/karatagor/playlists/*.json` | Playlists sauvegardées |

---

## Raccourcis clavier

| Raccourci | Action |
|---|---|
| `Ctrl+O` | Ouvrir un fichier MP3 |
| `Ctrl+L` | Basculer Bibliothèque / Paroles |
| `Ctrl+P` | Gestionnaire de playlists |
| `F1` | Aide |
| `Ctrl+Q` | Quitter |

---

## Conseil — Synchronisation des paroles

AcoustID peut proposer plusieurs versions d'un même titre (single, album, remaster, live…).
Si les paroles ne sont pas en rythme avec votre fichier audio, relancez l'identification et choisissez une autre version dans la liste — chaque version possède ses propres timestamps LRC.

---

## Stack technique

| Besoin | Bibliothèque |
|---|---|
| Interface graphique | [PyQt6](https://pypi.org/project/PyQt6/) |
| Lecture audio | [python-vlc](https://pypi.org/project/python-vlc/) |
| Tags ID3v2 | [mutagen](https://mutagen.readthedocs.io/) |
| Empreinte acoustique | [pyacoustid](https://pypi.org/project/pyacoustid/) + `fpcalc` |
| Identification | [AcoustID API](https://acoustid.org/webservice) |
| Métadonnées | [musicbrainzngs](https://python-musicbrainzngs.readthedocs.io/) |
| Pochettes | [Cover Art Archive](https://coverartarchive.org/) + iTunes Search API |
| Paroles | [LRCLIB](https://lrclib.net) |

---

## Licence

MIT
