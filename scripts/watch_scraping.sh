#!/bin/bash
# Script pour surveiller le scraping et donner des updates

echo "🔍 SURVEILLANCE DU SCRAPING PARIS"
echo "Appuyez sur Ctrl+C pour arrêter la surveillance"
echo ""

while true; do
    clear
    python scripts/check_scraping_progress.py
    echo ""
    echo "⏳ Prochaine mise à jour dans 30 secondes..."
    sleep 30
done



