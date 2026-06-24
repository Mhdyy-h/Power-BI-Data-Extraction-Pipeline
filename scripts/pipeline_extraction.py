
import pandas as pd
import numpy as np
import os
import shutil
import time
import logging
from datetime import datetime

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHARED_DIR = os.path.join(BASE_DIR, "shared_folder")
ARCHIVE_DIR = os.path.join(SHARED_DIR, "archives")
LOG_DIR = os.path.join(BASE_DIR, "logs")
LATEST_FILE = os.path.join(SHARED_DIR, "dataset_latest.parquet")
N_ROWS = 5_000_000
MAX_ARCHIVES = 7  # garder 7 jours d'historique

os.makedirs(ARCHIVE_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# --- Logging ---
log_file = os.path.join(LOG_DIR, f"extraction_{datetime.now():%Y%m%d_%H%M%S}.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(log_file, encoding="utf-8"), logging.StreamHandler()],
)
log = logging.getLogger(__name__)


def simulate_db_extraction(n_rows: int) -> pd.DataFrame:
    """Simule une requête SQL vers la base de données."""
    rng = np.random.default_rng()
    regions = ["Tunis", "Sfax", "Sousse", "Nabeul", "Bizerte", "Gabes", "Kairouan"]
    categories = ["Produit A", "Produit B", "Produit C", "Produit D", "Produit E"]
    statuts = ["Payé", "En attente", "Annulé"]

    return pd.DataFrame({
        "id_transaction": np.arange(1, n_rows + 1),
        "id_client": rng.integers(1, 200_000, size=n_rows),
        "date": pd.to_datetime("2024-01-01") + pd.to_timedelta(
            rng.integers(0, 730, size=n_rows), unit="D"
        ),
        "region": rng.choice(regions, size=n_rows),
        "categorie": rng.choice(categories, size=n_rows),
        "montant": np.round(rng.uniform(5, 2000, size=n_rows), 2),
        "quantite": rng.integers(1, 20, size=n_rows),
        "statut": rng.choice(statuts, size=n_rows, p=[0.8, 0.15, 0.05]),
    })


def cleanup_archives(max_keep: int):
    """Supprime les archives les plus anciennes au-delà de max_keep."""
    archives = sorted(
        [f for f in os.listdir(ARCHIVE_DIR) if f.endswith(".parquet")],
        reverse=True,
    )
    for old in archives[max_keep:]:
        os.remove(os.path.join(ARCHIVE_DIR, old))
        log.info(f"Archive supprimée : {old}")


def run_pipeline():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log.info(f"=== Début extraction — {timestamp} ===")

    # 1. Extraction
    t0 = time.time()
    df = simulate_db_extraction(N_ROWS)
    log.info(f"Extraction : {len(df):,} lignes en {time.time()-t0:.2f}s")

    # 2. Export horodaté (archive)
    archive_path = os.path.join(ARCHIVE_DIR, f"dataset_{timestamp}.parquet")
    t1 = time.time()
    df.to_parquet(archive_path, index=False, engine="pyarrow", compression="snappy")
    size_mb = os.path.getsize(archive_path) / 1e6
    log.info(f"Archive écrite : {archive_path} ({size_mb:.1f} MB) en {time.time()-t1:.2f}s")

    # 3. Copier comme "latest" (c'est ce fichier que Power BI lit)
    shutil.copy2(archive_path, LATEST_FILE)
    log.info(f"Fichier latest mis à jour : {LATEST_FILE}")

    # 4. Nettoyage
    cleanup_archives(MAX_ARCHIVES)

    log.info(f"=== Pipeline terminé en {time.time()-t0:.2f}s ===")


if __name__ == "__main__":
    run_pipeline()
