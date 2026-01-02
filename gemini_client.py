#!/usr/bin/env python3
"""
Client pour Google Gemini API
Gère les appels vers Gemini Flash et Gemini Pro pour l'analyse visuelle
"""

import os
import json
import base64
import requests
import time
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()


class GeminiClient:
    """Client pour Google Gemini API"""
    
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY non trouvée dans les variables d'environnement")
        
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.max_retries = 3
        self.retry_delay = 1  # secondes
        
    def analyze_image(
        self, 
        image_url: str, 
        prompt: str, 
        model: str = "gemini-1.5-flash",
        max_tokens: int = 800,
        temperature: float = 0.4
    ) -> Optional[Dict]:
        """
        Analyse une image avec Gemini
        
        Args:
            image_url: URL de l'image ou données base64
            prompt: Prompt texte pour l'analyse
            model: Modèle à utiliser ('gemini-1.5-flash' ou 'gemini-1.5-pro')
            max_tokens: Nombre maximum de tokens de sortie
            temperature: Température pour la génération (0.0-1.0)
        
        Returns:
            Réponse JSON parsée ou None en cas d'erreur
        """
        # Préparer l'image
        image_part = self._prepare_image_part(image_url)
        if not image_part:
            return None
        
        # Construire le payload
        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    image_part
                ]
            }],
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": temperature,
                "responseMimeType": "application/json"  # Forcer JSON en sortie
            }
        }
        
        # URL de l'endpoint
        url = f"{self.base_url}/models/{model}:generateContent?key={self.api_key}"
        
        # Headers
        headers = {
            'Content-Type': 'application/json'
        }
        
        # Faire l'appel avec retry logic
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    return self._parse_response(response.json())
                elif response.status_code == 429:  # Rate limit
                    if attempt < self.max_retries - 1:
                        wait_time = self.retry_delay * (2 ** attempt)
                        print(f"   ⏱️ Rate limit atteint, attente {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"   ❌ Rate limit après {self.max_retries} tentatives")
                        return None
                else:
                    print(f"   ❌ Erreur API Gemini: {response.status_code}")
                    print(f"   Réponse: {response.text[:200]}")
                    return None
                    
            except requests.exceptions.Timeout:
                if attempt < self.max_retries - 1:
                    print(f"   ⏱️ Timeout, nouvelle tentative...")
                    time.sleep(self.retry_delay)
                    continue
                else:
                    print(f"   ❌ Timeout après {self.max_retries} tentatives")
                    return None
            except Exception as e:
                print(f"   ❌ Erreur lors de l'appel Gemini: {e}")
                return None
        
        return None
    
    def _prepare_image_part(self, image_data: str) -> Optional[Dict]:
        """
        Prépare la partie image pour le payload Gemini
        
        Args:
            image_data: Données base64 de l'image (toujours en base64, jamais URL)
        
        Returns:
            Dict avec la structure image pour Gemini ou None
        """
        # Si c'est déjà en base64 (format data:image)
        if image_data.startswith('data:image'):
            # Extraire le base64
            base64_data = image_data.split(',')[1] if ',' in image_data else image_data
            return {
                "inline_data": {
                    "mime_type": "image/jpeg",
                    "data": base64_data
                }
            }
        # Si c'est du base64 pur (cas le plus courant)
        elif len(image_data) > 100:  # Probablement du base64
            return {
                "inline_data": {
                    "mime_type": "image/jpeg",
                    "data": image_data
                }
            }
        else:
            print(f"   ⚠️ Format d'image non reconnu: {image_data[:50]}...")
            return None
    
    def _parse_response(self, response_json: Dict) -> Optional[Dict]:
        """
        Parse la réponse Gemini et extrait le contenu JSON
        
        Args:
            response_json: Réponse JSON brute de Gemini
        
        Returns:
            Dict parsé ou None
        """
        try:
            # Structure Gemini: candidates[0].content.parts[0].text
            candidates = response_json.get('candidates', [])
            if not candidates:
                print(f"   ⚠️ Aucun candidat dans la réponse Gemini")
                return None
            
            content = candidates[0].get('content', {})
            parts = content.get('parts', [])
            if not parts:
                print(f"   ⚠️ Aucune partie dans la réponse Gemini")
                return None
            
            text = parts[0].get('text', '')
            if not text:
                print(f"   ⚠️ Aucun texte dans la réponse Gemini")
                return None
            
            # Parser le JSON (Gemini peut retourner du texte avant/après)
            text = text.strip()
            
            # Si le JSON est dans un bloc markdown
            if '```json' in text:
                text = text.split('```json')[1].split('```')[0].strip()
            elif '```' in text:
                text = text.split('```')[1].split('```')[0].strip()
            
            # Essayer de trouver le JSON dans le texte
            if text.startswith('{'):
                # Prendre jusqu'à la première accolade fermante correspondante
                json_text = self._extract_json(text)
            else:
                # Chercher le JSON dans le texte
                json_start = text.find('{')
                if json_start != -1:
                    json_text = self._extract_json(text[json_start:])
                else:
                    print(f"   ⚠️ JSON non trouvé dans la réponse")
                    return None
            
            return json.loads(json_text)
            
        except json.JSONDecodeError as e:
            print(f"   ❌ Erreur parsing JSON Gemini: {e}")
            print(f"   Texte reçu: {text[:300]}...")
            return None
        except Exception as e:
            print(f"   ❌ Erreur parsing réponse Gemini: {e}")
            return None
    
    def _extract_json(self, text: str) -> str:
        """
        Extrait le JSON d'un texte qui peut contenir du texte avant/après
        
        Args:
            text: Texte contenant potentiellement du JSON
        
        Returns:
            Chaîne JSON extraite
        """
        # Chercher la première accolade ouvrante
        start = text.find('{')
        if start == -1:
            return text
        
        # Compter les accolades pour trouver la fin
        brace_count = 0
        in_string = False
        escape_next = False
        
        for i in range(start, len(text)):
            char = text[i]
            
            if escape_next:
                escape_next = False
                continue
            
            if char == '\\':
                escape_next = True
                continue
            
            if char == '"' and not escape_next:
                in_string = not in_string
                continue
            
            if not in_string:
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        return text[start:i+1]
        
        # Si on arrive ici, retourner tout depuis le début
        return text[start:]
    
    def analyze_image_from_url(
        self,
        image_url: str,
        prompt: str,
        model: str = "gemini-1.5-flash",
        max_tokens: int = 800
    ) -> Optional[Dict]:
        """
        Analyse une image depuis son URL (télécharge et encode en base64)
        
        Args:
            image_url: URL de l'image
            prompt: Prompt pour l'analyse
            model: Modèle Gemini à utiliser
            max_tokens: Nombre max de tokens
        
        Returns:
            Résultat parsé ou None
        """
        try:
            # Télécharger l'image
            response = requests.get(image_url, timeout=10)
            if response.status_code != 200:
                print(f"   ❌ Erreur téléchargement image: {response.status_code}")
                return None
            
            # Encoder en base64
            image_base64 = base64.b64encode(response.content).decode('utf-8')
            
            # Utiliser la méthode principale
            return self.analyze_image(
                image_base64,
                prompt,
                model,
                max_tokens
            )
            
        except Exception as e:
            print(f"   ❌ Erreur lors du téléchargement/analyse: {e}")
            return None

