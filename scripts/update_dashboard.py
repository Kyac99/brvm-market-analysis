#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script pour mettre à jour le tableau de bord des valeurs BRVM et le déployer sur GitHub Pages.
Ce script exécute le processus de récupération des données et génère un tableau de bord HTML
dans le dossier docs/ pour GitHub Pages.
"""

import os
import sys
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import time
import re
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import logging
import shutil

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("update_dashboard.log"), logging.StreamHandler()]
)
logger = logging.getLogger("BRVM_Dashboard_Update")

def ensure_directory(directory):
    """S'assurer que le répertoire existe, le créer si nécessaire."""
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Répertoire '{directory}' créé.")

def get_session():
    """Initialise et renvoie une session HTTP avec les entêtes appropriés."""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'
    })
    return session

def get_brvm_values(session):
    """Récupère la liste des valeurs cotées à la BRVM depuis Sika Finance."""
    url = "https://www.sikafinance.com/marches/cotations-brvm"
    
    try:
        response = session.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Chercher le tableau des cotations
        table = soup.find('table', class_='table-cotation')
        
        if not table:
            logger.error("Tableau des cotations non trouvé.")
            return []
        
        values = []
        rows = table.find_all('tr')[1:]  # Ignorer l'en-tête
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 9:  # Vérifier qu'il y a assez de cellules
                # Extraire les informations de base
                try:
                    symbol = cells[0].text.strip()
                    name = cells[1].text.strip()
                    sector = cells[2].text.strip()
                    current_price = float(cells[3].text.strip().replace(' ', '').replace(',', '.') or 0)
                    change = cells[4].text.strip().replace('%', '').replace(',', '.').replace(' ', '')
                    change = float(change) if change else 0
                    volume = int(cells[5].text.strip().replace(' ', '') or 0)
                    previous_price = float(cells[6].text.strip().replace(' ', '').replace(',', '.') or 0)
                    year_high = float(cells[7].text.strip().replace(' ', '').replace(',', '.') or 0)
                    year_low = float(cells[8].text.strip().replace(' ', '').replace(',', '.') or 0)
                    
                    # Si possible, récupérer l'URL de la page de détail
                    detail_link = None
                    if cells[0].find('a'):
                        detail_link = cells[0].find('a').get('href')
                        if detail_link and not detail_link.startswith('http'):
                            detail_link = f"https://www.sikafinance.com{detail_link}"
                    
                    values.append({
                        'symbol': symbol,
                        'name': name,
                        'sector': sector,
                        'current_price': current_price,
                        'change': change,
                        'volume': volume,
                        'previous_price': previous_price,
                        'year_high': year_high,
                        'year_low': year_low,
                        'detail_link': detail_link
                    })
                except Exception as e:
                    logger.error(f"Erreur lors de l'extraction des données pour une valeur: {str(e)}")
                    continue
        
        logger.info(f"Récupéré {len(values)} valeurs cotées à la BRVM.")
        return values
    
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des valeurs: {str(e)}")
        return []

def get_market_cap(session, symbol, current_price):
    """Essaie de récupérer la capitalisation boursière pour une valeur donnée."""
    url = f"https://www.sikafinance.com/marches/cotation_seance/{symbol}"
    
    try:
        response = session.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Chercher les informations de capitalisation boursière
        market_cap = None
        
        # Méthode 1 : chercher directement dans la page
        cap_elements = soup.find_all(text=re.compile('Capitalisation', re.IGNORECASE))
        
        for element in cap_elements:
            parent = element.parent
            if parent:
                next_sibling = parent.find_next_sibling()
                if next_sibling:
                    cap_text = next_sibling.text.strip()
                    # Extraire les chiffres
                    cap_value = re.sub(r'[^\d,]', '', cap_text)
                    if cap_value:
                        try:
                            market_cap = float(cap_value.replace(',', '.'))
                            # Convertir en milliards si nécessaire
                            if 'milliard' in cap_text.lower():
                                market_cap *= 1e9
                            elif 'million' in cap_text.lower():
                                market_cap *= 1e6
                            break
                        except:
                            pass
        
        # Si pas trouvé, méthode 2 : chercher le nombre d'actions
        if not market_cap:
            shares_elements = soup.find_all(text=re.compile('Nombre d\'actions', re.IGNORECASE))
            
            for element in shares_elements:
                parent = element.parent
                if parent:
                    next_sibling = parent.find_next_sibling()
                    if next_sibling:
                        shares_text = next_sibling.text.strip()
                        # Extraire les chiffres
                        shares_value = re.sub(r'[^\d]', '', shares_text)
                        if shares_value:
                            try:
                                shares = int(shares_value)
                                market_cap = shares * current_price
                                break
                            except:
                                pass
        
        return market_cap
    
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de la capitalisation pour {symbol}: {str(e)}")
        return None

def get_financial_data(session, symbol):
    """Récupère les données financières (PER, dividendes) pour une valeur donnée."""
    url = f"https://www.sikafinance.com/bourse/societe/{symbol}"
    
    financial_data = {
        'per_2020': None,
        'per_2021': None,
        'per_2022': None,
        'per_2023': None,
        'per_2024': None,
        'div_2020': None,
        'div_2021': None,
        'div_2022': None,
        'div_2023': None,
        'div_2024': None
    }
    
    try:
        response = session.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Chercher les tableaux de données financières
        tables = soup.find_all('table')
        
        for table in tables:
            # Chercher les données de PER
            if 'PER' in table.text or 'P/E' in table.text or 'Price Earning Ratio' in table.text:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        header = cells[0].text.strip()
                        if '2020' in header:
                            per_text = cells[1].text.strip().replace(',', '.').replace(' ', '')
                            try:
                                financial_data['per_2020'] = float(per_text) if per_text and per_text != '-' else None
                            except:
                                pass
                        elif '2021' in header:
                            per_text = cells[1].text.strip().replace(',', '.').replace(' ', '')
                            try:
                                financial_data['per_2021'] = float(per_text) if per_text and per_text != '-' else None
                            except:
                                pass
                        elif '2022' in header:
                            per_text = cells[1].text.strip().replace(',', '.').replace(' ', '')
                            try:
                                financial_data['per_2022'] = float(per_text) if per_text and per_text != '-' else None
                            except:
                                pass
                        elif '2023' in header:
                            per_text = cells[1].text.strip().replace(',', '.').replace(' ', '')
                            try:
                                financial_data['per_2023'] = float(per_text) if per_text and per_text != '-' else None
                            except:
                                pass
                        elif '2024' in header:
                            per_text = cells[1].text.strip().replace(',', '.').replace(' ', '')
                            try:
                                financial_data['per_2024'] = float(per_text) if per_text and per_text != '-' else None
                            except:
                                pass
            
            # Chercher les données de dividende
            if 'Dividende' in table.text or 'DPA' in table.text or 'Div/Action' in table.text:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        header = cells[0].text.strip()
                        if '2020' in header:
                            div_text = cells[1].text.strip().replace(',', '.').replace(' ', '')
                            try:
                                financial_data['div_2020'] = float(div_text) if div_text and div_text != '-' else None
                            except:
                                pass
                        elif '2021' in header:
                            div_text = cells[1].text.strip().replace(',', '.').replace(' ', '')
                            try:
                                financial_data['div_2021'] = float(div_text) if div_text and div_text != '-' else None
                            except:
                                pass
                        elif '2022' in header:
                            div_text = cells[1].text.strip().replace(',', '.').replace(' ', '')
                            try:
                                financial_data['div_2022'] = float(div_text) if div_text and div_text != '-' else None
                            except:
                                pass
                        elif '2023' in header:
                            div_text = cells[1].text.strip().replace(',', '.').replace(' ', '')
                            try:
                                financial_data['div_2023'] = float(div_text) if div_text and div_text != '-' else None
                            except:
                                pass
                        elif '2024' in header:
                            div_text = cells[1].text.strip().replace(',', '.').replace(' ', '')
                            try:
                                financial_data['div_2024'] = float(div_text) if div_text and div_text != '-' else None
                            except:
                                pass
        
        return financial_data
    
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des données financières pour {symbol}: {str(e)}")
        return financial_data

def create_interactive_dashboard(df):
    """Créer un tableau de bord interactif avec Plotly."""
    # Filtrer les valeurs avec capitalisation boursière disponible
    df_filtered = df[df['market_cap'].notna()].copy()
    
    # Top 15 des capitalisations
    top_market_cap = df_filtered.sort_values(by='market_cap', ascending=False).head(15)
    
    # Créer le graphique interactif des capitalisations
    fig1 = px.bar(
        top_market_cap, 
        x='symbol', 
        y='market_cap',
        title='Top 15 des valeurs par capitalisation boursière',
        hover_data=['name', 'sector', 'current_price'],
        color='market_cap',
        color_continuous_scale='Blues',
        labels={
            'symbol': 'Symbole',
            'market_cap': 'Capitalisation boursière (FCFA)',
            'name': 'Nom',
            'sector': 'Secteur',
            'current_price': 'Cours actuel'
        }
    )
    
    fig1.update_layout(
        xaxis_tickangle=-45,
        autosize=True,
        height=500,
        margin=dict(l=50, r=50, b=100, t=100, pad=4)
    )
    
    # Préparer les données pour le graphique PER
    per_data = []
    symbols = top_market_cap['symbol'].tolist()
    
    for symbol in symbols:
        row = df[df['symbol'] == symbol].iloc[0]
        for year in [2020, 2021, 2022, 2023, 2024]:
            per_value = row[f'per_{year}']
            if not pd.isna(per_value):
                per_data.append({
                    'symbol': symbol,
                    'name': row['name'],
                    'year': year,
                    'per': per_value
                })
    
    per_df = pd.DataFrame(per_data)
    
    # Graphique d'évolution du PER
    if not per_df.empty:
        fig2 = px.line(
            per_df, 
            x='year', 
            y='per', 
            color='symbol',
            title='Évolution du PER des principales valeurs (2020-2024)',
            markers=True,
            hover_data=['name'],
            labels={
                'year': 'Année',
                'per': 'PER',
                'symbol': 'Symbole',
                'name': 'Nom'
            }
        )
        
        fig2.update_layout(
            autosize=True,
            height=500,
            margin=dict(l=50, r=50, b=50, t=100, pad=4)
        )
    else:
        fig2 = go.Figure()
        fig2.update_layout(
            title="Pas assez de données de PER disponibles",
            annotations=[dict(
                text="Données insuffisantes",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False
            )]
        )
    
    # Top 15 des rendements de dividendes
    df_filtered['dividend_yield'] = df_filtered.apply(
        lambda row: (row['div_2024'] / row['current_price'] * 100) if not pd.isna(row['div_2024']) and row['current_price'] > 0 else None,
        axis=1
    )
    
    top_div_yield = df_filtered[df_filtered['dividend_yield'].notna()].sort_values(by='dividend_yield', ascending=False).head(15)
    
    # Graphique des rendements de dividendes
    fig3 = px.bar(
        top_div_yield, 
        x='symbol', 
        y='dividend_yield',
        title='Top 15 des valeurs par rendement du dividende',
        hover_data=['name', 'sector', 'current_price', 'div_2024'],
        color='dividend_yield',
        color_continuous_scale='Greens',
        labels={
            'symbol': 'Symbole',
            'dividend_yield': 'Rendement du dividende (%)',
            'name': 'Nom',
            'sector': 'Secteur',
            'current_price': 'Cours actuel',
            'div_2024': 'Dividende 2024'
        }
    )
    
    fig3.update_layout(
        xaxis_tickangle=-45,
        autosize=True,
        height=500,
        margin=dict(l=50, r=50, b=100, t=100, pad=4)
    )
    
    # Scatter plot PER vs Dividend Yield
    df_scatter = df_filtered[(df_filtered['per_2024'].notna()) & (df_filtered['dividend_yield'].notna())].copy()
    
    if not df_scatter.empty:
        fig4 = px.scatter(
            df_scatter, 
            x='per_2024', 
            y='dividend_yield',
            size='market_cap',
            color='sector',
            hover_name='symbol',
            hover_data=['name', 'current_price'],
            title='Relation entre PER 2024 et rendement du dividende',
            labels={
                'per_2024': 'PER 2024',
                'dividend_yield': 'Rendement du dividende (%)',
                'market_cap': 'Capitalisation boursière',
                'sector': 'Secteur',
                'name': 'Nom',
                'current_price': 'Cours actuel'
            }
        )
        
        fig4.update_layout(
            autosize=True,
            height=500,
            margin=dict(l=50, r=50, b=50, t=100, pad=4)
        )
    else:
        fig4 = go.Figure()
        fig4.update_layout(
            title="Données insuffisantes pour la relation PER-Dividende",
            annotations=[dict(
                text="Données insuffisantes",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False
            )]
        )
    
    # Formater la date pour le titre
    today = datetime.now().strftime('%d/%m/%Y')
    
    # Combiner les graphiques en HTML
    html_content = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Classement des valeurs de la BRVM</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f8f9fa; }}
            .container {{ max-width: 1400px; margin: 0 auto; }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .card {{ margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); }}
            .chart-container {{ background-color: white; padding: 15px; border-radius: 5px; }}
            h1, h2 {{ color: #0d6efd; }}
            .table-container {{ overflow-x: auto; }}
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
            th, td {{ padding: 12px 15px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background-color: #f8f9fa; color: #495057; font-weight: bold; }}
            tr:hover {{ background-color: #f8f9fa; }}
            .positive {{ color: #198754; }}
            .negative {{ color: #dc3545; }}
            .footer {{ text-align: center; margin-top: 30px; padding: 10px; color: #6c757d; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Classement des valeurs de la BRVM</h1>
                <p class="text-muted">Données extraites le {today}</p>
            </div>
            
            <div class="row mb-4">
                <div class="col-12">
                    <div class="card">
                        <div class="card-header">
                            <h2>Tableau complet des valeurs classées par capitalisation boursière</h2>
                        </div>
                        <div class="card-body table-container">
                            {df.to_html(classes='table table-striped table-hover', index=False, na_rep='-')}
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row mb-4">
                <div class="col-12">
                    <div class="card">
                        <div class="card-header">
                            <h2>Top 15 des valeurs par capitalisation boursière</h2>
                        </div>
                        <div class="card-body chart-container">
                            {fig1.to_html(full_html=False, include_plotlyjs='cdn')}
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row mb-4">
                <div class="col-12">
                    <div class="card">
                        <div class="card-header">
                            <h2>Top 15 des valeurs par rendement du dividende</h2>
                        </div>
                        <div class="card-body chart-container">
                            {fig3.to_html(full_html=False, include_plotlyjs='cdn')}
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row mb-4">
                <div class="col-md-6">
                    <div class="card h-100">
                        <div class="card-header">
                            <h2>Évolution du PER (2020-2024)</h2>
                        </div>
                        <div class="card-body chart-container">
                            {fig2.to_html(full_html=False, include_plotlyjs='cdn')}
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card h-100">
                        <div class="card-header">
                            <h2>Relation PER vs Rendement du dividende</h2>
                        </div>
                        <div class="card-body chart-container">
                            {fig4.to_html(full_html=False, include_plotlyjs='cdn')}
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="footer">
                <p>© {datetime.now().year} - Analyse des valeurs de la BRVM - Mis à jour le {today}</p>
                <p><a href="https://github.com/Kyac99/brvm-market-analysis" target="_blank">Voir le projet sur GitHub</a></p>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """
    
    return html_content

def main():
    """Fonction principale pour mettre à jour le tableau de bord GitHub Pages."""
    logger.info("Démarrage de la mise à jour du tableau de bord pour GitHub Pages...")
    
    # Création des répertoires nécessaires
    docs_dir = "../docs"
    ensure_directory(docs_dir)
    
    # Initialiser la session HTTP
    session = get_session()
    
    # Récupérer la liste des valeurs cotées
    logger.info("Récupération des valeurs cotées à la BRVM...")
    values = get_brvm_values(session)
    
    if not values:
        logger.error("Aucune valeur récupérée. Arrêt du processus.")
        return
    
    # Créer un DataFrame avec les valeurs de base
    df_values = pd.DataFrame(values)
    
    # Récupérer les capitalisations boursières
    logger.info("Récupération des capitalisations boursières...")
    market_caps = []
    for index, row in df_values.iterrows():
        symbol = row['symbol']
        current_price = row['current_price']
        
        logger.info(f"Récupération de la capitalisation boursière pour {symbol}...")
        market_cap = get_market_cap(session, symbol, current_price)
        market_caps.append(market_cap)
        
        # Respecter une pause pour ne pas surcharger le serveur
        time.sleep(1)
    
    # Ajouter les capitalisations au DataFrame
    df_values['market_cap'] = market_caps
    
    # Récupérer les données financières pour chaque valeur
    logger.info("Récupération des données financières...")
    financial_data_list = []
    for index, row in df_values.iterrows():
        symbol = row['symbol']
        
        logger.info(f"Récupération des données financières pour {symbol}...")
        financial_data = get_financial_data(session, symbol)
        financial_data_list.append(financial_data)
        
        # Respecter une pause pour ne pas surcharger le serveur
        time.sleep(1)
    
    # Convertir la liste en DataFrame
    df_financial = pd.DataFrame(financial_data_list)
    
    # Joindre les deux DataFrames
    df_combined = pd.concat([df_values, df_financial], axis=1)
    
    # Calculer le rendement du dividende (dividende 2024 / cours actuel)
    df_combined['dividend_yield'] = df_combined.apply(
        lambda row: (row['div_2024'] / row['current_price'] * 100) if row['div_2024'] is not None and row['current_price'] > 0 else None,
        axis=1
    )
    
    # Sélectionner les colonnes pertinentes pour l'affichage
    columns_to_display = [
        'symbol', 'name', 'sector', 'current_price', 'market_cap', 
        'per_2020', 'per_2021', 'per_2022', 'per_2023', 'per_2024',
        'div_2020', 'div_2021', 'div_2022', 'div_2023', 'div_2024',
        'dividend_yield'
    ]
    
    df_display = df_combined[columns_to_display].copy()
    
    # Arrondir les valeurs numériques pour une meilleure lisibilité
    for col in df_display.columns:
        if col not in ['symbol', 'name', 'sector']:
            df_display[col] = df_display[col].round(2)
    
    # Trier le DataFrame par capitalisation boursière décroissante
    df_sorted = df_display.sort_values(by='market_cap', ascending=False).reset_index(drop=True)
    
    logger.info("Création du tableau de bord HTML interactif...")
    html_dashboard = create_interactive_dashboard(df_sorted)
    
    # Sauvegarder le tableau de bord dans le dossier docs
    index_file = os.path.join(docs_dir, "index.html")
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write(html_dashboard)
    
    # Sauvegarder aussi une copie datée pour garder un historique
    dated_file = os.path.join(docs_dir, f"classement_brvm_{datetime.now().strftime('%Y%m%d')}.html")
    shutil.copy2(index_file, dated_file)
    
    logger.info(f"Tableau de bord mis à jour: {index_file}")
    logger.info(f"Copie datée sauvegardée: {dated_file}")
    
    # Créer un fichier README pour le dossier docs
    readme_file = os.path.join(docs_dir, "README.md")
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(f"""# Tableau de bord des valeurs de la BRVM

Ce dossier contient les fichiers HTML du tableau de bord des valeurs mobilières cotées à la Bourse Régionale des Valeurs Mobilières (BRVM).

- **index.html** : Tableau de bord actuel, mis à jour le {datetime.now().strftime('%d/%m/%Y')}
- Des copies datées du tableau de bord sont également disponibles pour garder un historique des analyses

Ce tableau de bord est généré automatiquement par le script `scripts/update_dashboard.py`.

Pour plus d'informations, consultez le [dépôt GitHub](https://github.com/Kyac99/brvm-market-analysis).
""")

    logger.info("Mise à jour du tableau de bord terminée avec succès!")

if __name__ == "__main__":
    main()
