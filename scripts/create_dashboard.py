#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script pour générer un tableau de bord HTML interactif des analyses de la BRVM.
"""

import os
import sys
import glob
import pandas as pd
import numpy as np
import logging
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import jinja2

# Ajouter le répertoire parent au path pour pouvoir importer les modules du projet
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("dashboard.log"), logging.StreamHandler()]
)
logger = logging.getLogger("BRVM_Dashboard")

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

def create_performance_chart(perf_df):
    """Créer un graphique des performances totales des 15 meilleures valeurs."""
    # Sélectionner les 15 meilleures performances
    top_perf = perf_df.sort_values('total_return', ascending=False).head(15)
    
    # Créer le graphique
    fig = px.bar(
        top_perf, 
        x=top_perf.index, 
        y='total_return',
        title='Performance totale des 15 meilleures valeurs (%)',
        labels={'x': 'Valeur', 'total_return': 'Performance totale (%)'},
        color='total_return',
        color_continuous_scale=px.colors.sequential.Blues
    )
    
    # Mise en page
    fig.update_layout(
        xaxis_tickangle=-45,
        autosize=True,
        margin=dict(l=50, r=50, b=100, t=100, pad=4)
    )
    
    return fig.to_html(full_html=False, include_plotlyjs='cdn')

def create_sector_chart(perf_df):
    """Créer un graphique des performances moyennes par secteur."""
    # Obtenir classification sectorielle
    symbol_to_sector = get_sector_classification()
    perf_df['Secteur'] = perf_df.index.map(
        lambda x: symbol_to_sector.get(x, 'Indice' if x.startswith('BRVM') else 'Autres')
    )
    
    # Analyser les performances par secteur
    sector_perf = perf_df.groupby('Secteur').agg({
        'total_return': 'mean',
        'annual_return': 'mean',
        'volatility': 'mean',
        'sharpe_ratio': 'mean'
    }).round(2)
    
    # Trier par performance annualisée
    sector_perf = sector_perf.sort_values('annual_return', ascending=False)
    
    # Créer le graphique
    fig = px.bar(
        sector_perf, 
        x=sector_perf.index, 
        y='annual_return',
        title='Performance annualisée moyenne par secteur (%)',
        labels={'x': 'Secteur', 'annual_return': 'Performance annualisée moyenne (%)'},
        color='annual_return',
        color_continuous_scale=px.colors.sequential.Greens
    )
    
    # Mise en page
    fig.update_layout(
        xaxis_tickangle=-45,
        autosize=True,
        margin=dict(l=50, r=50, b=100, t=100, pad=4)
    )
    
    return fig.to_html(full_html=False, include_plotlyjs='cdn')

def create_brvm_evolution_chart(data_frames):
    """Créer un graphique de l'évolution de l'indice BRVM-Composite."""
    if 'BRVM-Composite' in data_frames:
        brvm_composite = data_frames['BRVM-Composite']
        
        # Créer le graphique
        fig = px.line(
            brvm_composite, 
            x='Date', 
            y='Cloture',
            title='Évolution de l\'indice BRVM-Composite',
            labels={'Date': 'Date', 'Cloture': 'Valeur de l\'indice'}
        )
        
        # Ajouter une ligne de tendance
        fig.add_trace(
            go.Scatter(
                x=brvm_composite['Date'],
                y=brvm_composite['Cloture'].rolling(window=50).mean(),
                mode='lines',
                name='Moyenne mobile (50 jours)',
                line=dict(color='red', width=1)
            )
        )
        
        # Mise en page
        fig.update_layout(
            autosize=True,
            margin=dict(l=50, r=50, b=50, t=100, pad=4),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig.to_html(full_html=False, include_plotlyjs='cdn')
    else:
        return "<p>Données de l'indice BRVM-Composite non disponibles.</p>"

def create_risk_return_chart(perf_df):
    """Créer un graphique risque/rendement interactif."""
    # Obtenir classification sectorielle
    symbol_to_sector = get_sector_classification()
    perf_df['Secteur'] = perf_df.index.map(
        lambda x: symbol_to_sector.get(x, 'Indice' if x.startswith('BRVM') else 'Autres')
    )
    
    # Filtrer pour garder uniquement les valeurs (pas les indices)
    values_df = perf_df[~perf_df.index.str.startswith('BRVM')].copy()
    
    # Ajouter le symbole comme colonne pour l'affichage
    values_df['Symbole'] = values_df.index
    
    # Créer le graphique
    fig = px.scatter(
        values_df, 
        x='volatility', 
        y='annual_return',
        size='total_return',
        color='Secteur',
        hover_name='Symbole',
        hover_data={
            'Symbole': True,
            'Secteur': True,
            'annual_return': ':.2f',
            'volatility': ':.2f',
            'sharpe_ratio': ':.2f',
            'total_return': ':.2f'
        },
        title='Risque vs Rendement des valeurs de la BRVM',
        labels={
            'volatility': 'Volatilité annualisée (%)',
            'annual_return': 'Rendement annualisé (%)',
            'total_return': 'Performance totale (%)',
            'sharpe_ratio': 'Ratio de Sharpe'
        },
        size_max=50
    )
    
    # Ajouter lignes de référence
    fig.add_shape(
        type="line",
        x0=0, y0=0, x1=values_df['volatility'].max(), y1=0,
        line=dict(color="red", width=1, dash="dash")
    )
    
    fig.add_shape(
        type="line",
        x0=0, y0=0, x1=0, y1=values_df['annual_return'].max(),
        line=dict(color="red", width=1, dash="dash")
    )
    
    # Mise en page
    fig.update_layout(
        autosize=True,
        margin=dict(l=50, r=50, b=50, t=100, pad=4),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig.to_html(full_html=False, include_plotlyjs='cdn')

def create_performance_table(perf_df):
    """Créer un tableau HTML des performances des valeurs."""
    # Sélectionner les colonnes pertinentes
    performance_table = perf_df[[
        'total_return', 'annual_return', 'volatility', 
        'sharpe_ratio', 'max_drawdown', 'duration_years'
    ]].copy()
    
    # Obtenir classification sectorielle
    symbol_to_sector = get_sector_classification()
    performance_table['Secteur'] = perf_df.index.map(
        lambda x: symbol_to_sector.get(x, 'Indice' if x.startswith('BRVM') else 'Autres')
    )
    
    # Renommer les colonnes
    performance_table.columns = [
        'Performance totale (%)', 'Performance annualisée (%)',
        'Volatilité (%)', 'Ratio de Sharpe', 'Drawdown max (%)',
        'Durée (années)', 'Secteur'
    ]
    
    # Réorganiser les colonnes
    performance_table = performance_table[[
        'Secteur', 'Performance totale (%)', 'Performance annualisée (%)',
        'Volatilité (%)', 'Ratio de Sharpe', 'Drawdown max (%)',
        'Durée (années)'
    ]]
    
    # Trier par performance totale
    performance_table = performance_table.sort_values('Performance totale (%)', ascending=False)
    
    # Formater les valeurs
    for col in performance_table.columns:
        if col != 'Secteur':
            performance_table[col] = performance_table[col].round(2)
    
    # Convertir en HTML avec style
    html_table = performance_table.to_html(
        classes=['table', 'table-striped', 'table-hover', 'table-sm'],
        border=0
    )
    
    return html_table

def create_dashboard(data_frames, output_dir="../dashboard"):
    """Créer un tableau de bord HTML interactif."""
    ensure_directory(output_dir)
    
    # Calculer les performances
    logger.info("Calcul des performances...")
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
    
    # Créer les graphiques
    logger.info("Création des graphiques interactifs...")
    performance_chart = create_performance_chart(perf_df)
    sector_chart = create_sector_chart(perf_df)
    brvm_evolution_chart = create_brvm_evolution_chart(data_frames)
    risk_return_chart = create_risk_return_chart(perf_df)
    
    # Créer le tableau de performance
    performance_table = create_performance_table(perf_df)
    
    # Préparer le modèle de template
    logger.info("Génération de la page HTML...")
    template_str = """
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Tableau de bord BRVM</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f8f9fa;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
            }
            .card {
                margin-bottom: 20px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            .chart-container {
                background-color: white;
                padding: 15px;
                border-radius: 5px;
            }
            .table-container {
                background-color: white;
                padding: 15px;
                border-radius: 5px;
                overflow-x: auto;
            }
            h1, h2, h3 {
                color: #0d6efd;
            }
            .header {
                text-align: center;
                margin-bottom: 30px;
                background-color: white;
                padding: 20px;
                border-radius: 5px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            .table {
                width: 100%;
                font-size: 0.9rem;
            }
            .footer {
                text-align: center;
                margin-top: 30px;
                padding: 10px;
                background-color: #343a40;
                color: white;
                border-radius: 5px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Analyse des performances de la BRVM</h1>
                <p class="text-muted">Rapport généré le {{ date_generation }}</p>
            </div>
            
            <div class="row">
                <div class="col-md-12">
                    <div class="card">
                        <div class="card-header">
                            <h2>Évolution de l'indice BRVM-Composite</h2>
                        </div>
                        <div class="card-body chart-container">
                            {{ brvm_evolution_chart }}
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h2>Performances des 15 meilleures valeurs</h2>
                        </div>
                        <div class="card-body chart-container">
                            {{ performance_chart }}
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h2>Performances par secteur</h2>
                        </div>
                        <div class="card-body chart-container">
                            {{ sector_chart }}
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row">
                <div class="col-md-12">
                    <div class="card">
                        <div class="card-header">
                            <h2>Analyse Risque/Rendement</h2>
                        </div>
                        <div class="card-body chart-container">
                            {{ risk_return_chart }}
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row">
                <div class="col-md-12">
                    <div class="card">
                        <div class="card-header">
                            <h2>Tableau des performances</h2>
                        </div>
                        <div class="card-body table-container">
                            {{ performance_table }}
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="footer">
                <p>© {{ year }} - Analyse des performances de la BRVM</p>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """
    
    # Compiler le template
    template = jinja2.Template(template_str)
    
    # Générer la page HTML
    html_content = template.render(
        date_generation=datetime.now().strftime("%d/%m/%Y à %H:%M"),
        year=datetime.now().year,
        brvm_evolution_chart=brvm_evolution_chart,
        performance_chart=performance_chart,
        sector_chart=sector_chart,
        risk_return_chart=risk_return_chart,
        performance_table=performance_table
    )
    
    # Nom du fichier avec date et heure
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    html_file = os.path.join(output_dir, f"brvm_dashboard_{timestamp}.html")
    
    # Écrire le fichier HTML
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    logger.info(f"Tableau de bord généré avec succès: {html_file}")
    
    return html_file

def main():
    """Fonction principale."""
    logger.info("Démarrage de la création du tableau de bord...")
    
    # Charger les données
    data_frames = load_data()
    
    if not data_frames:
        logger.error("Aucune donnée à analyser. Arrêt du processus.")
        return
    
    # Créer le tableau de bord
    dashboard_file = create_dashboard(data_frames)
    
    logger.info(f"Création du tableau de bord terminée avec succès. Fichier créé : {dashboard_file}")
    
    # Ouvrir le tableau de bord dans le navigateur par défaut
    try:
        import webbrowser
        webbrowser.open('file://' + os.path.abspath(dashboard_file))
    except Exception as e:
        logger.error(f"Erreur lors de l'ouverture du tableau de bord dans le navigateur: {str(e)}")

if __name__ == "__main__":
    main()
