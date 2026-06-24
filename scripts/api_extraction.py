
from flask import Flask, request, send_file, render_template_string, jsonify
import pandas as pd
import os
import io
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARQUET_PATH = os.path.join(BASE_DIR, "shared_folder", "dataset_latest.parquet")

app = Flask(__name__)

df_global = pd.read_parquet(PARQUET_PATH)
print(f"Donnees chargees : {len(df_global):,} lignes")

HTML_PAGE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Ooredoo — Extraction</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Segoe UI', sans-serif; background: #F0F2F5; color: #333; }

        .header { background: #1F4E79; padding: 20px 40px; display: flex; align-items: center; gap: 15px; }
        .header .logo { color: #E4002B; font-size: 28px; font-weight: 800; }
        .header .title { color: white; font-size: 20px; font-weight: 300; }

        .container { max-width: 900px; margin: 30px auto; padding: 0 20px; }

        .card { background: white; border-radius: 12px; padding: 25px; margin-bottom: 20px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
        .card h2 { color: #1F4E79; font-size: 16px; margin-bottom: 15px;
                    border-bottom: 2px solid #E8EEF4; padding-bottom: 8px; }

        .filters { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; }
        .filter-group label { display: block; font-weight: 600; margin-bottom: 8px; font-size: 13px; color: #555; }
        .filter-group select { width: 100%; padding: 8px; border: 1px solid #DDD; border-radius: 6px;
                               font-size: 13px; height: 140px; }

        .dates { display: flex; gap: 20px; margin-top: 15px; }
        .dates input { padding: 8px 12px; border: 1px solid #DDD; border-radius: 6px;
                       font-size: 13px; width: 160px; }
        .dates label { font-weight: 600; font-size: 13px; color: #555; margin-right: 5px; }

        .stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; }
        .stat-box { text-align: center; padding: 15px; background: #F8FAFC; border-radius: 8px; }
        .stat-box .value { font-size: 24px; font-weight: 700; color: #2E75B6; }
        .stat-box .label { font-size: 11px; color: #888; margin-top: 4px; }

        .actions { display: flex; justify-content: space-between; align-items: center; }
        .btn { padding: 12px 30px; border: none; border-radius: 8px; font-size: 14px;
               font-weight: 600; cursor: pointer; transition: all 0.2s; }
        .btn-extract { background: #28A745; color: white; font-size: 16px; padding: 14px 40px; }
        .btn-extract:hover { background: #218838; transform: translateY(-1px); }
        .btn-reset { background: #E0E0E0; color: #555; }
        .btn-reset:hover { background: #D0D0D0; }
        .btn-preview { background: #2E75B6; color: white; }
        .btn-preview:hover { background: #1F5F8B; }

        .loading { display: none; text-align: center; padding: 20px; }
        .loading.active { display: block; }
        .spinner { width: 40px; height: 40px; border: 4px solid #E0E0E0; border-top: 4px solid #2E75B6;
                   border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 10px; }
        @keyframes spin { to { transform: rotate(360deg); } }

        .success { background: #D4EDDA; color: #155724; padding: 15px; border-radius: 8px;
                   display: none; margin-top: 15px; text-align: center; font-weight: 600; }

        .info-bar { background: #E8EEF4; padding: 8px 40px; font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <div class="header">
        <span class="logo">OOREDOO</span>
        <span class="title">Extraction de Donnees</span>
    </div>
    <div class="info-bar">
        Source : dataset_latest.parquet | {{ n_total }} lignes disponibles |
        Derniere mise a jour : {{ last_update }}
    </div>

    <div class="container">
        <div class="card">
            <h2>Filtres</h2>
            <div class="filters">
                <div class="filter-group">
                    <label>Region (Ctrl+clic pour multi)</label>
                    <select id="region" multiple>
                        {% for r in regions %}<option value="{{ r }}">{{ r }}</option>{% endfor %}
                    </select>
                </div>
                <div class="filter-group">
                    <label>Categorie</label>
                    <select id="categorie" multiple>
                        {% for c in categories %}<option value="{{ c }}">{{ c }}</option>{% endfor %}
                    </select>
                </div>
                <div class="filter-group">
                    <label>Statut</label>
                    <select id="statut" multiple>
                        {% for s in statuts %}<option value="{{ s }}">{{ s }}</option>{% endfor %}
                    </select>
                </div>
            </div>
            <div class="dates">
                <div><label>Du :</label><input type="date" id="date_debut"></div>
                <div><label>Au :</label><input type="date" id="date_fin"></div>
            </div>
        </div>

        <div class="card">
            <h2>Apercu</h2>
            <div class="stats">
                <div class="stat-box"><div class="value" id="s_lignes">—</div><div class="label">Lignes</div></div>
                <div class="stat-box"><div class="value" id="s_total">—</div><div class="label">Montant total (TND)</div></div>
                <div class="stat-box"><div class="value" id="s_moyen">—</div><div class="label">Montant moyen (TND)</div></div>
                <div class="stat-box"><div class="value" id="s_clients">—</div><div class="label">Clients uniques</div></div>
            </div>
        </div>

        <div class="card">
            <div class="actions">
                <div>
                    <button class="btn btn-reset" onclick="resetFilters()">Reinitialiser</button>
                </div>
                <button class="btn btn-extract" onclick="extract('csv')" style="background:#2E75B6;margin-right:8px;">CSV</button>
                <button class="btn btn-extract" onclick="extract('excel')" style="margin-right:8px;">Excel</button>
                <button class="btn btn-extract" onclick="extractTotal()" style="background:#E4002B;">Extraction totale</button>
            </div>
            <div class="warning" id="warning" style="display:none;background:#FFF3CD;color:#856404;padding:12px;border-radius:8px;margin-top:10px;text-align:center;"></div>
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p id="loading_text">Extraction en cours...</p>
            </div>
            <div class="success" id="success"></div>
        </div>
    </div>

    <script>
        function getFilters() {
            const get = id => Array.from(document.getElementById(id).selectedOptions).map(o => o.value);
            return {
                regions: get('region'),
                categories: get('categorie'),
                statuts: get('statut'),
                date_debut: document.getElementById('date_debut').value,
                date_fin: document.getElementById('date_fin').value
            };
        }

        async function preview() {
            const resp = await fetch('/api/preview', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(getFilters())
            });
            const data = await resp.json();
            document.getElementById('s_lignes').textContent = Number(data.lignes).toLocaleString('fr-FR');
            document.getElementById('s_total').textContent = Number(data.montant_total).toLocaleString('fr-FR', {minimumFractionDigits: 2});
            document.getElementById('s_moyen').textContent = Number(data.montant_moyen).toLocaleString('fr-FR', {minimumFractionDigits: 2});
            document.getElementById('s_clients').textContent = Number(data.clients).toLocaleString('fr-FR');
        }

        async function extract(format) {
            const filters = getFilters();
            // Preview first to get count
            const prevResp = await fetch('/api/preview', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(filters)
            });
            const prevData = await prevResp.json();
            const count = prevData.lignes;

            document.getElementById('warning').style.display = 'none';

            document.getElementById('loading').classList.add('active');
            if (format === 'csv') {
                document.getElementById('loading_text').textContent = 'Export CSV en cours...';
            } else {
                document.getElementById('loading_text').textContent = 'Export Excel en cours...';
            }
            document.getElementById('success').style.display = 'none';

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
                a.href = url;
                a.download = `extraction_${ts}.${ext}`;
                a.click();
                URL.revokeObjectURL(url);

                const ct = resp.headers.get('X-Row-Count') || '?';
                document.getElementById('success').textContent = `Extraction reussie ! ${ct} lignes telecharges en ${ext.toUpperCase()}.`;
                document.getElementById('success').style.display = 'block';
            } else {
                alert('Erreur lors de extraction');
            }
        }

        async function extractTotal() {
            document.getElementById('loading').classList.add('active');
            document.getElementById('loading_text').textContent = 'Extraction totale en cours (plusieurs fichiers pagines)...';
            document.getElementById('success').style.display = 'none';
            document.getElementById('warning').style.display = 'none';

            const resp = await fetch('/api/extract_total', { method: 'POST' });
            document.getElementById('loading').classList.remove('active');

            if (resp.ok) {
                const data = await resp.json();
                document.getElementById('success').textContent =
                    `Extraction totale reussie ! ${data.lignes} lignes en ${data.fichiers} fichiers dans ${data.dossier}`;
                document.getElementById('success').style.display = 'block';
            } else {
                alert('Erreur lors de extraction totale');
            }
        }

        function resetFilters() {
            document.querySelectorAll('select').forEach(s => { for(let o of s.options) o.selected = false; });
            document.getElementById('date_debut').value = '';
            document.getElementById('date_fin').value = '';
            ['s_lignes','s_total','s_moyen','s_clients'].forEach(id => document.getElementById(id).textContent = '—');
        }

        // Auto preview on load
        preview();
        document.querySelectorAll('select, input').forEach(el => el.addEventListener('change', preview));
    </script>
</body>
</html>
"""


def filter_df(filters):
    df = df_global.copy()
    if filters.get("regions"):
        df = df[df["region"].isin(filters["regions"])]
    if filters.get("categories"):
        df = df[df["categorie"].isin(filters["categories"])]
    if filters.get("statuts"):
        df = df[df["statut"].isin(filters["statuts"])]
    if filters.get("date_debut"):
        df = df[df["date"] >= pd.to_datetime(filters["date_debut"])]
    if filters.get("date_fin"):
        df = df[df["date"] <= pd.to_datetime(filters["date_fin"])]
    return df


@app.route("/")
def index():
    last_mod = datetime.fromtimestamp(os.path.getmtime(PARQUET_PATH))
    return render_template_string(HTML_PAGE,
        regions=sorted(df_global["region"].unique()),
        categories=sorted(df_global["categorie"].unique()),
        statuts=sorted(df_global["statut"].unique()),
        n_total=f"{len(df_global):,}",
        last_update=last_mod.strftime("%d/%m/%Y %H:%M"),
    )


@app.route("/api/preview", methods=["POST"])
def api_preview():
    df = filter_df(request.json)
    return jsonify({
        "lignes": len(df),
        "montant_total": round(df["montant"].sum(), 2) if len(df) > 0 else 0,
        "montant_moyen": round(df["montant"].mean(), 2) if len(df) > 0 else 0,
        "clients": int(df["id_client"].nunique()) if len(df) > 0 else 0,
    })


@app.route("/api/extract", methods=["POST"])
def api_extract():
    df = filter_df(request.json)
    if len(df) == 0:
        return "Aucune donnee", 400

    fmt = request.json.get("format", "csv")
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
            resume = pd.DataFrame({
                "Metrique": ["Lignes", "Feuilles", "Date", "Montant total", "Montant moyen", "Clients"],
                "Valeur": [
                    f"{len(df):,}",
                    f"{n_pages}",
                    datetime.now().strftime("%d/%m/%Y %H:%M"),
                    f"{df['montant'].sum():,.2f} TND",
                    f"{df['montant'].mean():,.2f} TND",
                    f"{df['id_client'].nunique():,}",
                ],
            })
            resume.to_excel(writer, sheet_name="Resume", index=False)
        output.seek(0)
        mimetype = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ext = "xlsx"

    response = send_file(output, mimetype=mimetype,
                         as_attachment=True, download_name=f"extraction_{datetime.now():%Y%m%d_%H%M%S}.{ext}")
    response.headers["X-Row-Count"] = str(len(df))
    return response


@app.route("/api/extract_total", methods=["POST"])
def api_extract_total():
    export_dir = os.path.join(BASE_DIR, "shared_folder", "excel_export")
    os.makedirs(export_dir, exist_ok=True)
    MAX_ROWS = 1_000_000
    n_pages = max(1, (len(df_global) + MAX_ROWS - 1) // MAX_ROWS)

    for page in range(n_pages):
        start = page * MAX_ROWS
        end = min(start + MAX_ROWS, len(df_global))
        filepath = os.path.join(export_dir, f"donnees_page_{page+1}.csv")
        df_global.iloc[start:end].to_csv(filepath, index=False, encoding="utf-8-sig")

    index_path = os.path.join(export_dir, "_INDEX.txt")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(f"Export du {datetime.now():%d/%m/%Y %H:%M}\n")
        f.write(f"Total : {len(df_global):,} lignes en {n_pages} fichiers CSV\n")
        f.write(f"Pour ouvrir dans Excel : double-clic sur le fichier CSV\n\n")
        for i in range(n_pages):
            s = i * MAX_ROWS + 1
            e = min((i + 1) * MAX_ROWS, len(df_global))
            f.write(f"  donnees_page_{i+1}.csv : lignes {s:,} a {e:,}\n")

    return jsonify({
        "lignes": f"{len(df_global):,}",
        "fichiers": n_pages,
        "dossier": export_dir,
    })


if __name__ == "__main__":
    print("Serveur demarre sur http://localhost:5050")
    print("Utilisez le bouton dans Power BI pour y acceder.")
    app.run(port=5050, debug=False)
