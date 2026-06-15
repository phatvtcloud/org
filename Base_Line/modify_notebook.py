import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

notebook_files = [
    r"c:\Users\phatvt\OneDrive\Image\Hình ảnh\ThanhPhat_Masan\DC FMCG\org\Base_Line\E2E_NamNgu_Omachi_Wakeup_Mapping.ipynb",
    r"c:\Users\phatvt\OneDrive\Image\Hình ảnh\ThanhPhat_Masan\DC FMCG\org\Base_Line\e2e_raw_m6 copy.ipynb"
]

for notebook_path in notebook_files:
    if not os.path.exists(notebook_path):
        print(f"File not found: {notebook_path}")
        continue
        
    print(f"\nProcessing notebook: {notebook_path}")
    with open(notebook_path, "r", encoding="utf-8") as f:
        nb = json.load(f)

    modified = 0
    for cell in nb["cells"]:
        if cell["cell_type"] == "code":
            source_str = "".join(cell["source"])
            
            # --- Section 4: DC Stats ---
            if "df_dc = pd.read_parquet(PARQUET_PATH, columns=['dc', 'outlet_code', 'item_code', 'Case'])" in source_str or "columns=['dc', 'outlet_code', 'item_code', 'Case', 'forecast_qty']" in source_str:
                print("  -> Modifying Section 4 (DC Stats)...")
                cell["source"] = [
                    "start = time.time()\n",
                    "\n",
                    "print(\"Đang đọc dữ liệu các cột 'dc', 'outlet_code', 'item_code', 'Case', 'forecast_qty'...\")\n",
                    "df_dc = pd.read_parquet(PARQUET_PATH, columns=['dc', 'outlet_code', 'item_code', 'Case', 'forecast_qty'])\n",
                    "\n",
                    "print(\"Đang tính toán thống kê theo từng DC...\")\n",
                    "grouped_dc = df_dc.groupby('dc').agg(\n",
                    "    So_Outlet_Unique=('outlet_code', 'nunique'),\n",
                    "    So_Item_Unique=('item_code', 'nunique'),\n",
                    "    Tong_Case=('Case', 'sum'),\n",
                    "    Tong_Forecast_Qty=('forecast_qty', 'sum'),\n",
                    "    Tong_So_Dong=('outlet_code', 'count')\n",
                    ").reset_index()\n",
                    "\n",
                    "grouped_dc = grouped_dc.sort_values(by='So_Outlet_Unique', ascending=False).reset_index(drop=True)\n",
                    "\n",
                    "print(\"Đang tính toán dòng tổng cộng (Total) theo DC...\")\n",
                    "total_unique_outlets_dc = df_dc['outlet_code'].nunique()\n",
                    "total_unique_items_dc = df_dc['item_code'].nunique()\n",
                    "total_case_dc = df_dc['Case'].sum()\n",
                    "total_forecast_qty_dc = df_dc['forecast_qty'].sum()\n",
                    "total_rows_sum_dc = len(df_dc)\n",
                    "\n",
                    "total_row_dc = pd.DataFrame([{\n",
                    "    'dc': 'Total',\n",
                    "    'So_Outlet_Unique': total_unique_outlets_dc,\n",
                    "    'So_Item_Unique': total_unique_items_dc,\n",
                    "    'Tong_Case': total_case_dc,\n",
                    "    'Tong_Forecast_Qty': total_forecast_qty_dc,\n",
                    "    'Tong_So_Dong': total_rows_sum_dc\n",
                    "}])\n",
                    "\n",
                    "result_dc_df = pd.concat([grouped_dc, total_row_dc], ignore_index=True)\n",
                    "print(f\"Thống kê DC hoàn tất trong {time.time() - start:.1f} giây.\")\n",
                    "\n",
                    "result_dc_df.style.format({\n",
                    "    'So_Outlet_Unique': '{:,}',\n",
                    "    'So_Item_Unique': '{:,}',\n",
                    "    'Tong_Case': '{:,.2f}',\n",
                    "    'Tong_Forecast_Qty': '{:,.2f}',\n",
                    "    'Tong_So_Dong': '{:,}'\n",
                    "})"
                ]
                modified += 1
                
            # --- Section 5: Unit Stats ---
            elif "df_unit = pd.read_parquet(PARQUET_PATH, columns=['unit', 'outlet_code', 'item_code', 'Case'])" in source_str or "columns=['unit', 'outlet_code', 'item_code', 'Case', 'forecast_qty']" in source_str:
                print("  -> Modifying Section 5 (Unit Stats)...")
                cell["source"] = [
                    "start = time.time()\n",
                    "\n",
                    "print(\"Đang đọc dữ liệu các cột 'unit', 'outlet_code', 'item_code', 'Case', 'forecast_qty'...\")\n",
                    "df_unit = pd.read_parquet(PARQUET_PATH, columns=['unit', 'outlet_code', 'item_code', 'Case', 'forecast_qty'])\n",
                    "\n",
                    "print(\"Đang tính toán thống kê theo từng Unit...\")\n",
                    "grouped_unit = df_unit.groupby('unit').agg(\n",
                    "    So_Outlet_Unique=('outlet_code', 'nunique'),\n",
                    "    So_Item_Unique=('item_code', 'nunique'),\n",
                    "    Tong_Case=('Case', 'sum'),\n",
                    "    Tong_Forecast_Qty=('forecast_qty', 'sum'),\n",
                    "    Tong_So_Dong=('outlet_code', 'count')\n",
                    ").reset_index()\n",
                    "\n",
                    "grouped_unit = grouped_unit.sort_values(by='So_Outlet_Unique', ascending=False).reset_index(drop=True)\n",
                    "\n",
                    "print(\"Đang tính toán dòng tổng cộng (Total) theo Unit...\")\n",
                    "total_unique_outlets_unit = df_unit['outlet_code'].nunique()\n",
                    "total_unique_items_unit = df_unit['item_code'].nunique()\n",
                    "total_case_unit = df_unit['Case'].sum()\n",
                    "total_forecast_qty_unit = df_unit['forecast_qty'].sum()\n",
                    "total_rows_sum_unit = len(df_unit)\n",
                    "\n",
                    "total_row_unit = pd.DataFrame([{\n",
                    "    'unit': 'Total',\n",
                    "    'So_Outlet_Unique': total_unique_outlets_unit,\n",
                    "    'So_Item_Unique': total_unique_items_unit,\n",
                    "    'Tong_Case': total_case_unit,\n",
                    "    'Tong_Forecast_Qty': total_forecast_qty_unit,\n",
                    "    'Tong_So_Dong': total_rows_sum_unit\n",
                    "}])\n",
                    "\n",
                    "result_unit_df = pd.concat([grouped_unit, total_row_unit], ignore_index=True)\n",
                    "print(f\"Thống kê Unit hoàn tất trong {time.time() - start:.1f} giây.\")\n",
                    "\n",
                    "result_unit_df.style.format({\n",
                    "    'So_Outlet_Unique': '{:,}',\n",
                    "    'So_Item_Unique': '{:,}',\n",
                    "    'Tong_Case': '{:,.2f}',\n",
                    "    'Tong_Forecast_Qty': '{:,.2f}',\n",
                    "    'Tong_So_Dong': '{:,}'\n",
                    "})"
                ]
                modified += 1
                
            # --- Section 6: Item Stats ---
            elif "df_item = pd.read_parquet(PARQUET_PATH, columns=['item_code', 'outlet_code', 'dc', 'Case'])" in source_str or "columns=['item_code', 'outlet_code', 'dc', 'Case', 'forecast_qty']" in source_str:
                print("  -> Modifying Section 6 (Item Stats)...")
                cell["source"] = [
                    "start = time.time()\n",
                    "\n",
                    "print(\"Đang đọc dữ liệu các cột 'item_code', 'outlet_code', 'dc', 'Case', 'forecast_qty'...\")\n",
                    "df_item = pd.read_parquet(PARQUET_PATH, columns=['item_code', 'outlet_code', 'dc', 'Case', 'forecast_qty'])\n",
                    "\n",
                    "print(\"Đang tính toán thống kê theo từng Item...\")\n",
                    "grouped_item = df_item.groupby('item_code').agg(\n",
                    "    So_Outlet_Unique=('outlet_code', 'nunique'),\n",
                    "    So_DC_Unique=('dc', 'nunique'),\n",
                    "    Tong_Case=('Case', 'sum'),\n",
                    "    Tong_Forecast_Qty=('forecast_qty', 'sum'),\n",
                    "    Tong_So_Dong=('outlet_code', 'count')\n",
                    ").reset_index()\n",
                    "\n",
                    "# Sắp xếp giảm dần theo tổng số dòng giao dịch\n",
                    "grouped_item = grouped_item.sort_values(by='Tong_So_Dong', ascending=False).reset_index(drop=True)\n",
                    "\n",
                    "print(\"Đang tính toán dòng tổng cộng (Total) theo Item...\")\n",
                    "total_unique_outlets_item = df_item['outlet_code'].nunique()\n",
                    "total_unique_dcs_item = df_item['dc'].nunique()\n",
                    "total_case_item = df_item['Case'].sum()\n",
                    "total_forecast_qty_item = df_item['forecast_qty'].sum()\n",
                    "total_rows_sum_item = len(df_item)\n",
                    "\n",
                    "total_row_item = pd.DataFrame([{\n",
                    "    'item_code': 'Total',\n",
                    "    'So_Outlet_Unique': total_unique_outlets_item,\n",
                    "    'So_DC_Unique': total_unique_dcs_item,\n",
                    "    'Tong_Case': total_case_item,\n",
                    "    'Tong_Forecast_Qty': total_forecast_qty_item,\n",
                    "    'Tong_So_Dong': total_rows_sum_item\n",
                    "}])\n",
                    "\n",
                    "result_item_df = pd.concat([grouped_item, total_row_item], ignore_index=True)\n",
                    "print(f\"Thống kê Item hoàn tất trong {time.time() - start:.1f} giây.\")\n",
                    "\n",
                    "result_item_df.style.format({\n",
                    "    'So_Outlet_Unique': '{:,}',\n",
                    "    'So_DC_Unique': '{:,}',\n",
                    "    'Tong_Case': '{:,.2f}',\n",
                    "    'Tong_Forecast_Qty': '{:,.2f}',\n",
                    "    'Tong_So_Dong': '{:,}'\n",
                    "})"
                ]
                modified += 1
                
            # --- Section 9: Polars Stats ---
            elif "summary_dc = lf.group_by(\"dc\").agg([" in source_str and "Tong_Case" in source_str:
                print("  -> Modifying Section 9 (Polars Stats)...")
                cell["source"] = [
                    "try:\n",
                    "    import polars as pl\n",
                    "    # Lazy loading\n",
                    "    lf = pl.scan_parquet(PARQUET_PATH)\n",
                    "    \n",
                    "    print(\"--- THỐNG KÊ THEO DC BẰNG POLARS ---\")\n",
                    "    summary_dc = lf.group_by(\"dc\").agg([\n",
                    "        pl.col(\"outlet_code\").n_unique().alias(\"So_Outlet_Unique\"),\n",
                    "        pl.col(\"item_code\").n_unique().alias(\"So_Item_Unique\"),\n",
                    "        pl.col(\"Case\").sum().alias(\"Tong_Case\"),\n",
                    "        pl.col(\"forecast_qty\").sum().alias(\"Tong_Forecast_Qty\"),\n",
                    "        pl.col(\"outlet_code\").count().alias(\"Tong_So_Dong\")\n",
                    "    ]).sort(\"So_Outlet_Unique\", descending=True).collect()\n",
                    "    print(summary_dc)\n",
                    "    \n",
                    "    print(\"\\n--- THỐNG KÊ THEO UNIT BẰNG POLARS ---\")\n",
                    "    summary_unit = lf.group_by(\"unit\").agg([\n",
                    "        pl.col(\"outlet_code\").n_unique().alias(\"So_Outlet_Unique\"),\n",
                    "        pl.col(\"item_code\").n_unique().alias(\"So_Item_Unique\"),\n",
                    "        pl.col(\"Case\").sum().alias(\"Tong_Case\"),\n",
                    "        pl.col(\"forecast_qty\").sum().alias(\"Tong_Forecast_Qty\"),\n",
                    "        pl.col(\"outlet_code\").count().alias(\"Tong_So_Dong\")\n",
                    "    ]).sort(\"So_Outlet_Unique\", descending=True).collect()\n",
                    "    print(summary_unit)\n",
                    "\n",
                    "    print(\"\\n--- THỐNG KÊ THEO ITEM BẰNG POLARS ---\")\n",
                    "    summary_item = lf.group_by(\"item_code\").agg([\n",
                    "        pl.col(\"outlet_code\").n_unique().alias(\"So_Outlet_Unique\"),\n",
                    "        pl.col(\"dc\").n_unique().alias(\"So_DC_Unique\"),\n",
                    "        pl.col(\"Case\").sum().alias(\"Tong_Case\"),\n",
                    "        pl.col(\"forecast_qty\").sum().alias(\"Tong_Forecast_Qty\"),\n",
                    "        pl.col(\"outlet_code\").count().alias(\"Tong_So_Dong\")\n",
                    "    ]).sort(\"Tong_So_Dong\", descending=True).collect()\n",
                    "    print(summary_item)\n",
                    "except ImportError:\n",
                    "    print(\"Chưa cài đặt thư viện 'polars'. Bạn có thể cài đặt bằng lệnh: pip install polars\")"
                ]
                modified += 1

    print(f"Saving notebook: {notebook_path}. Modified cells: {modified}")
    with open(notebook_path, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)

print("Finished processing all notebooks!")
