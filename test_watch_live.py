#!/usr/bin/env python3
"""
Test en direct du watch avec modification simulée
"""

import subprocess
import time
import os
import signal

def test_watch_live():
    """Test le watch en action"""
    print("🧪 TEST EN DIRECT DU WATCH")
    print("=" * 60)
    
    # Lancer le watch en arrière-plan
    print("\n1️⃣  Lancement du watch...")
    process = subprocess.Popen(
        ['python', 'watch_scorecard.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    print("   ✅ Watch lancé (PID:", process.pid, ")")
    print("   ⏳ Attente de 3 secondes pour l'initialisation...")
    time.sleep(3)
    
    # Modifier un fichier
    print("\n2️⃣  Modification du fichier generate_scorecard_html.py...")
    test_file = 'generate_scorecard_html.py'
    if os.path.exists(test_file):
        original_mtime = os.path.getmtime(test_file)
        time.sleep(0.1)
        
        # Toucher le fichier pour simuler une modification
        os.utime(test_file, None)
        print("   ✅ Fichier modifié")
        
        # Attendre que le watch détecte et régénère
        print("\n3️⃣  Attente de la détection et régénération (5 secondes)...")
        time.sleep(5)
        
        # Lire la sortie du processus
        try:
            # Essayer de lire ce qui a été capturé
            process.poll()
            if process.returncode is None:
                print("   ℹ️  Le watch tourne toujours (normal)")
            else:
                output = process.stdout.read()
                if output:
                    print("\n📝 Sortie du watch:")
                    print(output)
        except:
            pass
        
        # Restaurer le mtime original
        os.utime(test_file, (original_mtime, original_mtime))
        print("\n   ✅ Fichier restauré")
    
    # Arrêter le processus
    print("\n4️⃣  Arrêt du watch...")
    try:
        process.terminate()
        process.wait(timeout=2)
        print("   ✅ Watch arrêté proprement")
    except:
        process.kill()
        print("   ⚠️  Watch arrêté forcément")
    
    print("\n" + "=" * 60)
    print("✅ Test terminé!")
    print("\n💡 Pour tester vous-même:")
    print("   1. Lancez: python watch_scorecard.py")
    print("   2. Dans un autre terminal, modifiez un fichier")
    print("   3. Regardez le watch régénérer automatiquement!")

if __name__ == "__main__":
    test_watch_live()










