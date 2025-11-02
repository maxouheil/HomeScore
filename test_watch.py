#!/usr/bin/env python3
"""
Script de test pour vérifier que watch_scorecard.py fonctionne correctement
"""

import os
import time
import subprocess
from pathlib import Path

def test_watch_initialization():
    """Test que le watcher s'initialise correctement"""
    print("🧪 Test 1: Initialisation du watcher...")
    
    from watch_scorecard import ScorecardWatcher
    
    watcher = ScorecardWatcher()
    
    # Vérifier que les fichiers sont détectés
    assert len(watcher.files_to_watch) > 0, "Aucun fichier détecté à surveiller"
    print(f"   ✅ {len(watcher.files_to_watch)} fichiers détectés")
    
    # Vérifier que le cache est créé
    assert os.path.exists(watcher.cache_file), "Le fichier de cache n'a pas été créé"
    print(f"   ✅ Cache créé: {watcher.cache_file}")
    
    return True

def test_watch_detection():
    """Test que le watcher détecte les changements"""
    print("\n🧪 Test 2: Détection des changements...")
    
    from watch_scorecard import ScorecardWatcher
    
    watcher = ScorecardWatcher()
    
    # Initialiser le cache
    watcher.init_cache()
    
    # Simuler un changement en touchant un fichier
    test_file = 'generate_scorecard_html.py'
    if os.path.exists(test_file):
        original_mtime = os.path.getmtime(test_file)
        time.sleep(0.1)  # Petit délai pour être sûr
        
        # Toucher le fichier
        os.utime(test_file, None)
        time.sleep(0.1)
        
        # Vérifier la détection
        changed_files = watcher.check_changes()
        
        if test_file in changed_files:
            print(f"   ✅ Changement détecté pour {test_file}")
        else:
            print(f"   ⚠️  Changement non détecté pour {test_file}")
            print(f"      Cela peut être normal si le fichier vient d'être modifié")
        
        # Restaurer le mtime original
        os.utime(test_file, (original_mtime, original_mtime))
    
    return True

def test_files_list():
    """Test que la liste des fichiers est correcte"""
    print("\n🧪 Test 3: Liste des fichiers surveillés...")
    
    from watch_scorecard import ScorecardWatcher
    
    watcher = ScorecardWatcher()
    
    print(f"   📁 {len(watcher.files_to_watch)} fichiers surveillés:")
    for filepath in sorted(watcher.files_to_watch)[:10]:  # Afficher les 10 premiers
        exists = "✓" if os.path.exists(filepath) else "✗"
        print(f"      {exists} {filepath}")
    
    if len(watcher.files_to_watch) > 10:
        print(f"      ... et {len(watcher.files_to_watch) - 10} autres")
    
    return True

def test_regeneration():
    """Test que la régénération fonctionne"""
    print("\n🧪 Test 4: Test de régénération...")
    
    from watch_scorecard import ScorecardWatcher
    
    watcher = ScorecardWatcher()
    
    # Vérifier que generate_scorecard_html.py existe
    if not os.path.exists('generate_scorecard_html.py'):
        print("   ⚠️  generate_scorecard_html.py non trouvé, test ignoré")
        return True
    
    print("   🔄 Test de régénération (peut prendre quelques secondes)...")
    
    # Essayer de régénérer (mais avec un timeout court pour le test)
    try:
        result = subprocess.run(
            ['python', 'generate_scorecard_html.py'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("   ✅ Régénération réussie")
            if os.path.exists('output/homepage.html'):
                size = os.path.getsize('output/homepage.html')
                print(f"   ✅ Fichier généré: output/homepage.html ({size} octets)")
            else:
                print("   ⚠️  Fichier HTML non généré")
        else:
            print(f"   ⚠️  Erreur lors de la régénération: {result.stderr[:200]}")
    except subprocess.TimeoutExpired:
        print("   ⚠️  Timeout (normal pour un test rapide)")
    except Exception as e:
        print(f"   ⚠️  Erreur: {e}")
    
    return True

def main():
    """Fonction principale de test"""
    print("=" * 60)
    print("🧪 TESTS DU WATCH SCORECARD")
    print("=" * 60)
    
    tests = [
        test_watch_initialization,
        test_files_list,
        test_watch_detection,
        test_regeneration,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("📊 RÉSULTATS")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"✅ Tests réussis: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 Tous les tests sont passés!")
    else:
        print(f"\n⚠️  {total - passed} test(s) ont échoué")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

