"""
API locale Flask dynamique — genere les filtres automatiquement
a partir de n'importe quel fichier Parquet.
"""

from flask import Flask, request, send_file, render_template_string, jsonify
import pandas as pd
import numpy as np
import os
import io
import zipfile
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHARED_DIR = os.path.join(BASE_DIR, "shared_folder")
MAX_FILTER_UNIQUE = 50

app = Flask(__name__)

datasets = {}


def scan_parquet_files():
    files = {}
    for f in os.listdir(SHARED_DIR):
        if f.endswith(".parquet"):
            path = os.path.join(SHARED_DIR, f)
            files[f] = {"path": path, "size": os.path.getsize(path) / 1e6}
    return files


def load_dataset(filename):
    if filename not in datasets:
        path = os.path.join(SHARED_DIR, filename)
        df = pd.read_parquet(path)
        cat_cols, date_cols, num_cols = detect_columns(df)
        datasets[filename] = {
            "df": df, "cat_cols": cat_cols,
            "date_cols": date_cols, "num_cols": num_cols,
        }
    return datasets[filename]


def detect_columns(df):
    cat_cols, date_cols, num_cols = [], [], []
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            date_cols.append(col)
        elif pd.api.types.is_numeric_dtype(df[col]):
            num_cols.append(col)
        elif df[col].nunique() <= MAX_FILTER_UNIQUE:
            cat_cols.append(col)
        else:
            num_cols.append(col)
    return cat_cols, date_cols, num_cols


def filter_df(df, filters, cat_cols, date_cols):
    for col in cat_cols:
        vals = filters.get(col, [])
        if vals:
            df = df[df[col].isin(vals)]
    for col in date_cols:
        d1 = filters.get(f"{col}_start", "")
        d2 = filters.get(f"{col}_end", "")
        if d1:
            df = df[df[col] >= pd.to_datetime(d1)]
        if d2:
            df = df[df[col] <= pd.to_datetime(d2)]
    return df


HTML_PAGE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Extraction de Donnees</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Segoe UI', sans-serif; background: #F0F2F5; color: #333; }
        .header { background: #1F4E79; padding: 20px 40px; display: flex; align-items: center; gap: 15px; }
        .header .logo { color: #E4002B; font-size: 28px; font-weight: 800; }
        .header .title { color: white; font-size: 20px; font-weight: 300; }
        .info-bar { background: #E8EEF4; padding: 8px 40px; font-size: 12px; color: #666; }
        .container { max-width: 950px; margin: 30px auto; padding: 0 20px; }
        .card { background: white; border-radius: 12px; padding: 25px; margin-bottom: 20px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
        .card h2 { color: #1F4E79; font-size: 16px; margin-bottom: 15px;
                    border-bottom: 2px solid #E8EEF4; padding-bottom: 8px; }
        .filters { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 20px; }
        .filter-group label { display: block; font-weight: 600; margin-bottom: 8px; font-size: 13px; color: #555; }
        .filter-group select { width: 100%; padding: 8px; border: 1px solid #DDD; border-radius: 6px;
                               font-size: 13px; height: 140px; }
        .dates { display: flex; flex-wrap: wrap; gap: 20px; margin-top: 15px; }
        .date-group { display: flex; align-items: center; gap: 8px; }
        .date-group label { font-weight: 600; font-size: 13px; color: #555; }
        .date-group input { padding: 8px 12px; border: 1px solid #DDD; border-radius: 6px; font-size: 13px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 15px; }
        .stat-box { text-align: center; padding: 15px; background: #F8FAFC; border-radius: 8px; }
        .stat-box .value { font-size: 22px; font-weight: 700; color: #2E75B6; }
        .stat-box .label { font-size: 11px; color: #888; margin-top: 4px; }
        .actions { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; }
        .btn { padding: 12px 30px; border: none; border-radius: 8px; font-size: 14px;
               font-weight: 600; cursor: pointer; transition: all 0.2s; }
        .btn:hover { transform: translateY(-1px); }
        .btn-csv { background: #2E75B6; color: white; }
        .btn-excel { background: #28A745; color: white; }
        .btn-total { background: #E4002B; color: white; }
        .btn-reset { background: #E0E0E0; color: #555; }
        .loading { display: none; text-align: center; padding: 20px; }
        .loading.active { display: block; }
        .spinner { width: 40px; height: 40px; border: 4px solid #E0E0E0; border-top: 4px solid #2E75B6;
                   border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 10px; }
        @keyframes spin { to { transform: rotate(360deg); } }
        .success { background: #D4EDDA; color: #155724; padding: 15px; border-radius: 8px;
                   display: none; margin-top: 15px; text-align: center; font-weight: 600; }
    </style>
</head>
<body>
    <div class="header">
        <span class="logo">EXTRACTION</span>
        <span class="title">de Donnees</span>
    </div>
    <div class="info-bar">
        Source : {{ filename }} | {{ n_total }} lignes | {{ n_cols }} colonnes |
        Filtres : {{ cat_cols_str }}
    </div>

    <div class="container">
        <div class="card">
            <h2>Filtres</h2>
            <div class="filters">
                {% for col in cat_cols %}
                <div class="filter-group">
                    <label>{{ col }} (Ctrl+clic)</label>
                    <select id="filter_{{ col }}" multiple>
                        {% for v in unique_vals[col] %}<option value="{{ v }}">{{ v }}</option>{% endfor %}
                    </select>
                </div>
                {% endfor %}
            </div>
            {% if date_cols %}
            <div class="dates">
                {% for col in date_cols %}
                <div class="date-group">
                    <label>{{ col }} du :</label>
                    <input type="date" id="{{ col }}_start">
                    <label>au :</label>
                    <input type="date" id="{{ col }}_end">
                </div>
                {% endfor %}
            </div>
            {% endif %}
        </div>

        <div class="card">
            <h2>Apercu</h2>
            <div class="stats">
                <div class="stat-box"><div class="value" id="s_lignes">—</div><div class="label">Lignes</div></div>
                {% for col in num_cols[:3] %}
                <div class="stat-box"><div class="value" id="s_{{ col }}">—</div><div class="label">{{ col }} (total)</div></div>
                {% endfor %}
            </div>
        </div>

        <div class="card">
            <div class="actions">
                <button class="btn btn-reset" onclick="resetFilters()">Reinitialiser</button>
                <div>
                    <button class="btn btn-csv" onclick="extract('csv')">CSV</button>
                    <button class="btn btn-excel" onclick="extract('excel')">Excel</button>
                    <button class="btn btn-total" onclick="extractTotal()">Extraction totale</button>
                </div>
            </div>
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p id="loading_text">Extraction en cours...</p>
            </div>
            <div class="success" id="success"></div>
        </div>
    </div>

    <script>
        const catCols = {{ cat_cols | tojson }};
        const dateCols = {{ date_cols | tojson }};
        const numCols = {{ num_cols_js | tojson }};
        const dataset = "{{ filename }}";

        function getFilters() {
            const filters = {dataset: dataset};
            catCols.forEach(col => {
                const sel = document.getElementById('filter_' + col);
                filters[col] = Array.from(sel.selectedOptions).map(o => o.value);
            });
            dateCols.forEach(col => {
                filters[col + '_start'] = document.getElementById(col + '_start').value;
                filters[col + '_end'] = document.getElementById(col + '_end').value;
            });
            return filters;
        }

        async function preview() {
            const resp = await fetch('/api/preview', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(getFilters())
            });
            const data = await resp.json();
            document.getElementById('s_lignes').textContent = Number(data.lignes).toLocaleString('fr-FR');
            numCols.forEach(col => {
                const el = document.getElementById('s_' + col);
                if (el) el.textContent = Number(data[col] || 0).toLocaleString('fr-FR', {minimumFractionDigits: 2});
            });
        }

        async function extract(format) {
            document.getElementById('loading').classList.add('active');
            document.getElementById('loading_text').textContent = `Export ${format.toUpperCase()} en cours...`;
            document.getElementById('success').style.display = 'none';

            const filters = getFilters();
            filters.format = format;
            const resp = await fetch('/api/extract', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(filters)
            });
            document.getElementById('loading').classList.remove('active');

            if (resp.ok) {
                const blob = await resp.blob();
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                const ts = new Date().toISOString().replace(/[-:T]/g, '').slice(0, 15);
                const ext = format === 'csv' ? 'csv' : 'xlsx';
                a.href = url; a.download = `extraction_${ts}.${ext}`; a.click();
                URL.revokeObjectURL(url);
                const ct = resp.headers.get('X-Row-Count') || '?';
                document.getElementById('success').textContent = `Extraction reussie ! ${ct} lignes.`;
                document.getElementById('success').style.display = 'block';
            } else { alert('Erreur'); }
        }

        async function extractTotal() {
            document.getElementById('loading').classList.add('active');
            document.getElementById('loading_text').textContent = 'Extraction totale en cours...';
            document.getElementById('success').style.display = 'none';

            const resp = await fetch('/api/extract_total', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({dataset: dataset})
            });
            document.getElementById('loading').classList.remove('active');

            if (resp.ok) {
                const blob = await resp.blob();
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                const ts = new Date().toISOString().replace(/[-:T]/g, '').slice(0, 15);
                a.href = url; a.download = `extraction_totale_${ts}.zip`; a.click();
                URL.revokeObjectURL(url);
                const ct = resp.headers.get('X-Row-Count') || '?';
                document.getElementById('success').textContent = `Extraction totale reussie ! ${ct} lignes telecharges en ZIP.`;
                document.getElementById('success').style.display = 'block';
            } else { alert('Erreur'); }
        }

        function resetFilters() {
            document.querySelectorAll('select').forEach(s => { for(let o of s.options) o.selected = false; });
            document.querySelectorAll('input[type=date]').forEach(i => i.value = '');
            preview();
        }

        preview();
        document.querySelectorAll('select, input').forEach(el => el.addEventListener('change', preview));
    </script>
</body>
</html>
"""

HTML_CHOOSER = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Extraction de Donnees</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Segoe UI', sans-serif; background: #F0F2F5; color: #333;
               display: flex; justify-content: center; align-items: center; min-height: 100vh; }
        .card { background: white; border-radius: 16px; padding: 40px; text-align: center;
                box-shadow: 0 4px 16px rgba(0,0,0,0.1); max-width: 500px; width: 100%; }
        h1 { color: #1F4E79; margin-bottom: 10px; }
        p { color: #666; margin-bottom: 25px; }
        a { display: block; padding: 15px 30px; margin: 10px 0; background: #2E75B6; color: white;
            border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 15px; }
        a:hover { background: #1F5F8B; }
        .size { color: #888; font-size: 12px; }
    </style>
</head>
<body>
    <div class="card">
        <h1>Extraction de Donnees</h1>
        <p>Choisissez un dataset :</p>
        {% for name, info in files.items() %}
        <a href="/dataset/{{ name }}">{{ name }} <span class="size">({{ "%.0f"|format(info.size) }} MB)</span></a>
        {% endfor %}
    </div>
</body>
</html>
"""


@app.route("/")
def index():
    files = scan_parquet_files()
    if len(files) == 1:
        name = list(files.keys())[0]
        return dataset_page(name)
    return render_template_string(HTML_CHOOSER, files=files)


@app.route("/dataset/<filename>")
def dataset_page(filename):
    try:
        ds = load_dataset(filename)
    except Exception as e:
        return f"Erreur : {e}", 500

    df = ds["df"]
    unique_vals = {col: sorted(str(v) for v in df[col].unique()) for col in ds["cat_cols"]}

    return render_template_string(HTML_PAGE,
        filename=filename,
        n_total=f"{len(df):,}",
        n_cols=len(df.columns),
        cat_cols=ds["cat_cols"],
        cat_cols_str=", ".join(ds["cat_cols"]) if ds["cat_cols"] else "aucun",
        date_cols=ds["date_cols"],
        num_cols=ds["num_cols"][:3],
        num_cols_js=ds["num_cols"][:3],
        unique_vals=unique_vals,
    )


@app.route("/api/preview", methods=["POST"])
def api_preview():
    data = request.json
    filename = data.get("dataset")
    ds = load_dataset(filename)
    df = filter_df(ds["df"].copy(), data, ds["cat_cols"], ds["date_cols"])

    result = {"lignes": len(df)}
    for col in ds["num_cols"]:
        result[col] = round(float(df[col].sum()), 2) if len(df) > 0 else 0
    return jsonify(result)


@app.route("/api/extract", methods=["POST"])
def api_extract():
    data = request.json
    filename = data.get("dataset")
    fmt = data.get("format", "csv")
    ds = load_dataset(filename)
    df = filter_df(ds["df"].copy(), data, ds["cat_cols"], ds["date_cols"])

    if len(df) == 0:
        return "Aucune donnee", 400

    output = io.BytesIO()
    MAX_ROWS = 1_000_000

    if fmt == "csv":
        df.to_csv(output, index=False, encoding="utf-8-sig")
        output.seek(0)
        mimetype = "text/csv"
        ext = "csv"
    else:
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            n_pages = max(1, (len(df) + MAX_ROWS - 1) // MAX_ROWS)
            for page in range(n_pages):
                start = page * MAX_ROWS
                end = min(start + MAX_ROWS, len(df))
                sheet_name = f"Donnees_{page+1}" if n_pages > 1 else "Donnees"
                df.iloc[start:end].to_excel(writer, sheet_name=sheet_name, index=False)
        output.seek(0)
        mimetype = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ext = "xlsx"

    response = send_file(output, mimetype=mimetype, as_attachment=True,
                         download_name=f"extraction_{datetime.now():%Y%m%d_%H%M%S}.{ext}")
    response.headers["X-Row-Count"] = str(len(df))
    return response


@app.route("/api/extract_total", methods=["POST"])
def api_extract_total():
    data = request.json
    filename = data.get("dataset")
    ds = load_dataset(filename)
    df = ds["df"]

    MAX_ROWS = 1_000_000
    n_pages = max(1, (len(df) + MAX_ROWS - 1) // MAX_ROWS)

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for page in range(n_pages):
            start = page * MAX_ROWS
            end = min(start + MAX_ROWS, len(df))
            csv_buffer = io.StringIO()
            df.iloc[start:end].to_csv(csv_buffer, index=False)
            zf.writestr(f"donnees_page_{page+1}.csv", csv_buffer.getvalue())

        index_text = f"Export du {datetime.now():%d/%m/%Y %H:%M}\n"
        index_text += f"Total : {len(df):,} lignes en {n_pages} fichiers CSV\n\n"
        for i in range(n_pages):
            s = i * MAX_ROWS + 1
            e = min((i + 1) * MAX_ROWS, len(df))
            index_text += f"  donnees_page_{i+1}.csv : lignes {s:,} a {e:,}\n"
        zf.writestr("_INDEX.txt", index_text)

    zip_buffer.seek(0)
    response = send_file(zip_buffer, mimetype="application/zip", as_attachment=True,
                         download_name=f"extraction_totale_{datetime.now():%Y%m%d_%H%M%S}.zip")
    response.headers["X-Row-Count"] = str(len(df))
    return response


if __name__ == "__main__":
    print("Serveur demarre sur http://localhost:5050")
    print(f"Dossier Parquet : {SHARED_DIR}")
    files = scan_parquet_files()
    for name, info in files.items():
        print(f"  - {name} ({info['size']:.0f} MB)")
    app.run(port=5050, debug=False)
