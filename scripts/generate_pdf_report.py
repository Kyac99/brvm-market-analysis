#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script pour générer un rapport PDF des analyses des valeurs de la BRVM.
"""

import os
import sys
import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import logging
from fpdf import FPDF
import matplotlib
matplotlib.use('Agg')  # Utiliser un backend non-interactif

# Ajouter le répertoire parent au path pour pouvoir importer les modules du projet
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("pdf_report.log"), logging.StreamHandler()]
)
logger = logging.getLogger("BRVM_PDF_Report")

class BRVMPDF(FPDF):
    """Classe personnalisée pour le rapport PDF."""
    
    def header(self):
        """En-tête du document."""
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Analyse des performances de la BRVM', 0, 1, 'C')
        self.set_font('Arial', 'I', 10)
        self.cell(0, 10, f'Rapport généré le {datetime.now().strftime("%d/%m/%Y à %H:%M")}', 0, 1, 'C')
        self.ln(10)
    
    def footer(self):
        """Pied de page du document."""
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', 0, 0, 'C')
    
    def chapter_title(self, title):
        """Afficher un titre de chapitre."""
        self.set_font('Arial', 'B', 12)
        self.set_fill_color(200, 220, 255)
        self.cell(0, 6, title, 0, 1, 'L', 1)
        self.ln(4)
    
    def chapter_body(self, body):
        """Afficher un corps de chapitre."""
        self.set_font('Arial', '', 11)
        self.multi_cell(0, 5, body)
        self.ln()
    
    def add_table(self, header, data):
        """Ajouter un tableau."""
        # Largeur des colonnes
        w = self.w / len(header)
        
        # En-têtes
        self.set_font('Arial', 'B', 10)
        self.set_fill_color(200, 220, 255)
        for col in header:
            self.cell(w, 7, col, 1, 0, 'C', 1)
        self.ln()
        
        # Données
        self.set_font('Arial', '', 10)
        self.set_fill_color(255, 255, 255)
        for row in data:
            for col in row:
                self.cell(w, 6, str(col), 1, 0, 'C')
            self.ln()
        
        self.ln(5)
    
    def add_image(self, img_path, w=0, h=0, caption=None):
        """Ajouter une image."""
        if os.path.exists(img_path):
            self.image(img_path, x=None, y=None, w=w, h=h)
            if caption:
                self.set_font('Arial', 'I', 9)
                self.ln(2)
                self.cell(0, 5, caption, 0, 1, 'C')
                self.ln(5)
        else:
            logger.error(f"Image non trouvée: {img_path}")

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

def generate_performance_chart(perf_df, output_dir):
    """Générer un graphique des performances totales."""
    plt.figure(figsize=(12, 8))
    
    # Sélectionner les 15 meilleures performances pour éviter un graphique trop chargé
    top_perf = perf_df.sort_values('total_return', ascending=False).head(15)
    
    # Créer le graphique
    ax = sns.barplot(x=top_perf.index, y='total_return', data=top_perf)
    
    plt.title('Performance totale des 15 meilleures valeurs (%)', fontsize=16)
    plt.xticks(rotation=90)
    plt.ylabel('Performance totale (%)')
    plt.xlabel('Valeur')
    
    # Ajouter les valeurs sur les barres
    for i, v in enumerate(top_perf['total_return']):
        ax.text(i, v + (5 if v >= 0 else -20), f"{v:.1f}%", ha='center', fontsize=10)
    
    plt.tight_layout()
    
    # Sauvegarder le graphique
    chart_path = os.path.join(output_dir, 'performance_chart.png')
    plt.savefig(chart_path, dpi=200)
    plt.close()
    
    return chart_path

def generate_sector_chart(perf_df, output_dir):
    """Générer un graphique des performances par secteur."""
    plt.figure(figsize=(12, 8))
    
    # Obtenir classification sectorielle
    symbol_to_sector = get_sector_classification()
    perf_df['Secteur'] = perf_df.index.map(
        lambda x: symbol_to_sector.get(x, 'Indice' if x.startswith('BRVM') else 'Autres')
    )
    
    # Analyser les performances par secteur
    sector_perf = perf_df.groupby('Secteur').agg({'annual_return': 'mean'}).round(2)
    sector_perf = sector_perf.sort_values('annual_return', ascending=False)
    
    # Créer le graphique
    ax = sns.barplot(x=sector_perf.index, y='annual_return', data=sector_perf)
    
    plt.title('Performance annualisée moyenne par secteur (%)', fontsize=16)
    plt.xticks(rotation=45)
    plt.ylabel('Performance annualisée moyenne (%)')
    plt.xlabel('Secteur')
    
    # Ajouter les valeurs sur les barres
    for i, v in enumerate(sector_perf['annual_return']):
        ax.text(i, v + (1 if v >= 0 else -3), f"{v:.1f}%", ha='center')
    
    plt.tight_layout()
    
    # Sauvegarder le graphique
    chart_path = os.path.join(output_dir, 'sector_chart.png')
    plt.savefig(chart_path, dpi=200)
    plt.close()
    
    return chart_path

def generate_brvm_evolution_chart(data_frames, output_dir):
    """Générer un graphique de l'évolution de l'indice BRVM-Composite."""
    if 'BRVM-Composite' in data_frames:
        plt.figure(figsize=(12, 6))
        
        brvm_composite = data_frames['BRVM-Composite']
        plt.plot(brvm_composite['Date'], brvm_composite['Cloture'])
        
        plt.title('Évolution de l\'indice BRVM-Composite', fontsize=16)
        plt.xlabel('Date')
        plt.ylabel('Valeur de l\'indice')
        plt.grid(True)
        plt.tight_layout()
        
        # Sauvegarder le graphique
        chart_path = os.path.join(output_dir, 'brvm_evolution.png')
        plt.savefig(chart_path, dpi=200)
        plt.close()
        
        return chart_path
    else:
        return None

def generate_risk_return_chart(perf_df, output_dir):
    """Générer un graphique risque/rendement."""
    plt.figure(figsize=(12, 8))
    
    # Filtrer pour garder uniquement les valeurs (pas les indices)
    values_df = perf_df[~perf_df.index.str.startswith('BRVM')]
    
    # Créer le graphique
    ax = sns.scatterplot(x='volatility', y='annual_return', size='total_return', 
                         hue='sharpe_ratio', data=values_df, sizes=(50, 300))
    
    plt.title('Risque vs Rendement des valeurs de la BRVM', fontsize=16)
    plt.xlabel('Volatilité annualisée (%)')
    plt.ylabel('Rendement annualisé (%)')
    plt.axhline(y=0, color='red', linestyle='--', alpha=0.5)
    plt.axvline(x=0, color='red', linestyle='--', alpha=0.5)
    
    # Ajouter des annotations pour chaque point (maximum 10 pour la lisibilité)
    top_sharpe = values_df.sort_values('sharpe_ratio', ascending=False).head(10)
    for symbol in top_sharpe.index:
        x = values_df.loc[symbol, 'volatility']
        y = values_df.loc[symbol, 'annual_return']
        plt.annotate(symbol, (x, y), fontsize=8, ha='center')
    
    plt.colorbar(ax.collections[0], label="Ratio de Sharpe")
    plt.tight_layout()
    
    # Sauvegarder le graphique
    chart_path = os.path.join(output_dir, 'risk_return_chart.png')
    plt.savefig(chart_path, dpi=200)
    plt.close()
    
    return chart_path

def generate_pdf_report(data_frames, output_dir="../reports"):
    """Générer un rapport PDF avec les analyses des valeurs de la BRVM."""
    ensure_directory(output_dir)
    
    # Créer un répertoire temporaire pour les graphiques
    temp_dir = os.path.join(output_dir, "temp")
    ensure_directory(temp_dir)
    
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
    
    # Générer les graphiques
    logger.info("Génération des graphiques...")
    performance_chart = generate_performance_chart(perf_df, temp_dir)
    sector_chart = generate_sector_chart(perf_df, temp_dir)
    brvm_evolution_chart = generate_brvm_evolution_chart(data_frames, temp_dir)
    risk_return_chart = generate_risk_return_chart(perf_df, temp_dir)
    
    # Nom du fichier PDF avec date et heure
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_file = os.path.join(output_dir, f"brvm_report_{timestamp}.pdf")
    
    logger.info(f"Génération du rapport PDF: {pdf_file}...")
    
    # Créer le PDF
    pdf = BRVMPDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # Introduction
    pdf.chapter_title("Présentation du rapport")
    pdf.chapter_body(
        "Ce rapport présente une analyse détaillée des performances des valeurs cotées à la "
        "Bourse Régionale des Valeurs Mobilières (BRVM). L'analyse couvre les performances "
        "historiques et les indicateurs de risque/rendement pour chaque valeur et par secteur."
    )
    
    # Évolution de l'indice BRVM-Composite
    if brvm_evolution_chart:
        pdf.add_page()
        pdf.chapter_title("Évolution de l'indice BRVM-Composite")
        pdf.chapter_body(
            "Le graphique ci-dessous montre l'évolution de l'indice BRVM-Composite sur la période étudiée. "
            "Cet indice est représentatif de la performance globale du marché."
        )
        pdf.add_image(brvm_evolution_chart, w=180, 
                      caption="Évolution de l'indice BRVM-Composite")
    
    # Performances globales
    pdf.add_page()
    pdf.chapter_title("Performances des valeurs")
    pdf.chapter_body(
        "Le graphique ci-dessous présente les performances totales des 15 meilleures valeurs depuis "
        "le début de leur cotation. La performance est exprimée en pourcentage du prix initial."
    )
    pdf.add_image(performance_chart, w=180, 
                 caption="Performance totale des 15 meilleures valeurs (%)")
    
    # Analyse sectorielle
    pdf.add_page()
    pdf.chapter_title("Analyse par secteur")
    pdf.chapter_body(
        "Cette section présente une analyse des performances moyennes par secteur. "
        "Les secteurs sont classés par ordre de performance annualisée décroissante."
    )
    pdf.add_image(sector_chart, w=180, 
                 caption="Performance annualisée moyenne par secteur (%)")
    
    # Top 10 des meilleures performances annualisées
    pdf.add_page()
    pdf.chapter_title("Top 10 des meilleures performances annualisées")
    
    # Préparer les données pour le tableau
    top_10 = perf_df.sort_values('annual_return', ascending=False).head(10)
    
    # Obtenir classification sectorielle
    symbol_to_sector = get_sector_classification()
    top_10['Secteur'] = top_10.index.map(
        lambda x: symbol_to_sector.get(x, 'Indice' if x.startswith('BRVM') else 'Autres')
    )
    
    # Sélectionner et formater les colonnes pour le tableau
    table_data = []
    for symbol, row in top_10.iterrows():
        table_data.append([
            symbol,
            row['Secteur'],
            f"{row['annual_return']:.2f}%",
            f"{row['volatility']:.2f}%",
            f"{row['sharpe_ratio']:.2f}",
            f"{row['duration_years']:.1f} ans"
        ])
    
    # Ajouter le tableau
    pdf.add_table(
        ['Symbole', 'Secteur', 'Rend. Ann.', 'Volatilité', 'Sharpe', 'Durée'],
        table_data
    )
    
    # Analyse risque/rendement
    pdf.add_page()
    pdf.chapter_title("Analyse Risque/Rendement")
    pdf.chapter_body(
        "Le graphique ci-dessous présente le rapport entre le risque (volatilité) et le rendement "
        "annualisé pour chaque valeur. La taille des cercles représente la performance totale, "
        "et la couleur indique le ratio de Sharpe (rendement ajusté au risque).\n\n"
        "Les valeurs situées en haut à gauche offrent le meilleur rapport risque/rendement. "
        "Les 10 valeurs avec les meilleurs ratios de Sharpe sont identifiées sur le graphique."
    )
    pdf.add_image(risk_return_chart, w=180, 
                 caption="Risque vs Rendement des valeurs de la BRVM")
    
    # Conclusion
    pdf.add_page()
    pdf.chapter_title("Conclusion")
    pdf.chapter_body(
        "Cette analyse des performances historiques des valeurs cotées à la BRVM nous a permis "
        "de dégager plusieurs observations importantes :\n\n"
        "1. Les valeurs les plus performantes en termes de rendement annualisé appartiennent "
        "principalement aux secteurs [à compléter selon les résultats].\n\n"
        "2. Les valeurs offrant le meilleur rapport risque/rendement (ratio de Sharpe élevé) "
        "sont [à compléter selon les résultats].\n\n"
        "3. L'indice BRVM-Composite montre une tendance globale [à compléter selon les résultats].\n\n"
        "Pour les investisseurs intéressés par le marché de la BRVM, ces résultats suggèrent "
        "qu'il pourrait être avantageux de [à compléter selon les recommandations].\n\n"
        "Cette analyse devra être complétée par une mise à jour régulière des données et une prise "
        "en compte des facteurs macroéconomiques affectant les marchés financiers d'Afrique de l'Ouest."
    )
    
    # Sauvegarder le PDF
    pdf.output(pdf_file)
    
    logger.info(f"Rapport PDF généré avec succès: {pdf_file}")
    
    # Nettoyer les fichiers temporaires
    for file in os.listdir(temp_dir):
        os.remove(os.path.join(temp_dir, file))
    os.rmdir(temp_dir)
    
    return pdf_file

def main():
    """Fonction principale."""
    logger.info("Démarrage de la génération du rapport PDF...")
    
    # Charger les données
    data_frames = load_data()
    
    if not data_frames:
        logger.error("Aucune donnée à analyser. Arrêt du processus.")
        return
    
    # Générer le rapport PDF
    pdf_file = generate_pdf_report(data_frames)
    
    logger.info(f"Génération du rapport PDF terminée avec succès. Fichier créé : {pdf_file}")

if __name__ == "__main__":
    main()
