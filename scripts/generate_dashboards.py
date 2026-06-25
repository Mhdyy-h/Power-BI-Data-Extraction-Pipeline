"""
Genere 3 datasets massifs simulant differents departements.
Chaque dataset a des colonnes differentes pour tester le dynamisme.
"""

import pandas as pd
import numpy as np
import os
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHARED_DIR = os.path.join(BASE_DIR, "shared_folder")
os.makedirs(SHARED_DIR, exist_ok=True)

rng = np.random.default_rng(42)


def generate_ventes(n=2_000_000):
    print(f"[Ventes] Generation de {n:,} lignes...")
    t = time.time()
    df = pd.DataFrame({
        "id_transaction": np.arange(1, n + 1),
        "date": pd.to_datetime("2024-01-01") + pd.to_timedelta(rng.integers(0, 730, size=n), unit="D"),
        "region": rng.choice(["Tunis", "Sfax", "Sousse", "Nabeul", "Bizerte", "Gabes", "Kairouan"], size=n),
        "canal": rng.choice(["Boutique", "En ligne", "Revendeur", "Centre appel"], size=n),
        "produit": rng.choice(["Forfait Voix", "Forfait Data", "Forfait Mix", "Recharge", "Equipement"], size=n),
        "montant": np.round(rng.uniform(5, 2000, size=n), 2),
        "quantite": rng.integers(1, 20, size=n),
        "statut_paiement": rng.choice(["Paye", "En attente", "Annule"], size=n, p=[0.8, 0.15, 0.05]),
    })
    path = os.path.join(SHARED_DIR, "dashboard_ventes.parquet")
    df.to_parquet(path, index=False, engine="pyarrow", compression="snappy")
    print(f"  -> {os.path.getsize(path)/1e6:.1f} MB en {time.time()-t:.1f}s")


def generate_clients(n=1_500_000):
    print(f"[Clients] Generation de {n:,} lignes...")
    t = time.time()
    df = pd.DataFrame({
        "id_client": np.arange(1, n + 1),
        "date_inscription": pd.to_datetime("2018-01-01") + pd.to_timedelta(rng.integers(0, 2500, size=n), unit="D"),
        "segment": rng.choice(["Particulier", "Professionnel", "Entreprise", "VIP"], size=n, p=[0.6, 0.2, 0.15, 0.05]),
        "ville": rng.choice(["Tunis", "Sfax", "Sousse", "Nabeul", "Bizerte", "Gabes", "Kairouan", "Monastir", "Ariana", "Ben Arous"], size=n),
        "offre": rng.choice(["Haya", "Haya+", "Max", "Max Pro", "Business"], size=n),
        "statut_compte": rng.choice(["Actif", "Suspendu", "Resilie"], size=n, p=[0.75, 0.15, 0.10]),
        "revenus_mensuel": np.round(rng.uniform(10, 500, size=n), 2),
        "anciennete_mois": rng.integers(1, 84, size=n),
    })
    path = os.path.join(SHARED_DIR, "dashboard_clients.parquet")
    df.to_parquet(path, index=False, engine="pyarrow", compression="snappy")
    print(f"  -> {os.path.getsize(path)/1e6:.1f} MB en {time.time()-t:.1f}s")


def generate_reseau(n=3_000_000):
    print(f"[Reseau] Generation de {n:,} lignes...")
    t = time.time()
    df = pd.DataFrame({
        "id_mesure": np.arange(1, n + 1),
        "date_mesure": pd.to_datetime("2024-01-01") + pd.to_timedelta(rng.integers(0, 730, size=n), unit="D"),
        "gouvernorat": rng.choice(["Tunis", "Sfax", "Sousse", "Nabeul", "Bizerte", "Gabes", "Kairouan", "Monastir", "Ariana", "Ben Arous", "Manouba", "Zaghouan"], size=n),
        "technologie": rng.choice(["2G", "3G", "4G", "5G"], size=n, p=[0.05, 0.15, 0.55, 0.25]),
        "type_mesure": rng.choice(["Debit", "Latence", "Couverture", "Disponibilite"], size=n),
        "valeur": np.round(rng.uniform(0.5, 150, size=n), 2),
        "qualite": rng.choice(["Excellent", "Bon", "Moyen", "Faible"], size=n, p=[0.35, 0.35, 0.20, 0.10]),
        "antenne_id": rng.integers(1, 5000, size=n),
    })
    path = os.path.join(SHARED_DIR, "dashboard_reseau.parquet")
    df.to_parquet(path, index=False, engine="pyarrow", compression="snappy")
    print(f"  -> {os.path.getsize(path)/1e6:.1f} MB en {time.time()-t:.1f}s")


if __name__ == "__main__":
    print("=" * 50)
    print("Generation des datasets pour 3 dashboards")
    print("=" * 50)
    t0 = time.time()
    generate_ventes()
    generate_clients()
    generate_reseau()
    print(f"\nTotal : {time.time()-t0:.1f}s")
