# Analyse des performances de la BRVM

Ce projet permet de collecter et d'analyser les données historiques des valeurs mobilières cotées à la Bourse Régionale des Valeurs Mobilières (BRVM) et des indices associés.

## Objectifs

- Scraper les données historiques des cours depuis les sites de la BRVM et de Sika Finance
- Analyser les performances de chaque valeur depuis le début de sa cotation
- Visualiser l'évolution des indices et des valeurs individuelles
- Comparer les performances par secteur
- Identifier les corrélations entre les différentes valeurs
- Exporter les données et analyses au format Excel
- Générer des rapports PDF
- Créer des tableaux de bord HTML interactifs

## Structure du projet

```
brvm-market-analysis/
├── data/                 # Dossier contenant les données collectées (créé automatiquement)
├── exports/              # Dossier contenant les exports Excel
├── notebooks/
│   └── analyse_performances.ipynb  # Notebook d'analyse des performances
├── reports/              # Dossier contenant les rapports PDF générés
├── dashboard/            # Dossier contenant les tableaux de bord HTML
├── scraper/
│   └── brvm_scraper.py   # Script de scraping des données
├── scripts/
│   ├── export_excel.py         # Script d'export Excel
│   ├── generate_pdf_report.py  # Script de génération de rapport PDF
│   └── create_dashboard.py     # Script de création de tableau de bord HTML
├── README.md             # Ce fichier
├── requirements.txt      # Liste des dépendances Python
└── run_analysis.py       # Script principal d'analyse
```

## Prérequis

- Python 3.6 ou plus récent
- Bibliothèques requises listées dans `requirements.txt`

Vous pouvez installer toutes les dépendances nécessaires avec la commande suivante :

```bash
pip install -r requirements.txt
```

## Utilisation

### 1. Collecte des données

Pour scraper les données historiques des valeurs de la BRVM :

```bash
cd scraper
python brvm_scraper.py
```

Ce script va :
- Récupérer la liste des valeurs cotées à la BRVM
- Collecter les données historiques pour chaque valeur et pour les indices
- Sauvegarder les données au format CSV dans le dossier `data/`

### 2. Analyse des performances

Plusieurs options s'offrent à vous pour analyser les données :

#### 2.1 Notebook Jupyter

Pour une analyse interactive avec des visualisations :

```bash
cd notebooks
jupyter notebook analyse_performances.ipynb
```

#### 2.2 Exporter les données et analyses au format Excel

Pour générer un fichier Excel avec toutes les données et analyses :

```bash
cd scripts
python export_excel.py
```

Le fichier Excel sera créé dans le dossier `exports/` avec les feuilles suivantes :
- Un résumé des performances de toutes les valeurs
- Une feuille pour chaque valeur avec ses données historiques
- Une analyse sectorielle

#### 2.3 Générer un rapport PDF

Pour créer un rapport PDF complet avec graphiques et analyses :

```bash
cd scripts
python generate_pdf_report.py
```

Le rapport PDF sera créé dans le dossier `reports/` et contiendra :
- L'évolution de l'indice BRVM-Composite
- Les performances des meilleures valeurs
- L'analyse par secteur
- L'analyse risque/rendement
- Des tableaux récapitulatifs

#### 2.4 Créer un tableau de bord HTML interactif

Pour générer un tableau de bord HTML interactif avec Plotly :

```bash
cd scripts
python create_dashboard.py
```

Le tableau de bord HTML sera créé dans le dossier `dashboard/` et s'ouvrira automatiquement dans votre navigateur web par défaut.

### 3. Utilisation du script principal

Vous pouvez également lancer l'ensemble du traitement d'analyse avec le script principal :

```bash
python run_analysis.py
```

Ce script exécutera les étapes suivantes :
1. Lancement du scraping des données (si nécessaire)
2. Vérification des données collectées
3. Lancement du notebook d'analyse

## Indicateurs de performance calculés

- **Rendement total** : Performance totale depuis le début de la cotation
- **Rendement annualisé** : Performance annuelle moyenne
- **Volatilité** : Écart-type des rendements (mesure du risque)
- **Ratio de Sharpe** : Ratio rendement/risque (performance ajustée au risque)
- **Drawdown maximum** : Perte maximale subie depuis un pic

## Sources de données

- [Site officiel de la BRVM](https://www.brvm.org/)
- [Sika Finance](https://www.sikafinance.com/)

## Limitations

- Le scraping dépend de la structure des sites web, qui peut changer
- Certaines valeurs peuvent avoir des données manquantes ou incomplètes
- Les ajustements pour dividendes et opérations sur titres peuvent ne pas être pris en compte

## Contributeurs

- [Kyac99](https://github.com/Kyac99)

## Licence

Ce projet est sous licence MIT - voir le fichier [LICENSE](LICENSE) pour plus de détails.
