#!/usr/bin/env python3
"""
Configuration centralisée du projet HomeScore
TOUJOURS utiliser PROJECT_ROOT pour tous les chemins de fichiers
"""

from pathlib import Path
import os
import warnings

# ⚠️ RÈGLE IMPORTANTE : TOUJOURS utiliser ce répertoire de base
# Ne JAMAIS utiliser Path(__file__).parent pour les chemins de données
# Utiliser le répertoire de travail actuel ou détecter automatiquement
import os
_cwd = Path(os.getcwd())
# Si on est dans le projet, utiliser le cwd, sinon utiliser le chemin absolu
if (_cwd / 'data' / 'scores').exists():
    PROJECT_ROOT = _cwd
else:
    # Fallback: utiliser le chemin absolu
    PROJECT_ROOT = Path('/Users/sou/Desktop/CURSOR/HomeScore')

# Vérifier que le répertoire existe, le créer si nécessaire
if not PROJECT_ROOT.exists():
    PROJECT_ROOT.mkdir(parents=True, exist_ok=True)
    print(f"⚠️  Répertoire créé: {PROJECT_ROOT}")

# Chemins standardisés (tous relatifs à PROJECT_ROOT)
DATA_DIR = PROJECT_ROOT / "data"
PHOTOS_DIR = DATA_DIR / "photos"
SCORES_DIR = DATA_DIR / "scores"
OUTPUT_DIR = PROJECT_ROOT / "output"
LOGS_DIR = PROJECT_ROOT / "logs"

# Fichiers principaux
APARTMENTS_FILE = SCORES_DIR / "all_apartments_scores.json"
JINKA_APARTMENTS_FILE = DATA_DIR / "jinka_apartments.json"

# Créer les répertoires si nécessaire
for directory in [DATA_DIR, PHOTOS_DIR, SCORES_DIR, OUTPUT_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


def validate_path(file_path: Path) -> bool:
    """
    Valide qu'un chemin de fichier est dans PROJECT_ROOT ou ses sous-répertoires
    
    Args:
        file_path: Chemin à valider
        
    Returns:
        True si le chemin est valide, False sinon
    """
    try:
        # Convertir en Path si nécessaire
        if isinstance(file_path, str):
            file_path = Path(file_path)
        
        # Résoudre le chemin absolu
        abs_path = file_path.resolve()
        abs_project_root = PROJECT_ROOT.resolve()
        
        # Vérifier que le fichier est dans PROJECT_ROOT
        try:
            abs_path.relative_to(abs_project_root)
            return True
        except ValueError:
            # Le fichier n'est pas dans PROJECT_ROOT
            warnings.warn(
                f"⚠️  ATTENTION: Fichier créé en dehors de PROJECT_ROOT:\n"
                f"   Fichier: {abs_path}\n"
                f"   PROJECT_ROOT: {abs_project_root}\n"
                f"   Utilisez PROJECT_ROOT pour tous les chemins de fichiers!",
                UserWarning
            )
            return False
    except Exception as e:
        warnings.warn(f"Erreur lors de la validation du chemin {file_path}: {e}")
        return False


def get_project_path(relative_path: str) -> Path:
    """
    Retourne un chemin absolu relatif à PROJECT_ROOT
    
    Args:
        relative_path: Chemin relatif (ex: "data/scores/file.json")
        
    Returns:
        Path absolu dans PROJECT_ROOT
    """
    return PROJECT_ROOT / relative_path


# Afficher un message au chargement du module pour rappel
if __name__ != "__main__":
    # Ne pas afficher en mode import pour éviter le spam
    pass

