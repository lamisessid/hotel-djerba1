import csv
import mysql.connector
from mysql.connector import Error

def export_to_csv():
    try:
        # Configuration de votre base de données
        connection = mysql.connector.connect(
            host='localhost',
            user='admin',
            password='AdminPasswordSecure789!', 
            database='projet_mobile_db'
        )
        
        if connection.is_connected():
            print("Connecté à MySQL")
            
            cursor = connection.cursor()
            
            # Récupérer les noms des colonnes
            cursor.execute("DESCRIBE reservation_elsofra")
            columns = [column[0] for column in cursor.fetchall()]
            print(f"Colonnes trouvées: {columns}")
            
            # Récupérer les données
            cursor.execute("SELECT * FROM reservation_elsofra")
            rows = cursor.fetchall()
            
            print(f"{len(rows)} enregistrements trouvés")
            
            # Écrire dans le fichier CSV
            with open('reservation_elsofra.csv', 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Écrire l'en-tête
                writer.writerow(columns)
                
                # Écrire les données
                for row in rows:
                    writer.writerow(row)
            
            print("Fichier CSV créé: reservation_elsofra.csv")
            
            # Aperçu des données
            print("\n Aperçu des premières lignes:")
            for i, row in enumerate(rows[:5]):
                print(f"  Ligne {i+1}: {row}")
                
    except Error as e:
        print(f"Erreur MySQL: {e}")
    except Exception as e:
        print(f"Erreur générale: {e}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            connection.close()
            print("Déconnecté de MySQL")

if __name__ == "__main__":
    export_to_csv()