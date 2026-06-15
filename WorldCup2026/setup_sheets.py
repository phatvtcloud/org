import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
base_dir = os.path.dirname(os.path.abspath(__file__))
credentials_path = os.path.join(base_dir, "credentials.json")
creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)
client = gspread.authorize(creds)

spreadsheet = client.open("WorldCup2026_Database")

# Define sheets and headers
sheets_to_create = {
    "Users": ["username", "password", "fullname", "department", "created_at"],
    "Matches": ["match_id", "date", "round", "home_team", "away_team", "home_logo", "away_logo", "home_score", "away_score", "status"],
    "Predictions": ["prediction_id", "username", "match_id", "predicted_home", "predicted_away", "points", "updated_at"]
}

for sheet_name, headers in sheets_to_create.items():
    try:
        worksheet = spreadsheet.worksheet(sheet_name)
        print(f"Sheet '{sheet_name}' already exists.")
    except gspread.exceptions.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=sheet_name, rows="1000", cols="20")
        print(f"Created sheet '{sheet_name}'.")
    
    # Thiết lập tiêu đề cột nếu chưa có
    first_row = worksheet.row_values(1)
    if not first_row or first_row[:len(headers)] != headers:
        worksheet.insert_row(headers, 1)
        print(f"Updated headers for '{sheet_name}'.")

print("Google Sheets Database initialization successful!")
