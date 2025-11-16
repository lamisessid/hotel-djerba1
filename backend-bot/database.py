import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    try:
        return mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'admin'), 
            password=os.getenv('DB_PASSWORD', 'AdminPasswordSecure789!'),
            database=os.getenv('DB_NAME', 'projet_mobile_db')
        )
    except Exception as e:
        print(f"Erreur DB: {e}")
        return None