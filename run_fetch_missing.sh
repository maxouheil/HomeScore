#!/bin/bash
# Script wrapper pour récupérer les annonces manquantes
# Usage: ./run_fetch_missing.sh [max_missing]

cd "$(dirname "$0")"

# Récupérer le nombre max d'appartements si fourni
MAX_MISSING=${1:-}

# Exécuter le script Python
if [ -z "$MAX_MISSING" ]; then
    python3 fetch_missing_from_dashboard.py
else
    python3 fetch_missing_from_dashboard.py "$MAX_MISSING"
fi

EXIT_CODE=$?

# Notification macOS (optionnel - décommentez si vous voulez)
# if [ $EXIT_CODE -eq 0 ]; then
#     osascript -e 'display notification "Récupération terminée avec succès" with title "HomeScore"'
# else
#     osascript -e 'display notification "Erreur lors de la récupération" with title "HomeScore"'
# fi

exit $EXIT_CODE

