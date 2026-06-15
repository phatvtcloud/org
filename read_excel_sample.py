import pandas as pd

file_path = r"c:\Users\phatvt\OneDrive\Image\Hình ảnh\ThanhPhat_Masan\DC FMCG\org\Base_Line\base line Supra.xlsx"

try:
    print("Reading excel file...")
    xls = pd.ExcelFile(file_path)
    print("Sheet names:", xls.sheet_names)
    
    for sheet in ["MD06"]:
        if sheet in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet)
            with open("output.txt", "w", encoding="utf-8") as f:
                f.write(f"--- Sheet: {sheet} ---\n")
                f.write(f"Columns: {df.columns.tolist()}\n")
                f.write(str(df[['Item No', 'UOM Conversion / Pallet']].head(5)) + "\n")
        else:
            print(f"Sheet {sheet} not found.")

except Exception as e:
    print(f"Error: {e}")
