import sys
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

sys.stdout.reconfigure(encoding='utf-8')

# Đường dẫn file
excel_path = r'c:\Users\phatvt\OneDrive\Image\Hình ảnh\ThanhPhat_Masan\DC FMCG\org\map\DC_Province.xlsx'
shp_path = r'c:\Users\phatvt\OneDrive\Image\Hình ảnh\ThanhPhat_Masan\DC FMCG\org\map\SHP LV1\diaphantinhenglish.shp'

# Đọc dữ liệu
print("Đang đọc dữ liệu...")
df = pd.read_excel(excel_path, sheet_name='Sheet1')
gdf = gpd.read_file(shp_path)

# Tìm cột chứa thông tin Nhóm
# Do trong file excel không có cột tên chính xác là "Nhóm", ta ưu tiên dùng "New DC" hoặc "DC Supra"
group_col = 'Nhóm'
if group_col not in df.columns:
    if 'New DC' in df.columns:
        group_col = 'New DC'
    elif 'DC Supra' in df.columns:
        group_col = 'DC Supra'
    else:
        # Nếu không có, lấy cột đầu tiên làm cột màu
        group_col = df.columns[0]

print(f"Sử dụng cột '{group_col}' để tô màu.")

# Chuẩn hóa cột Name để merge chính xác (loại bỏ khoảng trắng thừa)
df['Name'] = df['Name'].astype(str).str.strip()
gdf['Name'] = gdf['Name'].astype(str).str.strip()

# Nối dữ liệu (merge) dựa trên cột 'Name'
print("Đang ghép dữ liệu bản đồ và excel...")
merged = gdf.merge(df, on='Name', how='left')

# Vẽ bản đồ
print("Đang vẽ bản đồ...")
fig, ax = plt.subplots(1, 1, figsize=(12, 12))

# Sử dụng missing_kwds để tô màu xám cho các tỉnh không có dữ liệu khớp
merged.plot(column=group_col, 
            ax=ax, 
            categorical=True,
            legend=True, 
            legend_kwds={'loc': 'center left', 'bbox_to_anchor': (1, 0.5)},
            cmap='tab20', 
            edgecolor='black', 
            linewidth=0.5,
            missing_kwds={'color': 'lightgrey', 'edgecolor': 'black', 'label': 'No Data'})

plt.title(f"Bản đồ phân vùng tỉnh thành theo {group_col}", fontsize=16)
plt.axis('off')
plt.tight_layout()

# Hiển thị biểu đồ
plt.show()
print("Hoàn thành!")
