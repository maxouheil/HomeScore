#!/usr/bin/env python3
"""
Script pour extraire les URLs d'appartements depuis les emails d'alerte Jinka
Plus robuste que le scraping web car les emails ont un format stable
"""

import imaplib
import email
import re
import json
import os
from email.header import decode_header
from dotenv import load_dotenv

load_dotenv()

def decode_mime_words(s):
    """Décode les en-têtes MIME"""
    decoded = decode_header(s)
    return ''.join([text.decode(encoding or 'utf-8') if isinstance(text, bytes) else text 
                    for text, encoding in decoded])

def extract_urls_from_email_body(body):
    """
    Extrait les URLs d'appartements depuis le corps de l'email
    Version améliorée avec gestion HTML et texte brut
    """
    urls = set()
    
    if not body:
        return urls
    
    # Décoder les entités HTML
    from html import unescape
    body = unescape(body)
    
    # Essayer d'utiliser BeautifulSoup si disponible pour parser le HTML
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(body, 'html.parser')
        # Extraire les liens href
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if href:
                normalized = normalize_url_from_email(href)
                if normalized:
                    urls.add(normalized)
        # Ajouter aussi le texte pour chercher les patterns
        body_text = soup.get_text()
    except:
        body_text = body
    
    # Patterns pour trouver les URLs d'appartements Jinka
    patterns = [
        # URLs complètes
        r'https://www\.jinka\.fr/alert_result\?token=[^&\s<>"]+&ad=\d+[^\s<>"]*',
        r'https://www\.jinka\.fr/alert_result\?token=[^&\s<>"]+&ad=\d+',
        # Liens relatifs dans href
        r'href=["\'](/alert_result\?token=[^"\']+&ad=\d+[^"\']*)["\']',
        r'href=["\'](https://www\.jinka\.fr/alert_result[^"\']+)["\']',
        # IDs seuls (au moins 6 chiffres pour éviter faux positifs)
        r'ad=(\d{6,})',
        # Format loueragile
        r'loueragile://[^"\s<>]*id=(\d+)',
    ]
    
    # Chercher dans le body original et le texte extrait
    for text in [body, body_text]:
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0] if match else None
                
                if match:
                    normalized = normalize_url_from_email(match)
                    if normalized:
                        urls.add(normalized)
    
    return urls

def normalize_url_from_email(url_or_id):
    """Normalise une URL ou ID depuis un email"""
    if not url_or_id:
        return None
    
    token = "26c2ec3064303aa68ffa43f7c6518733"
    
    # Si c'est juste un ID numérique
    if url_or_id.isdigit():
        return f"https://www.jinka.fr/alert_result?token={token}&ad={url_or_id}&from=dashboard_card&from_alert_filter=all&from_alert_page=1"
    
    # Si c'est un lien relatif
    if url_or_id.startswith('/'):
        return f"https://www.jinka.fr{url_or_id}"
    
    # Si c'est déjà une URL complète
    if url_or_id.startswith('http'):
        return url_or_id
    
    # Si c'est un format loueragile
    if 'loueragile://' in url_or_id:
        match = re.search(r'id=(\d+)', url_or_id)
        if match:
            apt_id = match.group(1)
            return f"https://www.jinka.fr/alert_result?token={token}&ad={apt_id}&from=dashboard_card&from_alert_filter=all&from_alert_page=1"
    
    return None

def get_jinka_emails(imap_server='imap.gmail.com', email_address=None, password=None, 
                     days_back=7, sender_filter='jinka'):
    """
    Récupère les emails d'alerte Jinka depuis une boîte email
    
    Args:
        imap_server: Serveur IMAP (par défaut Gmail)
        email_address: Adresse email
        password: Mot de passe ou app password
        days_back: Nombre de jours en arrière pour chercher
        sender_filter: Filtre pour l'expéditeur (ex: 'jinka', 'noreply@jinka.fr')
    """
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
        print("✅ Connexion réussie")
        
        # Sélectionner la boîte de réception
        mail.select('inbox')
        
        # Chercher les emails de Jinka
        search_query = f'(FROM "{sender_filter}" OR SUBJECT "jinka" OR SUBJECT "alerte")'
        if days_back:
            # Chercher les emails des derniers X jours
            from datetime import datetime, timedelta
            date_since = (datetime.now() - timedelta(days=days_back)).strftime('%d-%b-%Y')
            search_query = f'(SINCE {date_since}) {search_query}'
        
        print(f"🔍 Recherche d'emails avec: {search_query}")
        status, messages = mail.search(None, search_query)
        
        if status != 'OK':
            print("❌ Erreur lors de la recherche")
            return []
        
        email_ids = messages[0].split()
        print(f"📬 {len(email_ids)} emails trouvés")
        
        all_urls = set()
        
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
                
                # Obtenir le sujet
                subject = decode_mime_words(email_message['Subject'] or '')
                print(f"\n📧 Email {i}/{len(email_ids)}: {subject[:60]}...")
                
                # Extraire le corps de l'email
                body = ""
                if email_message.is_multipart():
                    for part in email_message.walk():
                        content_type = part.get_content_type()
                        if content_type == "text/html" or content_type == "text/plain":
                            try:
                                body += part.get_payload(decode=True).decode('utf-8', errors='ignore')
                            except:
                                pass
                else:
                    try:
                        body = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
                    except:
                        pass
                
                # Extraire les URLs
                urls = extract_urls_from_email_body(body)
                print(f"   ✅ {len(urls)} URLs trouvées dans cet email")
                
                all_urls.update(urls)
                
            except Exception as e:
                print(f"   ⚠️ Erreur lors du traitement de l'email {i}: {e}")
                continue
        
        mail.close()
        mail.logout()
        
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
    print("=" * 60)
    print("📧 EXTRACTION DES URLs DEPUIS LES EMAILS JINKA")
    print("=" * 60)
    print()
    
    # Configuration
    email_address = os.getenv('JINKA_EMAIL') or os.getenv('EMAIL')
    password = os.getenv('EMAIL_PASSWORD') or os.getenv('GMAIL_APP_PASSWORD')
    
    if not email_address:
        print("⚠️ JINKA_EMAIL non configuré dans .env")
        email_address = input("Adresse email: ").strip()
    
    if not password:
        print("⚠️ EMAIL_PASSWORD non configuré dans .env")
        print("   Pour Gmail, utilise un 'App Password' depuis:")
        print("   https://myaccount.google.com/apppasswords")
        password = input("Mot de passe/App Password: ").strip()
    
    # Récupérer les emails
    urls = get_jinka_emails(
        email_address=email_address,
        password=password,
        days_back=30,  # Chercher dans les 30 derniers jours
        sender_filter='jinka'  # Chercher les emails de Jinka
    )
    
    if urls:
        print("\n" + "=" * 60)
        print(f"📊 RÉSULTATS: {len(urls)} URLs trouvées")
        print("=" * 60)
        
        print("\n📋 Liste des URLs:")
        for i, url in enumerate(urls, 1):
            print(f"   {i}. {url}")
        
        # Sauvegarder
        os.makedirs("data", exist_ok=True)
        output_file = "data/apartment_urls_from_email.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(urls, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 URLs sauvegardées dans: {output_file}")
        print(f"✅ TERMINÉ!")
        
        return urls
    else:
        print("\n❌ Aucune URL trouvée")
        print("   Vérifie:")
        print("   - Que tu as bien des emails d'alerte Jinka")
        print("   - Que les identifiants email sont corrects")
        print("   - Que tu utilises un App Password pour Gmail")
        return []

if __name__ == "__main__":
    main()

