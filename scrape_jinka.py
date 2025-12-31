#!/usr/bin/env python3
"""
Scraper Jinka pour extraire les données des appartements
"""

import asyncio
import json
import math
import os
import re
import aiohttp
import sys
import imaplib
import email
from email.header import decode_header
from datetime import datetime, timedelta
from playwright.async_api import async_playwright
from dotenv import load_dotenv
from extract_exposition import ExpositionExtractor

load_dotenv()

class JinkaScraper:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.apartments = []
        self.exposition_extractor = ExpositionExtractor()
        
    async def setup(self):
        """Initialise le navigateur et la page"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=False)  # Mode visible
        
        # Créer un contexte avec un user-agent réaliste pour éviter les 403
        self.context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='fr-FR',
            timezone_id='Europe/Paris'
        )
        self.page = await self.context.new_page()
        
        # Gestionnaire pour détecter les erreurs 429
        self.rate_limit_count = 0
        
        async def handle_response(response):
            if response.status == 429:
                self.rate_limit_count += 1
                print(f"\n⚠️  Erreur 429 détectée (#{self.rate_limit_count}) sur: {response.url[:80]}")
                wait_time = min(30 + (self.rate_limit_count * 10), 120)  # 30s, puis 40s, 50s... max 120s
                print(f"   Rate limiting activé - attente de {wait_time} secondes...")
                await asyncio.sleep(wait_time)  # asyncio.sleep attend des secondes
        
        self.page.on('response', handle_response)
        
    def get_activation_code_from_gmail(self, max_wait_seconds=120):
        """Récupère le code d'activation depuis Gmail"""
        print("📧 Récupération du code d'activation depuis Gmail...")
        
        gmail_email = os.getenv('GMAIL_EMAIL') or os.getenv('JINKA_EMAIL')
        gmail_password = os.getenv('GMAIL_PASSWORD') or os.getenv('JINKA_PASSWORD')
        
        if not gmail_email or not gmail_password:
            print("❌ Identifiants Gmail non trouvés dans .env")
            print("   Variables cherchées:")
            print(f"      GMAIL_EMAIL: {'✅' if os.getenv('GMAIL_EMAIL') else '❌'}")
            print(f"      GMAIL_PASSWORD: {'✅' if os.getenv('GMAIL_PASSWORD') else '❌'}")
            print(f"      JINKA_EMAIL: {'✅' if os.getenv('JINKA_EMAIL') else '❌'}")
            print(f"      JINKA_PASSWORD: {'✅' if os.getenv('JINKA_PASSWORD') else '❌'}")
            print("\n   💡 Ajoutez dans votre .env:")
            print("      GMAIL_EMAIL=votre@gmail.com")
            print("      GMAIL_PASSWORD=votre_mot_de_passe_application")
            print("   (ou utilisez JINKA_EMAIL/JINKA_PASSWORD si c'est le même compte)")
            return None
        
        print(f"   ✅ Utilisation de l'email: {gmail_email}")
        
        try:
            # Connexion IMAP à Gmail
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(gmail_email, gmail_password)
            mail.select("inbox")
            
            # Chercher les emails récents de Jinka (dernières 10 minutes)
            # Format IMAP: chercher depuis une date
            search_date = (datetime.now() - timedelta(minutes=10)).strftime("%d-%b-%Y")
            # Chercher les emails de Jinka avec "code" dans le sujet ou le corps
            status, messages = mail.search(None, f'(SINCE {search_date} FROM "noreply@jinka.fr")')
            
            # Si pas de résultats avec FROM, chercher juste les emails récents avec "code"
            if not messages[0]:
                status, messages = mail.search(None, f'(SINCE {search_date} SUBJECT "code")')
            
            # Si toujours rien, chercher tous les emails récents
            if not messages[0]:
                status, messages = mail.search(None, f'(SINCE {search_date})')
            
            if status != "OK" or not messages[0]:
                print("⚠️  Aucun email trouvé dans la recherche initiale")
                # Essayer une recherche plus large : tous les emails récents
                search_date = (datetime.now() - timedelta(minutes=10)).strftime("%d-%b-%Y")
                status, messages = mail.search(None, f'(SINCE {search_date})')
            
            if status != "OK" or not messages[0]:
                print("⚠️  Aucun email récent trouvé")
                mail.close()
                mail.logout()
                return None
            
            email_ids = messages[0].split()
            if not email_ids:
                print("⚠️  Aucun email trouvé")
                mail.close()
                mail.logout()
                return None
            
            # Parcourir les emails les plus récents en premier
            for email_id in reversed(email_ids[-5:]):  # Derniers 5 emails max
                status, msg_data = mail.fetch(email_id, "(RFC822)")
                
                if status != "OK":
                    continue
                
                email_body = msg_data[0][1]
                email_message = email.message_from_bytes(email_body)
                
                # Vérifier le sujet
                subject = decode_header(email_message["Subject"])[0][0]
                if isinstance(subject, bytes):
                    subject = subject.decode()
                
                # Vérifier que c'est bien un email de Jinka
                from_addr = email_message.get("From", "")
                if "jinka.fr" not in from_addr.lower():
                    continue
                
                # Chercher le code dans le corps de l'email
                body = ""
                if email_message.is_multipart():
                    for part in email_message.walk():
                        content_type = part.get_content_type()
                        if content_type == "text/plain" or content_type == "text/html":
                            try:
                                body_part = part.get_payload(decode=True)
                                if body_part:
                                    body += body_part.decode('utf-8', errors='ignore')
                            except:
                                pass
                else:
                    try:
                        body = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
                    except:
                        body = str(email_message.get_payload())
                
                # Chercher un code (format Jinka: "Jinka - XXXX est votre code de connexion")
                # D'abord chercher dans le sujet avec le format exact de Jinka
                subject_patterns = [
                    r'Jinka\s*-\s*(\d{4})\s+est votre code de connexion',  # "Jinka - 3709 est votre code de connexion"
                    r'(\d{4})\s+est votre code de connexion',  # "3709 est votre code de connexion"
                    r'(\d{4})\s+est votre code',  # "3709 est votre code"
                    r'code de connexion[:\s]+(\d{4})',  # "code de connexion: 3709"
                    r'votre code[:\s]+(\d{4})',  # "votre code: 3709"
                ]
                
                for pattern in subject_patterns:
                    matches = re.findall(pattern, subject, re.IGNORECASE)
                    if matches:
                        code = matches[0]
                        if len(code) == 4 and code.isdigit():
                            print(f"✅ Code d'activation trouvé dans le sujet: {code}")
                            mail.close()
                            mail.logout()
                            return code
                
                # Chercher aussi dans le corps avec patterns généraux
                body_patterns = [
                    r'code[:\s]+(\d{4,6})',  # "code: 1234" ou "code: 123456"
                    r'code d\'activation[:\s]+(\d{4,6})',
                    r'votre code[:\s]+(\d{4,6})',
                    r'code de connexion[:\s]+(\d{4,6})',
                    r'\b(\d{4})\b',  # Code à 4 chiffres isolé
                    r'\b(\d{6})\b',  # Code à 6 chiffres isolé
                ]
                
                for pattern in body_patterns:
                    matches = re.findall(pattern, body, re.IGNORECASE)
                    if matches:
                        code = matches[0]
                        # Vérifier que c'est bien un code (4 ou 6 chiffres)
                        if len(code) in [4, 6] and code.isdigit():
                            # Vérifier que ce n'est pas une année (2000-2099)
                            if not (len(code) == 4 and 2000 <= int(code) <= 2099):
                                print(f"✅ Code d'activation trouvé dans le corps: {code}")
                                mail.close()
                                mail.logout()
                                return code
            
            mail.close()
            mail.logout()
            print("⚠️  Aucun code d'activation trouvé dans les emails récents")
            return None
            
        except Exception as e:
            print(f"❌ Erreur lors de la récupération du code depuis Gmail: {e}")
            return None
    
    async def login(self):
        """Se connecte à Jinka via email avec code d'activation"""
        print("🔐 Connexion à Jinka par email...")
        print(f"📍 ÉTAPE 1: Début de la fonction login()")
        
        try:
            # Aller directement sur la page email au lieu de cliquer sur le bouton
            print(f"📍 ÉTAPE 3: Navigation directe vers la page email...")
            try:
                await self.page.goto('https://www.jinka.fr/sign/in/email', wait_until='domcontentloaded', timeout=30000)
                print(f"✅ ÉTAPE 3: Navigation réussie vers /sign/in/email")
            except Exception as e:
                print(f"❌ ÉTAPE 3: Erreur lors de la navigation: {e}")
                if '429' in str(e) or self.rate_limit_count > 0:
                    print("⚠️  Rate limiting détecté lors de la navigation")
                    wait_time = 30 + (self.rate_limit_count * 10)
                    print(f"   Attente de {wait_time} secondes...")
                    await asyncio.sleep(wait_time)
                    # Réessayer une fois
                    print(f"📍 ÉTAPE 3b: Nouvelle tentative de navigation...")
                    await self.page.goto('https://www.jinka.fr/sign/in/email', wait_until='domcontentloaded', timeout=30000)
                    print(f"✅ ÉTAPE 3b: Navigation réussie")
                else:
                    raise
            
            # Vérifier l'URL actuelle
            current_url = self.page.url
            print(f"📍 ÉTAPE 5: Vérification de l'URL actuelle: {current_url}")
            
            # Vérifier si on a reçu des erreurs 429
            if self.rate_limit_count > 0:
                print(f"⚠️  {self.rate_limit_count} erreur(s) 429 détectée(s) - attente supplémentaire...")
                await asyncio.sleep(10)
            
            print(f"✅ ÉTAPE 5: Page chargée et prête")
            
            # Saisir l'email - Utiliser wait_for_selector pour être plus rapide
            print(f"\n📍 ÉTAPE 8: Recherche du champ email...")
            
            email_input_selectors = [
                # Sélecteurs les plus probables en premier
                'input[type="email"]',
                'input[type="text"]',
                'div input[type="text"]',
                'form input[type="text"]',
                'input[name="email"]',
                'input[autocomplete="email"]',
                'input:visible',  # Dernier recours
            ]
            
            email_input = None
            
            # Essayer d'attendre directement le sélecteur le plus probable
            try:
                await self.page.wait_for_selector('input[type="email"], input[type="text"]', timeout=5000, state='visible')
                print("   ✅ Champ email détecté rapidement")
            except:
                print("   ⏳ Attente du champ email...")
            
            # Chercher le champ avec les sélecteurs optimisés
            for selector in email_input_selectors:
                try:
                    input_elem = self.page.locator(selector)
                    count = await input_elem.count()
                    if count > 0:
                        # Vérifier que le champ est visible
                        is_visible = await input_elem.first.is_visible()
                        if is_visible:
                            print(f"   ✅ Trouvé {count} champ(s) email avec sélecteur: {selector}")
                            email_input = input_elem.first
                            break
                except:
                    continue
                
                if email_input:
                    break
            
            if not email_input:
                print(f"⚠️  ÉTAPE 8: Champ email non trouvé avec les sélecteurs standards")
                print("   Recherche alternative : analyse de tous les inputs visibles...")
                
                # Recherche alternative : tous les inputs visibles
                try:
                    all_inputs = await self.page.locator('input:visible').all()
                    print(f"   Trouvé {len(all_inputs)} input(s) visible(s) sur la page")
                    
                    for i, inp in enumerate(all_inputs[:10]):  # Limiter aux 10 premiers
                        try:
                            input_type = await inp.get_attribute('type') or 'text'
                            input_name = await inp.get_attribute('name') or ''
                            input_id = await inp.get_attribute('id') or ''
                            input_placeholder = await inp.get_attribute('placeholder') or ''
                            input_class = await inp.get_attribute('class') or ''
                            
                            print(f"   Input {i+1}: type={input_type}, name={input_name}, id={input_id[:30]}")
                            print(f"      placeholder={input_placeholder[:40]}, class={input_class[:40]}")
                            
                            # Si c'est un input de type text ou email, c'est probablement le champ email
                            if input_type in ['text', 'email'] and 'password' not in input_type:
                                # Vérifier qu'il n'est pas un champ de recherche ou autre
                                if 'search' not in input_id.lower() and 'search' not in input_name.lower():
                                    # Reconstruire un sélecteur pour cet input
                                    if input_id:
                                        email_input = self.page.locator(f'input#{input_id}')
                                    elif input_name:
                                        email_input = self.page.locator(f'input[name="{input_name}"]')
                                    else:
                                        # Utiliser l'index
                                        email_input = self.page.locator(f'input:visible').nth(i)
                                    
                                    # Vérifier qu'on peut bien l'utiliser
                                    if await email_input.count() > 0:
                                        email_input = email_input.first
                                        selector_info = f"input#{input_id}" if input_id else f"input[name='{input_name}']"
                                        print(f"   ✅ Champ email probable trouvé: input {i+1}")
                                        print(f"      Sélecteur utilisé: {selector_info}")
                                        break
                        except Exception as e:
                            print(f"   Erreur analyse input {i+1}: {e}")
                            continue
                except Exception as e:
                    print(f"   Erreur recherche alternative: {e}")
                
                if not email_input:
                    print(f"❌ ÉTAPE 8: Champ email non trouvé après toutes les tentatives")
                    print("   Vérification de l'URL actuelle...")
                    current_url = self.page.url
                    print(f"   URL: {current_url}")
                    # Prendre un screenshot pour debug
                    try:
                        os.makedirs("data", exist_ok=True)
                        await self.page.screenshot(path="data/debug_no_email_field.png")
                        print("   📸 Screenshot sauvegardé: data/debug_no_email_field.png")
                    except:
                        pass
                    return False
            
            print(f"✅ ÉTAPE 8: Champ email trouvé")
            
            print(f"\n📍 ÉTAPE 9: Récupération de l'email depuis .env...")
            jinka_email = os.getenv('JINKA_EMAIL')
            if not jinka_email:
                print(f"❌ ÉTAPE 9: JINKA_EMAIL non trouvé dans .env")
                return False
            print(f"✅ ÉTAPE 9: Email trouvé: {jinka_email}")
            
            print(f"\n📍 ÉTAPE 10: Saisie de l'email...")
            await email_input.fill(jinka_email)
            print(f"✅ ÉTAPE 10: Email saisi")
            await asyncio.sleep(2)  # Délai plus long avant de continuer
            print(f"✅ ÉTAPE 10b: Attente terminée")
            
            # Chercher et cliquer sur le bouton "Continuer" ou "Suivant"
            continue_button_selectors = [
                'button:has-text("Continuer")',
                'button:has-text("Suivant")',
                'button[type="submit"]',
                'button:has-text("Envoyer")',
            ]
            
            for selector in continue_button_selectors:
                button = self.page.locator(selector)
                if await button.count() > 0:
                    await button.click()
                    break
            else:
                # Si pas de bouton, appuyer sur Enter
                await self.page.keyboard.press('Enter')
            
            print("⏳ Attente du code d'activation...")
            await asyncio.sleep(4)  # Délai plus long pour laisser le temps à l'email d'arriver
            
            # Attendre que le champ de code apparaisse et récupérer le code depuis Gmail
            # Le code peut être dans plusieurs inputs avec maxlength="1" (un par chiffre)
            print(f"\n📍 ÉTAPE 11: Recherche du champ de code...")
            print("   Le code peut être dans plusieurs inputs (un par chiffre)...")
            
            code_inputs = None  # Peut être une liste d'inputs ou un seul input
            max_attempts = 15  # 15 tentatives de 2 secondes = 30 secondes max
            
            for attempt in range(max_attempts):
                # Chercher d'abord les inputs avec maxlength="1" (format code par chiffre)
                inputs_maxlength_1 = await self.page.locator('input[type="text"][maxlength="1"]').all()
                if len(inputs_maxlength_1) >= 4:  # Au moins 4 inputs = probablement un code
                    print(f"   ✅ Trouvé {len(inputs_maxlength_1)} inputs avec maxlength='1' (format code par chiffre)")
                    code_inputs = inputs_maxlength_1[:6]  # Prendre les 6 premiers (code à 6 chiffres)
                    break
                
                # Chercher un input unique avec maxlength="6" ou "8"
                code_input_selectors = [
                    'input[maxlength="6"]',
                    'input[maxlength="8"]',
                    'input[name="code"]',
                    'input[placeholder*="code"]',
                    'input[placeholder*="Code"]',
                ]
                
                for selector in code_input_selectors:
                    input_elem = self.page.locator(selector)
                    count = await input_elem.count()
                    if count > 0:
                        # Vérifier que c'est bien le champ de code
                        placeholder = await input_elem.first.get_attribute('placeholder') or ''
                        if 'code' in placeholder.lower() or selector.startswith('input[maxlength'):
                            code_inputs = [input_elem.first]  # Un seul input
                            print(f"   ✅ Champ de code trouvé avec sélecteur: {selector}")
                            break
                
                if code_inputs:
                    break
                
                if attempt % 3 == 0:  # Log tous les 3 essais
                    print(f"   Tentative {attempt + 1}/{max_attempts}...")
                await asyncio.sleep(2)
            
            if not code_inputs:
                print("❌ ÉTAPE 11: Champ de code non trouvé")
                return False
            
            print(f"✅ ÉTAPE 11: Champ(s) de code trouvé(s) - {len(code_inputs)} input(s)")
            print("   Récupération du code depuis Gmail...")
            
            # Récupérer le code depuis Gmail
            print(f"\n📍 ÉTAPE 12: Récupération du code depuis Gmail...")
            activation_code = None
            for attempt in range(15):  # 15 tentatives de 3 secondes = 45 secondes max
                activation_code = self.get_activation_code_from_gmail()
                if activation_code:
                    break
                if attempt < 14:  # Ne pas attendre après la dernière tentative
                    await asyncio.sleep(3)
                    print(f"   Tentative {attempt + 1}/15 de récupération du code...")
            
            if not activation_code:
                print("❌ ÉTAPE 12: Code d'activation non trouvé dans Gmail")
                print("💡 Vérifiez votre boîte mail et entrez le code manuellement")
                print("⏳ Attente de 60 secondes pour saisie manuelle...")
                # Attendre que l'utilisateur entre le code manuellement (timeout 60s)
                await asyncio.sleep(60)
            else:
                print(f"✅ ÉTAPE 12: Code trouvé: {activation_code}")
                print(f"📍 ÉTAPE 13: Saisie du code...")
                
                # Si plusieurs inputs (format un chiffre par input)
                if len(code_inputs) > 1:
                    print(f"   Format multi-inputs détecté: {len(code_inputs)} inputs")
                    # Si le code fait 4 chiffres mais qu'on a 6 inputs, le compléter avec des zéros ou utiliser les 4 premiers
                    code_to_use = activation_code[:len(code_inputs)]
                    # Si code à 4 chiffres mais 6 inputs, répéter ou ajouter des zéros au début
                    if len(code_to_use) == 4 and len(code_inputs) == 6:
                        # Essayer de remplir les 4 premiers inputs avec le code
                        code_to_use = activation_code
                    
                    for i, digit in enumerate(code_to_use[:len(code_inputs)]):
                        try:
                            await code_inputs[i].fill(digit)
                            await asyncio.sleep(0.2)  # Petit délai entre chaque chiffre
                            print(f"      Chiffre {i+1}: {digit}")
                        except Exception as e:
                            print(f"   Erreur saisie chiffre {i+1}: {e}")
                else:
                    # Un seul input (format complet)
                    print(f"   Format input unique")
                    await code_inputs[0].fill(activation_code)
                
                await asyncio.sleep(0.5)
                print(f"✅ ÉTAPE 13: Code saisi")
                
                # Cliquer sur le bouton de validation
                submit_button_selectors = [
                    'button:has-text("Valider")',
                    'button:has-text("Continuer")',
                    'button:has-text("Confirmer")',
                    'button[type="submit"]',
                ]
                
                for selector in submit_button_selectors:
                    button = self.page.locator(selector)
                    if await button.count() > 0:
                        await button.click()
                        break
                else:
                    await self.page.keyboard.press('Enter')
                
                await asyncio.sleep(10)  # Attendre plus longtemps après la saisie du code
            
            # Vérifier que la connexion a réussi
            print("🔍 Vérification de la connexion...")
            await asyncio.sleep(10)  # Attendre plus longtemps avant de vérifier
            current_url = self.page.url
            print(f"📍 URL actuelle: {current_url}")
            
            if "sign/in" not in current_url and "jinka.fr" in current_url:
                print("✅ Connexion réussie !")
                return True
            else:
                print("⚠️  Vérification supplémentaire...")
                await asyncio.sleep(10)  # Attendre plus longtemps avant la vérification supplémentaire
                current_url = self.page.url
                print(f"📍 URL après vérification: {current_url}")
                if "sign/in" not in current_url:
                    print("✅ Connexion réussie !")
                    return True
                else:
                    print("❌ Connexion échouée - toujours sur la page de connexion")
                    print("💡 Vérifiez que le code a été correctement saisi")
                    return False
                
        except asyncio.TimeoutError as e:
            print(f"\n❌ TIMEOUT: La connexion a pris trop de temps")
            print(f"   Erreur: {e}")
            print(f"   Vérifiez les logs ci-dessus pour voir à quelle étape ça a bloqué")
            return False
        except Exception as e:
            print(f"\n❌ ERREUR GÉNÉRALE lors de la connexion")
            print(f"   Type d'erreur: {type(e).__name__}")
            print(f"   Message: {e}")
            print(f"   Vérifiez les logs ci-dessus pour voir à quelle étape ça a échoué")
            import traceback
            print("\n📋 Traceback complet:")
            traceback.print_exc()
            return False
    
    async def scrape_alert_page(self, alert_url):
        """Scrape une page d'alerte Jinka"""
        print(f"🏠 Scraping de l'alerte: {alert_url}")
        
        try:
            await self.page.goto(alert_url)
            await self.page.wait_for_load_state('networkidle')
            await self.page.wait_for_timeout(2000)
            
            # Attendre que la page se charge complètement
            await self.page.wait_for_timeout(3000)
            
            # Essayer différents sélecteurs pour les cartes d'appartements
            selectors = [
                'a[href*="alert_result"][href*="ad="]',  # Liens avec alert_result ET ad=
                'a[href*="alert_result"]',
                'a[href*="ad="]',
                'a.sc-bdVaJa.csp.sc-cJSrbW.doPXAe',  # Sélecteur exact d'après l'image
                'a.sc-bdVaJa',  # Sélecteur plus large
                '.apartment-card',
                '[data-testid="apartment-card"]',
                'a[href*="/alert_result"]'
            ]
            
            apartment_links = None
            count = 0
            
            for selector in selectors:
                try:
                    apartment_links = self.page.locator(selector)
                    count = await apartment_links.count()
                    if count > 0:
                        print(f"📋 {count} appartements trouvés avec sélecteur: {selector}")
                        break
                except:
                    continue
            
            if count == 0:
                print("🔍 Aucun appartement trouvé, debug de la page...")
                # Debug: afficher le contenu de la page
                page_content = await self.page.content()
                print(f"📄 Taille de la page: {len(page_content)} caractères")
                
                # Chercher tous les liens
                all_links = self.page.locator('a')
                all_links_count = await all_links.count()
                print(f"🔗 Total de liens sur la page: {all_links_count}")
                
                # Afficher les premiers liens trouvés
                for i in range(min(5, all_links_count)):
                    href = await all_links.nth(i).get_attribute('href')
                    print(f"   Lien {i+1}: {href}")
                
                return False
            
            # Extraire les URLs des appartements
            apartment_urls = []
            for i in range(count):
                href = await apartment_links.nth(i).get_attribute('href')
                print(f"   Lien {i+1}: href='{href}'")
                
                # Chercher les liens avec id= (format loueragile://) ou ad=
                if href and ('id=' in href or 'ad=' in href):
                    # Extraire l'ID de l'appartement
                    apartment_id = None
                    if 'id=' in href:
                        import re
                        match = re.search(r'id=(\d+)', href)
                        if match:
                            apartment_id = match.group(1)
                    elif 'ad=' in href:
                        import re
                        match = re.search(r'ad=(\d+)', href)
                        if match:
                            apartment_id = match.group(1)
                    
                    if apartment_id:
                        # Construire l'URL standard Jinka
                        full_url = f"https://www.jinka.fr/alert_result?token=26c2ec3064303aa68ffa43f7c6518733&ad={apartment_id}&from=dashboard_card&from_alert_filter=all&from_alert_page=1"
                        apartment_urls.append(full_url)
                        print(f"   ✅ Appartement {i+1} (ID: {apartment_id}): {full_url}")
                    else:
                        print(f"   ❌ Lien {i+1} ignoré: impossible d'extraire l'ID")
                else:
                    print(f"   ❌ Lien {i+1} ignoré: pas de paramètre 'id=' ou 'ad='")
            
            print(f"🔗 {len(apartment_urls)} URLs d'appartements extraites")
            
            # Scraper chaque appartement
            for i, url in enumerate(apartment_urls):
                print(f"🏠 Scraping appartement {i+1}/{len(apartment_urls)}")
                apartment_data = await self.scrape_apartment(url)
                if apartment_data:
                    self.apartments.append(apartment_data)
                    await self.save_apartment(apartment_data)
                
                # Pause entre les requêtes
                await self.page.wait_for_timeout(1000)
            
            # Mettre à jour scraped_apartments.json après le scraping
            print("\n📝 Mise à jour de scraped_apartments.json...")
            self.update_scraped_apartments_json()
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur scraping alerte: {e}")
            return False
    
    async def scrape_apartment(self, url):
        """Scrape les détails d'un appartement"""
        try:
            await self.page.goto(url)
            await self.page.wait_for_load_state('networkidle')
            await self.page.wait_for_timeout(2000)
            
            # Extraire l'ID de l'appartement
            apartment_id = self.extract_apartment_id(url)
            
            # Extraire les données
            description = await self.extract_description()
            caracteristiques = await self.extract_caracteristiques()
            photos = await self.extract_photos()
            etage = await self.extract_etage()
            if etage:
                print(f"   🏢 Étage trouvé: {etage}")
            else:
                print(f"   ⚠️ Étage non trouvé")
            
            # Télécharger les photos localement
            await self.download_apartment_photos(apartment_id, photos)
            
            data = {
                'id': apartment_id,
                'url': url,
                'scraped_at': datetime.now().isoformat(),
                'titre': await self.extract_titre(),
                'prix': await self.extract_prix(),
                'prix_m2': await self.extract_prix_m2(),
                'localisation': await self.extract_localisation(),
                'coordinates': await self.extract_coordinates(),
                'map_info': await self.extract_map_info(apartment_id),
                'surface': await self.extract_surface(),
                'pieces': await self.extract_pieces(),
                'date': await self.extract_date(),
                'transports': await self.extract_transports(),
                'description': description,
                'photos': photos,
                'caracteristiques': caracteristiques,
                'etage': etage,
                'agence': await self.extract_agence(),
                'style_haussmannien': await self.extract_style_haussmannien()
            }
            
            # Ajouter l'analyse d'exposition contextuelle
            data['exposition'] = self.exposition_extractor.extract_exposition_ultimate(data)
            
            print(f"✅ Appartement {apartment_id} scrapé")
            return data
            
        except Exception as e:
            print(f"❌ Erreur scraping appartement {url}: {e}")
            return None
    
    def extract_apartment_id(self, url):
        """Extrait l'ID de l'appartement depuis l'URL"""
        match = re.search(r'ad=(\d+)', url)
        return match.group(1) if match else "unknown"
    
    async def extract_titre(self):
        """Extrait le titre de l'appartement"""
        try:
            # Chercher le titre dans différents sélecteurs possibles
            selectors = ['h1', '.title', '[data-testid="title"]', 'h2']
            for selector in selectors:
                element = self.page.locator(selector).first
                if await element.count() > 0:
                    text = await element.text_content()
                    if text and len(text.strip()) > 5:
                        return text.strip()
            return "Titre non trouvé"
        except:
            return "Titre non trouvé"
    
    async def extract_prix(self):
        """Extrait le prix principal"""
        try:
            # Sélecteur pour le prix principal
            price_element = self.page.locator('.hmmXKG, [class*="price"], .price').first
            if await price_element.count() > 0:
                text = await price_element.text_content()
                # Nettoyer le prix
                price = re.search(r'[\d\s]+€', text or '')
                return price.group(0).strip() if price else "Prix non trouvé"
            return "Prix non trouvé"
        except:
            return "Prix non trouvé"
    
    async def extract_prix_m2(self):
        """Extrait le prix au m²"""
        try:
            # Chercher le prix au m² près du prix principal
            price_elements = self.page.locator('text=/€\/m²/')
            if await price_elements.count() > 0:
                text = await price_elements.first.text_content()
                if text:
                    # Extraire et formater le prix au m²
                    match = re.search(r'([\d\s]+)\s*€\s*/?\s*m²', text, re.IGNORECASE)
                    if match:
                        prix_clean = match.group(1).strip().replace(' ', ' ')
                        return f"{prix_clean} € / m²"
            return None
        except:
            return None
    
    async def extract_etage(self):
        """Extrait l'étage de la page d'appartement"""
        try:
            # Chercher d'abord dans les caractéristiques (section dédiée)
            try:
                # Chercher la section caractéristiques avec plusieurs sélecteurs possibles
                caracteristiques_selectors = [
                    'h3:has-text("Caractéristiques")',
                    'h2:has-text("Caractéristiques")',
                    '[class*="caracteristiques"]',
                    '[class*="Caractéristiques"]',
                ]
                
                caracteristiques_text = ""
                for selector in caracteristiques_selectors:
                    try:
                        char_header = self.page.locator(selector)
                        if await char_header.count() > 0:
                            # Récupérer tout le contenu de la section caractéristiques
                            # Chercher le parent ou le conteneur suivant
                            parent_elem = char_header.locator('..')
                            if await parent_elem.count() > 0:
                                caracteristiques_text = await parent_elem.first.text_content() or ""
                            else:
                                # Chercher l'élément suivant
                                next_elem = self.page.locator(f'{selector} + *')
                                if await next_elem.count() > 0:
                                    caracteristiques_text = await next_elem.first.text_content() or ""
                                else:
                                    # Chercher tous les éléments dans le même conteneur
                                    char_section = self.page.locator(f'{selector}').locator('..')
                                    if await char_section.count() > 0:
                                        caracteristiques_text = await char_section.first.text_content() or ""
                            
                            if caracteristiques_text:
                                break
                    except:
                        continue
                
                # Si pas trouvé avec les sélecteurs, chercher dans toute la page autour du titre "Caractéristiques"
                if not caracteristiques_text:
                    try:
                        # Chercher tous les éléments contenant "Caractéristiques"
                        all_text = await self.page.text_content('body') or ""
                        # Extraire la section après "Caractéristiques"
                        match = re.search(r'Caractéristiques[:\s]*(.*?)(?:\n\n|\n[A-Z]|$)', all_text, re.IGNORECASE | re.DOTALL)
                        if match:
                            caracteristiques_text = match.group(1)
                    except:
                        pass
                
                if caracteristiques_text:
                    # PRIORITÉ 1: Chercher RDC d'abord (car peut être mal interprété comme étage)
                    if re.search(r'\bRDC\b|rez-de-chaussée|rez de chaussée|rez-de-jardin', caracteristiques_text, re.IGNORECASE):
                        return "RDC"
                    
                    # Patterns pour trouver l'étage dans les caractéristiques (plus complets)
                    etage_patterns = [
                        r'(\d+)(?:er?|e|ème?)\s*étage',
                        r'étage\s*(\d+)',
                        r'(\d+)(?:er?|e|ème?)\s*ét\.',
                        r'Étage[:\s]+(\d+)',
                        r'étage[:\s]+(\d+)',
                        r'(\d+)\s*étage',  # Format simple "2 étage"
                        r'étage\s*:\s*(\d+)',  # Format "étage: 2"
                    ]
                    
                    for pattern in etage_patterns:
                        matches = re.findall(pattern, caracteristiques_text, re.IGNORECASE)
                        if matches:
                            etage_num = matches[0]
                            # Vérifier le contexte pour éviter les faux positifs (arrondissements)
                            match_obj = re.search(pattern, caracteristiques_text, re.IGNORECASE)
                            if match_obj:
                                start = max(0, match_obj.start() - 20)
                                end = min(len(caracteristiques_text), match_obj.end() + 20)
                                context = caracteristiques_text[start:end].lower()
                                # Exclure si c'est un arrondissement
                                if not any(word in context for word in ['arrondissement', 'arr.', 'arr ', 'paris']):
                                    if etage_num == '1':
                                        return "1er étage"
                                    else:
                                        return f"{etage_num}e étage"
            except Exception as e:
                print(f"  ⚠️ Erreur extraction étage depuis caractéristiques: {e}")
                pass  # Continuer si l'extraction depuis caractéristiques échoue
            
            # Chercher dans toute la page si pas trouvé dans caractéristiques
            page_content = await self.page.content()
            page_text = await self.page.text_content('body') or ""
            
            # PRIORITÉ 1: Chercher RDC d'abord (car peut être mal interprété comme étage)
            if re.search(r'\bRDC\b|rez-de-chaussée|rez de chaussée|rez-de-jardin', page_text, re.IGNORECASE):
                return "RDC"
            
            # Patterns pour trouver l'étage (plus robustes)
            # Priorité aux patterns avec "étage" explicite
            etage_patterns = [
                r'(\d+)(?:er?|e|ème?)\s*étage',
                r'étage\s*(\d+)',
                r'(\d+)(?:er?|e|ème?)\s*ét\.',
                r'au\s+(\d+)(?:er?|e|ème?)\s*étage',
                r'(\d+)(?:er?|e|ème?)\s*étage\s*(?:avec|sans)',
                r'étage\s*:\s*(\d+)',
                r'(\d+)\s*étage',  # Format simple "2 étage"
            ]
            
            for pattern in etage_patterns:
                matches = re.findall(pattern, page_content, re.IGNORECASE)
                if matches:
                    etage_num = matches[0]
                    # Vérifier le contexte pour éviter les faux positifs (arrondissements)
                    match_obj = re.search(pattern, page_text, re.IGNORECASE)
                    if match_obj:
                        start = max(0, match_obj.start() - 30)
                        end = min(len(page_text), match_obj.end() + 30)
                        context = page_text[start:end].lower()
                        # Exclure si c'est un arrondissement ou une zone géographique
                        if not any(word in context for word in ['arrondissement', 'arr.', 'arr ', 'paris', '750']):
                            # Formater comme "4e étage" ou "1er étage"
                            if etage_num == '1':
                                return "1er étage"
                            else:
                                return f"{etage_num}e étage"
            
            # Chercher les formats courts comme "2e" dans la section Caractéristiques uniquement
            # (pour éviter les faux positifs comme "10e arrondissement")
            try:
                caracteristiques_elem = self.page.locator('h3:has-text("Caractéristiques"), h2:has-text("Caractéristiques")')
                if await caracteristiques_elem.count() > 0:
                    # Récupérer le conteneur de la section caractéristiques
                    char_container = caracteristiques_elem.first.locator('..')
                    char_text = await char_container.text_content() or ""
                    
                    # Patterns pour formats courts dans caractéristiques
                    short_patterns = [
                        r'(\d+)(?:er|e|ème)(?:\s|,|\.|$)',  # Format "2e" suivi d'espace/ponctuation
                    ]
                    
                    for pattern in short_patterns:
                        matches = re.findall(pattern, char_text, re.IGNORECASE)
                        if matches:
                            # Prendre le premier match qui est probablement l'étage
                            # Les caractéristiques listent généralement: pièces, étage, exposition, etc.
                            for match in matches[:3]:  # Vérifier les 3 premiers matches au cas où
                                etage_num = match if isinstance(match, str) else str(match)
                                # Vérifier le contexte autour pour confirmer
                                match_obj = re.search(re.escape(etage_num) + r'(?:er|e|ème)?', char_text, re.IGNORECASE)
                                if match_obj:
                                    start = max(0, match_obj.start() - 30)
                                    end = min(len(char_text), match_obj.end() + 30)
                                    context = char_text[start:end].lower()
                                    # Si le contexte suggère un étage (pas un arrondissement ou autre)
                                    if any(word in context for word in ['étage', 'ét.', 'ét', 'ascenseur', 'rdc', 'rez']):
                                        # Éviter les faux positifs comme "10e arrondissement", "Paris 20e", "75020"
                                        if not any(word in context for word in ['arrondissement', 'arr.', 'arr ', 'paris', '750']):
                                            # Exclure les grands nombres qui sont probablement des arrondissements
                                            if int(etage_num) <= 10:  # Les étages normaux sont <= 10
                                                if etage_num == '1':
                                                    return "1er étage"
                                                else:
                                                    return f"{etage_num}e étage"
            except:
                pass
            
            # Chercher RDC (dernier recours)
            if re.search(r'\bRDC\b|rez-de-chaussée|rez de chaussée|rez-de-jardin', page_text, re.IGNORECASE):
                return "RDC"
            
            return None
        except Exception as e:
            print(f"  ⚠️ Erreur extraction étage: {e}")
            return None
    
    async def extract_style_for_photo(self):
        """Extrait le style de l'appartement pour la description de photo"""
        try:
            page_text = await self.page.text_content('body') or ""
            
            # Chercher des indices de style haussmannien
            style_keywords = {
                'haussmannien': 'Haussmannien',
                'haussmann': 'Haussmannien',
                'moulures': 'Haussmannien',
                'parquet': 'Haussmannien',
                'cheminée': 'Haussmannien',
                'restauré': 'Haussmannien',
                'contemporain': 'Contemporain',
                'moderne': 'Moderne',
                'ancien': 'Ancien',
                'neuf': 'Neuf'
            }
            
            for keyword, style in style_keywords.items():
                if re.search(keyword, page_text, re.IGNORECASE):
                    return style
            
            return "Style Inconnu"
        except Exception as e:
            print(f"  ⚠️ Erreur extraction style: {e}")
            return "Style Inconnu"
    
    def format_photo_description(self, surface=None, prix_m2=None, etage=None, style=None):
        """Formate la description de photo au format: 70 m² · 3e étage · Style Inconnu"""
        parts = []
        
        if surface:
            parts.append(surface)
        # Prix au m² masqué pour simplifier
        # if prix_m2:
        #     parts.append(prix_m2)
        if etage:
            parts.append(etage)
        if style:
            parts.append(style)
        
        return " · ".join(parts) if parts else "Appartement"
    
    async def extract_localisation(self):
        """Extrait la localisation (adresse exacte si possible)"""
        try:
            # Récupérer tout le contenu de la page
            page_text = await self.page.text_content('body')
            
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
                return adresses_trouvees[0]  # Retourner la première adresse trouvée
            
            # Fallback 1: chercher juste l'arrondissement
            selectors = ['text=/Paris \d+e/', 'text=/750\d+/', '[class*="location"]']
            for selector in selectors:
                element = self.page.locator(selector).first
                if await element.count() > 0:
                    text = await element.text_content()
                    if text and 'Paris' in text:
                        return text.strip()
            
            # Fallback 2: utiliser les stations de métro comme localisation
            try:
                transports = await self.extract_transports()
                if transports:
                    # Prendre les 2 premières stations comme localisation
                    stations_str = ", ".join(transports[:2])
                    return f"Proche de {stations_str}"
            except Exception as e:
                print(f"  ⚠️ Erreur fallback stations: {e}")
            
            return "Localisation non trouvée"
        except:
            return "Localisation non trouvée"
    
    async def extract_surface(self):
        """Extrait la surface"""
        try:
            # Chercher la surface dans différents formats
            surface_elements = self.page.locator('text=/\\d+\\s*m²/')
            if await surface_elements.count() > 0:
                text = await surface_elements.first.text_content()
                if text:
                    # Extraire juste la partie "XX m²"
                    match = re.search(r'(\d+(?:[.,]\d+)?)\s*m²', text, re.IGNORECASE)
                    if match:
                        # Arrondir si décimal et formater
                        surface_val = match.group(1).replace(',', '.')
                        try:
                            surface_num = float(surface_val)
                            return f"{int(surface_num)} m²" if surface_num == int(surface_num) else f"{surface_num:.1f} m²"
                        except:
                            return f"{match.group(1)} m²"
            return None
        except:
            return None
    
    async def extract_pieces(self):
        """Extrait le nombre de pièces"""
        try:
            # Chercher les pièces dans différents formats
            pieces_elements = self.page.locator('text=/\d+\s*pièces?/')
            if await pieces_elements.count() > 0:
                text = await pieces_elements.first.text_content()
                return text.strip() if text else "Pièces non trouvées"
            return "Pièces non trouvées"
        except:
            return "Pièces non trouvées"
    
    async def extract_date(self):
        """Extrait la date de publication"""
        try:
            # Chercher la date
            date_elements = self.page.locator('text=/le \d+ \w+ à/')
            if await date_elements.count() > 0:
                text = await date_elements.first.text_content()
                return text.strip() if text else "Date non trouvée"
            return "Date non trouvée"
        except:
            return "Date non trouvée"
    
    async def extract_transports(self):
        """Extrait les transports proches (stations de métro)"""
        try:
            transports = []
            
            # Méthode 1: Chercher la section "Proche des stations"
            try:
                # Chercher la div qui contient "Proche des stations"
                stations_div = self.page.locator('div.fz-16.sc-bdVaJa.bDXQKW:has(h3:has-text("Proche des stations"))')
                if await stations_div.count() > 0:
                    # Chercher tous les spans dans les li de la liste ul
                    station_spans = stations_div.locator('ul li span')
                    station_count = await station_spans.count()
                    
                    if station_count > 0:
                        for i in range(station_count):
                            station_text = await station_spans.nth(i).text_content()
                            if station_text and len(station_text.strip()) > 2:
                                transports.append(station_text.strip())
                    else:
                        # Fallback: utiliser les li directement
                        station_lis = stations_div.locator('ul li')
                        li_count = await station_lis.count()
                        for i in range(li_count):
                            station_text = await station_lis.nth(i).text_content()
                            if station_text:
                                # Nettoyer le texte (enlever les numéros de ligne)
                                station_name = re.sub(r'\s+\d+\s*$', '', station_text.strip())
                                if station_name and len(station_name) > 2:
                                    transports.append(station_name)
            except Exception as e:
                print(f"  ⚠️ Erreur extraction section stations: {e}")
            
            # Méthode 2: Chercher les images de métro et extraire les noms
            try:
                metro_images = await self.page.locator('img[src*="subway"], img[alt*="metro"]').all()
                for img in metro_images:
                    # Chercher le texte de la station dans le même conteneur
                    parent = img.locator('..')
                    station_text = await parent.text_content()
                    if station_text:
                        # Extraire le nom de la station (avant les icônes)
                        station_name = re.split(r'\s+\d+\s*', station_text)[0].strip()
                        if station_name and len(station_name) > 2 and station_name not in transports:
                            transports.append(station_name)
            except Exception as e:
                print(f"  ⚠️ Erreur extraction images métro: {e}")
            
            # Méthode 3: Fallback - chercher les patterns de stations
            if not transports:
                try:
                    transport_elements = self.page.locator('text=/[A-Za-z]+\s+\d+/')
                    for i in range(await transport_elements.count()):
                        text = await transport_elements.nth(i).text_content()
                        if text and re.match(r'[A-Za-z]+\s+\d+', text.strip()):
                            transports.append(text.strip())
                except Exception as e:
                    print(f"  ⚠️ Erreur extraction fallback: {e}")
            
            # Nettoyer et dédupliquer
            transports = list(dict.fromkeys(transports))  # Supprimer les doublons
            return transports[:10]  # Limiter à 10 transports
            
        except Exception as e:
            print(f"  ⚠️ Erreur extraction transports: {e}")
            return []
    
    async def extract_description(self):
        """Extrait la description détaillée"""
        try:
            # Essayer différents sélecteurs pour la description
            description_selectors = [
                '.fz-16.sc-bxivhb.fcnykg',
                '[class*="description"]',
                'p:has-text("Globalstone")',
                'text=/Globalstone/',
                'div:has-text("Globalstone")',
                'section:has-text("Globalstone")'
            ]
            
            for selector in description_selectors:
                try:
                    element = self.page.locator(selector).first
                    if await element.count() > 0:
                        text = await element.text_content()
                        if text and len(text.strip()) > 50:  # S'assurer qu'on a une vraie description
                            return text.strip()
                except:
                    continue
            
            return "Description non trouvée"
        except:
            return "Description non trouvée"
    
    async def extract_map_info(self, apartment_id=None):
        """Extrait les informations de la carte (rues, quartier, métros)"""
        try:
            print("   🗺️ Analyse de la carte...")
            
            # Initialiser screenshot_path
            screenshot_path = None
            
            # Prendre un screenshot de la carte pour analyse
            map_element = self.page.locator('.leaflet-container, [class*="map"], [class*="carte"]').first
            if await map_element.count() > 0:
                # Attendre que la carte se charge complètement pour cet appartement
                # Attendre que les tuiles de la carte soient chargées
                await self.page.wait_for_timeout(1000)
                
                # Attendre que la carte soit visible et chargée
                try:
                    await map_element.wait_for(state='visible', timeout=5000)
                except:
                    pass
                
                # Attendre un peu plus pour que la carte se centre sur l'appartement
                await self.page.wait_for_timeout(2000)
                
                # Scroller vers la carte pour s'assurer qu'elle est visible
                try:
                    await map_element.scroll_into_view_if_needed()
                    await self.page.wait_for_timeout(1000)
                except:
                    pass
                
                # Prendre un screenshot de la carte avec l'ID de l'appartement dans le nom
                if apartment_id:
                    screenshot_path = f"data/screenshots/map_{apartment_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                else:
                    screenshot_path = f"data/screenshots/map_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                os.makedirs("data/screenshots", exist_ok=True)
                await map_element.screenshot(path=screenshot_path)
                print(f"   📸 Screenshot de la carte sauvegardé: {screenshot_path}")
            
            # Extraire le texte visible sur la carte
            map_text = ""
            try:
                map_text = await map_element.text_content()
            except:
                pass
            
            # Chercher des noms de rues dans le contenu de la page
            page_content = await self.page.text_content('body')
            
            # Patterns pour identifier les rues et quartiers
            street_patterns = [
                r'Rue\s+[A-Za-z\s\-\']+',
                r'Avenue\s+[A-Za-z\s\-\']+',
                r'Boulevard\s+[A-Za-z\s\-\']+',
                r'Place\s+[A-Za-z\s\-\']+',
                r'Cours\s+[A-Za-z\s\-\']+',
                r'Villa\s+[A-Za-z\s\-\']+',
                r'Impasse\s+[A-Za-z\s\-\']+',
                r'Allée\s+[A-Za-z\s\-\']+',
                r'Passage\s+[A-Za-z\s\-\']+',
                r'Chemin\s+[A-Za-z\s\-\']+'
            ]
            
            metro_patterns = [
                r'[A-Za-z\s\-\']+\s*\(métro\)',
                r'Station\s+[A-Za-z\s\-\']+',
                r'Métro\s+[A-Za-z\s\-\']+'
            ]
            
            # Extraire les rues
            streets_found = []
            for pattern in street_patterns:
                matches = re.findall(pattern, page_content, re.IGNORECASE)
                for match in matches:
                    clean_street = re.sub(r'\s+', ' ', match.strip())
                    if len(clean_street) > 5 and clean_street not in streets_found:
                        streets_found.append(clean_street)
            
            # Extraire les métros
            metros_found = []
            for pattern in metro_patterns:
                matches = re.findall(pattern, page_content, re.IGNORECASE)
                for match in matches:
                    clean_metro = re.sub(r'\s+', ' ', match.strip())
                    if len(clean_metro) > 3 and clean_metro not in metros_found:
                        metros_found.append(clean_metro)
            
            # Identifier le quartier basé sur les rues trouvées
            quartier = self.identify_quartier(streets_found, metros_found)
            
            map_info = {
                "streets": streets_found[:10],  # Limiter à 10 rues
                "metros": metros_found[:5],     # Limiter à 5 métros
                "quartier": quartier,
                "screenshot": screenshot_path if 'screenshot_path' in locals() else None
            }
            
            print(f"   🏘️ Quartier identifié: {quartier}")
            print(f"   🛣️ Rues trouvées: {len(streets_found)}")
            print(f"   🚇 Métros trouvés: {len(metros_found)}")
            
            return map_info
            
        except Exception as e:
            print(f"   ❌ Erreur analyse carte: {e}")
            return {"streets": [], "metros": [], "quartier": "Non identifié", "error": str(e)}
    
    def identify_quartier(self, streets, metros):
        """Identifie le quartier basé sur les rues et métros trouvés - TOUS les arrondissements"""
        # Quartiers du 19e avec leurs rues caractéristiques
        quartiers_19e = {
            "Buttes-Chaumont": ["Rue Botzaris", "Avenue Secrétan", "Rue Manin", "Rue de Crimée", "Botzaris", "Secrétan", "Manin", "Crimée"],
            "Place des Fêtes": ["Rue Carducci", "Rue Mélingue", "Rue des Alouettes", "Rue de la Villette", "Carducci", "Mélingue", "Alouettes", "Villette"],
            "Jourdain": ["Rue de Belleville", "Rue Pelleport", "Rue de Mouzaïa", "Rue Compans", "Belleville", "Pelleport", "Mouzaïa", "Compans"],
            "Pyrénées": ["Rue Pradier", "Rue Clavel", "Rue Rébeval", "Rue Levert", "Pradier", "Clavel", "Rébeval", "Levert"],
            "Belleville": ["Rue de Belleville", "Rue du Faubourg du Temple", "Boulevard de la Villette", "Belleville", "Faubourg du Temple", "Villette"],
            "Canal de l'Ourcq": ["Quai de la Loire", "Quai de la Seine", "Rue de l'Ourcq", "Loire", "Seine", "Ourcq"]
        }
        
        # Quartiers du 20e avec leurs rues caractéristiques
        quartiers_20e = {
            "Ménilmontant": ["Rue de Ménilmontant", "Rue Oberkampf", "Rue de la Folie-Méricourt", "Rue de la Roquette", "Ménilmontant", "Oberkampf", "Folie-Méricourt", "Roquette"],
            "Père-Lachaise": ["Rue de la Roquette", "Rue de Ménilmontant", "Rue du Repos", "Rue des Pyrénées", "Rue Père-Lachaise", "Roquette", "Repos", "Père-Lachaise"],
            "Belleville (20e)": ["Rue de Belleville", "Rue des Pyrénées", "Rue de Ménilmontant", "Belleville", "Pyrénées"],
            "Charonne": ["Rue de Charonne", "Rue du Faubourg Saint-Antoine", "Charonne", "Faubourg Saint-Antoine"],
            "Gambetta": ["Place Gambetta", "Rue des Pyrénées", "Avenue Gambetta", "Gambetta"]
        }
        
        # Quartiers du 11e avec leurs rues caractéristiques
        quartiers_11e = {
            "Goncourt": ["Rue Oberkampf", "Rue de la Folie-Méricourt", "Rue Jean-Pierre Timbaud", "Oberkampf", "Folie-Méricourt", "Timbaud"],
            "République": ["Place de la République", "Boulevard Voltaire", "Rue du Faubourg du Temple", "République", "Voltaire"],
            "Nation": ["Place de la Nation", "Avenue du Trône", "Rue du Faubourg Saint-Antoine", "Nation", "Trône"],
            "Bastille": ["Place de la Bastille", "Rue de la Roquette", "Boulevard Richard-Lenoir", "Bastille", "Roquette", "Richard-Lenoir"]
        }
        
        # Quartiers du 10e avec leurs rues caractéristiques
        quartiers_10e = {
            "Rue des Boulets": ["Rue des Boulets", "Rue de Montreuil", "Boulets", "Montreuil"],
            "Gare du Nord": ["Rue du Faubourg Saint-Denis", "Boulevard de Magenta", "Faubourg Saint-Denis", "Magenta"],
            "Canal Saint-Martin": ["Quai de Valmy", "Quai de Jemmapes", "Rue du Faubourg du Temple", "Valmy", "Jemmapes"]
        }
        
        # Combiner tous les quartiers
        all_quartiers = {}
        all_quartiers.update(quartiers_19e)
        all_quartiers.update(quartiers_20e)
        all_quartiers.update(quartiers_11e)
        all_quartiers.update(quartiers_10e)
        
        # Métros caractéristiques par quartier
        metros_quartiers = {
            "Place des Fêtes": ["Place des Fêtes", "Place des Fetes"],
            "Jourdain": ["Jourdain"],
            "Pyrénées": ["Pyrénées", "Pyrenees"],
            "Buttes-Chaumont": ["Botzaris", "Crimée"],
            "Belleville": ["Belleville", "Couronnes"],
            "Ménilmontant": ["Ménilmontant", "Père-Lachaise", "Gambetta", "Philippe-Auguste"],
            "Père-Lachaise": ["Père-Lachaise", "Gambetta", "Philippe-Auguste", "Ménilmontant"],
            "Goncourt": ["Goncourt", "Parmentier", "République"],
            "République": ["République", "Goncourt", "Parmentier"],
            "Nation": ["Nation", "Faidherbe-Chaligny"],
            "Bastille": ["Bastille", "Ledru-Rollin", "Bréguet-Sabin"],
            "Rue des Boulets": ["Rue des Boulets", "Nation", "Faidherbe-Chaligny"]
        }
        
        # Compter les correspondances
        quartier_scores = {}
        
        # Score basé sur les rues
        for quartier, rues_quartier in all_quartiers.items():
            score = 0
            for rue in streets:
                for rue_quartier in rues_quartier:
                    if rue_quartier.lower() in rue.lower():
                        score += 1
            quartier_scores[quartier] = score
        
        # Ajouter les scores des métros (score plus élevé car plus fiable)
        for quartier, metros_quartier in metros_quartiers.items():
            for metro in metros:
                for metro_quartier in metros_quartier:
                    if metro_quartier.lower() in metro.lower():
                        quartier_scores[quartier] = quartier_scores.get(quartier, 0) + 2
        
        # Retourner le quartier avec le plus haut score
        if quartier_scores:
            best_quartier = max(quartier_scores, key=quartier_scores.get)
            if quartier_scores[best_quartier] > 0:
                return f"{best_quartier} (score: {quartier_scores[best_quartier]})"
        
        return "Quartier non identifié"
    
    def analyze_screenshot_for_quartier(self, screenshot_path):
        """Analyse le screenshot pour identifier le quartier (méthode basique)"""
        try:
            if not os.path.exists(screenshot_path):
                return "Screenshot non trouvé"
            
            # Pour l'instant, on retourne une analyse basée sur la description
            # Dans une version avancée, on pourrait utiliser OCR ou vision par ordinateur
            return "Analyse manuelle requise - voir screenshot"
            
        except Exception as e:
            return f"Erreur analyse: {e}"
    
    async def extract_coordinates(self):
        """Extrait les coordonnées GPS depuis la carte Leaflet"""
        try:
            # Chercher les éléments de la carte Leaflet avec différents sélecteurs
            leaflet_selectors = [
                '.leaflet-proxy',
                '.leaflet-map-pane', 
                '.leaflet-container',
                '[class*="leaflet"]'
            ]
            
            coordinates = None
            for selector in leaflet_selectors:
                elements = self.page.locator(selector)
                count = await elements.count()
                
                for i in range(count):
                    element = elements.nth(i)
                    style = await element.get_attribute('style')
                    
                    if style and 'translate3d' in style:
                        print(f"   🔍 Style trouvé: {style[:100]}...")
                        
                        # Extraire les coordonnées du transform avec regex plus robuste
                        import re
                        patterns = [
                            r'translate3d\(([^,]+),\s*([^,]+),\s*([^)]+)\)',
                            r'translate3d\(([^,]+),\s*([^,]+),\s*([^)]+)\)',
                            r'transform:\s*translate3d\(([^,]+),\s*([^,]+),\s*([^)]+)\)'
                        ]
                        
                        for pattern in patterns:
                            match = re.search(pattern, style)
                            if match:
                                try:
                                    x_str = match.group(1).strip()
                                    y_str = match.group(2).strip()
                                    scale_str = match.group(3).strip()
                                    
                                    print(f"   📍 Coordonnées brutes: x={x_str}, y={y_str}, scale={scale_str}")
                                    
                                    # Nettoyer et convertir les valeurs
                                    x = float(x_str.replace('px', '').replace('e+', 'e'))
                                    y = float(y_str.replace('px', '').replace('e+', 'e'))
                                    scale = float(scale_str.replace('px', '')) if scale_str != '0px' else 1.0
                                    
                                    # Vérifier que les valeurs sont valides (pas 0)
                                    if abs(x) > 1000 and abs(y) > 1000:  # Coordonnées Web Mercator valides
                                        # Convertir les coordonnées Web Mercator en lat/lng
                                        lon = (x / 20037508.34) * 180
                                        lat = (y / 20037508.34) * 180
                                        lat = 180 / 3.14159265359 * (2 * math.atan(math.exp(lat * 3.14159265359 / 180)) - 3.14159265359 / 2)
                                        
                                        coordinates = {
                                            "latitude": round(lat, 6),
                                            "longitude": round(lon, 6),
                                            "raw_x": x,
                                            "raw_y": y,
                                            "scale": scale
                                        }
                                        print(f"   ✅ Coordonnées converties: {lat:.6f}, {lon:.6f}")
                                        break
                                    else:
                                        print(f"   ⚠️ Coordonnées invalides (trop petites): x={x}, y={y}")
                                        
                                except ValueError as ve:
                                    print(f"   ❌ Erreur de conversion: {ve}")
                                    continue
                        
                        if coordinates:
                            break
                
                if coordinates:
                    break
            
            if not coordinates:
                print("   ❌ Aucune coordonnée valide trouvée")
                return {"latitude": None, "longitude": None, "error": "No valid coordinates found"}
            
            return coordinates
            
        except Exception as e:
            print(f"   ❌ Erreur générale: {e}")
            return {"latitude": None, "longitude": None, "error": str(e)}
    
    async def extract_style_haussmannien(self):
        """Extrait les éléments de style haussmannien"""
        try:
            # Récupérer la description
            description = await self.extract_description()
            if description == "Description non trouvée":
                return {"score": 0, "elements": [], "keywords": []}
            
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
            
            # Chercher les mots-clés par catégorie
            found_by_category = {}
            total_found = 0
            all_keywords = []
            
            for category, keywords in haussmann_keywords.items():
                found_in_category = []
                for keyword in keywords:
                    if keyword.lower() in description.lower():
                        found_in_category.append(keyword)
                        all_keywords.append(keyword)
                        total_found += 1
                
                if found_in_category:
                    found_by_category[category] = found_in_category
            
            # Calculer un score de style
            style_score = min(100, (total_found * 10) + 20)  # 10 points par mot-clé + 20 de base
            
            return {
                "score": style_score,
                "elements": found_by_category,
                "keywords": all_keywords,
                "total_found": total_found
            }
            
        except Exception as e:
            return {"score": 0, "elements": [], "keywords": [], "error": str(e)}
    
    async def extract_photos(self):
        """Extrait les URLs des photos d'appartement depuis la div spécifique"""
        try:
            print("   📸 Extraction des photos d'appartement...")
            
            # Extraire les informations pour la description des photos
            etage = await self.extract_etage()
            surface = await self.extract_surface()
            prix_m2 = await self.extract_prix_m2()
            style = await self.extract_style_for_photo()
            
            if etage:
                print(f"      🏢 Étage trouvé: {etage}")
            if surface:
                print(f"      📐 Surface trouvée: {surface}")
            if prix_m2:
                print(f"      💰 Prix au m² trouvé: {prix_m2}")
            if style:
                print(f"      🎨 Style trouvé: {style}")
            
            photos = []
            
            # Attendre un peu plus longtemps pour le chargement des images lazy
            await asyncio.sleep(1)
            
            # Scroller un peu pour déclencher le chargement lazy si nécessaire
            await self.page.evaluate('window.scrollTo(0, 200)')
            await asyncio.sleep(0.5)
            await self.page.evaluate('window.scrollTo(0, 0)')
            await asyncio.sleep(0.5)
            
            # Méthode 1: Cibler la div galerie principale (sc-cJSrbW juBoVb ou sc-gPEVay jnWxBz)
            # Aussi chercher dans les divs cachées avec display="none" qui contiennent toutes les photos
            gallery_selectors = [
                'div.sc-cJSrbW.juBoVb',  # Structure actuelle visible dans l'image
                'div.sc-gPEVay.jnWxBz',  # Ancienne structure
                '[class*="sc-cJSrbW"][class*="juBoVb"]',  # Sélecteurs partiels
                '[class*="sc-gPEVay"][class*="jnWxBz"]',
                'div.sc-bdVaJa.InsofV',  # Div cachée avec toutes les photos (display="none")
                '[class*="sc-bdVaJa"][class*="InsofV"]',  # Sélecteur partiel
                'div[style*="display: none"]',  # Toute div cachée
            ]
            
            gallery_found = False
            for selector in gallery_selectors:
                try:
                    gallery_div = self.page.locator(selector)
                    if await gallery_div.count() > 0:
                        print(f"      🎯 Div galerie trouvée ({selector}), extraction des images visibles...")
                        gallery_found = True
                        
                        # Extraire toutes les images de la galerie (visibles ET cachées avec preloader)
                        gallery_element = await gallery_div.first.element_handle()
                        img_elements = await gallery_element.evaluate('''
                            el => {
                                // Obtenir toutes les images dans l'ordre exact du DOM (même cachées)
                                const allImgs = Array.from(el.querySelectorAll('img'));
                                
                                // Extraire les infos avec position visuelle pour tri correct
                                return allImgs.map((img, domIndex) => {
                                    const rect = img.getBoundingClientRect();
                                    const computedStyle = window.getComputedStyle(img);
                                    return {
                                        domIndex: domIndex,  // Index dans le DOM
                                        src: img.src || img.getAttribute('data-src') || img.getAttribute('data-lazy-src') || '',
                                        alt: img.alt || '',
                                        width: img.naturalWidth || img.width || 0,
                                        height: img.naturalHeight || img.height || 0,
                                        display: computedStyle.display,
                                        visibility: computedStyle.visibility,
                                        top: rect.top,  // Position top pour tri visuel
                                        left: rect.left  // Position left pour tri visuel
                                    };
                                }).filter(img => {
                                    // Garder toutes les images avec une URL valide
                                    if (!img.src) return false;
                                    
                                    const srcLower = img.src.toLowerCase();
                                    const altLower = img.alt.toLowerCase();
                                    
                                    // Vérifier si l'image est visible (pas display:none et position non-0,0)
                                    const isVisible = img.display !== 'none' && (img.top !== 0 || img.left !== 0);
                                    const hasGoodDimensions = img.width > 200 && img.height > 200;
                                    
                                    // 1. Exclure les placeholders explicites (toujours)
                                    if (srcLower.includes('placeholder')) return false;
                                    
                                    // 2. LOGIQUE AMÉLIORÉE : Accepter les images VISIBLES même si FNAIM
                                    // Si l'image est visible ET a de bonnes dimensions, c'est probablement une vraie photo
                                    if (isVisible && hasGoodDimensions) {
                                        // Accepter les images visibles même si elles utilisent FNAIM
                                        // Car elles sont affichées sur la page
                                        return true;
                                    }
                                    
                                    // 3. Pour les images cachées ou petites, filtrer les placeholders FNAIM
                                    const placeholderUrlPatterns = [
                                        'imagesv2.fnaim.fr/images1/img/',  // Placeholder FNAIM
                                        'placeholder',
                                        'placeholder.jpg',
                                        'placeholder.png',
                                        'no-image',
                                        'default-image',
                                        'missing-image',
                                    ];
                                    const isPlaceholderUrl = placeholderUrlPatterns.some(pattern => srcLower.includes(pattern));
                                    if (isPlaceholderUrl && !isVisible) {
                                        // Si c'est un placeholder ET que l'image n'est pas visible, exclure
                                        return false;
                                    }
                                    
                                    // 4. Exclure les images avec alt="preloader" SI cachées ET placeholder FNAIM
                                    if ((altLower.includes('preloader') || altLower === 'preloader') && 
                                        srcLower.includes('imagesv2.fnaim.fr/images1/img/') && 
                                        !isVisible) {
                                        return false;
                                    }
                                    
                                    // 5. Détecter les vraies photos d'appartements (patterns étendus)
                                    const photoPatterns = [
                                        'loueragile', 
                                        'upload_pro_ad', 
                                        'media.apimo.pro', 
                                        'studio-net.fr', 
                                        'images.century21.fr', 
                                        'biens', 
                                        'apartement', 
                                        'transopera', 
                                        'staticlbi', 
                                        'uploadcaregdc', 
                                        'uploadcare', 
                                        's3.amazonaws.com', 
                                        'googleusercontent.com', 
                                        'cdn.safti.fr', 
                                        'safti.fr', 
                                        'paruvendu.fr', 
                                        'immo-facile.com', 
                                        'mms.seloger.com', 
                                        'seloger.com',
                                        'api.jinka.fr/apiv2/media/imgsrv',  // Proxy Jinka pour vraies photos
                                        'photos.ubif',  // Photos originales via proxy Jinka
                                        'res.cloudinary.com',  // Cloudinary (souvent utilisé pour photos immo)
                                        'cloudinary.com',
                                        'photos.',  // Pattern générique pour photos (mais pas "placeholder")
                                        'imagesv2.fnaim.fr',  // Accepter FNAIM si image visible avec bonnes dimensions
                                    ];
                                    const hasValidPhotoPattern = photoPatterns.some(pattern => srcLower.includes(pattern));
                                    
                                    // 6. Si c'est une vraie photo (pattern valide), on la garde
                                    // OU si c'est une image visible avec bonnes dimensions (même FNAIM)
                                    if (hasValidPhotoPattern || (isVisible && hasGoodDimensions)) {
                                        return true;
                                    }
                                    
                                    return false;
                                });
                            }
                        ''')
                        
                        # Extraire les photos avec leur index DOM pour préserver l'ordre de Jinka
                        photos_with_position = []
                        for img_data in img_elements:
                            try:
                                src_to_use = img_data.get('src', '')
                                if not src_to_use:
                                    continue
                                
                                # Vérifier que c'est une vraie photo (pas un logo)
                                src_lower = src_to_use.lower()
                                alt_lower = img_data.get('alt', '').lower()
                                
                                if 'logo' in src_lower or 'source_logos' in src_lower:
                                    continue
                                
                                # Vérifier si l'image est visible (position non-0,0 et bonnes dimensions)
                                position_top = img_data.get('position_top', 0)
                                position_left = img_data.get('position_left', 0)
                                width = img_data.get('width', 0)
                                height = img_data.get('height', 0)
                                is_visible = (position_top != 0 or position_left != 0)
                                has_good_dimensions = width > 200 and height > 200
                                
                                # LOGIQUE AMÉLIORÉE : Accepter les images VISIBLES même si FNAIM
                                # Si l'image est visible ET a de bonnes dimensions, c'est probablement une vraie photo
                                if is_visible and has_good_dimensions:
                                    # Accepter les images visibles même si elles utilisent FNAIM
                                    # Car elles sont affichées sur la page
                                    pass  # Continuer pour ajouter la photo
                                else:
                                    # Pour les images cachées ou petites, filtrer les placeholders FNAIM
                                    placeholder_patterns = [
                                        'imagesv2.fnaim.fr/images1/img/',  # Placeholder FNAIM
                                        'placeholder',
                                        'placeholder.jpg',
                                        'no-image',
                                        'default-image',
                                    ]
                                    if any(pattern in src_lower for pattern in placeholder_patterns):
                                        continue
                                    
                                    # Si alt="preloader" ET placeholder FNAIM ET pas visible, exclure
                                    if 'preloader' in alt_lower and 'imagesv2.fnaim.fr/images1/img/' in src_lower:
                                        continue
                                
                                # Accepter les URLs de vraies photos d'appartements (patterns étendus)
                                # OU accepter les images visibles avec bonnes dimensions (même FNAIM)
                                photo_patterns = [
                                    'loueragile', 
                                    'upload_pro_ad', 
                                    'media.apimo.pro', 
                                    'studio-net.fr', 
                                    'images.century21.fr', 
                                    'biens', 
                                    'apartement', 
                                    'transopera', 
                                    'staticlbi', 
                                    'uploadcaregdc', 
                                    'uploadcare', 
                                    's3.amazonaws.com', 
                                    'googleusercontent.com', 
                                    'cdn.safti.fr', 
                                    'safti.fr', 
                                    'paruvendu.fr', 
                                    'immo-facile.com', 
                                    'mms.seloger.com', 
                                    'seloger.com',
                                    'api.jinka.fr/apiv2/media/imgsrv',  # Proxy Jinka
                                    'photos.ubif',  # Photos via proxy Jinka
                                    'res.cloudinary.com',
                                    'cloudinary.com',
                                    'photos.',
                                    'imagesv2.fnaim.fr',  # Accepter FNAIM si image visible
                                ]
                                has_valid_pattern = any(pattern in src_lower for pattern in photo_patterns)
                                
                                # Accepter si pattern valide OU si image visible avec bonnes dimensions
                                if not has_valid_pattern and not (is_visible and has_good_dimensions):
                                    continue
                                
                                # Vérifier les dimensions de l'image (exclure les très petites comme les logos)
                                width = img_data.get('width', 0)
                                height = img_data.get('height', 0)
                                
                                # Les logos font généralement ~128x128px, les vraies photos sont beaucoup plus grandes
                                # On exclut seulement les images très petites (< 200px)
                                if width > 0 and height > 0:
                                    if width < 200 or height < 200:
                                        # Probablement un logo ou icône (ex: logo immobilier 128x128), on skip
                                        continue
                                
                                # Formater la description complète avec toutes les infos
                                alt = self.format_photo_description(surface, prix_m2, etage, style)
                                
                                position_top = img_data.get('top', 0)
                                position_left = img_data.get('left', 0)
                                
                                # Garder toutes les photos valides, même si cachées (display="none")
                                # Les photos avec alt="preloader" dans des divs cachées sont souvent les vraies photos
                                
                                photos_with_position.append({
                                    'url': src_to_use,
                                    'alt': alt or 'appartement',
                                    'selector': 'gallery_div_visible',
                                    'width': width,
                                    'height': height,
                                    'dom_index': img_data.get('domIndex', 0),
                                    'position_top': position_top,
                                    'position_left': position_left
                                })
                            except Exception as e:
                                continue
                        
                        # Dédupliquer par URL, en gardant la photo avec la meilleure position (visible de préférence)
                        url_to_photo = {}
                        for photo in photos_with_position:
                            url = photo['url']
                            top = photo.get('position_top', 0)
                            left = photo.get('position_left', 0)
                            
                            # Si on a déjà cette URL
                            if url in url_to_photo:
                                existing_top = url_to_photo[url].get('position_top', 0)
                                existing_left = url_to_photo[url].get('position_left', 0)
                                
                                # Préférer la photo avec position non-0,0 (visible)
                                if (top != 0 or left != 0) and (existing_top == 0 and existing_left == 0):
                                    # Nouvelle photo est visible, remplacer
                                    url_to_photo[url] = photo
                                elif (top == 0 and left == 0) and (existing_top != 0 or existing_left != 0):
                                    # Photo existante est visible, garder celle-là
                                    pass
                                else:
                                    # Les deux ont même type de position, garder la première
                                    pass
                            else:
                                # Première occurrence de cette URL
                                url_to_photo[url] = photo
                        
                        photos_with_position = list(url_to_photo.values())
                        
                        # Séparer les photos visibles (position != 0,0) des photos cachées (0,0)
                        visible_photos = [p for p in photos_with_position if p.get('position_top', 0) != 0 or p.get('position_left', 0) != 0]
                        hidden_photos = [p for p in photos_with_position if p.get('position_top', 0) == 0 and p.get('position_left', 0) == 0]
                        
                        # Trier les photos visibles par position (top puis left) pour l'ordre visuel
                        visible_photos.sort(key=lambda x: (x.get('position_top', 0), x.get('position_left', 0)))
                        
                        # Trier les photos cachées par index DOM pour préserver l'ordre de Jinka
                        hidden_photos.sort(key=lambda x: x.get('dom_index', 0))
                        
                        # Combiner : photos visibles d'abord, puis photos cachées dans l'ordre DOM
                        photos_with_position = visible_photos + hidden_photos
                        print(f"      ✅ {len(visible_photos)} photos visibles + {len(hidden_photos)} photos cachées = {len(photos_with_position)} photos au total")
                        
                        # Ajouter les photos dans l'ordre correct (ordre visuel de Jinka)
                        for photo_with_pos in photos_with_position:
                            photo = {k: v for k, v in photo_with_pos.items() if k not in ['dom_index', 'position_top', 'position_left']}
                            photos.append(photo)
                            print(f"      📸 Photo galerie (top: {photo_with_pos.get('position_top', 0):.0f}, left: {photo_with_pos.get('position_left', 0):.0f}, {photo_with_pos['width']}x{photo_with_pos['height']}): {photo_with_pos['url'][:60]}...")
                        
                        if len(photos) > 0:
                            # Ne pas break, continuer à chercher dans d'autres sélecteurs pour accumuler toutes les photos
                            pass
                except Exception as e:
                    continue
            
            # Après avoir cherché dans toutes les galeries, dédupliquer
            if len(photos) > 0:
                unique_photos_temp = []
                seen_urls_temp = set()
                for photo in photos:
                    if photo['url'] not in seen_urls_temp:
                        unique_photos_temp.append(photo)
                        seen_urls_temp.add(photo['url'])
                photos = unique_photos_temp
                print(f"      ✅ {len(photos)} photos uniques trouvées après déduplication")
            
            # Méthode 2: Si pas de photos dans la galerie, chercher les images visibles avec URLs d'appartement
            if len(photos) == 0:
                print("      ⚠️ Aucune photo dans la galerie, recherche d'images visibles...")
                
                # Attendre un peu pour que les images lazy-loaded se chargent
                await asyncio.sleep(2)
                
                # Chercher UNIQUEMENT les images visibles avec URLs d'appartement
                all_visible_images = await self.page.locator('img:visible').all()
                print(f"      🔍 {len(all_visible_images)} images visibles totales sur la page")
                
                # Méthode 2a: Chercher dans les images visibles
                for img in all_visible_images:
                    try:
                        # Vérifier que l'image est vraiment visible
                        display = await img.evaluate('el => window.getComputedStyle(el).display')
                        if display == 'none':
                            continue
                        
                        # Vérifier les dimensions de l'image (exclure les très petites comme les logos)
                        width = await img.evaluate('el => el.naturalWidth || el.width || 0')
                        height = await img.evaluate('el => el.naturalHeight || el.height || 0')
                        
                        # Les logos font généralement ~128x128px, les vraies photos sont beaucoup plus grandes
                        # On exclut seulement les images très petites (< 200px)
                        if width > 0 and height > 0:
                            if width < 200 or height < 200:
                                # Probablement un logo ou icône (ex: logo immobilier 128x128), on skip
                                continue
                        
                        src = await img.get_attribute('src')
                        # Chercher aussi dans data-src (lazy loading)
                        data_src = await img.get_attribute('data-src')
                        src_to_use = src or data_src
                        
                        # Vérifier si l'image est visible et a de bonnes dimensions
                        src_lower = src_to_use.lower()
                        alt_attr = await img.get_attribute('alt') or ''
                        alt_lower = alt_attr.lower()
                        
                        # Vérifier la visibilité réelle de l'image
                        is_visible_element = display != 'none'
                        bounding_box = await img.bounding_box()
                        is_in_viewport = bounding_box is not None and bounding_box['width'] > 0 and bounding_box['height'] > 0
                        is_visible = is_visible_element and is_in_viewport
                        
                        # LOGIQUE AMÉLIORÉE : Accepter les images VISIBLES même si FNAIM
                        # Si l'image est visible ET a de bonnes dimensions, c'est probablement une vraie photo
                        if is_visible and width > 200 and height > 200:
                            # Accepter les images visibles même si elles utilisent FNAIM
                            # Car elles sont affichées sur la page
                            pass  # Continuer pour ajouter la photo
                        else:
                            # Pour les images cachées ou petites, filtrer les placeholders FNAIM
                            placeholder_patterns = [
                                'imagesv2.fnaim.fr/images1/img/',  # Placeholder FNAIM
                                'placeholder',
                                'placeholder.jpg',
                                'no-image',
                                'default-image',
                            ]
                            if any(pattern in src_lower for pattern in placeholder_patterns):
                                continue
                            
                            # Si alt="preloader" ET placeholder FNAIM ET pas visible, exclure
                            if 'preloader' in alt_lower and 'imagesv2.fnaim.fr/images1/img/' in src_lower:
                                continue
                        
                        # Accepter les URLs de vraies photos d'appartements (patterns étendus)
                        photo_patterns = [
                            'loueragile', 
                            'upload_pro_ad', 
                            'media.apimo.pro', 
                            'studio-net.fr', 
                            'images.century21.fr', 
                            'biens', 
                            'apartement', 
                            'transopera', 
                            'staticlbi', 
                            'uploadcaregdc', 
                            'uploadcare', 
                            's3.amazonaws.com', 
                            'googleusercontent.com', 
                            'cdn.safti.fr', 
                            'safti.fr', 
                            'paruvendu.fr', 
                            'immo-facile.com', 
                            'mms.seloger.com', 
                            'seloger.com',
                            'api.jinka.fr/apiv2/media/imgsrv',  # Proxy Jinka
                            'photos.ubif',  # Photos via proxy Jinka
                            'res.cloudinary.com',
                            'cloudinary.com',
                            'photos.',
                            'imagesv2.fnaim.fr',  # Accepter FNAIM si image visible
                        ]
                        if src_to_use and any(pattern in src_lower for pattern in photo_patterns):
                            # Exclure les logos (mais pas si image visible avec bonnes dimensions)
                            if 'logo' in src_lower or 'source_logos' in src_lower:
                                if not (is_visible and width > 200 and height > 200):
                                    continue
                            
                            # Formater la description complète avec toutes les infos
                            alt = self.format_photo_description(surface, prix_m2, etage, style)
                            
                            photos.append({
                                'url': src_to_use,
                                'alt': alt or 'appartement',
                                'selector': 'global_search_visible',
                                'width': width,
                                'height': height
                            })
                            print(f"      📸 Photo visible ({width}x{height}): {src_to_use[:60]}...")
                    except Exception as e:
                        continue
                
                # Méthode 2b: Si toujours rien, chercher dans toutes les images (même cachées, au cas où)
                if len(photos) == 0:
                    print("      🔍 Recherche alternative dans toutes les images (y compris lazy-loaded)...")
                    all_images = await self.page.locator('img').all()
                    
                    for img in all_images:
                        try:
                            # Récupérer src et data-src (pour lazy loading)
                            src = await img.get_attribute('src')
                            data_src = await img.get_attribute('data-src')
                            data_lazy = await img.get_attribute('data-lazy-src')
                            src_to_use = src or data_src or data_lazy
                            
                            if not src_to_use:
                                continue
                            
                            # Vérifier les dimensions si l'image est chargée
                            width = 0
                            height = 0
                            try:
                                width = await img.evaluate('el => el.naturalWidth || el.width || 0')
                                height = await img.evaluate('el => el.naturalHeight || el.height || 0')
                            except:
                                pass  # Si l'image n'est pas encore chargée, on garde quand même
                            
                            # Vérifier si l'image est visible et a de bonnes dimensions
                            src_lower = src_to_use.lower()
                            alt_attr = await img.get_attribute('alt') or ''
                            alt_lower = alt_attr.lower()
                            
                            # Vérifier la visibilité et les dimensions
                            try:
                                bounding_box = await img.bounding_box()
                                is_visible = bounding_box is not None and bounding_box['width'] > 0 and bounding_box['height'] > 0
                            except:
                                is_visible = False
                            
                            # LOGIQUE AMÉLIORÉE : Accepter les images VISIBLES même si FNAIM
                            if is_visible and width > 200 and height > 200:
                                # Accepter les images visibles même si elles utilisent FNAIM
                                pass  # Continuer pour ajouter la photo
                            else:
                                # Pour les images cachées ou petites, filtrer les placeholders FNAIM
                                placeholder_patterns = [
                                    'imagesv2.fnaim.fr/images1/img/',  # Placeholder FNAIM
                                    'placeholder',
                                    'placeholder.jpg',
                                    'no-image',
                                    'default-image',
                                ]
                                if any(pattern in src_lower for pattern in placeholder_patterns):
                                    continue
                                
                                # Si alt="preloader" ET placeholder FNAIM ET pas visible, exclure
                                if 'preloader' in alt_lower and 'imagesv2.fnaim.fr/images1/img/' in src_lower:
                                    continue
                            
                            # Filtrer par URL (patterns étendus) OU accepter si visible avec bonnes dimensions
                            photo_patterns = [
                                'loueragile', 
                                'upload_pro_ad', 
                                'media.apimo.pro', 
                                'studio-net.fr', 
                                'images.century21.fr', 
                                'biens', 
                                'apartement', 
                                'transopera', 
                                'staticlbi', 
                                'uploadcaregdc', 
                                'uploadcare', 
                                's3.amazonaws.com', 
                                'googleusercontent.com', 
                                'cdn.safti.fr', 
                                'safti.fr', 
                                'paruvendu.fr', 
                                'immo-facile.com', 
                                'mms.seloger.com', 
                                'seloger.com',
                                'api.jinka.fr/apiv2/media/imgsrv',  # Proxy Jinka
                                'photos.ubif',  # Photos via proxy Jinka
                                'res.cloudinary.com',
                                'cloudinary.com',
                                'photos.',
                                'imagesv2.fnaim.fr',  # Accepter FNAIM si image visible
                            ]
                            has_valid_pattern = any(pattern in src_lower for pattern in photo_patterns)
                            
                            # Accepter si pattern valide OU si image visible avec bonnes dimensions
                            if not has_valid_pattern and not (is_visible and width > 200 and height > 200):
                                continue
                            
                            # Exclure les logos (mais pas si image visible avec bonnes dimensions)
                            if 'logo' in src_lower or 'source_logos' in src_lower:
                                if not (is_visible and width > 200 and height > 200):
                                    continue
                            
                            # Vérifier les dimensions finales (exclure les très petites sauf si visibles)
                            if width > 0 and height > 0:
                                if width < 200 or height < 200:
                                    # Si l'image est visible malgré sa petite taille, on l'accepte quand même
                                    if not is_visible:
                                        continue
                            
                            photos.append({
                                'url': src_to_use,
                                'alt': await img.get_attribute('alt') or 'appartement',
                                'selector': 'global_search_all',
                                'width': width,
                                'height': height
                            })
                            print(f"      📸 Photo trouvée (lazy-loaded?): {src_to_use[:60]}...")
                        except Exception as e:
                            continue
            
            # Dédupliquer
            unique_photos = []
            seen_urls = set()
            for photo in photos:
                if photo['url'] not in seen_urls:
                    unique_photos.append(photo)
                    seen_urls.add(photo['url'])
            
            print(f"   ✅ {len(unique_photos)} photos d'appartement trouvées")
            return unique_photos  # Retourner toutes les photos disponibles
            
        except Exception as e:
            print(f"   ❌ Erreur extraction photos: {e}")
            return []
    
    async def extract_caracteristiques(self):
        """Extrait les caractéristiques"""
        try:
            # Chercher la section caractéristiques
            char_elements = self.page.locator('h3:has-text("Caractéristiques") + *')
            if await char_elements.count() > 0:
                text = await char_elements.first.text_content()
                return text.strip() if text else "Caractéristiques non trouvées"
            return "Caractéristiques non trouvées"
        except:
            return "Caractéristiques non trouvées"
    
    async def extract_agence(self):
        """Extrait les informations de l'agence"""
        try:
            # Chercher le nom de l'agence
            agence_elements = self.page.locator('text=/[A-Z][A-Z\s]+/')
            for i in range(await agence_elements.count()):
                text = await agence_elements.nth(i).text_content()
                if text and len(text.strip()) > 3 and text.isupper():
                    return text.strip()
            return "Agence non trouvée"
        except:
            return "Agence non trouvée"
    
    async def save_apartment(self, apartment_data, skip_if_exists=False):
        """Sauvegarde les données d'un appartement
        
        Args:
            apartment_data: Données de l'appartement à sauvegarder
            skip_if_exists: Si True, ne pas écraser un fichier existant
        """
        try:
            os.makedirs('data/appartements', exist_ok=True)
            filename = f"data/appartements/{apartment_data['id']}.json"
            
            # Vérifier si le fichier existe déjà
            if skip_if_exists and os.path.exists(filename):
                print(f"⏭️  Appartement {apartment_data['id']} déjà sauvegardé - SKIP")
                return False
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(apartment_data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 Appartement {apartment_data['id']} sauvegardé")
            return True
            
        except Exception as e:
            print(f"❌ Erreur sauvegarde: {e}")
            return False
    
    def update_scraped_apartments_json(self):
        """Met à jour scraped_apartments.json depuis data/appartements/"""
        try:
            appartements_dir = 'data/appartements'
            scraped_file = 'data/scraped_apartments.json'
            
            if not os.path.exists(appartements_dir):
                print(f"⚠️  Dossier {appartements_dir} n'existe pas")
                return False
            
            # Charger tous les appartements depuis les fichiers individuels
            all_apartments = []
            for filename in os.listdir(appartements_dir):
                if filename.endswith('.json') and filename not in ['test_001.json', 'test_no_photo.json', 'unknown.json']:
                    filepath = os.path.join(appartements_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            apt_data = json.load(f)
                            if apt_data.get('id'):
                                all_apartments.append(apt_data)
                    except Exception as e:
                        print(f"⚠️  Erreur lecture {filepath}: {e}")
                        continue
            
            # Sauvegarder dans scraped_apartments.json
            os.makedirs(os.path.dirname(scraped_file), exist_ok=True)
            with open(scraped_file, 'w', encoding='utf-8') as f:
                json.dump(all_apartments, f, ensure_ascii=False, indent=2)
            
            print(f"✅ scraped_apartments.json mis à jour avec {len(all_apartments)} appartements")
            
            # Invalider le cache du backend si possible
            self.invalidate_backend_cache()
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur mise à jour scraped_apartments.json: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def invalidate_backend_cache(self):
        """Invalide le cache du backend en appelant l'endpoint ou en touchant le fichier"""
        try:
            # Méthode 1: Appeler l'endpoint du backend si disponible
            import aiohttp
            import asyncio
            
            async def invalidate_via_api():
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.post('http://localhost:8000/api/apartments/invalidate-cache', timeout=aiohttp.ClientTimeout(total=2)) as response:
                            if response.status == 200:
                                print("✅ Cache backend invalidé via API")
                                return True
                except Exception as e:
                    # Backend non disponible, utiliser méthode 2
                    return False
            
            # Essayer d'invalider via API (non-bloquant)
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Si une boucle est déjà en cours, créer une tâche
                    asyncio.create_task(invalidate_via_api())
                else:
                    loop.run_until_complete(invalidate_via_api())
            except Exception:
                # Si asyncio n'est pas disponible ou si le backend n'est pas démarré, utiliser méthode 2
                pass
            
            # Méthode 2: Toucher le fichier pour forcer le rechargement du cache
            scraped_file = 'data/scraped_apartments.json'
            if os.path.exists(scraped_file):
                # Modifier le timestamp du fichier pour forcer le rechargement
                os.utime(scraped_file, None)
                print("✅ Cache backend invalidé via touch du fichier")
            
        except Exception as e:
            # En cas d'erreur, ne pas bloquer le processus
            print(f"⚠️  Erreur invalidation cache backend: {e}")
            pass
    
    async def download_apartment_photos(self, apartment_id, photos):
        """Télécharge les photos d'un appartement localement avec filtrage par taille"""
        try:
            if not photos:
                return
                
            # Créer le dossier pour les photos
            photos_dir = f"data/photos/{apartment_id}"
            os.makedirs(photos_dir, exist_ok=True)
            
            # Supprimer toutes les photos existantes
            if os.path.exists(photos_dir):
                existing_files = [f for f in os.listdir(photos_dir) if f.endswith(('.jpg', '.jpeg', '.png'))]
                for existing_file in existing_files:
                    file_path = os.path.join(photos_dir, existing_file)
                    try:
                        os.remove(file_path)
                        print(f"      🗑️ Photo existante supprimée: {existing_file}")
                    except Exception as e:
                        print(f"      ⚠️ Erreur suppression {existing_file}: {e}")
            
            # Télécharger et filtrer les photos
            valid_photos = []
            async with aiohttp.ClientSession() as session:
                for i, photo in enumerate(photos):  # Télécharger toutes les photos disponibles
                    url = photo['url']
                    temp_filename = f"{photos_dir}/temp_photo_{i+1}.jpg"
                    
                    try:
                        async with session.get(url) as response:
                            if response.status == 200:
                                content = await response.read()
                                
                                # Sauvegarder temporairement pour analyser
                                with open(temp_filename, 'wb') as f:
                                    f.write(content)
                                
                                # Vérifier si c'est une vraie photo d'appartement
                                if self.is_valid_apartment_photo(temp_filename, content):
                                    # Renommer avec format simple: photo1.jpg, photo2.jpg, etc.
                                    photo_number = len(valid_photos) + 1
                                    final_filename = f"{photos_dir}/photo{photo_number}.jpg"
                                    os.rename(temp_filename, final_filename)
                                    valid_photos.append(final_filename)
                                    print(f"      📸 Photo {photo_number} téléchargée: {final_filename} ({len(content)} bytes)")
                                else:
                                    # Supprimer la photo invalide
                                    os.remove(temp_filename)
                                    print(f"      ❌ Photo {i+1} rejetée: {len(content)} bytes (logo/icône)")
                            else:
                                print(f"      ❌ Erreur photo {i+1}: HTTP {response.status}")
                    except Exception as e:
                        print(f"      ❌ Erreur téléchargement photo {i+1}: {e}")
                        if os.path.exists(temp_filename):
                            os.remove(temp_filename)
            
            print(f"      ✅ {len(valid_photos)} photos d'appartement téléchargées dans {photos_dir}/")
                        
        except Exception as e:
            print(f"❌ Erreur téléchargement photos: {e}")
    
    def is_valid_apartment_photo(self, filepath, content):
        """Vérifie si une photo est une vraie photo d'appartement"""
        try:
            # Vérifier la taille du fichier (pas trop petit, pas trop grand)
            if len(content) < 20000 or len(content) > 500000:  # 20KB - 500KB
                return False
            
            # Vérifier le type de fichier
            if not (content.startswith(b'\xff\xd8\xff') or  # JPEG
                    content.startswith(b'\x89PNG')):  # PNG
                return False
            
            # Pour les PNG, vérifier qu'ils ne sont pas des logos (carrés petits)
            if content.startswith(b'\x89PNG'):
                # Lire les dimensions PNG
                if len(content) >= 24:
                    width = int.from_bytes(content[16:20], 'big')
                    height = int.from_bytes(content[20:24], 'big')
                    # Rejeter les images carrées petites (logos)
                    if width == height and width < 600:
                        return False
                    # Rejeter les images trop petites
                    if width < 400 or height < 300:
                        return False
            
            return True
            
        except Exception as e:
            return False
    
    async def cleanup(self):
        """Ferme le navigateur"""
        if self.browser:
            await self.browser.close()

async def main():
    """Fonction principale"""
    if len(sys.argv) < 2:
        print("Usage: python scrape_jinka.py <URL_ALERTE>")
        print("Exemple: python scrape_jinka.py 'https://www.jinka.fr/alert_result?token=...'")
        return
    
    alert_url = sys.argv[1]
    
    scraper = JinkaScraper()
    
    try:
        await scraper.setup()
        
        if await scraper.login():
            await scraper.scrape_alert_page(alert_url)
            print(f"✅ Scraping terminé: {len(scraper.apartments)} appartements")
        else:
            print("❌ Échec de la connexion")
    
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    finally:
        await scraper.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
