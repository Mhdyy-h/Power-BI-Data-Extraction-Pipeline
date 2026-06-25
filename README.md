# Power BI Dynamic Data Extraction

A dynamic solution to overcome Power BI's export limitations (~150k rows). One single server handles extraction for any dashboard — no per-dashboard development needed.

## Problem

- **Export cap**: Power BI limits exports to ~30k-150k rows
- **Cloud dependency**: Each extraction goes through the cloud — slow and costly
- **Not scalable**: N users × N dashboards = massive redundant extractions
- **Per-dashboard development**: Traditional solutions require building a custom extraction tool for each dashboard

## Solution

A **single dynamic web server** that reads any Parquet file and automatically generates the appropriate filters and export options — no code changes required per dashboard.

```
Power BI Dashboard (Ventes)  ──→  bouton "Extraire"
                                       ↓
Power BI Dashboard (Clients) ──→  bouton "Extraire"     ──→  Same server
                                       ↓                     Same code
Power BI Dashboard (Réseau)  ──→  bouton "Extraire"          Dynamic filters
                                       ↓
                              http://localhost:5050/dataset/<filename>.parquet
                                       ↓
                              Auto-detected filters based on column types
                                       ↓
                              Export: CSV / Excel / ZIP (full extraction)
```

### How it works

1. The server reads the Parquet file specified in the URL
2. It detects column types automatically:
   - **Text columns** (< 50 unique values) → multi-select filter
   - **Date columns** → date range picker
   - **Numeric columns** → displayed as summary stats
3. The user filters and exports — choosing CSV, Excel, or full extraction (ZIP)

### Adding a new dashboard

1. Drop a `.parquet` file in `shared_folder/`
2. In Power BI, add a button → Action → Web URL → `http://localhost:5050/dataset/<filename>.parquet`
3. Done — zero code changes

## Why Parquet?

| Metric | CSV | Parquet | Gain |
|---|---|---|---|
| Write (5M rows) | 10.6s | 2.1s | **5x faster** |
| File size (5M rows) | 299 MB | 84 MB | **3.6x smaller** |
| Read (5M rows) | 5.2s | 0.7s | **7x faster** |
| Read (10M rows) | 9.7s | 0.5s | **18x faster** |

## Project Structure

```
├── Demarrer Serveur.bat              # Start the extraction server
├── README.md
├── *.pbix                            # Power BI dashboards (one per use case)
├── scripts/
│   ├── api_extraction.py             # Dynamic web server (single codebase)
│   └── generate_dashboards.py        # Generate test datasets
└── shared_folder/                    # Drop Parquet files here
    ├── dashboard_ventes.parquet      # Sales data (2M rows)
    ├── dashboard_clients.parquet     # Customer data (1.5M rows)
    └── dashboard_reseau.parquet      # Network data (3M rows)
```

## Quick Start

### Prerequisites
```
pip install pandas numpy pyarrow openpyxl flask
```

### 1. Generate test datasets
```
python scripts/generate_dashboards.py
```

### 2. Start the server
```
double-click "Demarrer Serveur.bat"
```

### 3. Connect Power BI
- Open a `.pbix` file connected to a Parquet in `shared_folder/`
- Add a button → Action → Web URL → `http://localhost:5050/dataset/<filename>.parquet`
- Click the button → extraction page opens with dynamic filters

## Export Options

| Format | Speed | Use case |
|---|---|---|
| **CSV** | Fast (~10s for 5M rows) | Universal — open in Excel by double-click |
| **Excel** | Slower (auto-paginated if >1M rows) | For .xlsx preference |
| **Full extraction (ZIP)** | Fast (~10s) | Complete dataset as paginated CSV files in a ZIP |

## Tech Stack

- **Python** — pandas, NumPy, PyArrow
- **Apache Parquet** — columnar storage with Snappy compression
- **Flask** — lightweight local web server with dynamic filter generation

## Key Design Decisions

| Decision | Rationale |
|---|---|
| Local server, no cloud | Eliminates cloud costs and latency |
| Parquet over CSV | 7-18x faster reads, 3.6x smaller files |
| Dynamic filter generation | One codebase serves all dashboards |
| URL-based dataset routing | Each Power BI button points to its dataset — no selection page |
| Browser download dialog | User chooses where to save exported files |
