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
Power BI Dashboard (Sales)   ──→  bouton "Extract"
                                       ↓
Power BI Dashboard (Clients) ──→  bouton "Extract"     ──→  Same server
                                       ↓                     Same code
Power BI Dashboard (Network) ──→  bouton "Extract"          Dynamic filters
                                       ↓
                              http://server:5050/dataset/<filename>.parquet
                                       ↓
                              Auto-detected filters based on column types
                                       ↓
                              Export: CSV / Excel / ZIP (full extraction)
```

### How it works

1. Drop any data file (CSV, XLSX, JSON, TSV) in `downloads/` — it is **automatically converted** to Parquet on server startup
2. The server reads the Parquet file specified in the URL
3. It detects column types automatically:
   - **Text columns** (< 50 unique values) → multi-select filter
   - **Date columns** → date range picker
   - **Numeric columns** → displayed as summary stats
4. The user filters and exports — choosing CSV, Excel, or full extraction (ZIP)

### Adding a new dashboard

1. Drop a data file in `downloads/` (CSV, XLSX, or any supported format)
2. Restart the server — auto-conversion to Parquet
3. In Power BI, add a button → Action → Web URL → `http://server:5050/dataset/<filename>.parquet`
4. Done — zero code changes

## Why Parquet?

| Metric | CSV | Parquet | Gain |
|---|---|---|---|
| Write (5M rows) | 10.6s | 2.1s | **5x faster** |
| File size (5M rows) | 625 MB | 115 MB | **5.4x smaller** |
| Read (5M rows) | 5.2s | 0.7s | **7x faster** |
| Read (10M rows) | 9.7s | 0.5s | **18x faster** |

## Project Structure

```
├── Demarrer Serveur.bat              # Start the server (auto-converts + launches)
├── Installer Dependances.bat         # Install all Python dependencies
├── requirements.txt                  # Python package list
├── README.md
│
├── scripts/
│   ├── api_extraction.py             # Dynamic web server (single codebase)
│   └── convert_to_parquet.py         # Standalone conversion utility
│
├── downloads/                        # Drop raw data files here (CSV, XLSX, JSON, TSV)
│   ├── sales_5000000.csv             # Auto-converted on server startup
│   └── bankdataset.xlsx              # Auto-converted on server startup
│
├── shared_folder/                    # Parquet files (auto-generated)
│   ├── sales_5000000.parquet
│   └── bankdataset.parquet
│
└── docs/
    └── guide_production.md           # Production deployment guide
```

## Quick Start

### 1. Install dependencies
```
double-click "Installer Dependances.bat"
```
Or manually:
```
pip install pandas numpy pyarrow openpyxl flask
```

### 2. Add your data
Drop CSV, XLSX, or any supported file into `downloads/`

### 3. Start the server
```
double-click "Demarrer Serveur.bat"
```
The server will:
- Auto-convert files in `downloads/` to Parquet
- Start on `http://localhost:5050`
- List all available datasets

### 4. Connect Power BI
- Open Power BI Desktop → Get Data → Parquet → select from `shared_folder/`
- Add a button → Action → Web URL → `http://localhost:5050/dataset/<filename>.parquet`
- Click the button → extraction page opens with dynamic filters

## Export Options

| Format | Speed | Use case |
|---|---|---|
| **CSV** | Fast (~10s for 5M rows) | Universal — open in Excel by double-click |
| **Excel** | Slower (auto-paginated if >1M rows) | For .xlsx preference |
| **Full extraction (ZIP)** | Fast (~10s) | Complete dataset as paginated CSV files |

## Production Deployment

In production, the only changes are:

| Element | POC | Production |
|---|---|---|
| Data source | CSV/XLSX in `downloads/` | SQL queries via scheduled pipeline |
| Server URL | `localhost:5050` | `http://internal-server:5050` |
| Server launch | Double-click .bat | Windows Service (NSSM) |
| Data refresh | Manual | Nightly scheduled task |

The server code (`api_extraction.py`) requires **zero modifications** between POC and production.

See [docs/guide_production.md](docs/guide_production.md) for the full deployment guide.

## Supported Input Formats

| Format | Extension | Auto-converted |
|---|---|---|
| CSV | .csv | Yes |
| Excel | .xlsx, .xls | Yes |
| TSV | .tsv | Yes |
| JSON | .json | Yes |
| Parquet | .parquet | Native (no conversion needed) |

## Tech Stack

- **Python** — pandas, NumPy, PyArrow
- **Apache Parquet** — columnar storage with Snappy compression
- **Flask** — lightweight local web server with dynamic filter generation

## Key Design Decisions

| Decision | Rationale |
|---|---|
| Local server, no cloud | Eliminates cloud costs and latency |
| Parquet over CSV | 7-18x faster reads, 5.4x smaller files |
| Dynamic filter generation | One codebase serves all dashboards |
| Auto-conversion on startup | Users drop files, server handles the rest |
| URL-based dataset routing | Each Power BI button points to its dataset — no selection page |
