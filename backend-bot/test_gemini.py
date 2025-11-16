import google.generativeai as genai

API_KEY = "AIzaSyCTIgdYmQIPLhriXfidz7SLkFHuhAAlyhA" 

try:
    genai.configure(api_key=API_KEY)
    
    # Utilise gemini-2.0-flash (stable)
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content("Dis 'Bonjour Hotel Djerba' en français")
    print(f"gemini-2.0-flash!")
    print(f"Réponse: {response.text}")
    
except Exception as e:
    print(f"ERREUR: {e}")