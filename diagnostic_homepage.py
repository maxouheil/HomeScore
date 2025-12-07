#!/usr/bin/env python3
"""
Diagnostic du problème d'affichage de homepage.html
"""

import re
from bs4 import BeautifulSoup

def diagnostic_homepage():
    """Diagnostique les problèmes potentiels dans homepage.html"""
    
    print("🔍 DIAGNOSTIC DE HOMEPAGE.HTML")
    print("=" * 60)
    
    # Lire le fichier HTML
    with open('output/homepage.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Parser avec BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 1. Compter les scorecards
    scorecards = soup.find_all('div', class_='scorecard')
    print(f"\n1. Nombre de scorecards trouvées: {len(scorecards)}")
    
    # 2. Vérifier la structure apartments-grid
    apartments_grid = soup.find('div', class_='apartments-grid')
    if apartments_grid:
        children = apartments_grid.find_all('div', class_='scorecard', recursive=False)
        print(f"2. Nombre de scorecards directement dans apartments-grid: {len(children)}")
        
        # Vérifier tous les enfants directs
        all_children = list(apartments_grid.children)
        visible_children = [c for c in all_children if isinstance(c, type(soup)) and c.name == 'div']
        print(f"   Total d'éléments enfants directs: {len(visible_children)}")
        
        # Vérifier s'il y a des éléments cachés
        hidden_elements = apartments_grid.find_all(style=re.compile(r'display:\s*none|visibility:\s*hidden'))
        print(f"   Éléments avec display:none ou visibility:hidden: {len(hidden_elements)}")
    
    # 3. Vérifier le CSS
    print(f"\n3. Analyse du CSS:")
    style_tag = soup.find('style')
    if style_tag:
        css_content = style_tag.string
        
        # Chercher des règles qui pourraient cacher des éléments
        hidden_patterns = [
            r'\.scorecard.*display:\s*none',
            r'\.scorecard.*visibility:\s*hidden',
            r'\.apartments-grid.*max-height',
            r'\.apartments-grid.*overflow:\s*hidden',
            r'\.scorecard:nth-child\(n\+2\)',  # Cacher tous sauf le premier
        ]
        
        for pattern in hidden_patterns:
            matches = re.findall(pattern, css_content, re.IGNORECASE)
            if matches:
                print(f"   ⚠️  Problème potentiel trouvé: {pattern}")
                print(f"      Matches: {matches}")
    
    # 4. Vérifier le JavaScript
    print(f"\n4. Analyse du JavaScript:")
    scripts = soup.find_all('script')
    for i, script in enumerate(scripts, 1):
        if script.string:
            js_content = script.string
            
            # Chercher des manipulations qui pourraient cacher des éléments
            problematic_patterns = [
                r'\.style\.display\s*=\s*[\'"]none',
                r'\.style\.visibility\s*=\s*[\'"]hidden',
                r'querySelector.*scorecard',
                r'\.hidden\s*=',
                r'\.remove\(\)',
            ]
            
            for pattern in problematic_patterns:
                matches = re.findall(pattern, js_content, re.IGNORECASE)
                if matches:
                    print(f"   ⚠️  Problème potentiel dans script {i}: {pattern}")
                    print(f"      Matches: {len(matches)} occurrences")
    
    # 5. Vérifier la structure HTML - chercher des problèmes de fermeture
    print(f"\n5. Vérification de la structure HTML:")
    
    # Compter les balises ouvrantes et fermantes pour scorecard
    opening_scorecards = html_content.count('<div class="scorecard"')
    closing_divs_after_grid = html_content[html_content.find('apartments-grid'):].count('</div>')
    
    print(f"   Balises <div class='scorecard'> ouvrantes: {opening_scorecards}")
    print(f"   Balises </div> après apartments-grid: {closing_divs_after_grid}")
    
    # 6. Vérifier les IDs et classes uniques
    print(f"\n6. Vérification des IDs de carousel:")
    carousel_ids = re.findall(r'data-carousel-id="([^"]+)"', html_content)
    unique_ids = set(carousel_ids)
    print(f"   IDs de carousel trouvés: {len(carousel_ids)}")
    print(f"   IDs uniques: {len(unique_ids)}")
    if len(carousel_ids) != len(unique_ids):
        print(f"   ⚠️  PROBLÈME: IDs dupliqués détectés!")
        duplicates = [id for id in carousel_ids if carousel_ids.count(id) > 1]
        print(f"      IDs dupliqués: {set(duplicates)}")
    
    # 7. Analyser le premier et le deuxième scorecard pour comparaison
    print(f"\n7. Comparaison des deux premiers scorecards:")
    if len(scorecards) >= 2:
        first_card = scorecards[0]
        second_card = scorecards[1]
        
        first_classes = first_card.get('class', [])
        second_classes = second_card.get('class', [])
        
        print(f"   Premier scorecard classes: {first_classes}")
        print(f"   Deuxième scorecard classes: {second_classes}")
        
        first_style = first_card.get('style', '')
        second_style = second_card.get('style', '')
        
        if first_style:
            print(f"   Premier scorecard style: {first_style}")
        if second_style:
            print(f"   Deuxième scorecard style: {second_style}")
    
    # 8. Vérifier si le problème vient du CSS grid
    print(f"\n8. Vérification du CSS Grid:")
    if style_tag:
        css = style_tag.string
        grid_rules = re.findall(r'\.apartments-grid\s*\{[^}]+\}', css, re.DOTALL)
        for rule in grid_rules:
            print(f"   Règle apartments-grid trouvée:")
            print(f"   {rule[:200]}...")
            
            # Vérifier max-height ou overflow
            if 'max-height' in rule.lower():
                print(f"   ⚠️  PROBLÈME: max-height trouvé dans apartments-grid!")
            if 'overflow' in rule.lower() and 'hidden' in rule.lower():
                print(f"   ⚠️  PROBLÈME: overflow:hidden trouvé dans apartments-grid!")
    
    # 9. Vérifier s'il y a un problème de CSS qui cache les éléments
    print(f"\n9. Vérification CSS approfondie:")
    if style_tag:
        css = style_tag.string
        
        # Chercher des règles qui pourraient affecter tous les scorecards sauf le premier
        problematic_css = [
            r'\.scorecard\s*\+\s*\.scorecard',  # Adjacent sibling selector
            r'\.scorecard:nth-child\(n\+2\)',   # Tous sauf le premier
            r'\.scorecard:not\(:first-child\)',  # Tous sauf le premier
            r'\.apartments-grid\s*>\s*\.scorecard:nth-child\(n\+2\)',  # Scorecards après le premier dans grid
        ]
        
        for pattern in problematic_css:
            matches = re.findall(pattern, css, re.IGNORECASE)
            if matches:
                print(f"   ⚠️  PROBLÈME TROUVÉ: {pattern}")
                print(f"      Cette règle CSS pourrait cacher les autres scorecards!")
                for match in matches:
                    # Trouver le contexte de cette règle
                    match_pos = css.find(match)
                    if match_pos != -1:
                        context_start = max(0, match_pos - 100)
                        context_end = min(len(css), match_pos + len(match) + 200)
                        context = css[context_start:context_end]
                        print(f"      Contexte: ...{context}...")
    
    # 10. Analyser la structure réelle du DOM
    print(f"\n10. Analyse de la structure DOM:")
    if apartments_grid:
        # Trouver tous les scorecards et vérifier leur parent réel
        all_scorecards_in_doc = soup.find_all('div', class_='scorecard')
        print(f"   Total scorecards dans document: {len(all_scorecards_in_doc)}")
        
        # Vérifier combien sont directement enfants de apartments-grid
        direct_children = []
        for card in all_scorecards_in_doc:
            parent = card.parent
            if parent and hasattr(parent, 'get') and parent.get('class') == ['apartments-grid']:
                direct_children.append(card)
        
        print(f"   Scorecards directement enfants de apartments-grid: {len(direct_children)}")
        
        if len(direct_children) != len(all_scorecards_in_doc):
            print(f"   ⚠️  PROBLÈME: {len(all_scorecards_in_doc) - len(direct_children)} scorecards ne sont PAS directement enfants de apartments-grid!")
            
            # Trouver où sont les autres
            for i, card in enumerate(all_scorecards_in_doc[:5]):
                parent = card.parent
                if parent:
                    parent_name = parent.name if hasattr(parent, 'name') else 'unknown'
                    parent_classes = parent.get('class', []) if hasattr(parent, 'get') else []
                    print(f"      Scorecard {i+1} parent: {parent_name}, classes: {parent_classes}")
    
    print("\n" + "=" * 60)
    print("✅ Diagnostic terminé")
    
    # Résumé des problèmes trouvés
    print("\n📋 RÉSUMÉ:")
    if len(scorecards) < 17:
        print(f"   ⚠️  Seulement {len(scorecards)} scorecards trouvées au lieu de 17")
    if apartments_grid and len(apartments_grid.find_all('div', class_='scorecard', recursive=False)) < 17:
        print(f"   ⚠️  Structure DOM incorrecte - scorecards pas tous directement dans apartments-grid")

if __name__ == "__main__":
    diagnostic_homepage()

