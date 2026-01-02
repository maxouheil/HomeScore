#!/usr/bin/env python3
"""
Configuration pour la récupération des appartements Jinka
"""

import os
from pathlib import Path
from project_config import (
    PROJECT_ROOT,
    DATA_DIR,
    PHOTOS_DIR,
    SCORES_DIR,
    APARTMENTS_FILE,
    JINKA_APARTMENTS_FILE
)

# Token de l'alerte Jinka
JINKA_ALERT_TOKEN = "26c2ec3064303aa68ffa43f7c6518733"

# URL de base de l'API Jinka
JINKA_API_BASE_URL = "https://api.jinka.fr/apiv2"

# URL du dashboard (pour référence)
JINKA_DASHBOARD_URL = f"https://www.jinka.fr/asrenter/alert/dashboard/{JINKA_ALERT_TOKEN}"

# Les chemins de stockage sont maintenant définis dans project_config.py
# DATA_DIR, PHOTOS_DIR, SCORES_DIR, APARTMENTS_FILE, JINKA_APARTMENTS_FILE
# sont importés depuis project_config.py pour garantir qu'ils pointent vers
# /Users/sou/Desktop/CURSOR/HomeScore

# Configuration pour les téléchargements
PHOTO_DOWNLOAD_TIMEOUT = 30  # secondes
PHOTO_DOWNLOAD_RETRIES = 3
PHOTO_DOWNLOAD_DELAY = 1  # secondes entre les téléchargements

# Configuration pour les requêtes API
API_REQUEST_TIMEOUT = 30  # secondes
API_REQUEST_RETRIES = 3
API_REQUEST_DELAY = 0.5  # secondes entre les requêtes

