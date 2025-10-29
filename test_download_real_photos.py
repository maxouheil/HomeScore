#!/usr/bin/env python3
"""
Test pour télécharger de vraies photos d'appartement avec le scraper
"""

import asyncio
import os
import aiohttp
from scrape_jinka import JinkaScraper

async def test_real_photos():
    """Teste le téléchargement de vraies photos d'appartement"""
    
    scraper = JinkaScraper()
    await scraper.setup()
    
    # URL de test
    test_url = 'https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=90931157&from=dashboard_card&from_alert_filter=all&from_alert_page=1'
    apartment_id = '90931157'
    
    print('🖼️ TEST TÉLÉCHARGEMENT VRAIES PHOTOS')
    print('=' * 50)
    
    try:
        # Aller sur la page
        await scraper.page.goto(test_url)
        await scraper.page.wait_for_load_state('networkidle')
        
        # Extraire les photos
        photos = await scraper.extract_photos()
        print(f'📸 {len(photos)} photos trouvées')
        
        # Créer le dossier
        photos_dir = f"data/photos/{apartment_id}_real"
        os.makedirs(photos_dir, exist_ok=True)
        
        # Télécharger les 3 premières photos
        async with aiohttp.ClientSession() as session:
            for i, photo in enumerate(photos[:3]):
                url = photo['url']
                filename = f'{photos_dir}/real_photo_{i+1}.jpg'
                
                print(f'📥 Téléchargement photo {i+1}...')
                try:
                    async with session.get(url) as response:
                        if response.status == 200:
                            content = await response.read()
                            with open(filename, 'wb') as f:
                                f.write(content)
                            size = len(content)
                            print(f'✅ Photo {i+1}: {filename} ({size} bytes)')
                        else:
                            print(f'❌ Photo {i+1}: Erreur HTTP {response.status}')
                except Exception as e:
                    print(f'❌ Photo {i+1}: Erreur {e}')
        
        print(f'\n📁 Photos sauvegardées dans: {photos_dir}')
        
    except Exception as e:
        print(f'❌ Erreur: {e}')
    finally:
        await scraper.cleanup()

if __name__ == "__main__":
    asyncio.run(test_real_photos())
