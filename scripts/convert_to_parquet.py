"""
Convertit n'importe quel fichier (CSV, XLSX, XLS, TSV, JSON) en Parquet.
Detecte automatiquement le format selon l'extension.

Usage :
  python convert_to_parquet.py fichier.csv
  python convert_to_parquet.py fichier.xlsx
  python convert_to_parquet.py fichier1.csv fichier2.xlsx
  python convert_to_parquet.py            (convertit tous les fichiers dans downloads/)
"""

import pandas as pd
import os
import sys
import time
import glob

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHARED_DIR = os.path.join(BASE_DIR, "shared_folder")
DOWNLOADS_DIR = os.path.join(BASE_DIR, "downloads")
SUPPORTED = {".csv", ".xlsx", ".xls", ".tsv", ".json"}


def convert_file(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    name = os.path.splitext(os.path.basename(filepath))[0]
    output = os.path.join(SHARED_DIR, f"{name}.parquet")

    print(f"\n{'='*50}")
    print(f"Fichier : {os.path.basename(filepath)}")
    print(f"Format  : {ext}")
    t = time.time()

    try:
        if ext == ".csv":
            df = pd.read_csv(filepath, low_memory=False)
        elif ext == ".tsv":
            df = pd.read_csv(filepath, sep="\t", low_memory=False)
        elif ext in (".xlsx", ".xls"):
            df = pd.read_excel(filepath)
        elif ext == ".json":
            df = pd.read_json(filepath)
        else:
            print(f"  [ERREUR] Format non supporte : {ext}")
            return False

        read_time = time.time() - t
        print(f"Lignes  : {len(df):,}")
        print(f"Colonnes: {len(df.columns)} ({', '.join(df.columns[:5])}{'...' if len(df.columns) > 5 else ''})")
        print(f"Lecture : {read_time:.1f}s")

        t2 = time.time()
        os.makedirs(SHARED_DIR, exist_ok=True)
        df.to_parquet(output, index=False, engine="pyarrow", compression="snappy")
        write_time = time.time() - t2

        size_in = os.path.getsize(filepath) / 1e6
        size_out = os.path.getsize(output) / 1e6

        print(f"Export  : {write_time:.1f}s")
        print(f"Taille  : {size_in:.1f} MB -> {size_out:.1f} MB (x{size_in/size_out:.1f} compression)")
        print(f"Sortie  : {output}")
        return True

    except Exception as e:
        print(f"  [ERREUR] {e}")
        return False


if __name__ == "__main__":
    os.makedirs(SHARED_DIR, exist_ok=True)

    if len(sys.argv) > 1:
        files = sys.argv[1:]
    else:
        files = []
        for ext in SUPPORTED:
            files.extend(glob.glob(os.path.join(DOWNLOADS_DIR, f"*{ext}")))

        if not files:
            print(f"Aucun fichier trouve dans {DOWNLOADS_DIR}")
            print(f"Formats supportes : {', '.join(SUPPORTED)}")
            sys.exit(1)

    print(f"Conversion de {len(files)} fichier(s) vers Parquet")
    print(f"Destination : {SHARED_DIR}")

    success = 0
    for f in files:
        if convert_file(f):
            success += 1

    print(f"\n{'='*50}")
    print(f"Termine : {success}/{len(files)} fichier(s) convertis")
    print(f"Fichiers Parquet dans : {SHARED_DIR}")
