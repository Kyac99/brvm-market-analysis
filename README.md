# Analyse des performances de la BRVM

Ce projet permet de collecter et d'analyser les données historiques des valeurs mobilières cotées à la Bourse Régionale des Valeurs Mobilières (BRVM) et des indices associés.

## Tableau de bord en ligne

Le tableau de bord interactif des valeurs de la BRVM est accessible en ligne via GitHub Pages à l'adresse suivante :
[https://Kyac99.github.io/brvm-market-analysis/](https://Kyac99.github.io/brvm-market-analysis/)

Ce tableau de bord présente :
- Le classement des valeurs par capitalisation boursière
- L'évolution des PER et dividendes entre 2020 et 2024
- Les rendements des dividendes
- Des visualisations interactives pour explorer les données

## Objectifs

- Scraper les données historiques des cours depuis les sites de la BRVM et de Sika Finance
- Analyser les performances de chaque valeur depuis le début de sa cotation
- Visualiser l'évolution des indices et des valeurs individuelles
- Comparer les performances par secteur
- Identifier les corrélations entre les différentes valeurs
- Classer les valeurs par capitalisation boursière, PER et rendement du dividende
- Exporter les données et analyses au format Excel
- Générer des rapports PDF
- Créer des tableaux de bord HTML interactifs
- Déployer les analyses sur GitHub Pages

## Structure du projet

```
brvm-market-analysis/
├── data/                 # Dossier contenant les données collectées (créé automatiquement)
├── docs/                 # Dossier pour GitHub Pages
│   ├── index.html       # Tableau de bord déployé sur GitHub Pages
│   └── README.md        # Documentation pour GitHub Pages
├── exports/              # Dossier contenant les exports Excel
├── notebooks/
│   ├── analyse_performances.ipynb  # Notebook d'analyse des performances
│   └── classement_valeurs.ipynb    # Notebook de classement par capitalisation
├── reports/              # Dossier contenant les rapports PDF générés
├── dashboard/            # Dossier contenant les tableaux de bord HTML
├── scraper/
│   └── brvm_scraper.py   # Script de scraping des données
├── scripts/
│   ├── export_excel.py         # Script d'export Excel
│   ├── generate_pdf_report.py  # Script de génération de rapport PDF
│   ├── create_dashboard.py     # Script de création de tableau de bord HTML
│   └── update_dashboard.py     # Script de mise à jour du tableau de bord GitHub Pages
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

#### 2.1 Notebook Jupyter d'analyse des performances

Pour une analyse interactive avec des visualisations :

```bash
cd notebooks
jupyter notebook analyse_performances.ipynb
```

#### 2.2 Notebook Jupyter de classement par capitalisation

Pour classer les valeurs par capitalisation boursière et analyser les PER et dividendes :

```bash
cd notebooks
jupyter notebook classement_valeurs.ipynb
```

#### 2.3 Exporter les données et analyses au format Excel

Pour générer un fichier Excel avec toutes les données et analyses :

```bash
cd scripts
python export_excel.py
```

Le fichier Excel sera créé dans le dossier `exports/`.

#### 2.4 Générer un rapport PDF

Pour créer un rapport PDF complet avec graphiques et analyses :

```bash
cd scripts
python generate_pdf_report.py
```

Le rapport PDF sera créé dans le dossier `reports/`.

#### 2.5 Créer un tableau de bord HTML interactif

Pour générer un tableau de bord HTML interactif avec Plotly :

```bash
cd scripts
python create_dashboard.py
```

Le tableau de bord HTML sera créé dans le dossier `dashboard/`.

#### 2.6 Mettre à jour le tableau de bord GitHub Pages

Pour mettre à jour le tableau de bord en ligne sur GitHub Pages :

```bash
cd scripts
python update_dashboard.py
```

Cette commande va générer et mettre à jour le tableau de bord dans le dossier `docs/`.

### 3. Utilisation du script principal

Vous pouvez également lancer l'ensemble du traitement d'analyse avec le script principal :

```bash
python run_analysis.py
```

## Déploiement sur GitHub Pages

Le projet est configuré pour être déployé automatiquement sur GitHub Pages. Pour activer GitHub Pages :

1. Accédez aux paramètres du dépôt sur GitHub (`Settings`)
2. Faites défiler jusqu'à la section "GitHub Pages"
3. Dans "Source", sélectionnez la branche "main" et le dossier "/docs"
4. Cliquez sur "Save"

Une fois activé, le tableau de bord sera accessible à l'adresse : `https://Kyac99.github.io/brvm-market-analysis/`

Pour mettre à jour les données affichées sur GitHub Pages, exécutez le script `update_dashboard.py`.

## Indicateurs de performance calculés

- **Rendement total** : Performance totale depuis le début de la cotation
- **Rendement annualisé** : Performance annuelle moyenne
- **Volatilité** : Écart-type des rendements (mesure du risque)
- **Ratio de Sharpe** : Ratio rendement/risque (performance ajustée au risque)
- **Drawdown maximum** : Perte maximale subie depuis un pic
- **Rendement du dividende** : Rapport entre dividende et cours actuel

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
