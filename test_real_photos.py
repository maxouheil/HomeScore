#!/usr/bin/env python3
"""
Test pour télécharger de vraies photos d'appartement
"""

import asyncio
import aiohttp
import os

async def download_test_photos():
    """Télécharge quelques photos de test pour vérifier leur contenu"""
    
    # URLs des photos trouvées
    test_photos = [
        "https://loueragile-media.s3.eu-west-3.amazonaws.com/upload_pro_ad/42f489c1-625e-4c8a-9b8a-8f8f8f8f8f8f.jpg",
        "https://loueragile-media.s3.eu-west-3.amazonaws.com/upload_pro_ad/1131ac6e-e19f-4c8a-9b8a-8f8f8f8f8f8f.jpg",
        "https://loueragile-media.s3.eu-west-3.amazonaws.com/upload_pro_ad/75e310f1-1168-4c8a-9b8a-8f8f8f8f8f8f.jpg"
    ]
    
    # Créer le dossier de test
    os.makedirs("data/photos/test_real", exist_ok=True)
    
    async with aiohttp.ClientSession() as session:
        for i, url in enumerate(test_photos):
            try:
                print(f"📸 Téléchargement photo {i+1}...")
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.read()
                        filename = f"data/photos/test_real/photo_{i+1}.jpg"
                        with open(filename, 'wb') as f:
                            f.write(content)
                        print(f"✅ Photo {i+1} téléchargée: {len(content)} bytes")
                    else:
                        print(f"❌ Erreur {response.status} pour photo {i+1}")
            except Exception as e:
                print(f"❌ Erreur téléchargement photo {i+1}: {e}")

if __name__ == "__main__":
    asyncio.run(download_test_photos())
