import os
import time
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# Duong dan du lieu
PARQUET_PATH = r"D:\\Download\\E2E\\E2E_combined.parquet"
OUTPUT_PATH = r"D:\\Download\\E2E\\E2E_NamNgu_Omachi_Wakeup_Mapping.parquet"

def load_excel_data(excel_path):
    """
    Doc cac sheet tu file Excel.
    Tu dong retry neu file bi Excel khoa (PermissionError) tren Windows.
    """
    xl = None
    for i in range(15):
        try:
            xl = pd.ExcelFile(excel_path)
            break
        except PermissionError:
            if i == 0:
                print("\n[WARNING] Excel file is currently locked/open in another process.")
                print("-> PLEASE CLOSE 'base line Supra.xlsx' in Microsoft Excel now to let this script run!")
            print(f"  -> Retrying to open Excel... ({i+1}/15)")
            time.sleep(3)
            
    if xl is None:
        print("\n[ERROR] Could not open Excel file due to PermissionError.")
        print("Please close 'base line Supra.xlsx' in Microsoft Excel and run the script again.")
        raise PermissionError("base line Supra.xlsx is locked by Excel.")
    
    sheet_names = xl.sheet_names
    print("Sheets in Excel file:", sheet_names)
    
    # 1. Doc sheet MD06
    md06_sheet = "MD06"
    MD06 = xl.parse(md06_sheet)
    print(f"  - Sheet '{md06_sheet}' read successfully: {len(MD06):,} rows")
    
    # 2. Doc sheet Info_Factoty
    factory_sheet = "Info_Factoty" if "Info_Factoty" in sheet_names else "Info_Factory"
    if factory_sheet not in sheet_names:
        for s in sheet_names:
            if "factor" in s.lower():
                factory_sheet = s
                break
    Info_Factoty = xl.parse(factory_sheet)
    print(f"  - Factory sheet '{factory_sheet}' read successfully: {len(Info_Factoty):,} rows")
    
    # 3. Doc sheet Info_DC
    dc_sheet = "Info_DC" if "Info_DC" in sheet_names else "DC"
    if dc_sheet not in sheet_names:
        for s in sheet_names:
            if "dc" in s.lower():
                dc_sheet = s
                break
    Info_DC = xl.parse(dc_sheet)
    print(f"  - DC sheet '{dc_sheet}' read successfully: {len(Info_DC):,} rows")
            
    return MD06, Info_Factoty, Info_DC

def main():
    start_time = time.time()
    
    # Xac dinh duong dan file Excel cung thu muc voi script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    excel_path = os.path.join(script_dir, "base line Supra.xlsx")
    
    print("=== STARTING DATA MAPPING PROCESS ===")
    print(f"Excel file: {os.path.basename(excel_path)}")
    print(f"Source Parquet: {os.path.basename(PARQUET_PATH)}")
    print(f"Output Parquet: {os.path.basename(OUTPUT_PATH)}")
    
    # Doc cac bang Excel
    MD06, Info_Factoty, Info_DC = load_excel_data(excel_path)
    
    # 1. Chuan hoa cac cot trong Pandas truoc
    print("Normalizing Excel columns in Pandas...")
    
    # Chuan hoa MD06 và lấy thêm các cột UOM1, UOM2, UOM Conversion
    MD06['Item No'] = MD06['Item No'].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
    MD06['UOM2/UOM1'] = pd.to_numeric(MD06['UOM2/UOM1'], errors='coerce')
    
    # Đảm bảo các cột mới ở dạng text/số phù hợp và xóa dòng trùng lặp dựa trên 'Item No'
    MD06_clean = MD06[['Item No', 'UOM2/UOM1', 'UOM1', 'UOM2', 'UOM Conversion', 'Item Name']].drop_duplicates(subset=['Item No'])
    
    # Tạo các từ điển để map nhanh (set_index)
    md06_map = MD06_clean.set_index('Item No')['UOM2/UOM1']
    uom1_map = MD06_clean.set_index('Item No')['UOM1']
    uom2_map = MD06_clean.set_index('Item No')['UOM2']
    uom_conv_map = MD06_clean.set_index('Item No')['UOM Conversion']
    item_name_map = MD06_clean.set_index('Item No')['Item Name']
    
    # Chuan hoa Info_Factoty
    fact_code_col = "Factory_Code" if "Factory_Code" in Info_Factoty.columns else Info_Factoty.columns[0]
    fact_name_col = "Factory" if "Factory" in Info_Factoty.columns else Info_Factoty.columns[1]
    Info_Factoty[fact_code_col] = Info_Factoty[fact_code_col].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
    Info_Factoty[fact_name_col] = Info_Factoty[fact_name_col].astype(str).str.strip()
    Factory_clean = Info_Factoty[[fact_code_col, fact_name_col]].drop_duplicates(subset=[fact_code_col])
    factory_map = Factory_clean.set_index(fact_code_col)[fact_name_col]
    
    # Chuan hoa Info_DC
    dc_code_col = "dc" if "dc" in Info_DC.columns else Info_DC.columns[0]
    dc_name_col = "DC_Out" if "DC_Out" in Info_DC.columns else Info_DC.columns[1]
    Info_DC[dc_code_col] = Info_DC[dc_code_col].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
    Info_DC[dc_name_col] = Info_DC[dc_name_col].astype(str).str.strip()
    DC_clean = Info_DC[[dc_code_col, dc_name_col]].drop_duplicates(subset=[dc_code_col])
    dc_map = DC_clean.set_index(dc_code_col)[dc_name_col]
    
    # 2. Mo file Parquet nguon va setup Writer
    print("Opening source Parquet file...")
    parquet_file = pq.ParquetFile(PARQUET_PATH)
    
    # Lay schema goc va tao schema moi bang cach append them 6 cot (gồm 3 cột cũ và 3 cột mới)
    orig_schema = parquet_file.schema.to_arrow_schema()
    writer_schema = orig_schema
    
    new_fields = [
        pa.field('Case', pa.float64()),
        pa.field('Factory', pa.string()),
        pa.field('DC_Out', pa.string()),
        pa.field('MD06[UOM1]', pa.string()),          # Thêm cột mới
        pa.field('MD06[UOM2]', pa.string()),          # Thêm cột mới
        pa.field('MD06[UOM Conversion]', pa.string()),
        pa.field('MD06[Item Name]', pa.string())     # Ten san phamêm cột mới (hoặc pa.float64() nếu cột này thuần số)
    ]
    
    for field in new_fields:
        if field.name in writer_schema.names:
            idx = writer_schema.get_field_index(field.name)
            writer_schema = writer_schema.remove(idx)
        writer_schema = writer_schema.append(field)
        
    print("\n[Engine: PyArrow Streaming] Processing chunk-by-chunk to save RAM...")
    
    # Initialize ParquetWriter
    writer = pq.ParquetWriter(OUTPUT_PATH, writer_schema, compression='snappy')
    
    # Doc va ghi theo batch (moi batch 2 trieu dong)
    total_rows = 0
    batch_index = 0
    for batch in parquet_file.iter_batches(batch_size=2000000):
        batch_start = time.time()
        df = batch.to_pandas()
        
        # Chuan hoa cac cot khoa
        df['item_code'] = df['item_code'].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
        df['Factory_Code'] = df['Factory_Code'].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
        df['dc'] = df['dc'].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
        
        # Mapping cac cot cu
        uom_factors = df['item_code'].map(md06_map)
        df['Case'] = df['forecast_qty'] / uom_factors
        df['Factory'] = df['Factory_Code'].map(factory_map)
        df['DC_Out'] = df['dc'].map(dc_map)
        
        # Mapping 3 cot moi tu MD06
        df['MD06[UOM1]'] = df['item_code'].map(uom1_map)
        df['MD06[UOM2]'] = df['item_code'].map(uom2_map)
        df['MD06[UOM Conversion]'] = df['item_code'].map(uom_conv_map)
        df['MD06[Item Name]'] = df['item_code'].map(item_name_map)
        
        # Casting cac kieu du lieu de phu hop voi Schema cua writer
        df['Case'] = pd.to_numeric(df['Case'], errors='coerce')
        df['Factory'] = df['Factory'].fillna("").astype(str)
        df['DC_Out'] = df['DC_Out'].fillna("").astype(str)
        
        # Ép kiểu dữ liệu text cho các cột mới và xử lý NaN
        df['MD06[UOM1]'] = df['MD06[UOM1]'].fillna("").astype(str)
        df['MD06[UOM2]'] = df['MD06[UOM2]'].fillna("").astype(str)
        df['MD06[UOM Conversion]'] = df['MD06[UOM Conversion]'].fillna("").astype(str)
        df['MD06[Item Name]'] = df['MD06[Item Name]'].fillna("").astype(str)
        
        # Sap xep dung thu tu cot cua Schema
        df = df[writer_schema.names]
        
        # Ghi vao parquet
        table = pa.Table.from_pandas(df, schema=writer_schema)
        writer.write_table(table)
        
        total_rows += len(df)
        batch_index += 1
        print(f"  -> Batch {batch_index}: Mapped and written {total_rows:,} rows total ({time.time() - batch_start:.1f}s)")
        
    writer.close()
    print(f"\n=== MAPPING COMPLETED SUCCESSFULY ===")
    print(f"Total rows written: {total_rows:,}")
    print(f"Completed in {time.time() - start_time:.1f} seconds.")

if __name__ == "__main__":
    main()