# Tableau de bord des valeurs de la BRVM pour GitHub Pages

Ce dossier contient les fichiers HTML du tableau de bord interactif des valeurs mobilières cotées à la Bourse Régionale des Valeurs Mobilières (BRVM).

## Contenu

- **index.html** : Tableau de bord actuel qui sera affiché sur GitHub Pages
- Des copies datées du tableau de bord peuvent également être ajoutées pour conserver un historique des analyses

## Mise à jour des données

Les données du tableau de bord sont générées et mises à jour par le script `scripts/update_dashboard.py`. Ce script :

1. Récupère les données actuelles des valeurs cotées à la BRVM depuis Sika Finance
2. Collecte les capitalisations boursières, PER et dividendes
3. Calcule les rendements des dividendes
4. Classe les valeurs par capitalisation boursière
5. Génère un tableau de bord interactif avec Plotly
6. Met à jour le fichier `index.html` dans ce dossier

## Activation de GitHub Pages

Pour activer GitHub Pages et publier ce tableau de bord en ligne :

1. Accédez aux paramètres du dépôt GitHub (`Settings`)
2. Faites défiler jusqu'à la section "GitHub Pages"
3. Dans "Source", sélectionnez la branche "main" et le dossier "/docs"
4. Cliquez sur "Save"

Une fois activé, le tableau de bord sera accessible à l'adresse : `https://Kyac99.github.io/brvm-market-analysis/`

## Automatisation des mises à jour

Pour automatiser les mises à jour du tableau de bord, vous pouvez :

1. Configurer une GitHub Action qui exécute le script `update_dashboard.py` périodiquement
2. Utiliser un service d'intégration continue comme GitHub Actions ou Travis CI
3. Configurer un cron job sur votre propre serveur qui met à jour le dépôt GitHub
