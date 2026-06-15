import os
import csv
from dotenv import load_dotenv
from supabase import create_client, Client

# 1. Tải các biến môi trường từ file .env
load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# 2. Khởi tạo kết nối tới Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def upload_test_data():
    """Hàm nạp dữ liệu mẫu vào bảng transport_logs từ file CSV"""
    print("Đang đọc file test_data.csv...")
    
    data_to_insert = []
    try:
        with open('test_data.csv', mode='r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                # Ép kiểu volume sang float để đúng kiểu dữ liệu
                row['volume'] = float(row['volume'])
                data_to_insert.append(row)
    except FileNotFoundError:
        print("Lỗi: Không tìm thấy file test_data.csv")
        return
        
    print(f"Đã đọc {len(data_to_insert)} dòng. Đang thử kết nối và upload dữ liệu...")
    
    try:
        # Chèn dữ liệu vào bảng 'transport_logs'
        response = supabase.table("transport_logs").insert(data_to_insert).execute()
        print(f"Upload thành công {len(data_to_insert)} dòng dữ liệu mẫu từ CSV!")
        print("Kết quả trả về từ server:", response.data)
    except Exception as e:
        print("Đã xảy ra lỗi khi upload:", e)

if __name__ == "__main__":
    upload_test_data()