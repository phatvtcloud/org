import pandas as pd
import json

def convert_excel_to_orgchart_json(file_path, output_json):
    # 1. Đọc file Excel
    # Lưu ý: Điều chỉnh tên sheet nếu cần thiết
    df = pd.read_excel(file_path)

    # 2. Làm sạch và ánh xạ các cột
    # OrgChart JS yêu cầu các trường tối thiểu là id và pid
    # Chúng ta sẽ map: 
    # 'Mã nhóm (ID)' -> id
    # 'Thuộc nhóm (Parent ID)' -> pid
    # 'Tên nhóm / Team' -> name
    
    org_data = []
    
    for index, row in df.iterrows():
        # Đếm số dấu chấm để xác định Level (Tầng)
        # 0 chấm = Level 1 (VD: 6)
        # 3 chấm = Level 4 (VD: 6.4.3.1)
        level = str(row['Mã nhóm (ID)']).count('.') + 1

        node = {
            "id": str(row['Mã nhóm (ID)']),
            "name": str(row['Tên nhóm / Team']),
            "manager": str(row['Manager']) if pd.notna(row['Manager']) else ""
        }
        
        # Vẫn xác định level
        level = str(row['Mã nhóm (ID)']).count('.') + 1

        tags = []
        if pd.notna(row['Thuộc nhóm (Parent ID)']):
            node["pid"] = str(row['Thuộc nhóm (Parent ID)'])

        # Gán tag 'xodoc' cho các nhóm từ Tầng 4 trở đi 
        if level >= 4:
            tags.append("xodoc")
            
        node["tags"] = tags
        # ---------------------
            
        # Thêm các thông tin bổ sung nếu muốn hiển thị trên UI
        if pd.notna(row['Ghi chú']):
            node["note"] = str(row['Ghi chú'])
            
        org_data.append(node)

    # 3. Xuất ra file JSON
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(org_data, f, ensure_ascii=False, indent=4)
    
    print(f"Đã chuyển đổi thành công sang {output_json}")
    return org_data

# Sử dụng hàm
# Giả sử file của bạn tên là 'org_data.xlsx'
convert_excel_to_orgchart_json(r'Org chart FMCG.xlsx', r'data_org.json')