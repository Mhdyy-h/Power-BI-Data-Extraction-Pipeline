# Guide de Mise en Production
## Solution d'Extraction Dynamique — Power BI

---

## 1. Vue d'Ensemble

### 1.1 Objectif
Permettre aux utilisateurs Power BI d'extraire des volumes massifs de données (2M+ lignes) via un simple bouton, sans passer par le cloud, avec une interface dynamique qui s'adapte automatiquement à chaque dashboard.

### 1.2 Architecture de Production

```
┌─────────────────────────────────────────────────────────────┐
│                    SERVEUR INTERNE                          │
│                                                             │
│   Base de données Ooredoo                                   │
│         ↓                                                   │
│   Pipeline ETL (tâche planifiée chaque nuit)                │
│         ↓                                                   │
│   Dossier partagé réseau (\\serveur\partage\)               │
│     ├── dashboard_ventes.parquet                            │
│     ├── dashboard_clients.parquet                           │
│     ├── dashboard_reseau.parquet                            │
│     └── dashboard_facturation.parquet                       │
│         ↓                                                   │
│   Serveur Flask (http://serveur-data:5050)                  │
│     → Lit les Parquet dynamiquement                         │
│     → Génère les filtres automatiquement                    │
│     → Exporte en CSV / Excel / ZIP                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
           ↑
    ┌──────┴──────────────────────────────────────┐
    │           POSTES UTILISATEURS               │
    │                                             │
    │   Power BI Desktop ou Service (navigateur)  │
    │     → Visualisation des dashboards          │
    │     → Bouton "Extraire"                     │
    │       → Ouvre la page d'extraction          │
    │       → Filtres dynamiques                  │
    │       → Téléchargement CSV/Excel            │
    │                                             │
    └─────────────────────────────────────────────┘
```

---

## 2. Prérequis Serveur

### 2.1 Matériel
- Serveur Windows (physique ou VM) accessible sur le réseau interne
- RAM : 8 Go minimum (16 Go recommandé pour les gros datasets)
- Stockage : selon le volume de données (prévoir ~100 MB par million de lignes en Parquet)

### 2.2 Logiciels
- Python 3.10 ou supérieur
- Packages Python : pandas, numpy, pyarrow, openpyxl, flask

### 2.3 Installation
```bash
# 1. Installer Python depuis https://python.org (cocher "Add to PATH")

# 2. Installer les dépendances
pip install pandas numpy pyarrow openpyxl flask

# 3. Copier le dossier du projet sur le serveur
#    Seuls ces fichiers sont nécessaires :
#    - scripts/api_extraction.py
#    - scripts/convert_to_parquet.py
#    - Demarrer Serveur.bat
```

---

## 3. Configuration du Pipeline de Données

### 3.1 Connexion à la Base de Données

Créer un script `pipeline_production.py` qui se connecte à la base de données Ooredoo et exporte en Parquet :

```python
"""
Pipeline de production — extraction depuis la base de données.
À exécuter chaque nuit via le Planificateur de tâches Windows.
"""

import pandas as pd
import sqlalchemy
import os
from datetime import datetime

# Configuration de connexion (adapter selon la base Ooredoo)
# Oracle :
# ENGINE = "oracle+cx_oracle://user:password@host:1521/service"
# SQL Server :
# ENGINE = "mssql+pyodbc://user:password@host/database?driver=ODBC+Driver+17+for+SQL+Server"
# MySQL :
# ENGINE = "mysql+pymysql://user:password@host:3306/database"

ENGINE = "oracle+cx_oracle://user:password@serveur-db:1521/ooredoo"

SHARED_DIR = r"\\serveur\partage\datasets"
os.makedirs(SHARED_DIR, exist_ok=True)


def extract_dashboard(query, output_name):
    """Extrait les données d'une requête SQL et les sauvegarde en Parquet."""
    print(f"[{datetime.now():%H:%M:%S}] Extraction : {output_name}")
    engine = sqlalchemy.create_engine(ENGINE)
    df = pd.read_sql(query, engine)
    output_path = os.path.join(SHARED_DIR, f"{output_name}.parquet")
    df.to_parquet(output_path, index=False, engine="pyarrow", compression="snappy")
    print(f"  → {len(df):,} lignes, {os.path.getsize(output_path)/1e6:.1f} MB")


# === DASHBOARDS À EXTRAIRE ===
# Ajouter une ligne par dashboard

extract_dashboard(
    "SELECT * FROM vw_dashboard_ventes WHERE date >= ADD_MONTHS(SYSDATE, -24)",
    "dashboard_ventes"
)

extract_dashboard(
    "SELECT * FROM vw_dashboard_clients",
    "dashboard_clients"
)

extract_dashboard(
    "SELECT * FROM vw_dashboard_reseau WHERE date_mesure >= ADD_MONTHS(SYSDATE, -12)",
    "dashboard_reseau"
)

extract_dashboard(
    "SELECT * FROM vw_dashboard_facturation WHERE periode >= ADD_MONTHS(SYSDATE, -24)",
    "dashboard_facturation"
)

print(f"\n[{datetime.now():%H:%M:%S}] Pipeline terminé.")
```

### 3.2 Planification de l'Extraction

1. Ouvrir le **Planificateur de tâches Windows** sur le serveur
2. **Créer une tâche** :
   - Nom : `Pipeline ETL Ooredoo`
   - Déclencheur : chaque jour à **02:00** (hors heures de travail)
   - Action : Démarrer un programme
     - Programme : `python`
     - Arguments : `C:\chemin\vers\pipeline_production.py`
3. Paramètres :
   - Exécuter que l'utilisateur soit connecté ou non
   - Exécuter avec les privilèges les plus élevés

### 3.3 Ajouter un Nouveau Dashboard

Pour ajouter un nouveau dashboard, il suffit d'ajouter une ligne dans le pipeline :

```python
extract_dashboard(
    "SELECT * FROM nouvelle_vue",
    "dashboard_nouveau"
)
```

Le serveur Flask détectera automatiquement le nouveau fichier Parquet au prochain démarrage.

---

## 4. Configuration du Serveur Flask

### 4.1 Lancement comme Service Windows

Pour que le serveur tourne en permanence (pas besoin de .bat) :

**Option A — NSSM (recommandé) :**
```bash
# 1. Télécharger NSSM depuis https://nssm.cc
# 2. Installer le service :
nssm install OoredooExtraction python C:\chemin\vers\scripts\api_extraction.py
nssm set OoredooExtraction AppDirectory C:\chemin\vers\projet
nssm start OoredooExtraction
```

**Option B — Script au démarrage :**
1. Créer un raccourci de `Demarrer Serveur.bat`
2. Placer dans `C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Startup`

### 4.2 Configuration Réseau

Le serveur Flask écoute par défaut sur `localhost` (accessible uniquement localement). Pour le rendre accessible sur le réseau interne, modifier dans `api_extraction.py` :

```python
# Avant (POC) :
app.run(port=5050, debug=False)

# Après (production) :
app.run(host="0.0.0.0", port=5050, debug=False)
```

Cela rend le serveur accessible à tous les postes du réseau via `http://nom-du-serveur:5050`.

### 4.3 Pare-feu

Ouvrir le port 5050 dans le pare-feu Windows du serveur :
```bash
netsh advfirewall firewall add rule name="Ooredoo Extraction" dir=in action=allow protocol=tcp localport=5050
```

---

## 5. Configuration Power BI

### 5.1 Créer un Dashboard

1. Ouvrir **Power BI Desktop**
2. **Obtenir les données** → **Parquet**
3. Chemin : `\\serveur\partage\datasets\dashboard_ventes.parquet`
4. Créer les visuels souhaités
5. Sauvegarder en `.pbix`

### 5.2 Ajouter le Bouton d'Extraction

1. **Insérer** → **Bouton** → **Vide**
2. Texte : `Extraire les données`
3. **Action** → Activer → Type : **URL web**
4. URL : `http://nom-du-serveur:5050/dataset/dashboard_ventes.parquet`
5. Sauvegarder

### 5.3 Convention de Nommage des URLs

```
http://nom-du-serveur:5050/dataset/<nom_du_fichier_parquet>
```

| Dashboard | Fichier Parquet | URL du Bouton |
|---|---|---|
| Ventes | dashboard_ventes.parquet | http://serveur:5050/dataset/dashboard_ventes.parquet |
| Clients | dashboard_clients.parquet | http://serveur:5050/dataset/dashboard_clients.parquet |
| Réseau | dashboard_reseau.parquet | http://serveur:5050/dataset/dashboard_reseau.parquet |
| Facturation | dashboard_facturation.parquet | http://serveur:5050/dataset/dashboard_facturation.parquet |

### 5.4 Publier sur Power BI Service

1. Dans Power BI Desktop : **Publier** → choisir **My Workspace** (ou un workspace dédié)
2. Les utilisateurs accèdent au rapport via le navigateur
3. Le bouton "Extraire" fonctionne depuis Power BI Service

**Note :** Le serveur Flask doit être accessible depuis les postes qui utilisent Power BI Service.

---

## 6. Guide Utilisateur Final

### 6.1 Consulter un Dashboard
1. Ouvrir Power BI (Desktop ou navigateur)
2. Sélectionner le rapport souhaité
3. Naviguer dans les visuels et filtres Power BI

### 6.2 Extraire des Données
1. Cliquer le bouton **"Extraire les données"** dans le rapport
2. La page d'extraction s'ouvre dans le navigateur
3. Sélectionner les filtres souhaités (les filtres correspondent aux colonnes du dataset)
4. Choisir le format :
   - **CSV** — rapide, compatible avec Excel (double-clic pour ouvrir)
   - **Excel** — format .xlsx, paginé automatiquement si > 1M lignes
   - **Extraction totale** — toutes les données en fichiers CSV paginés (ZIP)
5. Le fichier se télécharge — choisir où le sauvegarder

### 6.3 Importer un CSV dans Excel
1. Ouvrir Excel → fichier vide
2. **Données** → **À partir d'un fichier texte/CSV**
3. Sélectionner le fichier → **Charger**

---

## 7. Fonctionnement du Dynamisme

### 7.1 Comment les Filtres se Génèrent Automatiquement

Le serveur Flask analyse chaque fichier Parquet et classe les colonnes :

| Type de colonne détecté | Filtre généré | Exemple |
|---|---|---|
| Texte avec < 50 valeurs uniques | Liste multi-sélection | region, statut, produit |
| Date | Sélecteur de période (du / au) | date, date_inscription |
| Nombre | Affiché dans l'aperçu (somme) | montant, quantite, revenus |
| Texte avec > 50 valeurs uniques | Pas de filtre (trop de valeurs) | id_client, commentaire |

### 7.2 Ajouter un Nouveau Dashboard (procédure complète)

**Temps estimé : 10 minutes. Aucune modification de code.**

1. **Créer la vue SQL** dans la base de données :
   ```sql
   CREATE VIEW vw_dashboard_nouveau AS
   SELECT col1, col2, col3, date_col, montant
   FROM table_source
   WHERE conditions;
   ```

2. **Ajouter au pipeline** (`pipeline_production.py`) :
   ```python
   extract_dashboard("SELECT * FROM vw_dashboard_nouveau", "dashboard_nouveau")
   ```

3. **Créer le rapport Power BI** :
   - Obtenir les données → Parquet → `\\serveur\partage\datasets\dashboard_nouveau.parquet`
   - Créer les visuels
   - Ajouter le bouton → URL : `http://serveur:5050/dataset/dashboard_nouveau.parquet`
   - Publier

4. **C'est tout.** Le serveur Flask détecte le nouveau Parquet et génère les filtres automatiquement.

---

## 8. Maintenance

### 8.1 Surveillance
- Vérifier que le service Flask tourne : accéder à `http://serveur:5050` depuis un navigateur
- Vérifier les logs du pipeline ETL dans le Planificateur de tâches Windows
- Vérifier que les fichiers Parquet sont mis à jour chaque nuit (date de modification)

### 8.2 Problèmes Courants

| Problème | Cause | Solution |
|---|---|---|
| Bouton "Extraire" ne répond pas | Serveur Flask arrêté | Relancer le service ou le .bat |
| Page affiche "fichier non trouvé" | Parquet manquant ou mauvais nom dans l'URL | Vérifier le nom du fichier dans shared_folder |
| Données pas à jour | Pipeline ETL n'a pas tourné | Vérifier le Planificateur de tâches |
| Export Excel très lent | Volume > 1M lignes | Recommander le format CSV à l'utilisateur |
| Filtres manquants pour une colonne | Colonne a > 50 valeurs uniques | Ajuster MAX_FILTER_UNIQUE dans api_extraction.py |

### 8.3 Mises à Jour
- Le code `api_extraction.py` ne nécessite aucune mise à jour lors de l'ajout de nouveaux dashboards
- Pour modifier le seuil de filtres : changer `MAX_FILTER_UNIQUE` en haut du fichier
- Pour changer le port : modifier `app.run(port=5050)` à la fin du fichier

---

## 9. Sécurité

### 9.1 Réseau
- Le serveur Flask tourne sur le **réseau interne uniquement**
- Aucune donnée ne transite par le cloud ou Internet
- Le pare-feu doit autoriser uniquement le réseau interne sur le port 5050

### 9.2 Accès aux Données
- Les permissions du dossier partagé réseau contrôlent qui peut voir les fichiers Parquet
- Le serveur Flask ne gère pas l'authentification (réseau interne de confiance)
- Pour ajouter une authentification : possibilité d'intégrer Flask-Login

### 9.3 Recommandations
- Ne pas exposer le port 5050 sur Internet
- Utiliser les groupes Active Directory pour contrôler l'accès au dossier partagé
- Journaliser les extractions (ajouter un log dans api_extraction.py si nécessaire)

---

## 10. Résumé

| Aspect | Détail |
|---|---|
| **Code à maintenir** | 1 seul fichier : `api_extraction.py` |
| **Ajout d'un dashboard** | 10 minutes, zéro code à modifier dans le serveur |
| **Formats d'export** | CSV, Excel (paginé), ZIP (extraction totale) |
| **Volume supporté** | Testé jusqu'à 10M lignes |
| **Dynamisme** | Filtres générés automatiquement selon les colonnes |
| **Dépendances cloud** | Aucune — tout est local |
| **Coût** | Zéro — outils open source uniquement |
