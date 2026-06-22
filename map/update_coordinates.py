import pandas as pd
import json
import os
import sys

# Đảm bảo mã hóa UTF-8 cho Windows terminal
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# Đường dẫn file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
xlsx_path = os.path.join(BASE_DIR, 'DC_Province.xlsx')
output_json = os.path.join(BASE_DIR, 'dc_factories.json')

print("Đang đọc dữ liệu từ sheet 'LatLong' của file DC_Province.xlsx...")
try:
    df = pd.read_excel(xlsx_path, sheet_name='LatLong')
except Exception as e:
    print(f"Lỗi: Không thể mở file Excel hoặc không tìm thấy sheet 'LatLong'. Chi tiết: {e}")
    sys.exit(1)

# Xóa khoảng trắng thừa ở tiêu đề cột
df.columns = df.columns.str.strip()

# Kiểm tra các cột bắt buộc
required_cols = ['Phân loại', 'Latitude', 'Longitude']
for col in required_cols:
    if col not in df.columns:
        print(f"Lỗi: File Excel thiếu cột bắt buộc '{col}'. Các cột hiện có: {list(df.columns)}")
        sys.exit(1)

# Chuyển đổi tọa độ sang kiểu số và lọc dòng trống
df['Latitude'] = pd.to_numeric(df['Latitude'], errors='coerce')
df['Longitude'] = pd.to_numeric(df['Longitude'], errors='coerce')
df = df.dropna(subset=['Latitude', 'Longitude'])

facilities = []
for idx, row in df.iterrows():
    category = str(row['Phân loại']).strip()
    
    # Lấy tên theo Phân loại
    if category == 'DC':
        if 'Tên Tắt' in df.columns:
            name = str(row['Tên Tắt']).strip()
        else:
            name = str(row.get('Tên', '')).strip()
    elif category == 'Factory':
        name = str(row.get('Tên', '')).strip()
    else:
        name = str(row.get('Tên', row.get('Tên Tắt', ''))).strip()
        
    if not name or name.lower() == 'nan':
        continue
        
    facilities.append({
        'name': name,
        'category': category,
        'lat': float(row['Latitude']),
        'lng': float(row['Longitude'])
    })

# Lưu ra file JSON
with open(output_json, 'w', encoding='utf-8') as f:
    json.dump(facilities, f, ensure_ascii=False, indent=2)

print(f"\n[Thành công] Đã trích xuất {len(facilities)} tọa độ nhà máy/DC.")
print(f"File kết quả đã được lưu tại: {output_json}")
print("\nDanh sách 5 địa điểm đầu tiên:")
for f in facilities[:5]:
    print(f" - {f['category']} - {f['name']}: ({f['lat']}, {f['lng']})")
