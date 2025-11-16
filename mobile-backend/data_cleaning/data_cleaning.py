import pandas as pd
import re
import mysql.connector
from mysql.connector import Error

class DataCleaner:
    def __init__(self, csv_file_path):
        self.csv_file_path = csv_file_path
        self.df = pd.read_csv(csv_file_path)
        self.cleaning_report = []
        print(f"Chargement de {csv_file_path}: {len(self.df)} enregistrements")

    def clean_nombre_pax(self):
        """Nettoyer le nombre de personnes"""
        print("Nettoyage nombre_pax...")
        
        # Compter les valeurs manquantes
        problem_count = self.df['nombre_pax'].isna().sum()
        print(f"   {problem_count} valeurs manquantes trouvées")
        
        # Remplacer les NaN par 2 (valeur par défaut restaurant)
        self.df['nombre_pax'] = self.df['nombre_pax'].fillna(2)
        
        # Convertir en entier
        self.df['nombre_pax'] = pd.to_numeric(self.df['nombre_pax'], errors='coerce').fillna(2).astype(int)
        
        self.cleaning_report.append(f"nombre_pax: {problem_count} valeurs corrigées")

    def clean_heure_passage(self):
        """Corriger les heures comme '19h30' vers '19:30'"""
        print("Nettoyage heure_passage...")
        
        def correct_heure(heure_str):
            if pd.isna(heure_str) or heure_str == '':
                return '19:30'
            
            heure_str = str(heure_str)
            
            # Extraire l'heure et les minutes
            match = re.search(r'(\d{1,2})h(\d{2})', heure_str)
            if match:
                heures, minutes = match.groups()
                return f"{heures}:{minutes}"
            
            return '19:30'
        
        # Compter les problèmes
        problem_count = self.df['heure_passage'].apply(
            lambda x: 'h' in str(x) if pd.notna(x) else False
        ).sum()
        
        print(f"   {problem_count} heures à convertir (format '19h30')")
        
        self.df['heure_passage'] = self.df['heure_passage'].apply(correct_heure)
        self.cleaning_report.append(f"heure_passage: {problem_count} heures converties")

    def clean_numero_chambre(self):
        """Normaliser les numéros de chambre"""
        print("Nettoyage numero_chambre...")
        
        def format_chambre(chambre_str):
            if pd.isna(chambre_str) or chambre_str == '':
                return 'Non spécifié'
            
            chambre_str = str(chambre_str)
            
            # Remplacer les points par des tirets
            chambre_str = chambre_str.replace('.', '-')
            
            # Supprimer les espaces
            chambre_str = chambre_str.replace(' ', '')
            
            return chambre_str
        
        # Compter les chambres avec points
        problem_count = self.df['numero_chambre'].apply(
            lambda x: '.' in str(x) if pd.notna(x) else False
        ).sum()
        
        print(f"   {problem_count} numéros de chambre à normaliser")
        
        self.df['numero_chambre'] = self.df['numero_chambre'].apply(format_chambre)
        self.cleaning_report.append(f"numero_chambre: {problem_count} formats normalisés")

    def clean_statut(self):
        """Uniformiser les statuts"""
        print("🔧 Nettoyage statut...")
        
        def normaliser_statut(statut_str):
            if pd.isna(statut_str):
                return 'confirmé'
            
            statut = str(statut_str).lower().strip()
            
            if 'confirmé' in statut:
                return 'confirmé'
            elif 'annulé' in statut:
                return 'annulé'
            else:
                return 'confirmé'
        
        # Compter les statuts non standard
        problem_count = self.df['statut'].apply(
            lambda x: str(x).strip().lower() not in ['confirmé', 'annulé'] if pd.notna(x) else False
        ).sum()
        
        print(f"   {problem_count} statuts à uniformiser")
        
        self.df['statut'] = self.df['statut'].apply(normaliser_statut)
        self.cleaning_report.append(f"statut: {problem_count} statuts uniformisés")

    def update_database(self):
        """Mettre à jour la base de données MySQL"""
        print("Mise à jour de la base de données...")
        
        try:
            connection = mysql.connector.connect(
                host='localhost',
                user='admin',
                password='AdminPasswordSecure789!',
                database='projet_mobile_db'
            )
            
            cursor = connection.cursor()
            
            # Vider la table existante
            cursor.execute("DELETE FROM reservation_elsofra")
            print("   Table vidée")
            
            # Insérer les données nettoyées
            for index, row in self.df.iterrows():
                insert_query = """
                INSERT INTO reservation_elsofra 
                (date_passage, numero_chambre, nombre_pax, heure_passage, restaurant, type_service, nom_fichier_source, ligne_source, statut)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                cursor.execute(insert_query, (
                    row['date_passage'], 
                    row['numero_chambre'], 
                    row['nombre_pax'],
                    row['heure_passage'], 
                    row['restaurant'], 
                    row['type_service'],
                    row['nom_fichier_source'], 
                    row.get('ligne_source', ''), 
                    row['statut']
                ))
            
            connection.commit()
            print(f"{len(self.df)} enregistrements insérés")
            self.cleaning_report.append(f"base_donnees: {len(self.df)} enregistrements mis à jour")
            
            cursor.close()
            connection.close()
            
        except Exception as e:
            print(f"Erreur base de données: {e}")
            self.cleaning_report.append(f"base_donnees: ERREUR - {str(e)}")

    def run_cleaning_pipeline(self):
        """Exécuter le processus complet"""
        print("NETTOYAGE DES DONNÉES RESTAURANT EL SOFRA")
        print("=" * 50)
        
        # Aperçu avant nettoyage
        print("APERÇU AVANT NETTOYAGE:")
        print(self.df[['numero_chambre', 'nombre_pax', 'heure_passage', 'statut']].head(3))
        
        # Étapes de nettoyage
        self.clean_nombre_pax()
        self.clean_heure_passage()
        self.clean_numero_chambre()
        self.clean_statut()
        
        # Sauvegarder CSV nettoyé
        output_file = 'reservation_elsofra_clean.csv'
        self.df.to_csv(output_file, index=False)
        print(f"\n Fichier nettoyé sauvegardé: {output_file}")
        
        # Mettre à jour la base
        self.update_database()
        
        # Rapport final
        print("\n" + "=" * 50)
        print(" RAPPORT FINAL DE NETTOYAGE:")
        print("=" * 50)
        for report in self.cleaning_report:
            print(f" {report}")
        
        print(f"\n APERÇU APRÈS NETTOYAGE:")
        print(self.df[['numero_chambre', 'nombre_pax', 'heure_passage', 'statut']].head(3))
        
        print(f"\n {len(self.df)} enregistrements nettoyés - PRÊTS POUR LE CHATBOT ET L'APP MOBILE!")
        
        return self.df


# POINT D'ENTRÉE PRINCIPAL - CORRIGÉ
if __name__ == "__main__":
    csv_file = 'reservation_elsofra.csv'
    
    try:
        cleaner = DataCleaner(csv_file)
        cleaner.run_cleaning_pipeline()
    except FileNotFoundError:
        print(f" Fichier {csv_file} non trouvé!")
        print("💡 Assurez-vous d'avoir exporté les données d'abord")
    except Exception as e:
        print(f" Erreur: {e}")