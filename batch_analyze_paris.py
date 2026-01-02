#!/usr/bin/env python3
"""
Script de batch processing pour analyser tous les appartements Paris avec optimisations
- Vérification du cache avant analyse
- Batch processing avec rate limiting
- Retry automatique en cas d'erreur
- Skip des appartements déjà analysés
"""

import asyncio
import json
import os
import time
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from analyze_apartment_unified import UnifiedApartmentAnalyzer
from data_loader import load_apartments


class BatchAnalyzer:
    """Analyseur par batch avec optimisations de coût"""
    
    def __init__(self, batch_size: int = 50, delay_between_batches: float = 1.0):
        """
        Args:
            batch_size: Nombre d'appartements à traiter par batch
            delay_between_batches: Délai en secondes entre les batches (rate limiting)
        """
        self.batch_size = batch_size
        self.delay_between_batches = delay_between_batches
        self.analyzer = UnifiedApartmentAnalyzer()
        self.stats = {
            'total': 0,
            'analyzed': 0,
            'cached': 0,
            'skipped': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }
    
    def should_analyze_apartment(self, apartment: Dict) -> bool:
        """
        Détermine si un appartement doit être analysé
        
        Returns:
            True si l'appartement doit être analysé, False sinon
        """
        apartment_id = apartment.get('id', 'unknown')
        
        # OPTIMISATION 1: Vérifier si déjà analysé dans les données
        if apartment.get('_analysis_data') or apartment.get('style_analysis'):
            print(f"   ⏭️  {apartment_id}: Déjà analysé (skip)")
            self.stats['skipped'] += 1
            return False
        
        # OPTIMISATION 2: Vérifier si pas de photos
        photos = apartment.get('photos', [])
        if not photos:
            print(f"   ⏭️  {apartment_id}: Pas de photos (skip)")
            self.stats['skipped'] += 1
            return False
        
        return True
    
    async def analyze_apartment_with_retry(
        self, 
        apartment: Dict, 
        max_retries: int = 3,
        retry_delay: float = 2.0
    ) -> Optional[Dict]:
        """
        Analyse un appartement avec retry automatique
        
        Args:
            apartment: Données de l'appartement
            max_retries: Nombre maximum de tentatives
            retry_delay: Délai entre les tentatives (secondes)
        
        Returns:
            Résultat de l'analyse ou None en cas d'échec
        """
        apartment_id = apartment.get('id', 'unknown')
        
        for attempt in range(max_retries):
            try:
                # Vérifier le cache avant analyse (déjà fait dans analyze_apartment_unified)
                # Analyse jusqu'à 7 photos pour une meilleure couverture des critères
                result = self.analyzer.analyze_apartment_unified(apartment, max_photos=7)
                
                if result:
                    self.stats['analyzed'] += 1
                    return result
                else:
                    # Si None retourné, c'est peut-être un cache hit (déjà compté)
                    # Vérifier si c'était un cache hit ou une erreur
                    if attempt == 0:
                        # Première tentative, peut être un cache hit
                        self.stats['cached'] += 1
                    return None
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)  # Backoff exponentiel
                    print(f"   ⚠️  {apartment_id}: Erreur (tentative {attempt + 1}/{max_retries}): {e}")
                    print(f"      Retry dans {wait_time:.1f}s...")
                    await asyncio.sleep(wait_time)
                else:
                    print(f"   ❌ {apartment_id}: Échec après {max_retries} tentatives: {e}")
                    self.stats['errors'] += 1
                    return None
        
        return None
    
    async def analyze_batch(self, apartments: List[Dict]) -> List[Dict]:
        """
        Analyse un batch d'appartements
        
        Args:
            apartments: Liste des appartements à analyser
        
        Returns:
            Liste des résultats d'analyse
        """
        results = []
        
        for i, apartment in enumerate(apartments, 1):
            apartment_id = apartment.get('id', 'unknown')
            print(f"\n[{i}/{len(apartments)}] Appartement {apartment_id}")
            
            # Vérifier si doit être analysé
            if not self.should_analyze_apartment(apartment):
                continue
            
            # Analyser avec retry
            result = await self.analyze_apartment_with_retry(apartment)
            
            if result:
                # Ajouter le résultat aux données de l'appartement
                apartment['_analysis_data'] = result
                apartment['style_analysis'] = result  # Compatibilité
                results.append(apartment)
            
            # Petit délai entre chaque appartement pour éviter rate limiting
            await asyncio.sleep(0.1)
        
        return results
    
    async def analyze_all_apartments(self, apartments: List[Dict]) -> List[Dict]:
        """
        Analyse tous les appartements par batch
        
        Args:
            apartments: Liste complète des appartements
        
        Returns:
            Liste des appartements avec analyses ajoutées
        """
        self.stats['start_time'] = datetime.now()
        self.stats['total'] = len(apartments)
        
        print("🚀 BATCH ANALYZER - Analyse Optimisée")
        print("=" * 60)
        print(f"📊 Total appartements: {self.stats['total']}")
        print(f"📦 Taille batch: {self.batch_size}")
        print(f"⏱️  Délai entre batches: {self.delay_between_batches}s")
        print(f"📸 Photos par appartement: 3 (optimisé)")
        print()
        
        all_results = []
        total_batches = (len(apartments) + self.batch_size - 1) // self.batch_size
        
        for batch_num in range(total_batches):
            start_idx = batch_num * self.batch_size
            end_idx = min(start_idx + self.batch_size, len(apartments))
            batch = apartments[start_idx:end_idx]
            
            print(f"\n📦 BATCH {batch_num + 1}/{total_batches}")
            print("-" * 60)
            
            batch_results = await self.analyze_batch(batch)
            all_results.extend(batch_results)
            
            # Délai entre batches (sauf pour le dernier)
            if batch_num < total_batches - 1:
                print(f"\n⏳ Pause de {self.delay_between_batches}s avant le prochain batch...")
                await asyncio.sleep(self.delay_between_batches)
        
        self.stats['end_time'] = datetime.now()
        return all_results
    
    def print_stats(self):
        """Affiche les statistiques de l'analyse"""
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds() if self.stats['end_time'] else 0
        
        print("\n" + "=" * 60)
        print("📊 STATISTIQUES FINALES")
        print("=" * 60)
        print(f"Total appartements: {self.stats['total']}")
        print(f"✅ Analysés (nouveaux): {self.stats['analyzed']}")
        print(f"💾 Cache hits: {self.stats['cached']}")
        print(f"⏭️  Skippés (déjà analysés/pas de photos): {self.stats['skipped']}")
        print(f"❌ Erreurs: {self.stats['errors']}")
        print(f"⏱️  Durée totale: {duration:.1f}s")
        
        if self.stats['analyzed'] > 0:
            avg_time = duration / self.stats['analyzed']
            print(f"⚡ Temps moyen par analyse: {avg_time:.1f}s")
        
        # Estimation des coûts
        cost_per_apt = 0.00037  # €0.00037 par appartement (3 photos)
        total_cost = self.stats['analyzed'] * cost_per_apt
        print(f"\n💰 ESTIMATION COÛTS")
        print(f"Coût par appartement: €{cost_per_apt:.5f}")
        print(f"Total analysés: {self.stats['analyzed']}")
        print(f"💰 Coût total estimé: €{total_cost:.2f}")


async def main():
    """Fonction principale"""
    print("🏙️  ANALYSE BATCH - TOUS LES APPARTEMENTS PARIS")
    print("=" * 60)
    
    # Charger les appartements
    print("\n📥 Chargement des appartements...")
    apartments = load_apartments(prefer_api=True)
    
    if not apartments:
        print("❌ Aucun appartement trouvé")
        return
    
    print(f"✅ {len(apartments)} appartements chargés")
    
    # Filtrer seulement Paris (si nécessaire)
    paris_apartments = []
    for apt in apartments:
        localisation = apt.get('localisation', '').lower()
        postal_code = apt.get('_api_data', {}).get('postal_code', '')
        
        # Filtrer Paris (75xxx)
        if 'paris' in localisation or (postal_code and postal_code.startswith('75')):
            paris_apartments.append(apt)
    
    print(f"🏙️  {len(paris_apartments)} appartements Paris trouvés")
    
    if not paris_apartments:
        print("❌ Aucun appartement Paris trouvé")
        return
    
    # Créer l'analyseur batch
    batch_analyzer = BatchAnalyzer(
        batch_size=50,  # 50 appartements par batch
        delay_between_batches=1.0  # 1 seconde entre batches
    )
    
    # Analyser tous les appartements
    analyzed_apartments = await batch_analyzer.analyze_all_apartments(paris_apartments)
    
    # Afficher les statistiques
    batch_analyzer.print_stats()
    
    # Sauvegarder les résultats
    if analyzed_apartments:
        output_file = 'data/paris_apartments_analyzed.json'
        os.makedirs('data', exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analyzed_apartments, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n💾 Résultats sauvegardés: {output_file}")
        print(f"   {len(analyzed_apartments)} appartements avec analyses")


if __name__ == "__main__":
    asyncio.run(main())



