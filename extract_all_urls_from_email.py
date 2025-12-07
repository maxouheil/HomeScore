#!/usr/bin/env python3
"""
Script principal pour extraire TOUTES les URLs d'appartements depuis les emails Jinka
Gère l'historique et la déduplication pour éviter les doublons
"""

import imaplib
import email
import re
import json
import os
from datetime import datetime, timedelta
from email.header import decode_header
from dotenv import load_dotenv
from html import unescape
from bs4 import BeautifulSoup

load_dotenv()

# Token Jinka connu
JINKA_TOKEN = "26c2ec3064303aa68ffa43f7c6518733"

def decode_mime_words(s):
    """Décode les en-têtes MIME"""
    if not s:
        return ""
    decoded = decode_header(s)
    return ''.join([text.decode(encoding or 'utf-8') if isinstance(text, bytes) else text 
                    for text, encoding in decoded])

def extract_apartment_id_from_url(url):
    """Extrait l'ID d'appartement depuis une URL"""
    match = re.search(r'ad=(\d+)', url)
    return match.group(1) if match else None

def normalize_url(url):
    """
    Normalise une URL pour la déduplication
    Construit l'URL complète si nécessaire
    """
    if not url:
        return None
    
    # Si c'est juste un ID numérique
    if url.isdigit():
        return f"https://www.jinka.fr/alert_result?token={JINKA_TOKEN}&ad={url}&from=dashboard_card&from_alert_filter=all&from_alert_page=1"
    
    # Si c'est un lien relatif
    if url.startswith('/'):
        return f"https://www.jinka.fr{url}"
    
    # Si c'est déjà une URL complète
    if url.startswith('http'):
        return url
    
    # Si c'est un format loueragile
    if 'loueragile://' in url:
        match = re.search(r'id=(\d+)', url)
        if match:
            apt_id = match.group(1)
            return f"https://www.jinka.fr/alert_result?token={JINKA_TOKEN}&ad={apt_id}&from=dashboard_card&from_alert_filter=all&from_alert_page=1"
    
    return None

def extract_urls_from_email_body(body):
    """
    Extrait les URLs d'appartements depuis le corps de l'email
    Gère HTML et texte brut
    """
    urls = set()
    
    if not body:
        return urls
    
    # Décoder les entités HTML
    body = unescape(body)
    
    # Si c'est du HTML, extraire le texte aussi
    html_text = ""
    if '<html' in body.lower() or '<body' in body.lower():
        try:
            soup = BeautifulSoup(body, 'html.parser')
            html_text = soup.get_text()
            # Extraire aussi les liens href
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                if href:
                    normalized = normalize_url(href)
                    if normalized and 'ad=' in normalized:
                        urls.add(normalized)
        except:
            pass
    
    # Patterns pour trouver les URLs d'appartements Jinka
    patterns = [
        # URLs complètes
        r'https://www\.jinka\.fr/alert_result\?token=[^&\s<>"]+&ad=\d+[^\s<>"]*',
        r'https://www\.jinka\.fr/alert_result\?token=[^&\s<>"]+&ad=\d+',
        # Liens relatifs dans href
        r'href=["\'](/alert_result\?token=[^"\']+&ad=\d+[^"\']*)["\']',
        r'href=["\'](https://www\.jinka\.fr/alert_result[^"\']+)["\']',
        # IDs seuls (fallback)
        r'ad=(\d{6,})',  # Au moins 6 chiffres pour éviter les faux positifs
        # Format loueragile
        r'loueragile://[^"\s<>]*id=(\d+)',
    ]
    
    # Chercher dans le body et le texte HTML
    texts_to_search = [body]
    if html_text:
        texts_to_search.append(html_text)
    
    for text in texts_to_search:
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0] if match else None
                
                if match:
                    normalized = normalize_url(match)
                    if normalized and ('ad=' in normalized or 'alert_result' in normalized):
                        # Vérifier que c'est bien une URL valide
                        apt_id = extract_apartment_id_from_url(normalized)
                        if apt_id:
                            urls.add(normalized)
    
    return urls

def load_url_history():
    """Charge l'historique des URLs déjà extraites"""
    history_file = "data/apartment_urls_history.json"
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data.get('urls', []), data.get('last_extraction', None)
                elif isinstance(data, list):
                    return data, None
        except:
            pass
    return [], None

def save_url_history(urls, extraction_date=None):
    """Sauvegarde l'historique des URLs"""
    os.makedirs("data", exist_ok=True)
    history_file = "data/apartment_urls_history.json"
    
    data = {
        'urls': urls,
        'last_extraction': extraction_date or datetime.now().isoformat(),
        'total_count': len(urls)
    }
    
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Historique sauvegardé: {len(urls)} URLs dans {history_file}")

def get_jinka_emails(imap_server='imap.gmail.com', email_address=None, password=None, 
                     days_back=90, sender_filters=None):
    """
    Récupère les emails d'alerte Jinka depuis une boîte email
    
    Args:
        imap_server: Serveur IMAP (par défaut Gmail)
        email_address: Adresse email
        password: Mot de passe ou app password
        days_back: Nombre de jours en arrière pour chercher
        sender_filters: Liste de filtres pour l'expéditeur
    """
    if sender_filters is None:
        sender_filters = ['jinka', 'noreply@jinka.fr', 'alertes@jinka.fr']
    
    if not email_address:
        email_address = os.getenv('JINKA_EMAIL') or os.getenv('EMAIL')
    
    if not password:
        password = os.getenv('EMAIL_PASSWORD') or os.getenv('GMAIL_APP_PASSWORD')
    
    if not email_address or not password:
        print("❌ Email ou mot de passe non fourni")
        print("   Configure JINKA_EMAIL et EMAIL_PASSWORD dans .env")
        return []
    
    print(f"📧 Connexion à {email_address}...")
    
    try:
        # Connexion IMAP
        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(email_address, password)
        print("✅ Connexion IMAP réussie")
        
        # Sélectionner la boîte de réception
        mail.select('inbox')
        print("✅ Boîte de réception sélectionnée")
        
        # Construire la requête de recherche
        date_since = (datetime.now() - timedelta(days=days_back)).strftime('%d-%b-%Y')
        
        # Chercher les emails de Jinka - simplifier la requête
        # Gmail IMAP a des limitations, on va chercher par FROM d'abord
        all_email_ids = set()
        
        print(f"🔍 Recherche d'emails depuis {days_back} jours...")
        print(f"   Filtres: {', '.join(sender_filters)}")
        
        # Chercher pour chaque expéditeur séparément
        for sender in sender_filters:
            try:
                search_query = f'(SINCE {date_since}) FROM "{sender}"'
                status, messages = mail.search(None, search_query)
                if status == 'OK' and messages[0]:
                    email_ids = messages[0].split()
                    all_email_ids.update(email_ids)
                    print(f"   ✅ {len(email_ids)} emails trouvés avec filtre: {sender}")
            except Exception as e:
                print(f"   ⚠️ Erreur avec filtre {sender}: {e}")
                continue
        
        # Chercher aussi par sujet
        try:
            search_query = f'(SINCE {date_since}) SUBJECT "jinka"'
            status, messages = mail.search(None, search_query)
            if status == 'OK' and messages[0]:
                email_ids = messages[0].split()
                all_email_ids.update(email_ids)
                print(f"   ✅ {len(email_ids)} emails trouvés avec sujet 'jinka'")
        except Exception as e:
            print(f"   ⚠️ Erreur recherche par sujet: {e}")
        
        email_ids = list(all_email_ids)
        
        if status != 'OK':
            print("❌ Erreur lors de la recherche")
            return []
        
        # email_ids est déjà défini ci-dessus
        print(f"📬 {len(email_ids)} emails uniques trouvés au total")
        
        all_urls = set()
        processed_emails = 0
        
        # Parcourir les emails
        for i, email_id in enumerate(email_ids, 1):
            try:
                # Récupérer l'email
                status, msg_data = mail.fetch(email_id, '(RFC822)')
                
                if status != 'OK':
                    continue
                
                # Parser l'email
                email_body = msg_data[0][1]
                email_message = email.message_from_bytes(email_body)
                
                # Obtenir le sujet et l'expéditeur
                subject = decode_mime_words(email_message['Subject'] or '')
                sender = decode_mime_words(email_message['From'] or '')
                date = email_message['Date']
                
                if i <= 5 or i % 10 == 0:  # Afficher les 5 premiers et tous les 10
                    print(f"\n📧 Email {i}/{len(email_ids)}: {subject[:50]}...")
                    print(f"   De: {sender[:50]}...")
                
                # Extraire le corps de l'email (HTML et texte)
                body_html = ""
                body_text = ""
                
                if email_message.is_multipart():
                    for part in email_message.walk():
                        content_type = part.get_content_type()
                        content_disposition = str(part.get("Content-Disposition", ""))
                        
                        # Ignorer les pièces jointes
                        if "attachment" in content_disposition:
                            continue
                        
                        if content_type == "text/html":
                            try:
                                body_html += part.get_payload(decode=True).decode('utf-8', errors='ignore')
                            except:
                                pass
                        elif content_type == "text/plain":
                            try:
                                body_text += part.get_payload(decode=True).decode('utf-8', errors='ignore')
                            except:
                                pass
                else:
                    try:
                        payload = email_message.get_payload(decode=True)
                        if payload:
                            decoded = payload.decode('utf-8', errors='ignore')
                            if '<html' in decoded.lower():
                                body_html = decoded
                            else:
                                body_text = decoded
                    except:
                        pass
                
                # Extraire les URLs depuis HTML et texte
                urls_from_email = set()
                if body_html:
                    urls_from_email.update(extract_urls_from_email_body(body_html))
                if body_text:
                    urls_from_email.update(extract_urls_from_email_body(body_text))
                
                if urls_from_email:
                    print(f"   ✅ {len(urls_from_email)} URLs trouvées")
                    all_urls.update(urls_from_email)
                elif i <= 3:  # Debug pour les 3 premiers emails
                    print(f"   🔍 Debug: HTML={len(body_html)} chars, Text={len(body_text)} chars")
                    # Chercher manuellement quelques patterns pour debug
                    test_body = body_html + body_text
                    if 'alert_result' in test_body:
                        print(f"      ⚠️ 'alert_result' trouvé dans le body")
                        # Essayer de trouver directement
                        direct_matches = re.findall(r'https?://[^"\s<>]+alert_result[^"\s<>]+', test_body)
                        if direct_matches:
                            print(f"      ✅ URLs directes trouvées: {len(direct_matches)}")
                            for url in direct_matches[:2]:
                                print(f"         {url[:80]}...")
                    if 'ad=' in test_body:
                        matches = re.findall(r'ad=(\d{6,})', test_body)
                        if matches:
                            print(f"      ⚠️ IDs trouvés avec regex: {matches[:3]}")
                            # Essayer de construire les URLs
                            for apt_id in matches[:2]:
                                test_url = f"https://www.jinka.fr/alert_result?token={JINKA_TOKEN}&ad={apt_id}&from=dashboard_card&from_alert_filter=all&from_alert_page=1"
                                print(f"         URL construite: {test_url[:80]}...")
                
                processed_emails += 1
                
            except Exception as e:
                if i <= 5:  # Afficher les erreurs pour les premiers emails
                    print(f"   ⚠️ Erreur lors du traitement de l'email {i}: {e}")
                continue
        
        mail.close()
        mail.logout()
        
        print(f"\n✅ {processed_emails} emails traités")
        return sorted(list(all_urls))
        
    except imaplib.IMAP4.error as e:
        print(f"❌ Erreur IMAP: {e}")
        print("   Vérifie que tu utilises un 'App Password' pour Gmail")
        return []
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return []

def main():
    """Fonction principale"""
    print("=" * 70)
    print("📧 EXTRACTION COMPLÈTE DES URLs DEPUIS LES EMAILS JINKA")
    print("=" * 70)
    print()
    
    # Charger l'historique
    print("📚 Chargement de l'historique...")
    history_urls, last_extraction = load_url_history()
    history_set = set(history_urls)
    print(f"   Historique: {len(history_urls)} URLs déjà extraites")
    if last_extraction:
        print(f"   Dernière extraction: {last_extraction}")
    
    # Configuration
    email_address = os.getenv('JINKA_EMAIL') or os.getenv('EMAIL')
    password = os.getenv('EMAIL_PASSWORD') or os.getenv('GMAIL_APP_PASSWORD')
    
    if not email_address or not password:
        print("\n⚠️ Configuration email manquante")
        print("   Ajoute dans .env:")
        print("   JINKA_EMAIL=ton_email@gmail.com")
        print("   EMAIL_PASSWORD=ton_app_password")
        print("\n   Pour créer un App Password Gmail:")
        print("   https://myaccount.google.com/apppasswords")
        return []
    
    # Récupérer les emails (90 derniers jours)
    print("\n" + "=" * 70)
    urls_from_emails = get_jinka_emails(
        email_address=email_address,
        password=password,
        days_back=90,  # Chercher dans les 90 derniers jours
        sender_filters=['jinka', 'noreply@jinka.fr', 'alertes@jinka.fr']
    )
    
    if not urls_from_emails:
        print("\n❌ Aucune URL trouvée dans les emails")
        return []
    
    print("\n" + "=" * 70)
    print(f"📊 RÉSULTATS DE L'EXTRACTION")
    print("=" * 70)
    print(f"🏠 URLs trouvées dans les emails: {len(urls_from_emails)}")
    
    # Dédupliquer avec l'historique
    new_urls = []
    for url in urls_from_emails:
        apt_id = extract_apartment_id_from_url(url)
        # Vérifier si cette URL ou cet ID existe déjà dans l'historique
        is_new = True
        if url in history_set:
            is_new = False
        elif apt_id:
            # Vérifier par ID
            for hist_url in history_urls:
                hist_id = extract_apartment_id_from_url(hist_url)
                if hist_id == apt_id:
                    is_new = False
                    break
        
        if is_new:
            new_urls.append(url)
    
    # Combiner historique et nouvelles URLs
    all_urls = sorted(list(set(history_urls + urls_from_emails)))
    
    print(f"🆕 Nouvelles URLs: {len(new_urls)}")
    print(f"📚 Total URLs (historique + nouvelles): {len(all_urls)}")
    
    # Sauvegarder
    os.makedirs("data", exist_ok=True)
    
    # Sauvegarder toutes les URLs
    all_urls_file = "data/all_apartment_urls_from_email.json"
    with open(all_urls_file, 'w', encoding='utf-8') as f:
        json.dump(all_urls, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Toutes les URLs sauvegardées: {all_urls_file}")
    
    # Sauvegarder l'historique mis à jour
    save_url_history(all_urls)
    
    # Sauvegarder seulement les nouvelles URLs
    if new_urls:
        new_urls_file = "data/new_apartment_urls_from_email.json"
        with open(new_urls_file, 'w', encoding='utf-8') as f:
            json.dump(new_urls, f, indent=2, ensure_ascii=False)
        print(f"💾 Nouvelles URLs sauvegardées: {new_urls_file}")
        
        print(f"\n📋 Nouvelles URLs trouvées:")
        for i, url in enumerate(new_urls[:10], 1):
            apt_id = extract_apartment_id_from_url(url)
            print(f"   {i}. ID: {apt_id} - {url[:80]}...")
        if len(new_urls) > 10:
            print(f"   ... et {len(new_urls) - 10} autres")
    else:
        print("\n✅ Aucune nouvelle URL (toutes étaient déjà dans l'historique)")
    
    print(f"\n✅ TERMINÉ!")
    return all_urls

if __name__ == "__main__":
    main()

