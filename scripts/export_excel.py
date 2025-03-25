#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script pour exporter les données et les analyses de la BRVM au format Excel.
"""

import os
import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import sys
import logging

# Ajouter le répertoire parent au path pour pouvoir importer les modules du projet
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("export_excel.log"), logging.StreamHandler()]
)
logger = logging.getLogger("BRVM_Excel_Export")

def ensure_directory(directory):
    """S'assurer que le répertoire existe, le créer si nécessaire."""
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Répertoire '{directory}' créé.")

def load_data(data_dir="../data"):
    """Charger toutes les données des fichiers CSV."""
    logger.info(f"Chargement des données depuis {data_dir}...")
    
    all_files = glob.glob(os.path.join(data_dir, "*.csv"))
    
    if not all_files:
        logger.error(f"Aucun fichier CSV trouvé dans {data_dir}")
        return {}
    
    data_frames = {}
    
    for file_path in all_files:
        file_name = os.path.basename(file_path)
        symbol = file_name.split('_')[0]
        
        try:
            df = pd.read_csv(file_path)
            
            # Convertir la date en format datetime
            df['Date'] = pd.to_datetime(df['Date'])
            
            # S'assurer que les colonnes numériques le sont bien
            for col in ['Ouverture', 'Plus_Haut', 'Plus_Bas', 'Cloture', 'Volume']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Trier par date
            df = df.sort_values('Date')
            
            data_frames[symbol] = df
            logger.info(f"Chargé {len(df)} lignes pour {symbol}")
        except Exception as e:
            logger.error(f"Erreur lors du chargement de {file_path}: {str(e)}")
    
    return data_frames

def calculate_performance(df):
    """Calculer les indicateurs de performance pour une valeur."""
    if df.empty or len(df) < 2:
        return {}
    
    # Calculer les rendements journaliers
    df['Rendement'] = df['Cloture'].pct_change()
    
    # Dates de début et de fin
    start_date = df['Date'].min()
    end_date = df['Date'].max()
    duration_days = (end_date - start_date).days
    duration_years = duration_days / 365.25
    
    # Prix initial et final
    initial_price = df.iloc[0]['Cloture']
    final_price = df.iloc[-1]['Cloture']
    
    # Performance globale
    total_return = (final_price / initial_price - 1) * 100
    
    # Performance annualisée
    annual_return = (((final_price / initial_price) ** (1 / duration_years)) - 1) * 100 if duration_years > 0 else 0
    
    # Volatilité (écart-type des rendements journaliers annualisé)
    volatility = df['Rendement'].std() * np.sqrt(252) * 100  # Annualisé en %
    
    # Ratio de Sharpe (en supposant un taux sans risque de 3%)
    risk_free_rate = 0.03
    sharpe_ratio = (annual_return / 100 - risk_free_rate) / (volatility / 100) if volatility > 0 else 0
    
    # Rendement max et min
    max_daily_return = df['Rendement'].max() * 100
    min_daily_return = df['Rendement'].min() * 100
    
    # Drawdown maximum
    df['Cumul'] = (1 + df['Rendement']).cumprod()
    df['Drawdown'] = df['Cumul'] / df['Cumul'].cummax() - 1
    max_drawdown = df['Drawdown'].min() * 100
    
    return {
        'start_date': start_date,
        'end_date': end_date,
        'duration_days': duration_days,
        'duration_years': duration_years,
        'initial_price': initial_price,
        'final_price': final_price,
        'total_return': total_return,
        'annual_return': annual_return,
        'volatility': volatility,
        'sharpe_ratio': sharpe_ratio,
        'max_daily_return': max_daily_return,
        'min_daily_return': min_daily_return,
        'max_drawdown': max_drawdown
    }

def get_sector_classification():
    """Obtenir la classification des secteurs pour les valeurs."""
    sectors = {
        'Banque': ['SGBCI', 'BOA', 'ECOBANK', 'SIB', 'NSIA', 'BICI', 'BDM', 'CORIS'],
        'Agro-industrie': ['SOGB', 'SAPH', 'PALC', 'SIFCA', 'SICOR', 'SUCRIVOIRE'],
        'Distribution': ['CFAO', 'BERNABE', 'VIVO', 'TOTAL'],
        'Services publics': ['SODECI', 'CIE', 'SONATEL', 'ONATEL'],
        'Industrie': ['NESTLE', 'SOLIBRA', 'SMB', 'UNIWAX', 'FILTISAC', 'AIR'],
        'Transport': ['BOLLORE', 'MOVIS', 'SETAO']
    }
    
    # Créer une table de correspondance symbole -> secteur
    symbol_to_sector = {}
    for sector, symbols in sectors.items():
        for symbol in symbols:
            symbol_to_sector[symbol] = sector
    
    return symbol_to_sector

def export_to_excel(data_frames, output_dir="../exports"):
    """Exporter les données et analyses au format Excel."""
    ensure_directory(output_dir)
    
    # Nom du fichier avec date et heure
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    excel_file = os.path.join(output_dir, f"brvm_analysis_{timestamp}.xlsx")
    
    logger.info(f"Exportation des données vers {excel_file}...")
    
    # Créer un writer Excel avec xlsxwriter comme moteur
    with pd.ExcelWriter(excel_file, engine='xlsxwriter') as writer:
        workbook = writer.book
        
        # Format pour les dates
        date_format = workbook.add_format({'num_format': 'dd/mm/yyyy'})
        
        # Format pour les pourcentages
        pct_format = workbook.add_format({'num_format': '0.00%'})
        
        # Format pour les nombres
        num_format = workbook.add_format({'num_format': '#,##0.00'})
        
        # Format pour les titres
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#D7E4BC',
            'border': 1
        })
        
        # 1. Exporter un résumé global
        logger.info("Création de la feuille de résumé...")
        
        # Calculer les performances
        performances = {}
        for symbol, df in data_frames.items():
            try:
                perf = calculate_performance(df)
                if perf:  # Si le calcul a réussi
                    performances[symbol] = perf
            except Exception as e:
                logger.error(f"Erreur lors du calcul des performances pour {symbol}: {str(e)}")
        
        # Créer un DataFrame avec toutes les performances
        perf_df = pd.DataFrame.from_dict(performances, orient='index')
        perf_df.index.name = 'Symbole'
        
        # Ajouter le secteur
        symbol_to_sector = get_sector_classification()
        perf_df['Secteur'] = perf_df.index.map(
            lambda x: symbol_to_sector.get(x, 'Indice' if x.startswith('BRVM') else 'Autres')
        )
        
        # Trier par performance totale
        perf_df = perf_df.sort_values('total_return', ascending=False)
        
        # Sélectionner et renommer les colonnes pour le résumé
        summary_df = perf_df[[
            'Secteur', 'initial_price', 'final_price', 'total_return', 
            'annual_return', 'volatility', 'sharpe_ratio', 'max_drawdown'
        ]].copy()
        
        summary_df.columns = [
            'Secteur', 'Prix Initial', 'Prix Final', 'Performance Totale (%)', 
            'Performance Annualisée (%)', 'Volatilité (%)', 'Ratio de Sharpe', 'Drawdown Max (%)'
        ]
        
        # Écrire le résumé
        summary_df.to_excel(writer, sheet_name='Résumé', index=True)
        
        # Récupérer la feuille et ajuster le format
        worksheet = writer.sheets['Résumé']
        worksheet.set_column('A:A', 15)  # Symbole
        worksheet.set_column('B:B', 15)  # Secteur
        worksheet.set_column('C:D', 12, num_format)  # Prix
        worksheet.set_column('E:H', 18, num_format)  # Performances
        
        # 2. Exporter chaque valeur sur sa propre feuille
        for symbol, df in data_frames.items():
            if len(symbol) > 20:  # Excel a une limite de 31 caractères pour les noms de feuilles
                sheet_name = symbol[:20]
            else:
                sheet_name = symbol
            
            logger.info(f"Création de la feuille pour {symbol}...")
            
            # Reformater le DataFrame pour l'export
            export_df = df[['Date', 'Ouverture', 'Plus_Haut', 'Plus_Bas', 'Cloture', 'Volume']].copy()
            export_df.columns = ['Date', 'Ouverture', 'Plus Haut', 'Plus Bas', 'Clôture', 'Volume']
            
            # Écrire les données
            export_df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Récupérer la feuille et ajuster le format
            worksheet = writer.sheets[sheet_name]
            worksheet.set_column('A:A', 12, date_format)  # Date
            worksheet.set_column('B:E', 10, num_format)  # Prix
            worksheet.set_column('F:F', 12)  # Volume
            
        # 3. Exporter l'analyse sectorielle
        logger.info("Création de la feuille d'analyse sectorielle...")
        
        # Analyser les performances par secteur
        sector_perf = perf_df.groupby('Secteur').agg({
            'total_return': 'mean',
            'annual_return': 'mean',
            'volatility': 'mean',
            'sharpe_ratio': 'mean',
            'max_drawdown': 'mean'
        }).round(2)
        
        # Trier par performance annualisée
        sector_perf = sector_perf.sort_values('annual_return', ascending=False)
        
        # Renommer les colonnes
        sector_perf.columns = [
            'Performance Totale Moyenne (%)', 
            'Performance Annualisée Moyenne (%)', 
            'Volatilité Moyenne (%)', 
            'Ratio de Sharpe Moyen', 
            'Drawdown Max Moyen (%)'
        ]
        
        # Écrire l'analyse sectorielle
        sector_perf.to_excel(writer, sheet_name='Analyse Sectorielle')
        
        # Récupérer la feuille et ajuster le format
        worksheet = writer.sheets['Analyse Sectorielle']
        worksheet.set_column('A:A', 18)  # Secteur
        worksheet.set_column('B:F', 25, num_format)  # Métriques
    
    logger.info(f"Exportation terminée : {excel_file}")
    return excel_file

def main():
    """Fonction principale."""
    logger.info("Démarrage de l'exportation Excel des données BRVM...")
    
    # Charger les données
    data_frames = load_data()
    
    if not data_frames:
        logger.error("Aucune donnée à exporter. Arrêt du processus.")
        return
    
    # Exporter vers Excel
    excel_file = export_to_excel(data_frames)
    
    logger.info(f"Exportation Excel terminée avec succès. Fichier créé : {excel_file}")

if __name__ == "__main__":
    main()
