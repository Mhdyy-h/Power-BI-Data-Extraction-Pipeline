
import pandas as pd
import numpy as np
import time
import os

N_ROWS = 5_000_000

print(f"Génération de {N_ROWS:,} lignes...")
start = time.time()

rng = np.random.default_rng(42)

regions = ["Tunis", "Sfax", "Sousse", "Nabeul", "Bizerte", "Gabes", "Kairouan"]
categories = ["Produit A", "Produit B", "Produit C", "Produit D", "Produit E"]
statuts = ["Payé", "En attente", "Annulé"]

df = pd.DataFrame({
    "id_transaction": np.arange(1, N_ROWS + 1),
    "id_client": rng.integers(1, 200_000, size=N_ROWS),
    "date": pd.to_datetime("2024-01-01") + pd.to_timedelta(
        rng.integers(0, 730, size=N_ROWS), unit="D"
    ),
    "region": rng.choice(regions, size=N_ROWS),
    "categorie": rng.choice(categories, size=N_ROWS),
    "montant": np.round(rng.uniform(5, 2000, size=N_ROWS), 2),
    "quantite": rng.integers(1, 20, size=N_ROWS),
    "statut": rng.choice(statuts, size=N_ROWS, p=[0.8, 0.15, 0.05]),
})

elapsed_gen = time.time() - start
print(f"Génération terminée en {elapsed_gen:.2f} sec.")
print(df.head())
print(f"Taille en mémoire : {df.memory_usage(deep=True).sum() / 1e6:.1f} MB")

# --- Export Parquet ---
output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "shared_folder")
os.makedirs(output_dir, exist_ok=True)

parquet_path = os.path.join(output_dir, "dataset_extraction.parquet")
start_export = time.time()
df.to_parquet(parquet_path, index=False, engine="pyarrow", compression="snappy")
elapsed_parquet = time.time() - start_export
size_parquet = os.path.getsize(parquet_path) / 1e6

# --- Export CSV (comparaison) ---
csv_path = os.path.join(output_dir, "dataset_extraction.csv")
start_csv = time.time()
df.to_csv(csv_path, index=False)
elapsed_csv = time.time() - start_csv
size_csv = os.path.getsize(csv_path) / 1e6

# --- Lecture comparative ---
start_read_pq = time.time()
_ = pd.read_parquet(parquet_path)
read_parquet = time.time() - start_read_pq

start_read_csv = time.time()
_ = pd.read_csv(csv_path)
read_csv = time.time() - start_read_csv

# --- Résultats ---
print(f"\n{'='*60}")
print(f"RÉSULTATS COMPARATIFS — {N_ROWS:,} lignes")
print(f"{'='*60}")
print(f"{'Métrique':<25} {'CSV':>12} {'Parquet':>12} {'Ratio':>10}")
print(f"{'-'*60}")
print(f"{'Temps export (sec)':<25} {elapsed_csv:>12.2f} {elapsed_parquet:>12.2f} {elapsed_csv/elapsed_parquet:>9.1f}x")
print(f"{'Taille disque (MB)':<25} {size_csv:>12.1f} {size_parquet:>12.1f} {size_csv/size_parquet:>9.1f}x")
print(f"{'Temps lecture (sec)':<25} {read_csv:>12.2f} {read_parquet:>12.2f} {read_csv/read_parquet:>9.1f}x")
print(f"{'='*60}")
