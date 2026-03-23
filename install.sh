#!/bin/bash
set -e

echo "=== KaraTagor — Installation ==="

sudo apt update
sudo apt install -y \
    python3-pip \
    python3-pyqt6 \
    vlc \
    libchromaprint-tools \
    libvlc-dev \
    python3-dev

echo "Installation des dépendances Python..."
pip3 install --break-system-packages -r requirements.txt

echo ""
echo "=== Installation terminée ==="
echo "Lancez l'application avec : python3 main.py"
