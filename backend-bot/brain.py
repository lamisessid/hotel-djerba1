import os
import google.generativeai as genai
from dotenv import load_dotenv
from database import get_db_connection  

load_dotenv()

class Brain:
    def __init__(self):
        self.config = {
            'name': 'Holiday Beach Djerba',
            'tel': '+216 75 758 063',
            'email': 'booking@holidaybeach.com.tn',
        }
        self.gemini = self._setup_ai()
        print(f"STATUT IA: {'ACTIVÉE' if self.gemini else 'DÉSACTIVÉE'}")
    
    def _setup_ai(self):
        # LECTURE FORCÉE du .env
        api_key = None
        try:
            with open('.env', 'r') as f:
                for line in f:
                    if 'GOOGLE_API_KEY' in line and '=' in line:
                        api_key = line.split('=', 1)[1].strip()
                        break
        except:
            pass
            
        print(f"Clé lue: {api_key[:20] if api_key else 'AUCUNE'}...")
        
        if not api_key: 
            return None
            
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.0-flash')
            print("Gemini CONFIGURÉ avec succès!")
            return model
        except Exception as e:
            print(f"Erreur configuration: {e}")
            return None

    def process(self, message, user_id):
        print(f"Message reçu: '{message}'")
        print(f"IA disponible: {self.gemini is not None}")
        
        # FORCER l'IA si disponible
        if self.gemini:
            print("Utilisation de l'IA...")
            return self._ai_response(message)
        else:
            print("Fallback sans IA...")
            return self._smart_response(message)

    def _ai_response(self, message):
        try:
            prompt = f"""
Tu es l'assistant IA de l'hôtel Holiday Beach Djerba (4 étoiles).
Réponds de manière naturelle et utile en 1-2 phrases.

Client: {message}

Réponse:
"""
            response = self.gemini.generate_content(prompt)
            print(f"Réponse IA: {response.text}")
            return {
                "content": f"{response.text}",
                "quick_replies": ["Réserver", "Contact", "Horaires", "Services"],
                "type": "ai"
            }
        except Exception as e:
            print(f"Erreur IA: {e}")
            return self._smart_response(message)

    def _smart_response(self, message):
        msg = message.lower()
        
        if any(word in msg for word in ['bonjour', 'salut', 'hello']):
            return {
                "content": f"Bonjour ! Bienvenue à {self.config['name']}",
                "quick_replies": ["Réserver", "Horaires", "Contact"],
                "type": "smart"
            }
        elif any(word in msg for word in ['réservation', 'réserver', 'reserver', 'chambre']):
            count = self._get_db_count("hotel_reservations")
            content = f"Réservation: {self.config['tel']}"
            if count: content += f"\n{count} réservations"
            return {"content": content, "quick_replies": ["Chambre", "Restaurant", "Contact"], "type": "smart"}
        else:
            return {
                "content": f"{self.config['name']} - {self.config['tel']}",
                "quick_replies": ["Réserver", "Horaires", "Contact"],
                "type": "smart"
            }

    def _get_db_count(self, table_name):
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                conn.close()
                return count
            except: 
                return None
        return None

brain = Brain()