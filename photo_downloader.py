#!/usr/bin/env python3
"""
Module pour télécharger et stocker les photos des appartements
"""

import os
import requests
import time
import hashlib
from pathlib import Path
from typing import List, Dict, Optional
from config_jinka import (
    PHOTOS_DIR,
    PHOTO_DOWNLOAD_TIMEOUT,
    PHOTO_DOWNLOAD_RETRIES,
    PHOTO_DOWNLOAD_DELAY
)


class PhotoDownloader:
    """Gestionnaire de téléchargement de photos"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        })
    
    def _get_file_hash(self, file_path: Path) -> Optional[str]:
        """Calcule le hash MD5 d'un fichier"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return None
    
    def _download_photo(self, url: str, destination: Path) -> bool:
        """
        Télécharge une photo depuis une URL
        
        Args:
            url: URL de la photo
            destination: Chemin de destination
            
        Returns:
            True si le téléchargement a réussi, False sinon
        """
        # Vérifier si le fichier existe déjà
        if destination.exists():
            print(f"   ⏭️  Photo déjà téléchargée: {destination.name}")
            return True
        
        for attempt in range(PHOTO_DOWNLOAD_RETRIES):
            try:
                response = self.session.get(
                    url,
                    timeout=PHOTO_DOWNLOAD_TIMEOUT,
                    stream=True
                )
                response.raise_for_status()
                
                # Créer le répertoire si nécessaire
                destination.parent.mkdir(parents=True, exist_ok=True)
                
                # Télécharger le fichier
                with open(destination, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                # Vérifier que le fichier n'est pas vide
                if destination.stat().st_size == 0:
                    destination.unlink()
                    raise ValueError("Fichier vide")
                
                return True
                
            except Exception as e:
                print(f"   ⚠️  Erreur lors du téléchargement (tentative {attempt + 1}/{PHOTO_DOWNLOAD_RETRIES}): {e}")
                if attempt < PHOTO_DOWNLOAD_RETRIES - 1:
                    time.sleep(PHOTO_DOWNLOAD_DELAY * (attempt + 1))
                else:
                    print(f"   ❌ Échec du téléchargement après {PHOTO_DOWNLOAD_RETRIES} tentatives")
                    return False
        
        return False
    
    def download_apartment_photos(
        self,
        apartment_id: str,
        photo_urls: List[str],
        base_dir: Optional[Path] = None
    ) -> List[Dict[str, str]]:
        """
        Télécharge toutes les photos d'un appartement
        
        Args:
            apartment_id: ID de l'appartement
            photo_urls: Liste des URLs des photos
            base_dir: Répertoire de base (par défaut PHOTOS_DIR)
            
        Returns:
            Liste de dictionnaires avec 'url' et 'local_path' pour chaque photo
        """
        if base_dir is None:
            base_dir = PHOTOS_DIR
        
        apartment_dir = base_dir / apartment_id
        apartment_dir.mkdir(parents=True, exist_ok=True)
        
        downloaded_photos = []
        
        print(f"📸 Téléchargement de {len(photo_urls)} photo(s) pour l'appartement {apartment_id}...")
        
        for index, url in enumerate(photo_urls):
            if not url or not isinstance(url, str):
                continue
            
            # Déterminer l'extension du fichier
            extension = '.jpg'  # Par défaut
            if '.' in url:
                ext = url.split('.')[-1].split('?')[0].lower()
                if ext in ['jpg', 'jpeg', 'png', 'webp']:
                    extension = f'.{ext}'
            
            filename = f"{apartment_id}_{index}{extension}"
            destination = apartment_dir / filename
            
            # Télécharger la photo
            if self._download_photo(url, destination):
                # Chemin relatif depuis le répertoire du projet
                relative_path = f"data/photos/{apartment_id}/{filename}"
                downloaded_photos.append({
                    'url': url,
                    'local_path': relative_path
                })
                print(f"   ✅ Photo {index + 1}/{len(photo_urls)} téléchargée")
            else:
                # Même en cas d'échec, on garde l'URL pour référence
                downloaded_photos.append({
                    'url': url,
                    'local_path': None
                })
            
            # Délai entre les téléchargements
            if index < len(photo_urls) - 1:
                time.sleep(PHOTO_DOWNLOAD_DELAY)
        
        print(f"✅ {len([p for p in downloaded_photos if p.get('local_path')])}/{len(photo_urls)} photo(s) téléchargée(s)")
        
        return downloaded_photos


def main():
    """Test du téléchargeur de photos"""
    downloader = PhotoDownloader()
    
    # Test avec une URL de photo exemple
    test_urls = [
        "https://res.cloudinary.com/loueragile/image/upload/v1653311807/web/jinka/Logo-Jinka-a.svg"
    ]
    
    print("=" * 80)
    print("🔍 TEST DU TÉLÉCHARGEUR DE PHOTOS")
    print("=" * 80)
    print()
    
    results = downloader.download_apartment_photos("test_123", test_urls)
    print()
    print("Résultats:")
    for result in results:
        print(f"  URL: {result['url']}")
        print(f"  Local: {result.get('local_path', 'N/A')}")
        print()


if __name__ == "__main__":
    main()

