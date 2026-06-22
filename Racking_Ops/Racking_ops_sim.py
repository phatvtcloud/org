import os
import sys
import io
import json

# Set stdout/stderr encoding to UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import glob
import pandas as pd
import numpy as np
import re
from datetime import datetime, timedelta

# Define paths
INV_DIR = r"C:\Users\phatvt\OneDrive - WIN\DR-WCM - 15.9.3 Operation\INV\INV14_pq"
INV03_DIR = r"C:\Users\phatvt\OneDrive - WIN\DR-WCM - 15.9.3 Operation\INV03\Data_pq"
MD06_PATH = r"C:\Users\phatvt\OneDrive - WIN\DR-WCM - 15.9.4 OP&Fin\04. Master Data\MD_06.xlsb"
WH_FMCG_PATH = r"C:\Users\phatvt\OneDrive - WIN\DR-WCM - 15.9.4 OP&Fin\WH_FMCG.xlsx"

def extract_reporting_date(fname):
    """
    Parses datetime from filename and adds 7 hours, returning a date object.
    Example: 2026-06-15T17_07_54+00_00_... -> 2026-06-15 17:07:54 + 7h -> 2026-06-16
    """
    match = re.search(r"(\d{4}-\d{2}-\d{2})T(\d{2})_(\d{2})_(\d{2})", fname)
    if match:
        date_str = match.group(1)
        h, m, s = int(match.group(2)), int(match.group(3)), int(match.group(4))
        try:
            dt_obj = datetime.strptime(f"{date_str} {h}:{m}:{s}", "%Y-%m-%d %H:%M:%S")
            dt_reporting = dt_obj + timedelta(hours=7)
            return dt_reporting.date()
        except ValueError:
            pass
            
    match_date = re.search(r"(\d{4}-\d{2}-\d{2})", fname)
    if match_date:
        date_str = match_date.group(1)
        try:
            dt_obj = datetime.strptime(date_str, "%Y-%m-%d")
            dt_reporting = dt_obj + timedelta(hours=7)
            return dt_reporting.date()
        except ValueError:
            pass
            
    return None

def get_files_last_7_days_by_mtime(directory, pattern):
    """
    Finds files in a directory matching a pattern, gets their modification dates,
    and returns files modified in the last 7 days relative to the maximum modification date.
    """
    search_path = os.path.join(directory, pattern)
    files = glob.glob(search_path)
    if not files:
        return []
    
    file_info = []
    for f in files:
        try:
            mtime = os.path.getmtime(f)
            mdate = datetime.fromtimestamp(mtime).date()
            file_info.append((mdate, f))
        except Exception as e:
            print(f"Error getting mtime for {f}: {e}")
            
    if not file_info:
        return []
        
    max_date = max(d for d, _ in file_info)
    start_date = max_date - timedelta(days=6) # 7 days inclusive
    
    print(f"Directory: {directory}")
    print(f"Latest modification date in folder: {max_date}")
    print(f"Filtering files modified between {start_date} and {max_date} (last 7 days)")
    
    selected_files = [f for d, f in file_info if start_date <= d <= max_date]
    selected_files.sort(key=lambda x: (os.path.getmtime(x), x))
    return selected_files

# =========================================
# --- LOAD REFERENTIAL DATASETS ---
# =========================================
print("=========================================")
print("--- LOADING REFERENTIAL DATASETS ---")
print("=========================================")

# Load D_DC from WH_FMCG.xlsx
df_dc = pd.DataFrame()
if os.path.exists(WH_FMCG_PATH):
    try:
        df_dc = pd.read_excel(WH_FMCG_PATH, sheet_name="Inventory")
        print(f"Loaded D_DC. Shape: {df_dc.shape}")
    except Exception as e:
        print("Error loading D_DC from WH_FMCG.xlsx:", e)
else:
    print("WH_FMCG.xlsx not found.")

# Load MD06 from MD_06.xlsb
df_md06 = pd.DataFrame()
if os.path.exists(MD06_PATH):
    try:
        from pyxlsb import open_workbook
        with open_workbook(MD06_PATH) as wb:
            sheets = wb.sheets
            first_sheet = sheets[0] if sheets else None
        if first_sheet:
            df_md06 = pd.read_excel(MD06_PATH, sheet_name=first_sheet, header=1, engine='pyxlsb')
            print(f"Loaded MD06. Shape: {df_md06.shape}")
    except Exception as e:
        print("Error loading MD06.xlsb:", e)
else:
    print("MD_06.xlsb not found.")


# =========================================
# --- 1. PROCESSING INVENTORY (INV14) ---
# =========================================
print("\n=========================================")
print("--- 1. PROCESSING INVENTORY (INV14) ---")
print("=========================================")
inv_files = get_files_last_7_days_by_mtime(INV_DIR, "*.parquet")
print(f"Found {len(inv_files)} files modified in the last 7 days.")

dfs_inv = []
for f in inv_files:
    fname = os.path.basename(f)
    mdate = datetime.fromtimestamp(os.path.getmtime(f)).date()
    rep_date = extract_reporting_date(fname)
    
    try:
        df = pd.read_parquet(f)
        df['Ngày báo cáo'] = rep_date
        dfs_inv.append(df)
    except Exception as e:
        print(f"  [FAILED]  Read {fname} (Modified: {mdate}) - Error: {e}")

if dfs_inv:
    df_inventory = pd.concat(dfs_inv, ignore_index=True)
    print("Combined Inventory shape before operations:", df_inventory.shape)
    
    # Map DC Name using D_DC
    if not df_dc.empty:
        df_dc_lookup = df_dc[['Mã DC', 'Tên DC', 'Khu vực']].rename(columns={
            'Mã DC': 'Ware house',
            'Tên DC': 'D_DC_Tên DC',
            'Khu vực': 'D_DC_Khu vực'
        })
        
        # Merge D_DC info
        df_inventory = df_inventory.merge(df_dc_lookup, on='Ware house', how='left')
        
        # Apply logic for "DC Name"
        def compute_dc_name(row):
            sub = str(row['Sub']) if pd.notna(row['Sub']) else ''
            khu_vuc = str(row['D_DC_Khu vực']) if pd.notna(row['D_DC_Khu vực']) else ''
            locator = str(row['Locator']) if pd.notna(row['Locator']) else ''
            dc_name_raw = row['D_DC_Tên DC']
            
            if pd.isna(dc_name_raw):
                return dc_name_raw
                
            if sub == "SS4" and khu_vuc == "3. Miền Đông":
                return "08.1. Kho Vân Trúc"
            elif locator == "DROP_EX1" and dc_name_raw == "08. Kerry":
                return "10. TBS"
            elif sub in ["SM1", "SM2", "SM0"] and dc_name_raw in ["08. Kerry", "10. TBS"]:
                return "08.1. Kho Vân Trúc"
            elif sub == "SS3" and dc_name_raw == "08. Kerry":
                return "08.2. Kho BW"
            else:
                return dc_name_raw
                
        df_inventory['DC Name'] = df_inventory.apply(compute_dc_name, axis=1)
        # Drop temp columns
        df_inventory = df_inventory.drop(columns=['D_DC_Tên DC', 'D_DC_Khu vực'])
    else:
        df_inventory['DC Name'] = None
        
    # Map MD06 data into Inventory
    if not df_md06.empty:
        df_inventory['Mã Item'] = df_inventory['Mã Item'].astype(str).str.strip()
        df_md06_temp = df_md06.copy()
        df_md06_temp['Item No'] = df_md06_temp['Item No'].astype(str).str.strip()
        
        # Merge all MD06 columns
        df_inventory = df_inventory.merge(df_md06_temp, left_on='Mã Item', right_on='Item No', how='left')
        print("Mapped MD06 data to Inventory!")
    else:
        print("Skipping MD06 mapping as MD06 dataframe is empty.")
        
    # Filter only "DC Name" = "08. Kerry"
    df_inventory = df_inventory[df_inventory['DC Name'] == "08. Kerry"].reset_index(drop=True)
    print("Filtered Inventory for '08. Kerry'. Shape:", df_inventory.shape)

    # Filter only "Pallet chồng đôi" = null/blank for terminal simulation run
    df_racking_inv = df_inventory[df_inventory['Pallet chồng đôi'].isna()].reset_index(drop=True)
    
    # Safe conversion of "Số lượng Pallet"
    df_inventory['Số lượng Pallet'] = pd.to_numeric(
        df_inventory['Số lượng Pallet'].astype(str).str.replace(',', ''), errors='coerce'
    ).fillna(0.0)
    df_racking_inv['Số lượng Pallet'] = pd.to_numeric(
        df_racking_inv['Số lượng Pallet'].astype(str).str.replace(',', ''), errors='coerce'
    ).fillna(0.0)

else:
    df_inventory = pd.DataFrame()
    df_racking_inv = pd.DataFrame()
    print("[WARNING] Inventory dataset is empty.")


# =========================================
# --- 2. PROCESSING ACTUAL OUTBOUND (INV03) ---
# =========================================
print("\n=========================================")
print("--- 2. PROCESSING ACTUAL OUTBOUND (INV03) ---")
print("=========================================")
inv03_files = get_files_last_7_days_by_mtime(INV03_DIR, "*.parquet")
print(f"Found {len(inv03_files)} files modified in the last 7 days.")

dfs_inv03 = []
for f in inv03_files:
    fname = os.path.basename(f)
    mdate = datetime.fromtimestamp(os.path.getmtime(f)).date()
    try:
        df = pd.read_parquet(f)
        dfs_inv03.append(df)
    except Exception as e:
        print(f"  [FAILED]  Read {fname} (Modified: {mdate}) - Error: {e}")

if dfs_inv03:
    df_inv03 = pd.concat(dfs_inv03, ignore_index=True)
    print("Combined INV03 shape before operations:", df_inv03.shape)
    
    # Map DC Name from D_DC (LOOKUP VALUE on ORG CODE)
    if not df_dc.empty:
        df_dc_lookup_inv03 = df_dc[['Mã DC', 'Tên DC']].rename(columns={
            'Mã DC': 'ORG CODE',
            'Tên DC': 'DC Name'
        })
        
        # Convert keys to string and strip
        df_inv03['ORG CODE'] = df_inv03['ORG CODE'].astype(str).str.strip()
        df_dc_lookup_inv03['ORG CODE'] = df_dc_lookup_inv03['ORG CODE'].astype(str).str.strip()
        
        # Merge
        df_inv03 = df_inv03.merge(df_dc_lookup_inv03, on='ORG CODE', how='left')
        print("Mapped 'DC Name' to INV03!")
    else:
        df_inv03['DC Name'] = None
        
    # Filter only "DC Name" = "08. Kerry"
    df_inv03 = df_inv03[df_inv03['DC Name'] == "08. Kerry"].reset_index(drop=True)
    print("Filtered INV03 for '08. Kerry'. Shape:", df_inv03.shape)
    
    # Map MD06 "Pallet chồng đôi" to INV03
    if not df_md06.empty:
        df_inv03['Mã SP'] = df_inv03['Mã SP'].astype(str).str.strip()
        df_md06_key = df_md06[['Item No', 'Pallet chồng đôi']].copy()
        df_md06_key['Item No'] = df_md06_key['Item No'].astype(str).str.strip()
        
        df_inv03 = df_inv03.merge(df_md06_key, left_on='Mã SP', right_on='Item No', how='left')
        print("Mapped 'Pallet chồng đôi' to INV03!")
    else:
        df_inv03['Pallet chồng đôi'] = None

    # Map DRP/D2C column (if "Địa chỉ giao hàng" is null/blank -> DRP, else D2C)
    df_inv03['DRP/D2C'] = np.where(df_inv03['Địa chỉ giao hàng'].isna() | (df_inv03['Địa chỉ giao hàng'].astype(str).str.strip() == ''), 'DRP', 'D2C')

    # Safe conversion of "Số lượng" and "Pallet" in INV03
    df_inv03['Số lượng'] = pd.to_numeric(
        df_inv03['Số lượng'].astype(str).str.replace(',', ''), errors='coerce'
    ).fillna(0.0)
    df_inv03['Pallet'] = pd.to_numeric(
        df_inv03['Pallet'], errors='coerce'
    ).fillna(0.0)
    
else:
    df_inv03 = pd.DataFrame()
    print("[WARNING] INV03 dataset is empty.")


# =========================================
# --- 3. SIMULATIONS AND REPORTS ---
# =========================================
print("\n=========================================")
print("--- 3. SIMULATIONS AND ANALYSIS REPORTS ---")
print("=========================================")

# 3.1. Racking simulation table
if not df_racking_inv.empty:
    print("\n>>> 3.1. Racking Capacity Simulation Report (by Ngày báo cáo):")
    df_grouped = df_racking_inv.groupby(['Ngày báo cáo', 'Mã Item', 'Lot number'])['Số lượng Pallet'].sum().reset_index()
    df_grouped['locations_needed'] = np.ceil(df_grouped['Số lượng Pallet'] / 8.0).astype(int)
    
    df_sim = df_grouped.groupby('Ngày báo cáo')['locations_needed'].sum().reset_index()
    df_sim['Total Racking Capacity'] = 624
    df_sim['Thừa/Thiếu Racking'] = 624 - df_sim['locations_needed']
    df_sim['Utilization %'] = (df_sim['locations_needed'] / 624.0 * 100).round(2)
    print(df_sim.to_string(index=False, formatters={'Utilization %': '{:,.2f}%'.format}))
else:
    print("\n[WARNING] Cannot run simulation: racking inventory is empty.")

# 3.2. Outbound racking percentage report
if not df_inv03.empty:
    print("\n>>> 3.2. Outbound Racking Flow Analysis (by Ngày xuất):")
    df_inv03['is_racking'] = df_inv03['Pallet chồng đôi'].isna()
    df_inv03['racking_qty'] = np.where(df_inv03['is_racking'], df_inv03['Số lượng'], 0.0)
    df_inv03['racking_pallet'] = np.where(df_inv03['is_racking'], df_inv03['Pallet'], 0.0)
    
    df_pivot = df_inv03.groupby('Ngày xuất').agg(
        total_qty=('Số lượng', 'sum'),
        racking_qty=('racking_qty', 'sum'),
        total_pallets=('Pallet', 'sum'),
        racking_pallets=('racking_pallet', 'sum')
    ).reset_index()
    
    df_pivot['% Item in Racking'] = (df_pivot['racking_qty'] / df_pivot['total_qty'] * 100).round(2)
    df_pivot['% Pallet in Racking'] = (df_pivot['racking_pallets'] / df_pivot['total_pallets'] * 100).round(2)
    print(df_pivot[['Ngày xuất', 'total_qty', 'racking_qty', '% Item in Racking', 'total_pallets', 'racking_pallets', '% Pallet in Racking']].to_string(index=False, formatters={
        '% Item in Racking': '{:,.2f}%'.format,
        '% Pallet in Racking': '{:,.2f}%'.format
    }))
else:
    print("\n[WARNING] Cannot compute outbound racking percentage: INV03 is empty.")


# =========================================
# --- 4. EXPORT DATA FOR INTERACTIVE HTML ---
# =========================================
print("\n=========================================")
print("--- 4. GENERATING INTERACTIVE SIMULATION WEB PAGE ---")
print("=========================================")

# Get the list of 7 dates for Inventory
dates_inv = sorted(df_inventory['Ngày báo cáo'].dropna().unique())
dates_inv_str = [d.strftime('%Y-%m-%d') for d in dates_inv]

# Aggregate unique Item details
item_groups = df_inventory.groupby('Mã Item')
items_data = []

for item_code, group in item_groups:
    # Get details
    item_name = str(group['Tên Item'].iloc[0]) if 'Tên Item' in group.columns and pd.notna(group['Tên Item'].iloc[0]) else ''
    p_chong_doi = group['Pallet chồng đôi'].iloc[0] if 'Pallet chồng đôi' in group.columns else None
    p_chong_doi_str = 'N/A' if pd.isna(p_chong_doi) else str(p_chong_doi)
    
    # Calculate daily pallet stocks
    daily_p = {}
    for d in dates_inv:
        d_str = d.strftime('%Y-%m-%d')
        date_sum = group[group['Ngày báo cáo'] == d]['Số lượng Pallet'].sum()
        daily_p[d_str] = round(float(date_sum), 2)
        
    avg_p = round(float(np.mean(list(daily_p.values()))), 2)
    
    items_data.append({
        'item_code': str(item_code),
        'item_name': item_name,
        'pallet_chong_doi': p_chong_doi_str,
        'daily_pallets': daily_p,
        'avg_pallets': avg_p,
        'default_checked': True if p_chong_doi_str == 'N/A' else False
    })

# Aggregate lot-level data for Racking Capacity Simulation
lot_groups = df_inventory.groupby(['Ngày báo cáo', 'Mã Item', 'Lot number'])['Số lượng Pallet'].sum().reset_index()
lot_data = []
for idx, row in lot_groups.iterrows():
    d_str = row['Ngày báo cáo'].strftime('%Y-%m-%d')
    lot_data.append({
        'date': d_str,
        'item_code': str(row['Mã Item']),
        'lot_number': str(row['Lot number']),
        'pallets': round(float(row['Số lượng Pallet']), 2)
    })

# Aggregate outbound transaction data
ob_groups = df_inv03.groupby(['Ngày xuất', 'Mã SP', 'DRP/D2C']).agg(
    qty=('Số lượng', 'sum'),
    pallets=('Pallet', 'sum')
).reset_index()
ob_data = []
for idx, row in ob_groups.iterrows():
    ob_data.append({
        'date': str(row['Ngày xuất']),
        'item_code': str(row['Mã SP']),
        'drp_d2c': str(row['DRP/D2C']),
        'qty': round(float(row['qty']), 2),
        'pallets': round(float(row['pallets']), 2)
    })

# Gather Detailed Inventory Rows for Sheet 1
inv_detail_cols = ['Ngày báo cáo', 'Mã Item', 'Tên Item', 'Locator', 'Lot number', 'Số lượng tồn 1', 'Số lượng Pallet', 'Pallet chồng đôi']
existing_inv_cols = [c for c in inv_detail_cols if c in df_inventory.columns]
df_inv_detail = df_inventory[existing_inv_cols].copy()
df_inv_detail['Ngày báo cáo'] = df_inv_detail['Ngày báo cáo'].apply(lambda x: x.strftime('%Y-%m-%d') if pd.notna(x) else '')
df_inv_detail = df_inv_detail.fillna('')
inventory_detail_list = df_inv_detail.to_dict(orient='records')

# Gather Detailed Outbound Rows for Sheet 2
inv03_detail_cols = ['Ngày xuất', 'Mã SP', 'Tên SP', 'Số lượng', 'Pallet', 'Lot', 'Phiếu xuất', 'ORG CODE', 'Pallet chồng đôi', 'DRP/D2C']
existing_inv03_cols = [c for c in inv03_detail_cols if c in df_inv03.columns]
df_inv03_detail = df_inv03[existing_inv03_cols].copy()
df_inv03_detail = df_inv03_detail.fillna('')
inv03_detail_list = df_inv03_detail.to_dict(orient='records')

# HTML File path
html_path = r"c:\Users\phatvt\OneDrive\Image\Hình ảnh\ThanhPhat_Masan\DC FMCG\org\Racking_Ops\Racking_ops_sim.html"

# HTML Template
html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Warehouse Racking Simulation Dashboard</title>
    <!-- Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <!-- SheetJS (XLSX Export Library) -->
    <script src="https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js"></script>
    
    <style>
        :root {
            --bg-color: #0b0f19;
            --card-bg: rgba(22, 28, 45, 0.65);
            --border-color: rgba(255, 255, 255, 0.08);
            --text-main: #f3f4f6;
            --text-muted: #9ca3af;
            --primary: #3b82f6;
            --primary-hover: #2563eb;
            --accent-emerald: #10b981;
            --accent-amber: #f59e0b;
            --accent-rose: #f43f5e;
            --card-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Outfit', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            padding: 24px;
            background-image: 
                radial-gradient(at 0% 0%, rgba(59, 130, 246, 0.1) 0px, transparent 50%),
                radial-gradient(at 50% 0%, rgba(16, 185, 129, 0.05) 0px, transparent 50%),
                radial-gradient(at 100% 0%, rgba(245, 158, 11, 0.05) 0px, transparent 50%);
            background-attachment: fixed;
            min-height: 100vh;
        }

        .dashboard-container {
            max-width: 1600px;
            margin: 0 auto;
        }

        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
            padding-bottom: 16px;
            border-bottom: 1px solid var(--border-color);
        }

        .header-title h1 {
            font-size: 28px;
            font-weight: 700;
            background: linear-gradient(135deg, #3b82f6, #10b981, #f59e0b);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .header-title p {
            color: var(--text-muted);
            font-size: 14px;
            margin-top: 4px;
        }

        /* KPI Panel */
        .kpis-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 20px;
            margin-bottom: 24px;
        }

        .kpi-card {
            background: var(--card-bg);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 20px;
            box-shadow: var(--card-shadow);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }

        .kpi-card .kpi-label {
            font-size: 14px;
            color: var(--text-muted);
            font-weight: 500;
        }

        .kpi-card .kpi-value {
            font-size: 32px;
            font-weight: 700;
            margin: 10px 0 4px 0;
        }

        .kpi-card .kpi-subtext {
            font-size: 12px;
            color: var(--text-muted);
        }

        .kpi-blue { border-left: 4px solid var(--primary); }
        .kpi-emerald { border-left: 4px solid var(--accent-emerald); }
        .kpi-amber { border-left: 4px solid var(--accent-amber); }
        .kpi-rose { border-left: 4px solid var(--accent-rose); }

        /* Main Workspace Grid */
        .workspace-grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 24px;
        }

        @media (min-width: 1200px) {
            .workspace-grid {
                grid-template-columns: 3fr 2fr;
            }
        }

        .glass-card {
            background: var(--card-bg);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 24px;
            box-shadow: var(--card-shadow);
            margin-bottom: 24px;
        }

        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            padding-bottom: 12px;
        }

        .card-header h2 {
            font-size: 18px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        /* Table Styles */
        .table-wrapper {
            width: 100%;
            overflow-x: auto;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            text-align: left;
            font-size: 14px;
        }

        th {
            color: var(--text-muted);
            font-weight: 600;
            padding: 12px 16px;
            border-bottom: 1px solid rgba(255,255,255,0.08);
            cursor: pointer;
            user-select: none;
            transition: color 0.2s;
        }

        th:hover {
            color: var(--text-main);
        }

        th .sort-icon {
            margin-left: 6px;
            font-size: 12px;
            display: inline-block;
        }

        td {
            padding: 12px 16px;
            border-bottom: 1px solid rgba(255,255,255,0.04);
            color: #d1d5db;
        }

        tr:hover td {
            background-color: rgba(255,255,255,0.02);
        }

        /* Badge Styles */
        .badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 9999px;
            font-size: 11px;
            font-weight: 500;
            text-transform: uppercase;
        }

        .badge-na {
            background-color: rgba(156, 163, 175, 0.15);
            color: #d1d5db;
        }

        .badge-double {
            background-color: rgba(245, 158, 11, 0.15);
            color: #f59e0b;
        }

        /* Form Controls */
        .controls-row {
            display: flex;
            flex-wrap: wrap;
            gap: 16px;
            align-items: center;
            margin-bottom: 16px;
        }

        .search-box {
            flex: 1;
            min-width: 250px;
            position: relative;
        }

        .search-box input {
            width: 100%;
            padding: 10px 16px;
            background: rgba(0, 0, 0, 0.2);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            color: var(--text-main);
            font-size: 14px;
            outline: none;
            transition: border-color 0.2s;
        }

        .search-box input:focus {
            border-color: var(--primary);
        }

        .select-filter {
            padding: 10px 16px;
            background: rgba(0, 0, 0, 0.2);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            color: var(--text-main);
            font-size: 14px;
            outline: none;
            cursor: pointer;
        }

        .btn {
            padding: 10px 16px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            border: 1px solid transparent;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .btn-primary {
            background-color: var(--primary);
            color: #fff;
        }

        .btn-primary:hover {
            background-color: var(--primary-hover);
        }

        .btn-outline {
            background-color: transparent;
            border-color: var(--border-color);
            color: var(--text-main);
        }

        .btn-outline:hover {
            background-color: rgba(255,255,255,0.05);
            border-color: var(--text-muted);
        }

        .btn-success {
            background-color: var(--accent-emerald);
            color: #fff;
        }

        .btn-success:hover {
            background-color: #059669;
        }

        /* Checkbox custom style */
        .checkbox-cell {
            text-align: center;
            width: 50px;
        }

        input[type="checkbox"] {
            width: 18px;
            height: 18px;
            accent-color: var(--primary);
            cursor: pointer;
        }

        /* Pagination */
        .pagination-container {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 16px;
            padding-top: 16px;
            border-top: 1px solid rgba(255,255,255,0.05);
        }

        .pagination-info {
            font-size: 14px;
            color: var(--text-muted);
        }

        .pagination-buttons {
            display: flex;
            gap: 8px;
        }

        /* Charts Layout */
        .charts-grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 24px;
            margin-bottom: 24px;
        }

        @media (min-width: 992px) {
            .charts-grid {
                grid-template-columns: 1fr 1fr;
            }
        }

        .chart-container {
            position: relative;
            height: 320px;
            width: 100%;
        }

        /* Table highlights */
        .text-rose { color: var(--accent-rose) !important; font-weight: 600; }
        .text-emerald { color: var(--accent-emerald) !important; font-weight: 600; }
        
    </style>
</head>
<body>

<div class="dashboard-container">
    <!-- Header -->
    <header>
        <div class="header-title">
            <h1>Warehouse Racking Operations Simulator</h1>
            <p>Interactive what-if simulation tool for racking capacity and flow analysis (Kerry DC)</p>
        </div>
        <div style="display: flex; gap: 8px; align-items: center;">
            <select class="select-filter" id="drpD2cFilter" onchange="handleDrpD2cChange()">
                <option value="ALL">Outbound: All</option>
                <option value="DRP">Outbound: DRP only</option>
                <option value="D2C">Outbound: D2C only</option>
            </select>
            <button class="btn btn-outline" onclick="resetToDefault()">Reset to Default</button>
            <button class="btn btn-primary" onclick="selectAllFiltered(true)">Select All</button>
            <button class="btn btn-outline" onclick="selectAllFiltered(false)">Clear All</button>
            <button class="btn btn-success" onclick="exportDetailedExcel()">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg>
                Xuất File Excel Chi Tiết
            </button>
        </div>
    </header>

    <!-- KPIs -->
    <div class="kpis-grid">
        <div class="kpi-card kpi-blue">
            <span class="kpi-label">Total Selected SKUs</span>
            <span class="kpi-value" id="kpi-selected-skus">0</span>
            <span class="kpi-subtext" id="kpi-total-skus">Out of 0 total SKUs</span>
        </div>
        <div class="kpi-card kpi-emerald">
            <span class="kpi-label">Avg Racking Utilization</span>
            <span class="kpi-value" id="kpi-avg-utilization">0.00%</span>
            <span class="kpi-subtext">Target Capacity: 624 locations</span>
        </div>
        <div class="kpi-card kpi-amber">
            <span class="kpi-label">Avg Outbound Flow (Pallet)</span>
            <span class="kpi-value" id="kpi-avg-ob-pallet">0.00%</span>
            <span class="kpi-subtext">Percentage shipped from rack</span>
        </div>
        <div class="kpi-card kpi-rose">
            <span class="kpi-label">Avg Outbound Flow (Item)</span>
            <span class="kpi-value" id="kpi-avg-ob-item">0.00%</span>
            <span class="kpi-subtext">Percentage shipped from rack</span>
        </div>
    </div>

    <!-- Charts -->
    <div class="charts-grid">
        <div class="glass-card">
            <div class="card-header">
                <h2>Racking Location Capacity vs Needs</h2>
            </div>
            <div class="chart-container">
                <canvas id="capacityChart"></canvas>
            </div>
        </div>
        <div class="glass-card">
            <div class="card-header">
                <h2>Outbound Flow Percentage from Rack</h2>
            </div>
            <div class="chart-container">
                <canvas id="flowChart"></canvas>
            </div>
        </div>
    </div>

    <!-- Workspace -->
    <div class="workspace-grid">
        <!-- SKU Selection Panel -->
        <div class="glass-card">
            <div class="card-header">
                <h2>SKU Inventory Selection Table</h2>
                <span style="font-size: 13px; color: var(--text-muted);" id="table-row-count">Showing 0 of 0 SKUs</span>
            </div>

            <!-- Search and filters -->
            <div class="controls-row">
                <div class="search-box">
                    <input type="text" id="searchInput" placeholder="Search by SKU code or name..." oninput="handleSearchChange()">
                </div>
                <select class="select-filter" id="chongDoiFilter" onchange="handleFilterChange()">
                    <option value="ALL">Pallet chồng đôi: All</option>
                    <option value="NA">Pallet chồng đôi: null/blank</option>
                    <option value="Y">Pallet chồng đôi: Y</option>
                </select>
                <select class="select-filter" id="pageSizeSelect" onchange="handlePageSizeChange()">
                    <option value="10">10 per page</option>
                    <option value="25">25 per page</option>
                    <option value="50" selected>50 per page</option>
                    <option value="100">100 per page</option>
                </select>
            </div>

            <!-- Table -->
            <div class="table-wrapper">
                <table id="skuTable">
                    <thead>
                        <tr id="skuTableHeaderRow">
                            <th class="checkbox-cell"><input type="checkbox" id="selectAllHeader" onclick="toggleSelectAllPage(this)"></th>
                            <th onclick="handleSort('item_code')">Mã Item <span class="sort-icon" id="sort-item_code">↕</span></th>
                            <th onclick="handleSort('item_name')">Tên Item <span class="sort-icon" id="sort-item_name">↕</span></th>
                            <th onclick="handleSort('pallet_chong_doi')">Chồng đôi <span class="sort-icon" id="sort-pallet_chong_doi">↕</span></th>
                            <th onclick="handleSort('avg_pallets')">Tồn trung bình <span class="sort-icon" id="sort-avg_pallets">↕</span></th>
                        </tr>
                    </thead>
                    <tbody id="skuTableBody">
                        <!-- Dynamic content -->
                    </tbody>
                </table>
            </div>

            <!-- Pagination -->
            <div class="pagination-container">
                <div class="pagination-info" id="paginationInfo">
                    Showing 1 to 50 of 500 SKUs
                </div>
                <div class="pagination-buttons">
                    <button class="btn btn-outline" onclick="changePage(-1)" id="prevPageBtn">Prev</button>
                    <button class="btn btn-outline" onclick="changePage(1)" id="nextPageBtn">Next</button>
                </div>
            </div>
        </div>

        <!-- Right side reports -->
        <div>
            <!-- Simulation report table -->
            <div class="glass-card" style="margin-bottom: 24px;">
                <div class="card-header">
                    <h2>Racking Capacity Simulation</h2>
                </div>
                <div class="table-wrapper">
                    <table>
                        <thead>
                            <tr>
                                <th>Ngày báo cáo</th>
                                <th>Location cần</th>
                                <th>Sức chứa</th>
                                <th>Thừa/Thiếu</th>
                                <th>Hiệu suất %</th>
                            </tr>
                        </thead>
                        <tbody id="simReportBody">
                            <!-- Dynamic content -->
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Outbound flow report table -->
            <div class="glass-card">
                <div class="card-header">
                    <h2>Outbound Flow Analysis</h2>
                </div>
                <div class="table-wrapper">
                    <table>
                        <thead>
                            <tr>
                                <th>Ngày xuất</th>
                                <th>Tổng Pallet</th>
                                <th>Pallet Rack</th>
                                <th>% Pallet</th>
                                <th>% Qty (Item)</th>
                            </tr>
                        </thead>
                        <tbody id="flowReportBody">
                            <!-- Dynamic content -->
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
    // Embedded Data Arrays injected by python script
    const datesInvList = __DATES_INV__;
    const itemsData = __ITEMS_DATA__;
    const lotData = __LOT_DATA__;
    const obData = __OB_DATA__;
    const inventoryDetail = __INVENTORY_DETAIL__;
    const inv03Detail = __INV03_DETAIL__;

    // Selected Items tracking Set
    let checkedItems = new Set();
    
    // UI State
    let currentPage = 1;
    let pageSize = 50;
    let searchQuery = '';
    let filterChongDoi = 'ALL';
    let currentSortColumn = 'avg_pallets';
    let currentSortDir = 'desc';

    // Charts objects
    let capacityChartInstance = null;
    let flowChartInstance = null;

    // Initialize Page
    function init() {
        // Dynamic generation of header columns for each date
        const headerRow = document.getElementById('skuTableHeaderRow');
        datesInvList.forEach(d => {
            const th = document.createElement('th');
            th.innerText = d.substring(5); // Show mm-dd
            th.onclick = function() { handleSortDate(d); };
            const span = document.createElement('span');
            span.className = 'sort-icon';
            span.id = 'sort-date-' + d;
            span.innerText = ' ↕';
            th.appendChild(span);
            headerRow.insertBefore(th, headerRow.lastElementChild);
        });

        // Set default checked items
        itemsData.forEach(item => {
            if (item.default_checked) {
                checkedItems.add(item.item_code);
            }
        });

        updateSortIcons();
        recalculateAndRender();
    }

    function resetToDefault() {
        checkedItems.clear();
        itemsData.forEach(item => {
            if (item.default_checked) {
                checkedItems.add(item.item_code);
            }
        });
        recalculateAndRender();
    }

    function selectAllFiltered(shouldSelect) {
        const filtered = getFilteredAndSortedItems();
        filtered.forEach(item => {
            if (shouldSelect) {
                checkedItems.add(item.item_code);
            } else {
                checkedItems.delete(item.item_code);
            }
        });
        recalculateAndRender();
    }

    // Filtering & Sorting logic
    function getFilteredAndSortedItems() {
        let result = itemsData.filter(item => {
            const matchesSearch = item.item_code.toLowerCase().includes(searchQuery.toLowerCase()) || 
                                  item.item_name.toLowerCase().includes(searchQuery.toLowerCase());
            
            let matchesFilter = true;
            if (filterChongDoi === 'NA') {
                matchesFilter = item.pallet_chong_doi === 'N/A';
            } else if (filterChongDoi === 'Y') {
                matchesFilter = item.pallet_chong_doi === 'Y';
            }
            
            return matchesSearch && matchesFilter;
        });

        // Sort
        result.sort((a, b) => {
            let valA, valB;
            if (currentSortColumn.startsWith('date_')) {
                const dateKey = currentSortColumn.substring(5);
                valA = a.daily_pallets[dateKey] || 0;
                valB = b.daily_pallets[dateKey] || 0;
            } else {
                valA = a[currentSortColumn];
                valB = b[currentSortColumn];
            }

            if (typeof valA === 'number' && typeof valB === 'number') {
                return currentSortDir === 'asc' ? valA - valB : valB - valA;
            }
            
            valA = String(valA).toLowerCase();
            valB = String(valB).toLowerCase();
            if (valA < valB) return currentSortDir === 'asc' ? -1 : 1;
            if (valA > valB) return currentSortDir === 'asc' ? 1 : -1;
            return 0;
        });

        return result;
    }

    // Recalculations
    function recalculateAndRender() {
        // 1. Calculate Racking Capacity Simulation per date
        const capacityResults = {};
        datesInvList.forEach(d => {
            capacityResults[d] = 0;
        });

        lotData.forEach(lot => {
            if (checkedItems.has(lot.item_code)) {
                const locations = Math.ceil(lot.pallets / 8.0);
                if (capacityResults[lot.date] !== undefined) {
                    capacityResults[lot.date] += locations;
                }
            }
        });

        // Render Capacity Simulation Table
        const simBody = document.getElementById('simReportBody');
        simBody.innerHTML = '';
        
        let sumUtilization = 0;
        const capChartLabels = [];
        const capChartNeeds = [];

        datesInvList.forEach(d => {
            const needed = capacityResults[d] || 0;
            const diff = 624 - needed;
            const util = (needed / 624.0 * 100);
            sumUtilization += util;
            
            capChartLabels.push(d);
            capChartNeeds.push(needed);

            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${d}</td>
                <td style="font-weight: 500;">${needed}</td>
                <td style="color: var(--text-muted);">624</td>
                <td class="${diff < 0 ? 'text-rose' : 'text-emerald'}">${diff}</td>
                <td class="${util > 100 ? 'text-rose' : ''}" style="font-weight:600;">${util.toFixed(2)}%</td>
            `;
            simBody.appendChild(tr);
        });

        // 2. Calculate Outbound Racking Analysis per date
        const drpD2cFilterVal = document.getElementById('drpD2cFilter').value;
        const outboundResults = {};
        obData.forEach(ob => {
            if (drpD2cFilterVal !== 'ALL' && ob.drp_d2c !== drpD2cFilterVal) {
                return;
            }
            if (!outboundResults[ob.date]) {
                outboundResults[ob.date] = { total_qty: 0, racking_qty: 0, total_pallets: 0, racking_pallets: 0 };
            }
            outboundResults[ob.date].total_qty += ob.qty;
            outboundResults[ob.date].total_pallets += ob.pallets;
            if (checkedItems.has(ob.item_code)) {
                outboundResults[ob.date].racking_qty += ob.qty;
                outboundResults[ob.date].racking_pallets += ob.pallets;
            }
        });

        const flowBody = document.getElementById('flowReportBody');
        flowBody.innerHTML = '';
        
        let sumFlowPallet = 0;
        let sumFlowItem = 0;
        let flowDaysCount = 0;
        
        const flowChartLabels = [];
        const flowChartPallets = [];
        const flowChartItems = [];

        const obDates = Object.keys(outboundResults).sort();
        obDates.forEach(d => {
            const res = outboundResults[d];
            const pctPallet = res.total_pallets > 0 ? (res.racking_pallets / res.total_pallets * 100) : 0;
            const pctItem = res.total_qty > 0 ? (res.racking_qty / res.total_qty * 100) : 0;
            
            sumFlowPallet += pctPallet;
            sumFlowItem += pctItem;
            flowDaysCount++;

            flowChartLabels.push(d);
            flowChartPallets.push(pctPallet);
            flowChartItems.push(pctItem);

            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${d}</td>
                <td>${res.total_pallets.toLocaleString(undefined, {minimumFractionDigits: 1, maximumFractionDigits: 1})}</td>
                <td>${res.racking_pallets.toLocaleString(undefined, {minimumFractionDigits: 1, maximumFractionDigits: 1})}</td>
                <td style="font-weight: 600; color: var(--primary);">${pctPallet.toFixed(2)}%</td>
                <td style="font-weight: 600; color: var(--accent-emerald);">${pctItem.toFixed(2)}%</td>
            `;
            flowBody.appendChild(tr);
        });

        // Update KPIs
        document.getElementById('kpi-selected-skus').innerText = checkedItems.size;
        document.getElementById('kpi-total-skus').innerText = `Out of ${itemsData.length} total SKUs`;
        document.getElementById('kpi-avg-utilization').innerText = `${(sumUtilization / datesInvList.length).toFixed(2)}%`;
        if (flowDaysCount > 0) {
            document.getElementById('kpi-avg-ob-pallet').innerText = `${(sumFlowPallet / flowDaysCount).toFixed(2)}%`;
            document.getElementById('kpi-avg-ob-item').innerText = `${(sumFlowItem / flowDaysCount).toFixed(2)}%`;
        }

        // Render Table & Pagination
        renderSKUTable();
        
        // Update Charts
        updateCharts(capChartLabels, capChartNeeds, flowChartLabels, flowChartPallets, flowChartItems);
    }

    // Render SKU Selection Table
    function renderSKUTable() {
        const filteredSorted = getFilteredAndSortedItems();
        const body = document.getElementById('skuTableBody');
        body.innerHTML = '';

        document.getElementById('table-row-count').innerText = `Showing ${filteredSorted.length} of ${itemsData.length} SKUs`;

        const totalItems = filteredSorted.length;
        const totalPages = Math.ceil(totalItems / pageSize) || 1;
        if (currentPage > totalPages) currentPage = totalPages;
        if (currentPage < 1) currentPage = 1;

        const startIndex = (currentPage - 1) * pageSize;
        const endIndex = Math.min(startIndex + pageSize, totalItems);

        const pageItems = filteredSorted.slice(startIndex, endIndex);

        pageItems.forEach(item => {
            const isChecked = checkedItems.has(item.item_code);
            const badgeClass = item.pallet_chong_doi === 'Y' ? 'badge-double' : 'badge-na';
            
            // Build date columns cell HTML
            let dateCellsHtml = '';
            datesInvList.forEach(d => {
                const val = item.daily_pallets[d] || 0;
                dateCellsHtml += `<td style="text-align: right; color: var(--text-muted);">${val > 0 ? val.toFixed(1) : '-'}</td>`;
            });
            
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td class="checkbox-cell"><input type="checkbox" ${isChecked ? 'checked' : ''} onclick="toggleItem('${item.item_code}')"></td>
                <td style="font-family: monospace; font-weight: 500;">${item.item_code}</td>
                <td style="max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${item.item_name}">${item.item_name}</td>
                <td><span class="badge ${badgeClass}">${item.pallet_chong_doi}</span></td>
                ${dateCellsHtml}
                <td style="font-weight: 500; text-align: right; color: #fff; padding-right: 16px;">${item.avg_pallets.toFixed(1)}</td>
            `;
            body.appendChild(tr);
        });

        // Update pagination UI
        document.getElementById('paginationInfo').innerText = totalItems > 0 
            ? `Showing ${startIndex + 1} to ${endIndex} of ${totalItems} SKUs`
            : `Showing 0 to 0 of 0 SKUs`;

        document.getElementById('prevPageBtn').disabled = currentPage === 1;
        document.getElementById('nextPageBtn').disabled = currentPage === totalPages;
        
        // Update select all header checkbox state
        const allPageChecked = pageItems.length > 0 && pageItems.every(item => checkedItems.has(item.item_code));
        document.getElementById('selectAllHeader').checked = allPageChecked;
    }

    // Checkbox click handler
    function toggleItem(code) {
        if (checkedItems.has(code)) {
            checkedItems.delete(code);
        } else {
            checkedItems.add(code);
        }
        recalculateAndRender();
    }

    function toggleSelectAllPage(headerCheckbox) {
        const filteredSorted = getFilteredAndSortedItems();
        const startIndex = (currentPage - 1) * pageSize;
        const endIndex = Math.min(startIndex + pageSize, filteredSorted.length);
        const pageItems = filteredSorted.slice(startIndex, endIndex);

        pageItems.forEach(item => {
            if (headerCheckbox.checked) {
                checkedItems.add(item.item_code);
            } else {
                checkedItems.delete(item.item_code);
            }
        });
        recalculateAndRender();
    }

    // Search and filters handlers
    function handleSearchChange() {
        searchQuery = document.getElementById('searchInput').value;
        currentPage = 1;
        renderSKUTable();
    }

    // Filter by Double Stack Pallet
    function handleFilterChange() {
        filterChongDoi = document.getElementById('chongDoiFilter').value;
        currentPage = 1;
        renderSKUTable();
    }

    // Filter by DRP/D2C
    function handleDrpD2cChange() {
        currentPage = 1;
        recalculateAndRender();
    }

    function handlePageSizeChange() {
        pageSize = parseInt(document.getElementById('pageSizeSelect').value);
        currentPage = 1;
        renderSKUTable();
    }

    function changePage(direction) {
        currentPage += direction;
        renderSKUTable();
    }

    // Sort column handler
    function handleSort(column) {
        if (currentSortColumn === column) {
            currentSortDir = currentSortDir === 'asc' ? 'desc' : 'asc';
        } else {
            currentSortColumn = column;
            currentSortDir = 'desc';
        }
        currentPage = 1;
        updateSortIcons();
        renderSKUTable();
    }

    function handleSortDate(dateKey) {
        const column = 'date_' + dateKey;
        handleSort(column);
    }

    function updateSortIcons() {
        ['item_code', 'item_name', 'pallet_chong_doi', 'avg_pallets'].forEach(col => {
            const el = document.getElementById('sort-' + col);
            if (!el) return;
            if (col === currentSortColumn) {
                el.innerText = currentSortDir === 'asc' ? ' ▲' : ' ▼';
                el.style.opacity = '1';
                el.style.color = 'var(--primary)';
            } else {
                el.innerText = ' ↕';
                el.style.opacity = '0.4';
                el.style.color = '';
            }
        });

        datesInvList.forEach(d => {
            const el = document.getElementById('sort-date-' + d);
            if (!el) return;
            if (currentSortColumn === 'date_' + d) {
                el.innerText = currentSortDir === 'asc' ? ' ▲' : ' ▼';
                el.style.opacity = '1';
                el.style.color = 'var(--primary)';
            } else {
                el.innerText = ' ↕';
                el.style.opacity = '0.4';
                el.style.color = '';
            }
        });
    }

    // Charts updates using Chart.js
    function updateCharts(capLabels, capNeeds, flowLabels, flowPallets, flowItems) {
        if (capacityChartInstance) {
            capacityChartInstance.data.labels = capLabels;
            capacityChartInstance.data.datasets[0].data = capNeeds;
            capacityChartInstance.data.datasets[1].data = Array(capLabels.length).fill(624);
            capacityChartInstance.update();
        } else {
            const ctx = document.getElementById('capacityChart').getContext('2d');
            capacityChartInstance = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: capLabels,
                    datasets: [
                        {
                            label: 'Racking Locations Needed',
                            data: capNeeds,
                            borderColor: '#3b82f6',
                            backgroundColor: 'rgba(59, 130, 246, 0.12)',
                            borderWidth: 3,
                            fill: true,
                            tension: 0.3
                        },
                        {
                            label: 'Capacity (624)',
                            data: Array(capLabels.length).fill(624),
                            borderColor: '#f43f5e',
                            borderWidth: 2,
                            borderDash: [5, 5],
                            pointRadius: 0,
                            fill: false
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            labels: { color: '#f3f4f6', font: { family: 'Outfit' } }
                        }
                    },
                    scales: {
                        y: {
                            grid: { color: 'rgba(255, 255, 255, 0.05)' },
                            ticks: { color: '#9ca3af', font: { family: 'Outfit' } },
                            min: 0
                        },
                        x: {
                            grid: { display: false },
                            ticks: { color: '#9ca3af', font: { family: 'Outfit' } }
                        }
                    }
                }
            });
        }

        if (flowChartInstance) {
            flowChartInstance.data.labels = flowLabels;
            flowChartInstance.data.datasets[0].data = flowPallets;
            flowChartInstance.data.datasets[1].data = flowItems;
            flowChartInstance.update();
        } else {
            const ctx = document.getElementById('flowChart').getContext('2d');
            flowChartInstance = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: flowLabels,
                    datasets: [
                        {
                            label: '% Outbound Pallets in Rack',
                            data: flowPallets,
                            borderColor: '#8b5cf6',
                            borderWidth: 3,
                            fill: false,
                            tension: 0.3
                        },
                        {
                            label: '% Outbound Items in Rack',
                            data: flowItems,
                            borderColor: '#10b981',
                            borderWidth: 3,
                            fill: false,
                            tension: 0.3
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            labels: { color: '#f3f4f6', font: { family: 'Outfit' } }
                        }
                    },
                    scales: {
                        y: {
                            grid: { color: 'rgba(255, 255, 255, 0.05)' },
                            ticks: { 
                                color: '#9ca3af', 
                                font: { family: 'Outfit' },
                                callback: function(value) { return value + '%'; }
                            },
                            min: 0,
                            max: 100
                        },
                        x: {
                            grid: { display: false },
                            ticks: { color: '#9ca3af', font: { family: 'Outfit' } }
                        }
                    }
                }
            });
        }
    }

    // Helper to round numbers
    function roundNum(n) {
        return Math.round((n + Number.EPSILON) * 100) / 100;
    }

    // Export Details to Excel with 3 Sheets using SheetJS
    function exportDetailedExcel() {
        const drpD2cFilterVal = document.getElementById('drpD2cFilter').value;

        // 1. Prepare Inventory Detail rows (all rows, adding a column 'Có sử dụng rack')
        const detailedInv = inventoryDetail.map(row => {
            const isRacking = checkedItems.has(row['Mã Item']);
            return {
                'Ngày báo cáo': row['Ngày báo cáo'],
                'Mã Item': row['Mã Item'],
                'Tên Item': row['Tên Item'],
                'Locator': row['Locator'],
                'Lot number': row['Lot number'],
                'Số lượng tồn 1': parseFloat(row['Số lượng tồn 1']) || 0,
                'Số lượng Pallet': parseFloat(row['Số lượng Pallet']) || 0,
                'Pallet chồng đôi': row['Pallet chồng đôi'],
                'Có sử dụng rack': isRacking ? 'Có' : 'Không'
            };
        });

        // 2. Prepare Outbound Detail rows (filtered by selected DRP/D2C status, adding a column 'Có sử dụng rack')
        const rawDetailedInv03 = inv03Detail.map(row => {
            const isRacking = checkedItems.has(row['Mã SP']);
            return {
                'Ngày xuất': row['Ngày xuất'],
                'Mã SP': row['Mã SP'],
                'Tên SP': row['Tên SP'],
                'Số lượng': parseFloat(row['Số lượng']) || 0,
                'Pallet': parseFloat(row['Pallet']) || 0,
                'Lot': row['Lot'],
                'Phiếu xuất': row['Phiếu xuất'],
                'ORG CODE': row['ORG CODE'],
                'Pallet chồng đôi': row['Pallet chồng đôi'],
                'DRP/D2C': row['DRP/D2C'],
                'Có sử dụng rack': isRacking ? 'Có' : 'Không'
            };
        });

        const detailedInv03 = rawDetailedInv03.filter(row => {
            return drpD2cFilterVal === 'ALL' || row['DRP/D2C'] === drpD2cFilterVal;
        });

        // 3. Calculate Daily Inventory Summary
        const invSummary = [];
        datesInvList.forEach(d => {
            let rackPallets = 0;
            let nonRackPallets = 0;
            detailedInv.forEach(row => {
                if (row['Ngày báo cáo'] === d) {
                    const p = row['Số lượng Pallet'];
                    if (row['Có sử dụng rack'] === 'Có') {
                        rackPallets += p;
                    } else {
                        nonRackPallets += p;
                    }
                }
            });
            const total = rackPallets + nonRackPallets;
            invSummary.push({
                'Ngày báo cáo': d,
                'Pallet sử dụng rack': roundNum(rackPallets),
                'Pallet không sử dụng rack': roundNum(nonRackPallets),
                'Tổng cộng Pallet': roundNum(total),
                'Tỷ lệ sử dụng rack %': total > 0 ? roundNum((rackPallets / total) * 100) + '%' : '0%'
            });
        });

        // 4. Calculate Daily Outbound Summary
        const obDatesSet = new Set();
        detailedInv03.forEach(row => {
            if (row['Ngày xuất']) obDatesSet.add(row['Ngày xuất']);
        });
        const obDates = Array.from(obDatesSet).sort();

        const obSummary = [];
        obDates.forEach(d => {
            let rackPallets = 0;
            let nonRackPallets = 0;
            detailedInv03.forEach(row => {
                if (row['Ngày xuất'] === d) {
                    const p = row['Pallet'];
                    if (row['Có sử dụng rack'] === 'Có') {
                        rackPallets += p;
                    } else {
                        nonRackPallets += p;
                    }
                }
            });
            const total = rackPallets + nonRackPallets;
            obSummary.push({
                'Ngày xuất': d,
                'Pallet xuất từ rack': roundNum(rackPallets),
                'Pallet xuất không từ rack': roundNum(nonRackPallets),
                'Tổng cộng Pallet xuất': roundNum(total),
                'Tỷ lệ xuất từ rack %': total > 0 ? roundNum((rackPallets / total) * 100) + '%' : '0%'
            });
        });

        // 5. Construct Summary sheet rows
        const summaryRows = [];
        summaryRows.push(['TỔNG HỢP SỐ LƯỢNG PALLET TỒN KHO THEO NGÀY']);
        summaryRows.push(['Ngày báo cáo', 'Pallet sử dụng rack', 'Pallet không sử dụng rack (Block/Floor)', 'Tổng cộng Pallet tồn', 'Tỷ lệ sử dụng rack %']);
        invSummary.forEach(row => {
            summaryRows.push([
                row['Ngày báo cáo'], 
                row['Pallet sử dụng rack'], 
                row['Pallet không sử dụng rack'], 
                row['Tổng cộng Pallet'], 
                row['Tỷ lệ sử dụng rack %']
            ]);
        });
        
        summaryRows.push([]); // blank row
        summaryRows.push([]); // blank row
        
        summaryRows.push(['TỔNG HỢP SỐ LƯỢNG PALLET XUẤT KHO THEO NGÀY']);
        summaryRows.push(['Ngày xuất', 'Pallet xuất từ rack', 'Pallet xuất không từ rack (Block/Floor)', 'Tổng cộng Pallet xuất', 'Tỷ lệ xuất từ rack %']);
        obSummary.forEach(row => {
            summaryRows.push([
                row['Ngày xuất'], 
                row['Pallet xuất từ rack'], 
                row['Pallet xuất không từ rack'], 
                row['Tổng cộng Pallet xuất'], 
                row['Tỷ lệ xuất từ rack %']
            ]);
        });

        const wsSummary = XLSX.utils.aoa_to_sheet(summaryRows);
        const wsInv = XLSX.utils.json_to_sheet(detailedInv);
        const wsInv03 = XLSX.utils.json_to_sheet(detailedInv03);

        // Adjust column widths for better readability
        const adjustWidths = (ws, data) => {
            if (!data || data.length === 0) return;
            const keys = Object.keys(data[0]);
            const cols = keys.map(key => {
                let maxLen = key.length;
                data.forEach(row => {
                    const val = String(row[key] || '');
                    if (val.length > maxLen) maxLen = val.length;
                });
                return { wch: Math.min(maxLen + 3, 50) };
            });
            ws['!cols'] = cols;
        };

        wsSummary['!cols'] = [
            { wch: 18 }, // Ngày
            { wch: 25 }, // Sử dụng rack
            { wch: 38 }, // Không sử dụng rack
            { wch: 25 }, // Tổng cộng
            { wch: 25 }  // Tỷ lệ
        ];

        adjustWidths(wsInv, detailedInv);
        adjustWidths(wsInv03, detailedInv03);

        // Create Workbook
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, wsSummary, "Tổng Hợp");
        XLSX.utils.book_append_sheet(wb, wsInv, "Inventory Detail");
        XLSX.utils.book_append_sheet(wb, wsInv03, "Outbound (INV03) Detail");

        // Download Excel File
        XLSX.writeFile(wb, "Racking_Simulation_Details.xlsx");
    }

    // Start App
    window.onload = init;
</script>
</body>
</html>
"""

# Inject data placeholders by string replacement to avoid f-string brackets errors
html_content = html_template.replace('__DATES_INV__', json.dumps(dates_inv_str))
html_content = html_content.replace('__ITEMS_DATA__', json.dumps(items_data))
html_content = html_content.replace('__LOT_DATA__', json.dumps(lot_data))
html_content = html_content.replace('__OB_DATA__', json.dumps(ob_data))
html_content = html_content.replace('__INVENTORY_DETAIL__', json.dumps(inventory_detail_list))
html_content = html_content.replace('__INV03_DETAIL__', json.dumps(inv03_detail_list))

try:
    with open(html_path, 'w', encoding='utf-8') as fh:
        fh.write(html_content)
    print(f"\n[SUCCESS] Generated interactive simulation page: {html_path}")
except Exception as e:
    print(f"\n[FAILED] Write HTML file: {e}")