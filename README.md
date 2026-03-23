# 🎤 KaraTagor

> **Lecteur karaoké de bureau pour Linux** — paroles synchronisées, identification acoustique, gestion des tags ID3v2 et bibliothèque musicale.

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PyQt6](https://img.shields.io/badge/PyQt6-6.4+-41CD52?style=for-the-badge&logo=qt&logoColor=white)
![Linux](https://img.shields.io/badge/Linux-Debian%20%2F%20Ubuntu-E95420?style=for-the-badge&logo=ubuntu&logoColor=white)
![License](https://img.shields.io/badge/Licence-MIT-blue?style=for-the-badge)
![Release](https://img.shields.io/badge/Release-v1.0.0-00d4ff?style=for-the-badge)

</div>

---

## 🎵 Présentation

**KaraTagor** est une application de bureau Python qui transforme votre collection MP3 en expérience karaoké complète. Chargez un fichier, les paroles s'affichent et défilent automatiquement en rythme avec la musique.

```
┌─────────────────────────────────────────────────────────────────┐
│  📁 Explorateur    │      🎤 Paroles karaoké      │  🏷️ Tags   │
│  ─────────────     │   ─────────────────────────  │  ───────── │
│  🎵 chanson1.mp3   │                              │  Titre     │
│  🎵 chanson2.mp3   │    ♪ Ligne précédente ♪     │  Artiste   │
│  ─────────────     │                              │  Album     │
│  📋 Playlists      │  ► LIGNE EN COURS ◄         │  Année     │
│  ▶ En cours        │                              │  🖼️ Cover  │
│    ├ chanson1      │    ♪ Ligne suivante ♪        │            │
│    └ chanson2      │                              │ [Identifier]│
│  ☰ Ma playlist     │                              │ [Sauvegarder]│
└─────────────────────────────────────────────────────────────────┘
```

---

## ✨ Fonctionnalités

### 🎤 Karaoké
- Affichage synchronisé des paroles au format **LRC** avec surbrillance dynamique
- Défilement automatique centré sur la ligne active
- Réglage du décalage de synchronisation **±0,5 s** en temps réel, sauvegardé dans le fichier MP3
- Récupération automatique des paroles depuis **[LRCLIB](https://lrclib.net)** *(gratuit, sans clé API)*
- Intégration des paroles dans le tag **USLT** et création du fichier `.lrc` adjacent

### 🎵 Lecture audio
- Contrôles **lecture / pause / stop / précédent / suivant**
- Barre de progression **seekable** — cliquez n'importe où pour sauter à cette position
- Démarrage de la lecture depuis une position choisie sans avoir à appuyer sur Play au début
- Contrôle du **volume** et **égaliseur** basses/aigus

### 📚 Bibliothèque musicale
- Vue en **grille de pochettes** avec chargement en arrière-plan
- ⭐ **Favoris** affichés en tête de liste, sauvegardés localement
- Historique d'écoute avec compteur et date de dernière lecture
- Recherche en temps réel par titre, artiste ou album
- Double-clic → lecture + retour automatique à la vue karaoké

### 📋 Playlists
- Arborescence **En cours** + playlists sauvegardées dans le panneau gauche
- Clic sur une chanson d'une playlist → charge et démarre depuis ce point
- Sauvegarde, chargement et suppression de playlists nommées
- Drag & drop depuis le gestionnaire de fichiers

### 🏷️ Tags ID3v2
- Lecture et écriture : **titre, artiste, album, année, piste, genre, commentaire**
- 🖼️ **Pochette d'album** : import par clic ou glisser-déposer, récupération automatique
- Backup automatique `.bak` avant toute écriture

### 🔍 Identification acoustique
- Empreinte acoustique via **fpcalc** (Chromaprint)
- Identification via **[AcoustID](https://acoustid.org)** avec liste de candidats et score de confiance
- Enrichissement des métadonnées via **[MusicBrainz](https://musicbrainz.org)**
- Récupération automatique de la pochette depuis **[Cover Art Archive](https://coverartarchive.org)** et **iTunes**
- Récupération automatique des paroles après identification

---

## 🚀 Installation

### 📦 Paquet Debian (recommandé)

Téléchargez le `.deb` depuis la [page des releases](https://github.com/nouhailler/KaraTagor/releases) :

```bash
sudo dpkg -i karatagor_1.0.0_all.deb
```

### 🔧 Installation manuelle

**1. Prérequis système**

```bash
sudo apt install python3-pip python3-pyqt6 vlc libchromaprint-tools libvlc-dev
```

**2. Cloner et installer**

```bash
git clone https://github.com/nouhailler/KaraTagor.git
cd KaraTagor
bash install.sh
```

**3. Lancer**

```bash
python3 main.py
# ou avec un fichier directement
python3 main.py /chemin/vers/chanson.mp3
```

---

## 🔑 Clé API AcoustID

L'identification acoustique nécessite une clé API **gratuite** :

1. Créez un compte sur [acoustid.org](https://acoustid.org/login)
2. Enregistrez une nouvelle application avec l'URL :
   `https://github.com/nouhailler/KaraTagor`
3. Au premier clic sur **Identifier (AcoustID)**, KaraTagor vous demandera votre clé et la sauvegardera automatiquement

> 💡 Sans clé AcoustID, toutes les autres fonctionnalités (lecture, paroles LRCLIB, tags) restent pleinement utilisables.

---

## ⌨️ Raccourcis clavier

| Raccourci | Action |
|:---:|---|
| `Ctrl+O` | 📂 Ouvrir un fichier MP3 |
| `Ctrl+L` | 📚 Basculer Bibliothèque / Paroles |
| `Ctrl+P` | 📋 Gestionnaire de playlists |
| `F1` | ❓ Aide intégrée |
| `Ctrl+Q` | 🚪 Quitter |

---

## 🗂️ Structure du projet

```
karatagor/
├── 🚀 main.py                      Point d'entrée
├── 📋 requirements.txt
├── ⚙️  install.sh
├── assets/
│   ├── style.qss                   Thème sombre (fond #1a1a2e, accent #00d4ff)
│   └── icons/                      Icônes SVG (play, pause, stop, étoile…)
├── core/
│   ├── audio_engine.py             Lecture audio — python-vlc + QTimer 100ms
│   ├── tagger.py                   Tags ID3v2 — mutagen + backup auto
│   ├── fingerprint.py              AcoustID + MusicBrainz + Cover Art Archive
│   ├── lyrics_fetcher.py           LRCLIB + parser LRC multi-formats
│   ├── library.py                  Bibliothèque et playlists (JSON local)
│   └── config.py                   Configuration ~/.config/karatagor/
└── gui/
    ├── main_window.py              Fenêtre principale — layout 3 colonnes
    ├── lyrics_widget.py            Vue karaoké — rendu canvas, scroll centré
    ├── library_widget.py           Bibliothèque — grille de pochettes async
    ├── playlist_tree_widget.py     Arbre de playlists avec drag & drop
    ├── tag_editor.py               Panneau tags + identification AcoustID
    ├── file_browser.py             Explorateur filtré *.mp3
    ├── playlist_manager.py         Dialog sauvegarder / charger playlists
    └── help_dialog.py              Aide intégrée (HTML)
```

---

## 💾 Données utilisateur

| 📁 Fichier | Contenu |
|---|---|
| `~/.config/karatagor/config.ini` | Clé AcoustID, dossier par défaut, préférences |
| `~/.config/karatagor/library.json` | Historique d'écoute et favoris ⭐ |
| `~/.config/karatagor/playlists/*.json` | Playlists sauvegardées 📋 |

---

## 🛠️ Stack technique

| Besoin | Bibliothèque | Notes |
|---|---|---|
| 🖥️ Interface | [PyQt6](https://pypi.org/project/PyQt6/) | Thème sombre custom |
| 🔊 Audio | [python-vlc](https://pypi.org/project/python-vlc/) | Wrapper VLC |
| 🏷️ Tags | [mutagen](https://mutagen.readthedocs.io/) | ID3v2 complet |
| 🔬 Empreinte | [pyacoustid](https://pypi.org/project/pyacoustid/) + `fpcalc` | Chromaprint |
| 🔍 Identification | [AcoustID API](https://acoustid.org/webservice) | Gratuit |
| 📀 Métadonnées | [musicbrainzngs](https://python-musicbrainzngs.readthedocs.io/) | 1 req/sec |
| 🖼️ Pochettes | [Cover Art Archive](https://coverartarchive.org/) + iTunes | Fallback auto |
| 🎤 Paroles | [LRCLIB](https://lrclib.net) | Sans clé API |

---

## 💡 Conseil — Synchronisation des paroles

> 🎯 AcoustID peut proposer plusieurs versions d'un même titre (single, album, remaster, live…).
> Si les paroles **ne sont pas en rythme** avec votre fichier audio, relancez l'identification
> et choisissez une **autre version** dans la liste — chaque version possède ses propres timestamps LRC.
>
> En dernier recours, utilisez les boutons **−0,5s / +0,5s** dans la barre de contrôle
> pour affiner manuellement. Le réglage est sauvegardé dans le fichier MP3.

---

## 📄 Licence

MIT — libre d'utilisation, de modification et de distribution.

---

<div align="center">
  <sub>🎵 Fait avec ♥ en Python · PyQt6 · VLC · mutagen · AcoustID · MusicBrainz · LRCLIB</sub>
</div>
