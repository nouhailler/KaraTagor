"""
Fenêtre d'aide de KaraTagor.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextBrowser, QLabel, QSizePolicy, QWidget,
)

HELP_HTML = """
<html>
<head>
<style>
  body      { background:#1a1a2e; color:#e0e0e0;
              font-family:"Segoe UI","Noto Sans",sans-serif; font-size:13px;
              margin:0; padding:0; }
  h1        { color:#00d4ff; font-size:22px; margin-bottom:4px; }
  h2        { color:#00d4ff; font-size:15px; border-bottom:1px solid #2a2a4a;
              padding-bottom:4px; margin-top:24px; }
  h3        { color:#4fc3f7; font-size:13px; margin-bottom:2px; margin-top:14px; }
  p, li     { color:#c8d8e8; line-height:1.6; }
  ul        { margin:4px 0 8px 18px; padding:0; }
  li        { margin-bottom:3px; }
  code      { background:#12122a; color:#ffab40; padding:1px 5px;
              border-radius:3px; font-family:monospace; font-size:12px; }
  .tip      { background:#003a20; border-left:3px solid #00e676;
              padding:8px 12px; border-radius:4px; margin:10px 0; color:#b0f0c0; }
  .warn     { background:#3a2000; border-left:3px solid #ffab40;
              padding:8px 12px; border-radius:4px; margin:10px 0; color:#ffe0a0; }
  .key      { background:#2a2a4a; color:#00d4ff; padding:1px 7px;
              border-radius:4px; border:1px solid #3a3a6a;
              font-family:monospace; font-size:12px; }
  .section  { padding:0 20px 16px 20px; }
</style>
</head>
<body>

<div style="background:#12122a; padding:20px 20px 12px 20px;">
  <h1>KaraTagor — Guide d'utilisation</h1>
  <p style="color:#7090a0; margin:0;">
    Lecteur karaoké avec gestion des tags ID3v2, bibliothèque musicale
    et identification acoustique.
  </p>
</div>

<div class="section">

<!-- ═══════════════════════════════════════════ -->
<h2>1. Ouvrir des fichiers MP3</h2>

<h3>Glisser-déposer</h3>
<ul>
  <li>Glissez un ou plusieurs fichiers <code>.mp3</code> directement sur la fenêtre
      depuis votre gestionnaire de fichiers.</li>
  <li>Les fichiers sont ajoutés à la playlist et le premier est chargé automatiquement.</li>
</ul>

<h3>Menu Fichier</h3>
<ul>
  <li><b>Ouvrir un fichier MP3…</b> <span class="key">Ctrl+O</span> — ouvre un fichier unique.</li>
  <li><b>Ouvrir un dossier…</b> — définit le dossier racine de l'explorateur de fichiers.</li>
</ul>

<h3>Explorateur de fichiers (panneau gauche haut)</h3>
<ul>
  <li>Naviguez dans l'arborescence de vos dossiers musicaux.</li>
  <li>Double-cliquez sur un fichier <code>.mp3</code> pour le charger et l'ajouter à la playlist.</li>
  <li>Cliquez sur <code>…</code> pour changer le dossier racine.</li>
</ul>

<!-- ═══════════════════════════════════════════ -->
<h2>2. Playlists (panneau gauche bas)</h2>

<p>Le panneau de playlists affiche une arborescence avec deux niveaux :</p>

<h3>▶ En cours</h3>
<ul>
  <li>Contient les pistes de la session active.</li>
  <li>La piste en cours de lecture est affichée en <span style="color:#00d4ff">cyan et en gras</span>.</li>
  <li>Cliquez sur une chanson pour la jouer immédiatement.</li>
  <li>Glissez des fichiers MP3 directement dans le panneau pour les ajouter.</li>
  <li>Clic droit sur une chanson → <b>Retirer de la playlist</b>.</li>
</ul>

<h3>☰ Playlists sauvegardées</h3>
<ul>
  <li>Chaque playlist sauvegardée apparaît comme un nœud expandable.</li>
  <li>Cliquez sur une chanson d'une playlist → charge toute la playlist et démarre
      depuis cette chanson.</li>
  <li>Clic droit sur un nœud playlist → <b>Charger</b> ou <b>Supprimer</b>.</li>
</ul>

<h3>Sauvegarder une playlist</h3>
<ul>
  <li>Cliquez sur <b>Sauvegarder</b> sous l'arbre, donnez un nom.</li>
  <li>Ou utilisez <b>Affichage → Gestionnaire de playlists…</b>
      <span class="key">Ctrl+P</span> pour gérer toutes vos playlists
      (sauvegarder, charger, supprimer).</li>
</ul>

<!-- ═══════════════════════════════════════════ -->
<h2>3. Contrôles de lecture</h2>

<h3>Barre de contrôle (bas de fenêtre)</h3>
<ul>
  <li><b>⏮ Précédent / ⏭ Suivant</b> — piste précédente ou suivante.</li>
  <li><b>▶ Play / ⏸ Pause</b> — démarre ou met en pause la lecture.</li>
  <li><b>⏹ Stop</b> — arrête et remet la position à zéro.</li>
  <li><b>Volume</b> — curseur à droite des boutons de transport.</li>
</ul>

<h3>Barre de progression (seekbar)</h3>
<ul>
  <li>Cliquez n'importe où ou faites glisser le curseur pour choisir une position.</li>
  <li>Si le morceau est à l'arrêt, la position est mémorisée :
      appuyez sur <b>Play</b> pour démarrer depuis cet endroit.</li>
  <li>Si le morceau est en cours de lecture, le seek est immédiat.</li>
</ul>

<!-- ═══════════════════════════════════════════ -->
<h2>4. Paroles karaoké (vue centrale)</h2>

<h3>Affichage</h3>
<ul>
  <li>La ligne en cours est affichée en <span style="color:#00d4ff"><b>grand et en cyan</b></span>.</li>
  <li>Les lignes passées sont grisées, les lignes à venir en blanc atténué.</li>
  <li>Le défilement est automatique et centré sur la ligne active.</li>
</ul>

<h3>Sources de paroles (ordre de priorité)</h3>
<ul>
  <li>Fichier <code>.lrc</code> adjacent au MP3 (même nom, extension <code>.lrc</code>).</li>
  <li>Tag <b>USLT</b> intégré dans le fichier MP3.</li>
  <li>Recherche en ligne via le bouton <b>Rechercher en ligne</b>.</li>
</ul>

<h3>Recherche en ligne (LRCLIB)</h3>
<ul>
  <li>Cliquez sur <b>Rechercher en ligne</b> dans la zone karaoké,
      ou laissez l'identification AcoustID le faire automatiquement.</li>
  <li>Les paroles synchronisées (LRC) sont récupérées gratuitement
      depuis <code>lrclib.net</code>, sans clé API.</li>
</ul>

<!-- ═══════════════════════════════════════════ -->
<h2>5. Synchronisation des paroles</h2>

<h3>Réglage manuel du décalage</h3>
<ul>
  <li>Boutons <code>−0.5s</code> et <code>+0.5s</code> à droite du volume dans la barre du bas.</li>
  <li><code>−0.5s</code> — <b>avance</b> les paroles (surbrillance plus tôt).</li>
  <li><code>+0.5s</code> — <b>retarde</b> les paroles (surbrillance plus tard).</li>
  <li>Le décalage s'affiche entre les boutons
      (<span style="color:#7090a0">gris = neutre</span>,
       <span style="color:#00d4ff">cyan = avancé</span>,
       <span style="color:#ffab40">orange = retardé</span>).</li>
</ul>

<h3>Sauvegarde automatique</h3>
<ul>
  <li>Le décalage réglé est <b>enregistré dans le fichier MP3</b>
      (tag <code>TXXX:KaraTagor_sync_offset</code>) et restauré automatiquement
      à la prochaine ouverture.</li>
</ul>

<div class="tip">
  <b>Conseil :</b> Si les paroles ne sont pas synchronisées, essayez d'abord
  de changer de version lors de l'identification AcoustID (voir section 7).
  Chaque version d'un même titre (single, album, live, remaster…) a ses propres
  timestamps LRC.
</div>

<!-- ═══════════════════════════════════════════ -->
<h2>6. Bibliothèque musicale</h2>

<p>Accessible via <b>Affichage → Bibliothèque musicale</b>
   <span class="key">Ctrl+L</span> — bascule la vue centrale entre
   les paroles et la bibliothèque.</p>

<h3>Affichage en grille</h3>
<ul>
  <li>Toutes les chansons écoutées sont affichées avec leur <b>pochette d'album</b>.</li>
  <li>Les pochettes sont chargées progressivement en arrière-plan.</li>
  <li>Les <b>favoris</b> (étoile ★) apparaissent en tête de liste.</li>
  <li>Utilisez la barre de recherche pour filtrer par titre, artiste ou album.</li>
</ul>

<h3>Navigation</h3>
<ul>
  <li><b>Double-cliquez</b> sur une chanson pour la jouer — la vue bascule
      automatiquement vers les paroles.</li>
</ul>

<h3>Favoris</h3>
<ul>
  <li>Cliquez sur l'<b>étoile ☆</b> à côté d'une chanson pour la marquer favorite
      (étoile <span style="color:#ffab40">★ orange</span>).</li>
  <li>Les favoris restent toujours en tête de la bibliothèque.</li>
  <li>L'état est sauvegardé dans <code>~/.config/karatagor/library.json</code>.</li>
</ul>

<!-- ═══════════════════════════════════════════ -->
<h2>7. Édition des tags ID3 (panneau droit)</h2>

<h3>Champs disponibles</h3>
<ul>
  <li>Titre, Artiste, Album, Année, Piste, Genre, Commentaire.</li>
  <li>Modifiez les champs puis cliquez sur <b>Sauvegarder Tags</b>.</li>
</ul>

<h3>Pochette d'album</h3>
<ul>
  <li><b>Cliquez</b> sur la zone image pour importer depuis le disque
      (JPG, PNG, WebP, BMP).</li>
  <li><b>Glissez-déposez</b> une image directement sur la zone.</li>
  <li><b>Récupérer la pochette</b> — télécharge automatiquement depuis
      <b>Cover Art Archive</b> (MusicBrainz) ou <b>iTunes</b> en fallback.</li>
</ul>

<h3>Backup et sauvegarde</h3>
<ul>
  <li>Une copie <code>fichier.mp3.bak</code> est créée automatiquement
      avant chaque écriture (désactivable dans <code>config.ini</code>).</li>
</ul>

<h3>Intégration des paroles</h3>
<ul>
  <li>Après une recherche réussie, cliquez sur <b>Intégrer Paroles</b>
      pour écrire les paroles dans le tag <b>USLT</b> et créer le fichier
      <code>.lrc</code> adjacent.</li>
</ul>

<!-- ═══════════════════════════════════════════ -->
<h2>8. Identification acoustique (AcoustID)</h2>

<h3>Prérequis</h3>
<ul>
  <li><code>fpcalc</code> installé :
      <code>sudo apt install libchromaprint-tools</code></li>
  <li>Clé API AcoustID gratuite sur <code>acoustid.org</code>
      (indiquez <code>https://github.com/nouhailler/KaraTagor</code>
      comme URL de projet).</li>
  <li>La clé est demandée au premier usage et sauvegardée dans
      <code>~/.config/karatagor/config.ini</code>.</li>
</ul>

<h3>Workflow</h3>
<ul>
  <li>Cliquez sur <b>Identifier (AcoustID)</b> dans le panneau Tags.</li>
  <li>Une empreinte acoustique est générée via <code>fpcalc</code>.</li>
  <li>AcoustID retourne une liste de correspondances avec score de confiance.</li>
  <li>Sélectionnez la version correcte puis cliquez OK.</li>
  <li>Les métadonnées sont enrichies via <b>MusicBrainz</b>.</li>
  <li>La pochette et les paroles sont récupérées automatiquement.</li>
</ul>

<div class="warn">
  <b>Important — Synchronisation :</b> AcoustID peut proposer plusieurs versions
  (single, album, remaster, live…). Si les paroles ne sont pas en rythme,
  relancez l'identification et choisissez une autre version.
  Chaque version a ses propres timestamps LRC.
</div>

<!-- ═══════════════════════════════════════════ -->
<h2>9. Configuration</h2>
<ul>
  <li>Fichier : <code>~/.config/karatagor/config.ini</code></li>
  <li><code>acoustid_api_key</code> — clé API AcoustID.</li>
  <li><code>default_music_folder</code> — dossier musical par défaut.</li>
  <li><code>backup_enabled</code> — backups avant écriture (<code>true</code>/<code>false</code>).</li>
  <li>Bibliothèque : <code>~/.config/karatagor/library.json</code></li>
  <li>Playlists : <code>~/.config/karatagor/playlists/*.json</code></li>
</ul>

<!-- ═══════════════════════════════════════════ -->
<h2>10. Raccourcis clavier</h2>
<ul>
  <li><span class="key">Ctrl+O</span> — ouvrir un fichier MP3.</li>
  <li><span class="key">Ctrl+L</span> — basculer Bibliothèque / Paroles.</li>
  <li><span class="key">Ctrl+P</span> — gestionnaire de playlists.</li>
  <li><span class="key">F1</span> — afficher cette aide.</li>
  <li><span class="key">Ctrl+Q</span> — quitter.</li>
</ul>

<br>
<p style="color:#445566; font-size:11px; text-align:center;">
  KaraTagor v1.0 — Python / PyQt6 / VLC / mutagen / AcoustID / MusicBrainz / LRCLIB<br>
  <a href="https://github.com/nouhailler/KaraTagor" style="color:#3a6a8a;">
    github.com/nouhailler/KaraTagor
  </a>
</p>

</div>
</body>
</html>
"""


class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("KaraTagor — Aide")
        self.setMinimumSize(720, 580)
        self.resize(760, 640)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setHtml(HELP_HTML)
        browser.setStyleSheet(
            "QTextBrowser { background:#1a1a2e; border:none; }"
            "QScrollBar:vertical { background:#12122a; width:8px; border-radius:4px; }"
            "QScrollBar::handle:vertical { background:#3a3a5a; border-radius:4px; }"
            "QScrollBar::handle:vertical:hover { background:#00d4ff; }"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0; }"
        )
        layout.addWidget(browser)

        btn_bar = QWidget()
        btn_bar.setStyleSheet("background:#12122a; border-top:1px solid #2a2a4a;")
        btn_layout = QHBoxLayout(btn_bar)
        btn_layout.setContentsMargins(12, 8, 12, 8)

        btn_close = QPushButton("Fermer")
        btn_close.setMaximumWidth(100)
        btn_close.clicked.connect(self.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_close)

        layout.addWidget(btn_bar)
