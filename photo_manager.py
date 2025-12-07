#!/usr/bin/env python3
"""
Gestionnaire de photos pour HomeScore v2
Télécharge les photos en local et les utilise pour les analyses
"""

import os
import requests
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import urlparse
import hashlib


class PhotoManager:
    """Gestionnaire de téléchargement et stockage des photos"""
    
    def __init__(self, base_dir: str = "data/photos"):
        """
        Initialise le gestionnaire de photos
        
        Args:
            base_dir: Répertoire de base pour stocker les photos
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def get_photo_filename(self, url: str, index: int) -> str:
        """
        Génère un nom de fichier unique pour une photo
        
        Args:
            url: URL de la photo
            index: Index de la photo (1, 2, 3...)
        
        Returns:
            Nom de fichier (ex: photo_1_abc123.jpg)
        """
        # Créer un hash de l'URL pour éviter les doublons
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        
        # Extraire l'extension depuis l'URL ou utiliser .jpg par défaut
        parsed = urlparse(url)
        ext = Path(parsed.path).suffix or '.jpg'
        if ext not in ['.jpg', '.jpeg', '.png', '.webp']:
            ext = '.jpg'
        
        return f"photo_{index}_{url_hash}{ext}"
    
    def download_photo(self, url: str, local_path: Path, timeout: int = 30) -> bool:
        """
        Télécharge une photo depuis une URL
        
        Args:
            url: URL de la photo
            local_path: Chemin local où sauvegarder
            timeout: Timeout en secondes
        
        Returns:
            True si succès, False sinon
        """
        try:
            response = requests.get(url, timeout=timeout, stream=True)
            if response.status_code == 200:
                with open(local_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                return True
            else:
                print(f"   ⚠️  Erreur HTTP {response.status_code} pour {url[:60]}...")
                return False
        except Exception as e:
            print(f"   ⚠️  Erreur téléchargement {url[:60]}...: {e}")
            return False
    
    def download_apartment_photos(
        self, 
        apartment_data: Dict, 
        max_photos: int = 10,
        force_redownload: bool = False
    ) -> Dict:
        """
        Télécharge les photos d'un appartement en local
        
        Args:
            apartment_data: Données de l'appartement (avec photos)
            max_photos: Nombre maximum de photos à télécharger
            force_redownload: Forcer le re-téléchargement même si déjà présent
        
        Returns:
            Données de l'appartement avec local_path ajouté aux photos
        """
        apartment_id = apartment_data.get('id')
        if not apartment_id:
            return apartment_data
        
        photos = apartment_data.get('photos', [])
        if not photos:
            return apartment_data
        
        # Créer le dossier pour cet appartement
        apartment_dir = self.base_dir / str(apartment_id)
        apartment_dir.mkdir(parents=True, exist_ok=True)
        
        downloaded_photos = []
        downloaded_count = 0
        skipped_count = 0
        
        for i, photo in enumerate(photos[:max_photos], 1):
            if isinstance(photo, str):
                url = photo
                alt = f"Photo {i}"
            else:
                url = photo.get('url')
                alt = photo.get('alt', f"Photo {i}")
            
            if not url:
                continue
            
            # Générer le nom de fichier
            filename = self.get_photo_filename(url, i)
            local_path = apartment_dir / filename
            
            # Préparer les données de la photo
            if isinstance(photo, dict):
                photo_data = photo.copy()
            else:
                photo_data = {'url': photo}
            
            # Vérifier si déjà téléchargée
            if local_path.exists() and not force_redownload:
                skipped_count += 1
                photo_data.update({
                    'local_path': str(local_path),
                    'alt': alt,
                    'downloaded': False  # Déjà présente
                })
                downloaded_photos.append(photo_data)
                continue
            
            # Télécharger la photo
            print(f"   📥 Photo {i}/{min(len(photos), max_photos)}: {url[:60]}...")
            if self.download_photo(url, local_path):
                downloaded_count += 1
                photo_data.update({
                    'local_path': str(local_path),
                    'alt': alt,
                    'downloaded': True
                })
                downloaded_photos.append(photo_data)
                print(f"      ✅ Sauvegardée: {local_path}")
            else:
                # Même en cas d'échec, garder l'URL originale
                photo_data.update({
                    'alt': alt,
                    'downloaded': False,
                    'error': True
                })
                downloaded_photos.append(photo_data)
        
        # Mettre à jour les données de l'appartement
        apartment_data['photos'] = downloaded_photos
        
        if downloaded_count > 0 or skipped_count > 0:
            print(f"   📊 {downloaded_count} téléchargées, {skipped_count} déjà présentes")
        
        return apartment_data
    
    def get_photo_path(self, photo: Dict) -> Optional[str]:
        """
        Retourne le chemin local d'une photo si disponible, sinon None
        
        Args:
            photo: Dictionnaire photo avec 'local_path' ou 'url'
        
        Returns:
            Chemin local ou None
        """
        local_path = photo.get('local_path')
        if local_path and Path(local_path).exists():
            return local_path
        return None
    
    def get_photo_url_or_path(self, photo: Dict) -> str:
        """
        Retourne le chemin local si disponible, sinon l'URL
        
        Args:
            photo: Dictionnaire photo
        
        Returns:
            Chemin local ou URL
        """
        local_path = self.get_photo_path(photo)
        if local_path:
            return local_path
        return photo.get('url', '')
    
    def load_photo_for_analysis(self, photo: Dict) -> Optional[bytes]:
        """
        Charge une photo depuis le chemin local ou télécharge depuis l'URL
        
        Args:
            photo: Dictionnaire photo
        
        Returns:
            Contenu binaire de l'image ou None
        """
        # Essayer le chemin local d'abord
        local_path = self.get_photo_path(photo)
        if local_path:
            try:
                with open(local_path, 'rb') as f:
                    return f.read()
            except Exception as e:
                print(f"   ⚠️  Erreur lecture {local_path}: {e}")
        
        # Fallback : télécharger depuis l'URL
        url = photo.get('url')
        if url:
            try:
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    return response.content
            except Exception as e:
                print(f"   ⚠️  Erreur téléchargement {url[:60]}...: {e}")
        
        return None


def download_photos_for_apartments(apartments: List[Dict], max_photos: int = 10) -> List[Dict]:
    """
    Télécharge les photos pour une liste d'appartements
    
    Args:
        apartments: Liste des appartements
        max_photos: Nombre maximum de photos par appartement
    
    Returns:
        Liste des appartements avec photos téléchargées
    """
    manager = PhotoManager()
    
    print(f"📸 Téléchargement des photos pour {len(apartments)} appartements...")
    
    for i, apartment in enumerate(apartments, 1):
        apartment_id = apartment.get('id', 'unknown')
        print(f"\n🏠 Appartement {i}/{len(apartments)}: {apartment_id}")
        apartment = manager.download_apartment_photos(apartment, max_photos=max_photos)
        apartments[i-1] = apartment
    
    print(f"\n✅ Téléchargement terminé")
    return apartments


if __name__ == "__main__":
    """Test du gestionnaire de photos"""
    from data_loader import load_apartments
    
    print("🧪 TEST DU GESTIONNAIRE DE PHOTOS")
    print("=" * 60)
    
    # Charger un appartement
    apartments = load_apartments(prefer_api=True)
    if apartments:
        test_apt = apartments[0]
        print(f"\n📋 Test avec appartement: {test_apt.get('id')}")
        print(f"   Photos disponibles: {len(test_apt.get('photos', []))}")
        
        # Télécharger les photos
        manager = PhotoManager()
        test_apt = manager.download_apartment_photos(test_apt, max_photos=3)
        
        print(f"\n✅ Photos téléchargées:")
        for photo in test_apt.get('photos', [])[:3]:
            local_path = photo.get('local_path')
            if local_path:
                exists = Path(local_path).exists()
                print(f"   {'✅' if exists else '❌'} {local_path}")
    else:
        print("❌ Aucun appartement trouvé")

