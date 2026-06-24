# Power BI Data Extraction Pipeline

A solution to overcome Power BI's export limitations (~150k rows) by implementing a local ETL pipeline with a user-friendly extraction interface.

## Problem

Business Intelligence tools like Power BI impose strict limits on data export volumes. When analysts need millions of rows for statistics or machine learning, they hit a wall:

- **Export cap**: Power BI limits exports to ~30k-150k rows
- **Cloud dependency**: Each extraction goes through the cloud — slow and costly
- **No scalability**: N users making individual extractions = N times the load
- **Non-technical users**: Need a simple, one-click solution

## Solution

A **centralized ETL pipeline** extracts data once (scheduled nightly) into a local shared folder using **Apache Parquet** format. Users access the data through a desktop app or a web interface — no cloud, no re-extraction.

```
Database
    ↓  (1 scheduled extraction per night)
Python ETL Pipeline
    ↓
Parquet file on local shared folder (84 MB for 5M rows)
    ↓
┌─────────────────┬──────────────────┬────────────────┐
│  Power BI       │  Extraction App  │  Python / R    │
│  (dashboards)   │  (filtered CSV)  │  (ML models)   │
└─────────────────┴──────────────────┴────────────────┘
```

## Why Parquet?

Benchmark results on the same dataset:

| Metric | 1M rows | 5M rows | 10M rows |
|---|---|---|---|
| **Write speed** (vs CSV) | 8x faster | 5x faster | 6x faster |
| **File size** (vs CSV) | 3.4x smaller | 3.6x smaller | 3.6x smaller |
| **Read speed** (vs CSV) | 5x faster | 7x faster | 18x faster |

Read performance **scales better** with larger volumes — exactly what's needed for 2M+ row datasets.

## Features

### ETL Pipeline (`pipeline_extraction.py`)
- Automated nightly extraction with timestamped archives
- Parquet output with Snappy compression
- Rolling archive (7 days retention)
- Execution logs for traceability

### Desktop App (`Extraction Ooredoo.bat`)
- Filter by region, category, status, date range
- Real-time preview (row count, totals, averages)
- Export formats: **CSV** (fast) or **Excel** (paginated if >1M rows)
- **Full extraction**: paginated CSV files for the complete dataset
- File dialog to choose save location

### Web Interface (`Demarrer Serveur.bat`)
- Same features as the desktop app, accessible via browser
- Integrates with Power BI through a URL button
- Runs locally on `localhost:5050` — no cloud

## Project Structure

```
├── Extraction Ooredoo.bat        # Launch desktop extraction app
├── Demarrer Serveur.bat          # Start local web server
├── ooredoo.pbix                  # Power BI report template
│
├── scripts/
│   ├── app_extraction.py         # Desktop app (CustomTkinter)
│   ├── api_extraction.py         # Web server (Flask)
│   ├── pipeline_extraction.py    # ETL pipeline
│   └── generate_dataset.py       # Benchmark script
│
├── shared_folder/                # Simulated shared network folder
│   ├── dataset_latest.parquet    # Current dataset (5M rows)
│   ├── archives/                 # Timestamped backups
│   └── excel_export/             # Paginated CSV files
│
├── logs/                         # Pipeline execution logs
└── docs/                         # Full documentation
```

## Quick Start

### Prerequisites
```
pip install pandas numpy pyarrow openpyxl flask customtkinter tkcalendar
```

### 1. Generate the dataset
```
python scripts/pipeline_extraction.py
```

### 2. Use the desktop app
```
double-click "Extraction Ooredoo.bat"
```

### 3. Or use the web interface
```
double-click "Demarrer Serveur.bat"
open http://localhost:5050
```

### 4. Connect Power BI
Open `ooredoo.pbix` — it reads directly from `shared_folder/dataset_latest.parquet`.

## Export Options

| Format | Max volume | Speed (5M rows) | Use case |
|---|---|---|---|
| **CSV** | Unlimited | ~10 seconds | Recommended — universal compatibility |
| **Excel** | Auto-paginated (1M/sheet) | Several minutes | For .xlsx preference |
| **Full extraction** | 5M+ (paginated CSV) | ~10 seconds | Complete dataset without filters |

## Tech Stack

- **Python** — pandas, NumPy, PyArrow
- **Apache Parquet** — columnar storage with Snappy compression
- **Flask** — lightweight local web server
- **CustomTkinter** — modern desktop UI
- **Power BI Desktop** — dashboards and visualization

## License

This project was developed as an internship prototype for a Tableau-to-Power BI migration.
