import pandas as pd
import json

def convert_excel_to_orgchart_json(file_path, output_json):
    # 1. Đọc file Excel
    df = pd.read_excel(file_path)

    org_data = []
    
    for index, row in df.iterrows():
        # D3 Org Chart sử dụng trường 'id' và 'parentId' thay vì 'pid'
        node = {
            "id": str(row['Mã nhóm (ID)']),
            "name": str(row['Tên nhóm / Team']),
            "manager": str(row['Manager']) if pd.notna(row['Manager']) else ""
        }
        
        # Xử lý Parent ID
        if pd.notna(row['Thuộc nhóm (Parent ID)']):
            node["parentId"] = str(row['Thuộc nhóm (Parent ID)'])

        # Thêm các thông tin bổ sung để tô màu theo yêu cầu
        if pd.notna(row['Ghi chú']):
            node["note"] = str(row['Ghi chú'])
            
        org_data.append(node)

    # 3. Xuất ra file JSON
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(org_data, f, ensure_ascii=False, indent=4)
    
    print(f"Success: {output_json} created.")
    return org_data

# Sử dụng hàm
if __name__ == "__main__":
    convert_excel_to_orgchart_json(r'Org chart FMCG.xlsx', r'data_org_v2.json')
