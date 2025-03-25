#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script principal pour lancer l'analyse complète des données de la BRVM.
Ce script:
1. Lance le scraping des données
2. Vérifie que les données ont été collectées correctement
3. Prépare l'environnement pour l'analyse
"""

import os
import sys
import subprocess
import glob
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("run_analysis.log"), logging.StreamHandler()]
)
logger = logging.getLogger("BRVM_Analysis")

def ensure_directory(directory):
    """S'assure que le répertoire existe, le crée si nécessaire."""
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Répertoire '{directory}' créé.")

def run_scraper():
    """Lance le script de scraping."""
    logger.info("Lancement du script de scraping...")
    
    # Chemin vers le script de scraping
    scraper_path = os.path.join("scraper", "brvm_scraper.py")
    
    if not os.path.exists(scraper_path):
        logger.error(f"Script de scraping non trouvé: {scraper_path}")
        return False
    
    try:
        # Exécuter le script de scraping
        subprocess.run([sys.executable, scraper_path], check=True)
        logger.info("Script de scraping exécuté avec succès.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Erreur lors de l'exécution du script de scraping: {str(e)}")
        return False

def check_data():
    """Vérifie que les données ont été correctement collectées."""
    logger.info("Vérification des données collectées...")
    
    data_dir = "data"
    if not os.path.exists(data_dir):
        logger.error(f"Répertoire de données non trouvé: {data_dir}")
        return False
    
    csv_files = glob.glob(os.path.join(data_dir, "*.csv"))
    
    if not csv_files:
        logger.error("Aucun fichier CSV trouvé dans le répertoire de données.")
        return False
    
    logger.info(f"{len(csv_files)} fichiers CSV trouvés.")
    
    return True

def launch_notebook():
    """Lance Jupyter Notebook pour l'analyse."""
    logger.info("Lancement de Jupyter Notebook...")
    
    notebook_path = os.path.join("notebooks", "analyse_performances.ipynb")
    
    if not os.path.exists(notebook_path):
        logger.error(f"Notebook d'analyse non trouvé: {notebook_path}")
        return False
    
    try:
        # Ouvrir Jupyter Notebook
        subprocess.Popen(["jupyter", "notebook", notebook_path])
        logger.info("Jupyter Notebook lancé. Veuillez suivre les instructions dans votre navigateur.")
        return True
    except Exception as e:
        logger.error(f"Erreur lors du lancement de Jupyter Notebook: {str(e)}")
        return False

def main():
    """Fonction principale."""
    logger.info("Démarrage de l'analyse des données de la BRVM...")
    
    # S'assurer que les répertoires nécessaires existent
    ensure_directory("data")
    ensure_directory("notebooks")
    
    # Lancer le scraping
    if not run_scraper():
        logger.error("Erreur lors de la collecte des données. Arrêt du traitement.")
        return
    
    # Vérifier les données
    if not check_data():
        logger.error("Problème avec les données collectées. Veuillez vérifier les logs.")
        return
    
    # Lancer l'analyse
    if not launch_notebook():
        logger.error("Erreur lors du lancement de l'analyse. Veuillez vérifier les prérequis.")
        return
    
    logger.info("Traitement complet lancé avec succès.")

if __name__ == "__main__":
    main()
