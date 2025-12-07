#!/usr/bin/env python3
"""
Script de test pour l'extraction des données d'un appartement spécifique
"""

import asyncio
import json
import re
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()

async def test_apartment_extraction():
    """Test l'extraction des données d'un appartement spécifique"""
    
    apartment_url = "https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad=90931157&from=dashboard_card&from_alert_filter=all&from_alert_page=1"
    
    print(f"🔍 Test d'extraction pour: {apartment_url}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # Aller sur la page de l'appartement
            await page.goto(apartment_url)
            await page.wait_for_load_state('networkidle')
            await page.wait_for_timeout(3000)
            
            print("\n" + "="*60)
            print("📊 EXTRACTION DES DONNÉES")
            print("="*60)
            
            # 1. PRIX - Facile
            print("\n💰 PRIX:")
            try:
                # Essayer différents sélecteurs pour le prix
                price_selectors = [
                    '.hmmXKG',
                    '[class*="price"]',
                    'text=/\\d+\\s*€/',
                    'h1:has-text("€")',
                    'h2:has-text("€")'
                ]
                
                prix_trouve = False
                for selector in price_selectors:
                    try:
                        element = page.locator(selector).first
                        if await element.count() > 0:
                            text = await element.text_content()
                            if text and '€' in text:
                                print(f"   ✅ Sélecteur '{selector}': {text.strip()}")
                                prix_trouve = True
                                break
                    except:
                        continue
                
                if not prix_trouve:
                    print("   ❌ Prix non trouvé")
                    
            except Exception as e:
                print(f"   ❌ Erreur prix: {e}")
            
            # 2. TAILLE - Facile
            print("\n📐 TAILLE:")
            try:
                # Chercher la surface dans différents formats
                surface_patterns = [
                    r'(\d+)\s*m²',
                    r'(\d+)\s*m2',
                    r'(\d+)\s*mètres? carrés?'
                ]
                
                surface_trouvee = False
                page_content = await page.content()
                
                for pattern in surface_patterns:
                    matches = re.findall(pattern, page_content, re.IGNORECASE)
                    if matches:
                        print(f"   ✅ Pattern '{pattern}': {matches[0]} m²")
                        surface_trouvee = True
                        break
                
                if not surface_trouvee:
                    print("   ❌ Surface non trouvée")
                    
            except Exception as e:
                print(f"   ❌ Erreur surface: {e}")
            
            # 3. ÉTAGE - Facile
            print("\n🏢 ÉTAGE:")
            try:
                # Chercher l'étage dans différents formats
                etage_patterns = [
                    r'(\d+)(?:er?|e|ème?)\s*étage',
                    r'étage\s*(\d+)',
                    r'(\d+)(?:er?|e|ème?)\s*ét\.',
                    r'RDC|rez-de-chaussée|rez de chaussée'
                ]
                
                etage_trouve = False
                page_content = await page.content()
                
                for pattern in etage_patterns:
                    matches = re.findall(pattern, page_content, re.IGNORECASE)
                    if matches:
                        if pattern == 'RDC|rez-de-chaussée|rez de chaussée':
                            print(f"   ✅ Pattern '{pattern}': RDC")
                        else:
                            print(f"   ✅ Pattern '{pattern}': {matches[0]}e étage")
                        etage_trouve = True
                        break
                
                if not etage_trouve:
                    print("   ❌ Étage non trouvé")
                    
            except Exception as e:
                print(f"   ❌ Erreur étage: {e}")
            
            # 4. LOCALISATION - Semi-facile (adresse exacte)
            print("\n📍 LOCALISATION (adresse exacte):")
            try:
                # Récupérer tout le contenu de la page
                page_text = await page.text_content('body')
                
                # Chercher l'adresse exacte avec différents patterns
                address_patterns = [
                    r'(\d+[,\s]*[a-zA-Z\s]*[Rr]ue[^,\n]*)',
                    r'(\d+[,\s]*[a-zA-Z\s]*[Aa]venue[^,\n]*)',
                    r'(\d+[,\s]*[a-zA-Z\s]*[Bb]oulevard[^,\n]*)',
                    r'(\d+[,\s]*[a-zA-Z\s]*[Pp]lace[^,\n]*)',
                    r'(\d+[,\s]*[a-zA-Z\s]*[Cc]ours[^,\n]*)',
                    r'(\d+[,\s]*[a-zA-Z\s]*[Vv]illa[^,\n]*)',
                    r'(\d+[,\s]*[a-zA-Z\s]*[Ii]mpasse[^,\n]*)',
                    r'(\d+[,\s]*[a-zA-Z\s]*[Aa]llée[^,\n]*)',
                    r'(\d+[,\s]*[a-zA-Z\s]*[Pp]assage[^,\n]*)',
                    r'(\d+[,\s]*[a-zA-Z\s]*[Cc]hemin[^,\n]*)'
                ]
                
                adresses_trouvees = []
                for pattern in address_patterns:
                    matches = re.findall(pattern, page_text, re.IGNORECASE)
                    for match in matches:
                        # Nettoyer l'adresse
                        clean_addr = re.sub(r'\s+', ' ', match.strip())
                        if len(clean_addr) > 5 and clean_addr not in adresses_trouvees:
                            adresses_trouvees.append(clean_addr)
                
                if adresses_trouvees:
                    print(f"   ✅ Adresses trouvées:")
                    for i, addr in enumerate(adresses_trouvees[:3], 1):  # Afficher les 3 premières
                        print(f"      {i}. {addr}")
                else:
                    print("   ❌ Aucune adresse exacte trouvée")
                    
                    # Debug: chercher tous les patterns numériques + texte
                    print("   🔍 Debug - Patterns numériques trouvés:")
                    numeric_patterns = re.findall(r'\d+[a-zA-Z\s]{3,30}', page_text)
                    for pattern in numeric_patterns[:10]:  # Afficher les 10 premiers
                        if len(pattern.strip()) > 5:
                            print(f"      - {pattern.strip()}")
                    
            except Exception as e:
                print(f"   ❌ Erreur localisation: {e}")
            
            # 5. STYLE - Semi-facile (mots-clés dans description)
            print("\n🏛️ STYLE (mots-clés haussmanniens):")
            try:
                # Mots-clés haussmanniens étendus
                haussmann_keywords = {
                    'architectural': [
                        'haussmannien', 'haussmannienne', 'haussmann',
                        'moulures', 'moulure', 'mouluré', 'moulurée',
                        'cheminée', 'cheminées', 'cheminée de marbre',
                        'parquet', 'parquets', 'parquet d\'origine', 'parquet ancien',
                        'corniches', 'corniche', 'corniche moulurée',
                        'rosaces', 'rosace', 'rosace de plafond',
                        'balcon', 'balcons', 'balcon en fer forgé', 'balcon forgé',
                        'fer forgé', 'fer forgée', 'grille en fer forgé',
                        'hauteur sous plafond', 'haut plafond', 'plafond haut',
                        'escalier', 'escaliers', 'escalier d\'honneur'
                    ],
                    'caractère': [
                        'caractère', 'caractères', 'caractéristique',
                        'restauré', 'restaurée', 'rénové', 'rénovée',
                        'authentique', 'authentiques', 'original', 'originale',
                        'époque', 'période', 'époque haussmannienne',
                        'ancien', 'ancienne', 'ancien immeuble',
                        'vieux', 'vieille', 'vieux immeuble',
                        'charme', 'charmant', 'charmante',
                        'prestige', 'prestigieux', 'prestigieuse',
                        'noble', 'noblesse', 'noblesse des matériaux'
                    ],
                    'matériaux': [
                        'marbre', 'marbres', 'marbre de carrare',
                        'bois', 'bois noble', 'bois précieux',
                        'pierre', 'pierres', 'pierre de taille',
                        'stuc', 'stucs', 'stuc décoratif',
                        'plâtre', 'plâtres', 'plâtre moulé',
                        'métal', 'métaux', 'métal forgé'
                    ],
                    'détails': [
                        'moulure', 'moulures', 'moulure de plafond',
                        'décoration', 'décoratif', 'décorative',
                        'ornement', 'ornements', 'ornemental',
                        'détail', 'détails', 'détail architectural',
                        'finesse', 'finesses', 'finitions',
                        'élégance', 'élégant', 'élégante'
                    ]
                }
                
                # Récupérer la description complète
                description_selectors = [
                    '.fz-16.sc-bxivhb.fcnykg',
                    '[class*="description"]',
                    'p:has-text("Globalstone")',
                    'text=/Globalstone/',
                    'div:has-text("Globalstone")',
                    'section:has-text("Globalstone")'
                ]
                
                description_text = ""
                for selector in description_selectors:
                    try:
                        element = page.locator(selector).first
                        if await element.count() > 0:
                            description_text = await element.text_content()
                            if len(description_text) > 50:  # S'assurer qu'on a une vraie description
                                break
                    except:
                        continue
                
                if description_text:
                    print(f"   📝 Description trouvée ({len(description_text)} caractères)")
                    
                    # Chercher les mots-clés par catégorie
                    found_by_category = {}
                    total_found = 0
                    
                    for category, keywords in haussmann_keywords.items():
                        found_in_category = []
                        for keyword in keywords:
                            if keyword.lower() in description_text.lower():
                                found_in_category.append(keyword)
                                total_found += 1
                        
                        if found_in_category:
                            found_by_category[category] = found_in_category
                    
                    if found_by_category:
                        print(f"   ✅ Mots-clés haussmanniens trouvés ({total_found} total):")
                        for category, keywords in found_by_category.items():
                            print(f"      {category.title()}: {', '.join(keywords)}")
                        
                        # Calculer un score de style
                        style_score = min(100, (total_found * 10) + 20)  # 10 points par mot-clé + 20 de base
                        print(f"   🎯 Score de style estimé: {style_score}/100")
                    else:
                        print("   ❌ Aucun mot-clé haussmannien trouvé")
                        print("   🔍 Recherche de mots génériques...")
                        
                        # Chercher des mots génériques qui pourraient indiquer un style
                        generic_style_words = ['duplex', 'contemporain', 'moderne', 'design', 'architecte']
                        found_generic = [word for word in generic_style_words if word.lower() in description_text.lower()]
                        if found_generic:
                            print(f"      Mots génériques trouvés: {', '.join(found_generic)}")
                    
                    # Afficher un extrait de la description
                    print(f"   📄 Extrait: {description_text[:300]}...")
                else:
                    print("   ❌ Description non trouvée")
                    
            except Exception as e:
                print(f"   ❌ Erreur style: {e}")
            
            # 6. AUTRES DONNÉES UTILES
            print("\n🔍 AUTRES DONNÉES:")
            try:
                # Pièces
                pieces_match = re.search(r'(\d+)\s*pièces?', page_content, re.IGNORECASE)
                if pieces_match:
                    print(f"   🏠 Pièces: {pieces_match.group(1)}")
                
                # Chambres
                chambres_match = re.search(r'(\d+)\s*chambres?', page_content, re.IGNORECASE)
                if chambres_match:
                    print(f"   🛏️ Chambres: {chambres_match.group(1)}")
                
                # Cuisine
                if 'cuisine américaine' in page_content.lower():
                    print("   🍳 Cuisine: Américaine ouverte")
                elif 'cuisine ouverte' in page_content.lower():
                    print("   🍳 Cuisine: Ouverte")
                elif 'cuisine fermée' in page_content.lower():
                    print("   🍳 Cuisine: Fermée")
                else:
                    print("   🍳 Cuisine: Type non spécifié")
                
                # Luminosité
                if 'lumineux' in page_content.lower():
                    print("   ☀️ Luminosité: Lumineux")
                if 'spacieux' in page_content.lower():
                    print("   📏 Espace: Spacieux")
                    
            except Exception as e:
                print(f"   ❌ Erreur autres données: {e}")
            
            print("\n" + "="*60)
            print("✅ Test d'extraction terminé")
            print("="*60)
            
        except Exception as e:
            print(f"❌ Erreur générale: {e}")
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_apartment_extraction())
