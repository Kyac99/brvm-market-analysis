#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script de scraping pour récupérer les données historiques des valeurs mobilières de la BRVM
(Bourse Régionale des Valeurs Mobilières) et Sika Finance.
"""

import os
import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
import json
from datetime import datetime
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("scraping.log"), logging.StreamHandler()]
)
logger = logging.getLogger("BRVM_Scraper")

# Création du dossier data s'il n'existe pas
if not os.path.exists('data'):
    os.makedirs('data')
    logger.info("Dossier 'data' créé")

class BRVMScraper:
    """Classe pour scraper les données de la BRVM."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'
        })
        
        # Liste des indices et valeurs principales
        self.indices = ["BRVM-Composite", "BRVM-30"]
        
    def get_all_stocks(self):
        """Récupérer la liste de toutes les valeurs cotées."""
        try:
            # URL de la page des cours de la BRVM
            url = "https://www.brvm.org/fr/cours-actions/0"
            
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extraction de la liste des symboles
            stocks = []
            stock_table = soup.select_one("table.table")
            
            if stock_table:
                rows = stock_table.select("tbody tr")
                for row in rows:
                    cols = row.select("td")
                    if len(cols) >= 2:
                        symbol = cols[0].text.strip()
                        name = cols[1].text.strip()
                        stocks.append({"symbol": symbol, "name": name})
            
            logger.info(f"Récupéré {len(stocks)} valeurs cotées")
            return stocks
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des valeurs: {str(e)}")
            return []
    
    def scrape_sika_finance(self, symbol, start_date='01/01/2010', end_date=None):
        """
        Scraper les données historiques d'une valeur depuis Sika Finance.
        
        Args:
            symbol (str): Le symbole de la valeur
            start_date (str): Date de début au format DD/MM/YYYY
            end_date (str): Date de fin au format DD/MM/YYYY
        
        Returns:
            pd.DataFrame: DataFrame contenant les données historiques
        """
        if end_date is None:
            end_date = datetime.now().strftime('%d/%m/%Y')
        
        logger.info(f"Récupération des données historiques pour {symbol} de {start_date} à {end_date}")
        
        try:
            url = "https://www.sikafinance.com/api/general/GetHistorique"
            
            # SikaFinance attend un format différent pour la date
            start_date_obj = datetime.strptime(start_date, '%d/%m/%Y')
            end_date_obj = datetime.strptime(end_date, '%d/%m/%Y')
            
            payload = {
                "ticker": symbol,
                "dateDebut": start_date_obj.strftime('%Y-%m-%d'),
                "dateFin": end_date_obj.strftime('%Y-%m-%d')
            }
            
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            if "intraday" in data and len(data["intraday"]) > 0:
                # Conversion en DataFrame
                df = pd.DataFrame(data["intraday"])
                
                # Renommage des colonnes
                df = df.rename(columns={
                    "date": "Date",
                    "ouverture": "Ouverture",
                    "plus_haut": "Plus_Haut",
                    "plus_bas": "Plus_Bas",
                    "cloture": "Cloture",
                    "variation": "Variation",
                    "volume": "Volume"
                })
                
                # Conversion de la date en format datetime
                df["Date"] = pd.to_datetime(df["Date"])
                
                # Tri par date
                df = df.sort_values("Date")
                
                # Ajout du symbole
                df["Symbole"] = symbol
                
                logger.info(f"Récupéré {len(df)} lignes de données pour {symbol}")
                return df
            else:
                logger.warning(f"Aucune donnée disponible pour {symbol}")
                return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Erreur lors du scraping de {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def scrape_brvm_official(self, symbol, start_date='01/01/2010', end_date=None):
        """
        Scraper les données historiques d'une valeur depuis le site officiel de la BRVM.
        
        Args:
            symbol (str): Le symbole de la valeur
            start_date (str): Date de début au format DD/MM/YYYY
            end_date (str): Date de fin au format DD/MM/YYYY
        
        Returns:
            pd.DataFrame: DataFrame contenant les données historiques
        """
        if end_date is None:
            end_date = datetime.now().strftime('%d/%m/%Y')
        
        logger.info(f"Récupération des données officielles BRVM pour {symbol} de {start_date} à {end_date}")
        
        try:
            # Conversion des dates
            start_date_obj = datetime.strptime(start_date, '%d/%m/%Y')
            end_date_obj = datetime.strptime(end_date, '%d/%m/%Y')
            
            # URL pour les données historiques de la BRVM
            # Noter que cette implémentation est indicative et devra être adaptée
            # selon la structure exacte de l'API ou la page de la BRVM
            url = f"https://www.brvm.org/fr/historique/{symbol}"
            
            params = {
                "start": start_date_obj.strftime('%Y-%m-%d'),
                "end": end_date_obj.strftime('%Y-%m-%d')
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extraction des données du tableau
            data = []
            table = soup.select_one("table.table")
            
            if table:
                rows = table.select("tbody tr")
                for row in rows:
                    cols = row.select("td")
                    if len(cols) >= 6:
                        date_str = cols[0].text.strip()
                        opening = cols[1].text.strip().replace(',', '.')
                        high = cols[2].text.strip().replace(',', '.')
                        low = cols[3].text.strip().replace(',', '.')
                        closing = cols[4].text.strip().replace(',', '.')
                        volume = cols[5].text.strip().replace(' ', '')
                        
                        data.append({
                            "Date": datetime.strptime(date_str, '%d/%m/%Y'),
                            "Ouverture": float(opening) if opening else None,
                            "Plus_Haut": float(high) if high else None,
                            "Plus_Bas": float(low) if low else None,
                            "Cloture": float(closing) if closing else None,
                            "Volume": int(volume) if volume else 0,
                            "Symbole": symbol
                        })
            
            df = pd.DataFrame(data)
            if not df.empty:
                df = df.sort_values("Date")
                logger.info(f"Récupéré {len(df)} lignes de données officielles BRVM pour {symbol}")
            else:
                logger.warning(f"Aucune donnée officielle disponible pour {symbol}")
            
            return df
            
        except Exception as e:
            logger.error(f"Erreur lors du scraping officiel BRVM pour {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def get_all_historical_data(self, use_sika=True, use_brvm=True):
        """
        Récupérer les données historiques pour toutes les valeurs.
        
        Args:
            use_sika (bool): Utiliser Sika Finance comme source
            use_brvm (bool): Utiliser le site officiel BRVM comme source
        """
        stocks = self.get_all_stocks()
        
        # Ajouter les indices
        all_symbols = stocks + [{"symbol": idx, "name": idx} for idx in self.indices]
        
        for stock in all_symbols:
            symbol = stock["symbol"]
            
            df_combined = pd.DataFrame()
            
            # Tentative avec Sika Finance
            if use_sika:
                df_sika = self.scrape_sika_finance(symbol)
                if not df_sika.empty:
                    df_combined = df_sika
            
            # Tentative avec le site officiel BRVM
            if use_brvm and df_combined.empty:
                df_brvm = self.scrape_brvm_official(symbol)
                if not df_brvm.empty:
                    df_combined = df_brvm
            
            # Sauvegarder les données si on a récupéré quelque chose
            if not df_combined.empty:
                output_path = f"data/{symbol.replace('/', '-')}_historical.csv"
                df_combined.to_csv(output_path, index=False)
                logger.info(f"Données sauvegardées pour {symbol} dans {output_path}")
            else:
                logger.warning(f"Aucune donnée n'a pu être récupérée pour {symbol}")
            
            # Respecter la politesse avec les serveurs
            time.sleep(2)


def main():
    """Point d'entrée principal."""
    logger.info("Début du scraping des données BRVM")
    
    scraper = BRVMScraper()
    scraper.get_all_historical_data()
    
    logger.info("Scraping terminé")


if __name__ == "__main__":
    main()
