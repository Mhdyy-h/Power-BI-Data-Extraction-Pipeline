
import customtkinter as ctk
from tkinter import filedialog, messagebox
import tkinter as tk
from tkcalendar import DateEntry
import pandas as pd
import os
import threading
import subprocess
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARQUET_PATH = os.path.join(BASE_DIR, "shared_folder", "dataset_latest.parquet")
LOGO_COLOR = "#E4002B"
PRIMARY = "#1F4E79"
ACCENT = "#2E75B6"
SUCCESS = "#28A745"

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

df_global = None


def load_data():
    global df_global
    try:
        df_global = pd.read_parquet(PARQUET_PATH)
        return True
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible de lire le fichier :\n{e}")
        return False


def get_unique(col):
    return sorted(df_global[col].unique().tolist()) if df_global is not None else []


def apply_filters():
    if df_global is None:
        return pd.DataFrame()
    df = df_global.copy()

    sel_regions = [region_vars[r].cget("text") for r in region_vars if region_vars[r].get()]
    if sel_regions:
        df = df[df["region"].isin(sel_regions)]

    sel_categories = [cat_vars[c].cget("text") for c in cat_vars if cat_vars[c].get()]
    if sel_categories:
        df = df[df["categorie"].isin(sel_categories)]

    sel_statuts = [stat_vars[s].cget("text") for s in stat_vars if stat_vars[s].get()]
    if sel_statuts:
        df = df[df["statut"].isin(sel_statuts)]

    if date_debut_active:
        try:
            d1 = date_debut_entry.get().strip()
            if d1:
                df = df[df["date"] >= pd.to_datetime(d1, dayfirst=True)]
        except Exception:
            pass

    if date_fin_active:
        try:
            d2 = date_fin_entry.get().strip()
            if d2:
                df = df[df["date"] <= pd.to_datetime(d2, dayfirst=True)]
        except Exception:
            pass

    return df


def update_preview(*args):
    df = apply_filters()
    n = len(df)
    count_val.configure(text=f"{n:,}")
    if n > 0:
        total_val.configure(text=f"{df['montant'].sum():,.2f}")
        moyen_val.configure(text=f"{df['montant'].mean():,.2f}")
        clients_val.configure(text=f"{df['id_client'].nunique():,}")
    else:
        for v in [total_val, moyen_val, clients_val]:
            v.configure(text="—")
    state = "normal" if n > 0 else "disabled"
    for btn in [csv_btn, excel_btn, total_btn]:
        try:
            btn.configure(state=state)
        except NameError:
            pass


def get_filter_summary():
    parts = []
    sel_r = [r for r in region_vars if region_vars[r].get()]
    if sel_r:
        parts.append(f"Regions: {', '.join(sel_r)}")
    sel_c = [c for c in cat_vars if cat_vars[c].get()]
    if sel_c:
        parts.append(f"Categories: {', '.join(sel_c)}")
    sel_s = [s for s in stat_vars if stat_vars[s].get()]
    if sel_s:
        parts.append(f"Statuts: {', '.join(sel_s)}")
    if date_debut_active and date_debut_entry.get().strip():
        parts.append(f"Du: {date_debut_entry.get().strip()}")
    if date_fin_active and date_fin_entry.get().strip():
        parts.append(f"Au: {date_fin_entry.get().strip()}")
    return " | ".join(parts) if parts else "Aucun filtre"


EXPORT_DIR = os.path.join(BASE_DIR, "shared_folder", "excel_export")


def extract_csv():
    do_extract("csv")


def extract_excel():
    do_extract("excel")


def extract_total():
    """Extraction totale paginee dans shared_folder/excel_export/"""
    if df_global is None:
        return

    for btn in [csv_btn, excel_btn, total_btn]:
        btn.configure(state="disabled")
    progress_label.configure(text="Extraction totale en cours...")
    progress_label.pack(pady=(5, 0))
    progress.pack(pady=(0, 10), padx=30, fill="x")
    progress.start()

    def do_total():
        try:
            os.makedirs(EXPORT_DIR, exist_ok=True)
            MAX_ROWS = 1_000_000
            n_pages = max(1, (len(df_global) + MAX_ROWS - 1) // MAX_ROWS)

            for page in range(n_pages):
                start = page * MAX_ROWS
                end = min(start + MAX_ROWS, len(df_global))
                filepath = os.path.join(EXPORT_DIR, f"donnees_page_{page+1}.csv")
                df_global.iloc[start:end].to_csv(filepath, index=False, encoding="utf-8-sig")
                root.after(0, lambda p=page+1, t=n_pages:
                    progress_label.configure(text=f"Fichier {p}/{t} en cours..."))

            index_path = os.path.join(EXPORT_DIR, "_INDEX.txt")
            with open(index_path, "w", encoding="utf-8") as f:
                f.write(f"Export du {datetime.now():%d/%m/%Y %H:%M}\n")
                f.write(f"Total : {len(df_global):,} lignes en {n_pages} fichiers CSV\n")
                f.write(f"Pour ouvrir dans Excel : double-clic sur le fichier CSV\n\n")
                for i in range(n_pages):
                    s = i * MAX_ROWS + 1
                    e = min((i + 1) * MAX_ROWS, len(df_global))
                    f.write(f"  donnees_page_{i+1}.csv : lignes {s:,} a {e:,}\n")

            root.after(0, lambda: on_done(EXPORT_DIR, len(df_global), "excel"))
        except Exception as e:
            root.after(0, lambda: on_error(str(e)))

    threading.Thread(target=do_total, daemon=True).start()


def do_extract(fmt):
    df = apply_filters()
    if len(df) == 0:
        messagebox.showwarning("Attention", "Aucune donnee avec ces filtres.")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if fmt == "csv":
        filepath = filedialog.asksaveasfilename(
            title="Enregistrer en CSV",
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("Tous", "*.*")],
            initialfile=f"extraction_{timestamp}.csv",
        )
    else:
        filepath = filedialog.asksaveasfilename(
            title="Enregistrer en Excel",
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx"), ("Tous", "*.*")],
            initialfile=f"extraction_{timestamp}.xlsx",
        )

    if not filepath:
        return

    for btn in [csv_btn, excel_btn, total_btn]:
        btn.configure(state="disabled")
    progress_label.configure(text=f"Export {fmt.upper()} en cours...")
    progress_label.pack(pady=(5, 0))
    progress.pack(pady=(0, 10), padx=30, fill="x")
    progress.start()

    def do_export():
        try:
            if fmt == "csv":
                df.to_csv(filepath, index=False, encoding="utf-8-sig")
            else:
                MAX_ROWS = 1_000_000
                with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
                    n_pages = max(1, (len(df) + MAX_ROWS - 1) // MAX_ROWS)
                    for page in range(n_pages):
                        start = page * MAX_ROWS
                        end = min(start + MAX_ROWS, len(df))
                        sheet_name = f"Donnees_{page+1}" if n_pages > 1 else "Donnees"
                        df.iloc[start:end].to_excel(writer, sheet_name=sheet_name, index=False)
                        root.after(0, lambda p=page+1, t=n_pages:
                            progress_label.configure(text=f"Feuille {p}/{t} en cours..."))
                    resume = pd.DataFrame({
                        "Metrique": ["Lignes", "Feuilles", "Date", "Montant total", "Montant moyen", "Clients", "Filtres"],
                        "Valeur": [
                            f"{len(df):,}", f"{n_pages}",
                            datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                            f"{df['montant'].sum():,.2f} TND",
                            f"{df['montant'].mean():,.2f} TND",
                            f"{df['id_client'].nunique():,}",
                            get_filter_summary(),
                        ],
                    })
                    resume.to_excel(writer, sheet_name="Resume", index=False)
            root.after(0, lambda: on_done(filepath, len(df), fmt))
        except Exception as e:
            root.after(0, lambda: on_error(str(e)))

    threading.Thread(target=do_export, daemon=True).start()


def on_done(path, count, fmt):
    progress.stop()
    progress.pack_forget()
    progress_label.pack_forget()
    for btn in [csv_btn, excel_btn, total_btn]:
        btn.configure(state="normal")
    result = messagebox.askyesno(
        "Extraction reussie",
        f"{count:,} lignes exportees !\n\n{path}\n\nOuvrir le dossier ?",
    )
    if result:
        if os.path.isdir(path):
            subprocess.Popen(f'explorer "{path}"')
        else:
            subprocess.Popen(f'explorer /select,"{path}"')


def on_error(err):
    progress.stop()
    progress.pack_forget()
    progress_label.pack_forget()
    for btn in [csv_btn, excel_btn, total_btn]:
        btn.configure(state="normal")
    messagebox.showerror("Erreur", err)


def reset_filters():
    for v in region_vars.values():
        v.deselect()
    for v in cat_vars.values():
        v.deselect()
    for v in stat_vars.values():
        v.deselect()
    global date_debut_active, date_fin_active
    date_debut_active = False
    date_fin_active = False
    date_debut_entry.configure(state="normal")
    date_debut_entry.delete(0, "end")
    date_debut_entry.configure(state="readonly")
    date_fin_entry.configure(state="normal")
    date_fin_entry.delete(0, "end")
    date_fin_entry.configure(state="readonly")
    update_preview()


def select_all(var_dict, select=True):
    for v in var_dict.values():
        if select:
            v.select()
        else:
            v.deselect()
    update_preview()


# === WINDOW ===
root = ctk.CTk()
root.title("Ooredoo — Extraction de Donnees")
root.geometry("800x750")
root.resizable(False, False)

# === HEADER ===
header = ctk.CTkFrame(root, fg_color=PRIMARY, height=70, corner_radius=0)
header.pack(fill="x")
header.pack_propagate(False)

title_frame = ctk.CTkFrame(header, fg_color="transparent")
title_frame.pack(expand=True)

ctk.CTkLabel(title_frame, text="OOREDOO", font=("Segoe UI", 28, "bold"),
             text_color=LOGO_COLOR).pack(side="left", padx=(0, 10))
ctk.CTkLabel(title_frame, text="Extraction de Donnees", font=("Segoe UI", 20),
             text_color="white").pack(side="left")

# === INFO BAR ===
info_bar = ctk.CTkFrame(root, fg_color="#E8EEF4", height=30, corner_radius=0)
info_bar.pack(fill="x")
info_bar.pack_propagate(False)

source_text = os.path.basename(PARQUET_PATH)
if df_global is None:
    load_data()
n_total = f"{len(df_global):,}" if df_global is not None else "?"
info_label = ctk.CTkLabel(info_bar, text=f"Source : {source_text}  |  {n_total} lignes disponibles",
                           font=("Segoe UI", 11), text_color="#555")
info_label.pack(expand=True)

# === MAIN CONTENT ===
main = ctk.CTkFrame(root, fg_color="transparent")
main.pack(fill="both", expand=True, padx=20, pady=10)

# --- FILTERS ---
filters_label = ctk.CTkLabel(main, text="FILTRES", font=("Segoe UI", 12, "bold"), text_color=PRIMARY)
filters_label.pack(anchor="w", pady=(0, 5))

filters_frame = ctk.CTkFrame(main, fg_color="white", corner_radius=10, border_width=1, border_color="#DDD")
filters_frame.pack(fill="x", pady=(0, 10))

# Checkboxes frame
checks_frame = ctk.CTkFrame(filters_frame, fg_color="transparent")
checks_frame.pack(fill="x", padx=15, pady=10)

region_vars = {}
cat_vars = {}
stat_vars = {}


def make_filter_column(parent, title, values, var_dict, col):
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    frame.grid(row=0, column=col, sticky="nsew", padx=10)
    parent.columnconfigure(col, weight=1)

    header_frame = ctk.CTkFrame(frame, fg_color="transparent")
    header_frame.pack(fill="x")
    ctk.CTkLabel(header_frame, text=title, font=("Segoe UI", 11, "bold"), text_color="#333").pack(side="left")

    btn_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
    btn_frame.pack(side="right")
    ctk.CTkButton(btn_frame, text="Tous", width=40, height=20, font=("Segoe UI", 9),
                  fg_color="#DDD", text_color="#555", hover_color="#CCC",
                  command=lambda: select_all(var_dict, True)).pack(side="left", padx=1)
    ctk.CTkButton(btn_frame, text="Aucun", width=40, height=20, font=("Segoe UI", 9),
                  fg_color="#DDD", text_color="#555", hover_color="#CCC",
                  command=lambda: select_all(var_dict, False)).pack(side="left", padx=1)

    scroll = ctk.CTkScrollableFrame(frame, fg_color="transparent", height=100)
    scroll.pack(fill="x")
    for v in values:
        cb = ctk.CTkCheckBox(scroll, text=v, font=("Segoe UI", 10), command=update_preview,
                             checkbox_width=18, checkbox_height=18, corner_radius=4)
        cb.pack(anchor="w", pady=1)
        var_dict[v] = cb


make_filter_column(checks_frame, "Region", get_unique("region"), region_vars, 0)
make_filter_column(checks_frame, "Categorie", get_unique("categorie"), cat_vars, 1)
make_filter_column(checks_frame, "Statut", get_unique("statut"), stat_vars, 2)

# Dates
dates_frame = ctk.CTkFrame(filters_frame, fg_color="transparent")
dates_frame.pack(fill="x", padx=15, pady=(0, 10))

date_debut_active = False
date_fin_active = False

ctk.CTkLabel(dates_frame, text="Periode :", font=("Segoe UI", 10, "bold"), text_color="#333").pack(side="left", padx=(0, 10))
ctk.CTkLabel(dates_frame, text="Du", font=("Segoe UI", 10), text_color="#666").pack(side="left")

date_debut_entry = ctk.CTkEntry(dates_frame, width=120, placeholder_text="Cliquer pour choisir")
date_debut_entry.pack(side="left", padx=5)
date_debut_entry.configure(state="readonly")

def pick_date_debut():
    global date_debut_active
    top = tk.Toplevel(root)
    top.title("Date debut")
    top.geometry("300x280")
    top.grab_set()
    cal = DateEntry(top, width=20, date_pattern="dd/mm/yyyy", font=("Segoe UI", 12))
    cal.pack(pady=20)
    def on_select():
        global date_debut_active
        date_debut_entry.configure(state="normal")
        date_debut_entry.delete(0, "end")
        date_debut_entry.insert(0, cal.get())
        date_debut_entry.configure(state="readonly")
        date_debut_active = True
        top.destroy()
        update_preview()
    def on_clear():
        global date_debut_active
        date_debut_entry.configure(state="normal")
        date_debut_entry.delete(0, "end")
        date_debut_entry.configure(state="readonly", placeholder_text="Cliquer pour choisir")
        date_debut_active = False
        top.destroy()
        update_preview()
    tk.Button(top, text="Valider", command=on_select, bg="#28A745", fg="white",
              font=("Segoe UI", 11, "bold"), width=12).pack(pady=5)
    tk.Button(top, text="Effacer", command=on_clear, font=("Segoe UI", 10), width=12).pack(pady=5)

date_debut_entry.bind("<Button-1>", lambda e: pick_date_debut())

ctk.CTkLabel(dates_frame, text="Au", font=("Segoe UI", 10), text_color="#666").pack(side="left", padx=(10, 0))

date_fin_entry = ctk.CTkEntry(dates_frame, width=120, placeholder_text="Cliquer pour choisir")
date_fin_entry.pack(side="left", padx=5)
date_fin_entry.configure(state="readonly")

def pick_date_fin():
    global date_fin_active
    top = tk.Toplevel(root)
    top.title("Date fin")
    top.geometry("300x280")
    top.grab_set()
    cal = DateEntry(top, width=20, date_pattern="dd/mm/yyyy", font=("Segoe UI", 12))
    cal.pack(pady=20)
    def on_select():
        global date_fin_active
        date_fin_entry.configure(state="normal")
        date_fin_entry.delete(0, "end")
        date_fin_entry.insert(0, cal.get())
        date_fin_entry.configure(state="readonly")
        date_fin_active = True
        top.destroy()
        update_preview()
    def on_clear():
        global date_fin_active
        date_fin_entry.configure(state="normal")
        date_fin_entry.delete(0, "end")
        date_fin_entry.configure(state="readonly", placeholder_text="Cliquer pour choisir")
        date_fin_active = False
        top.destroy()
        update_preview()
    tk.Button(top, text="Valider", command=on_select, bg="#28A745", fg="white",
              font=("Segoe UI", 11, "bold"), width=12).pack(pady=5)
    tk.Button(top, text="Effacer", command=on_clear, font=("Segoe UI", 10), width=12).pack(pady=5)

date_fin_entry.bind("<Button-1>", lambda e: pick_date_fin())

# --- STATS PREVIEW ---
stats_label = ctk.CTkLabel(main, text="APERCU", font=("Segoe UI", 12, "bold"), text_color=PRIMARY)
stats_label.pack(anchor="w", pady=(5, 5))

stats_frame = ctk.CTkFrame(main, fg_color="white", corner_radius=10, border_width=1, border_color="#DDD")
stats_frame.pack(fill="x", pady=(0, 10))

stats_inner = ctk.CTkFrame(stats_frame, fg_color="transparent")
stats_inner.pack(fill="x", padx=10, pady=15)


def make_stat_box(parent, title, col, color=ACCENT):
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    frame.grid(row=0, column=col, sticky="nsew", padx=5)
    parent.columnconfigure(col, weight=1)
    ctk.CTkLabel(frame, text=title, font=("Segoe UI", 10), text_color="#888").pack()
    val = ctk.CTkLabel(frame, text="—", font=("Segoe UI", 20, "bold"), text_color=color)
    val.pack()
    return val


count_val = make_stat_box(stats_inner, "Lignes", 0, PRIMARY)
total_val = make_stat_box(stats_inner, "Montant total (TND)", 1)
moyen_val = make_stat_box(stats_inner, "Montant moyen (TND)", 2)
clients_val = make_stat_box(stats_inner, "Clients uniques", 3)

# --- BUTTONS ---
btn_frame = ctk.CTkFrame(main, fg_color="transparent")
btn_frame.pack(fill="x", pady=(5, 0))

ctk.CTkButton(btn_frame, text="Reinitialiser les filtres", width=180, height=40,
              fg_color="#E0E0E0", text_color="#555", hover_color="#D0D0D0",
              font=("Segoe UI", 11), command=reset_filters).pack(side="left")

total_btn = ctk.CTkButton(btn_frame, text="Extraction totale", width=160, height=45,
                           fg_color="#E4002B", hover_color="#B8001F", text_color="white",
                           font=("Segoe UI", 12, "bold"), command=extract_total)
total_btn.pack(side="right")

excel_btn = ctk.CTkButton(btn_frame, text="Excel", width=110, height=45,
                           fg_color=SUCCESS, hover_color="#218838", text_color="white",
                           font=("Segoe UI", 12, "bold"), command=extract_excel)
excel_btn.pack(side="right", padx=(0, 8))

csv_btn = ctk.CTkButton(btn_frame, text="CSV", width=110, height=45,
                         fg_color=ACCENT, hover_color="#1F5F8B", text_color="white",
                         font=("Segoe UI", 12, "bold"), command=extract_csv)
csv_btn.pack(side="right", padx=(0, 8))

# Progress
progress_label = ctk.CTkLabel(main, text="", font=("Segoe UI", 11), text_color="#666")
progress = ctk.CTkProgressBar(main, mode="indeterminate", progress_color=ACCENT)

# --- INIT ---
update_preview()
root.mainloop()
