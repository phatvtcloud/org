from flask import Flask, send_from_directory, render_template_string, request, jsonify
import os
import sys
import webbrowser
from threading import Timer
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime

# Configure Windows terminal encoding safety
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

app = Flask(__name__)
PORT = 5000

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_PATH = os.path.join(os.path.dirname(BASE_DIR), "WorldCup2026", "credentials.json")

# Helper to connect to Google Sheets
def get_worksheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_PATH, scope)
    client = gspread.authorize(creds)
    
    try:
        spreadsheet = client.open("DC_Quiz_Database")
    except gspread.exceptions.SpreadsheetNotFound:
        raise Exception(
            "Không tìm thấy Google Sheet 'DC_Quiz_Database'. "
            "Vui lòng tạo Google Sheet tên 'DC_Quiz_Database' trong Google Drive của bạn, "
            "sau đó chia sẻ quyền chỉnh sửa (Editor) cho email service account: "
            "python-excel-bot@phatvt-0309.iam.gserviceaccount.com"
        )
        
    try:
        worksheet = spreadsheet.worksheet("Result")
    except gspread.exceptions.WorksheetNotFound:
        headers = [
            "Timestamp", "Session ID", "Username", "Game Mode", 
            "Question Number", "Target Name", "Target Type", 
            "Answer Lat", "Answer Lng", "Target Lat", "Target Lng", 
            "Distance Error (km)", "Is Correct", "Response Time (s)"
        ]
        worksheet = spreadsheet.add_worksheet(title="Result", rows="5000", cols="20")
        worksheet.insert_row(headers, 1)
        
    return worksheet

@app.route('/')
def index():
    html_path = os.path.join(BASE_DIR, 'index.html')
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    return render_template_string(html_content)

@app.route('/diaphantinh.geojson')
def geojson():
    return send_from_directory(BASE_DIR, 'diaphantinh.geojson')

@app.route('/provinces.json')
def provinces():
    return send_from_directory(BASE_DIR, 'provinces.json')

@app.route('/dc_factories.json')
def dc_factories():
    return send_from_directory(BASE_DIR, 'dc_factories.json')

@app.route('/api/save_answer', methods=['POST'])
def save_answer():
    try:
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400
            
        action = data.get("action")
        worksheet = get_worksheet()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if action == "saveRound":
            answers = data.get("answers", [])
            if not answers:
                return jsonify({"status": "success", "message": "No answers to save"})
                
            rows = []
            for a in answers:
                rows.append([
                    timestamp,
                    data.get("sessionId", ""),
                    data.get("username", "Anonymous"),
                    data.get("gameMode", ""),
                    a.get("questionNumber", 1),
                    a.get("targetName", ""),
                    a.get("targetType", ""),
                    a.get("answerLat", ""),
                    a.get("answerLng", ""),
                    a.get("targetLat", ""),
                    a.get("targetLng", ""),
                    a.get("distanceError", ""),
                    str(a.get("isCorrect", False)).upper(),
                    a.get("responseTime", 0)
                ])
            worksheet.append_rows(rows)
            return jsonify({"status": "success", "count": len(rows)})
        else:
            # Fallback for single question
            row = [
                timestamp,
                data.get("sessionId", ""),
                data.get("username", "Anonymous"),
                data.get("gameMode", ""),
                data.get("questionNumber", 1),
                data.get("targetName", ""),
                data.get("targetType", ""),
                data.get("answerLat", ""),
                data.get("answerLng", ""),
                data.get("targetLat", ""),
                data.get("targetLng", ""),
                data.get("distanceError", ""),
                str(data.get("isCorrect", False)).upper(),
                data.get("responseTime", 0)
            ]
            worksheet.append_row(row)
            return jsonify({"status": "success"})
    except Exception as e:
        print(f"Error saving answer: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/rankings', methods=['GET'])
def get_rankings():
    try:
        worksheet = get_worksheet()
        records = worksheet.get_all_records()
        
        if not records:
            return jsonify({
                "provinces": {"rounds": [], "players": []},
                "dc_factory": {"rounds": [], "players": []}
            })
            
        df = pd.DataFrame(records)
        
        # Normalize columns
        df['Is Correct'] = df['Is Correct'].astype(str).str.upper() == 'TRUE'
        df['Response Time (s)'] = pd.to_numeric(df['Response Time (s)'], errors='coerce').fillna(0)
        
        # 1. Round-level stats
        round_groups = df.groupby(['Session ID', 'Game Mode', 'Username'])
        rounds = []
        for (session_id, game_mode, username), group in round_groups:
            total_questions = len(group)
            correct_questions = group['Is Correct'].sum()
            total_time = group['Response Time (s)'].sum()
            accuracy = round((correct_questions / total_questions * 100), 1) if total_questions > 0 else 0
            
            time_str = f"{int(total_time)}s"
            if total_time >= 60:
                time_str = f"{int(total_time // 60)}m {int(total_time % 60)}s"
                
            rounds.append({
                "sessionId": session_id,
                "gameMode": game_mode,
                "username": username,
                "total": total_questions,
                "correct": int(correct_questions),
                "accuracy": accuracy,
                "time": total_time,
                "timeStr": time_str,
                "date": group['Timestamp'].min()
            })
            
        provinces_rounds = [r for r in rounds if r['gameMode'] == 'provinces']
        dc_factory_rounds = [r for r in rounds if r['gameMode'] == 'dc_factory']
        
        provinces_rounds.sort(key=lambda x: (-x['accuracy'], x['time']))
        dc_factory_rounds.sort(key=lambda x: (-x['accuracy'], x['time']))
        
        # 2. Player-level (Pivot) stats
        provinces_players_dict = {}
        for r in provinces_rounds:
            user = r['username']
            if user not in provinces_players_dict:
                provinces_players_dict[user] = {"username": user, "accuracy_sum": 0, "time_sum": 0, "rounds_count": 0}
            provinces_players_dict[user]["accuracy_sum"] += r["accuracy"]
            provinces_players_dict[user]["time_sum"] += r["time"]
            provinces_players_dict[user]["rounds_count"] += 1
            
        provinces_players = []
        for user, data in provinces_players_dict.items():
            avg_accuracy = round(data["accuracy_sum"] / data["rounds_count"], 1)
            avg_time = data["time_sum"] / data["rounds_count"]
            time_str = f"{int(avg_time)}s"
            if avg_time >= 60:
                time_str = f"{int(avg_time // 60)}m {int(avg_time % 60)}s"
            provinces_players.append({
                "username": user,
                "avgAccuracy": avg_accuracy,
                "avgTime": avg_time,
                "avgTimeStr": time_str,
                "roundsCount": data["rounds_count"]
            })
        provinces_players.sort(key=lambda x: (-x['avgAccuracy'], x['avgTime']))
        
        dc_factory_players_dict = {}
        for r in dc_factory_rounds:
            user = r['username']
            if user not in dc_factory_players_dict:
                dc_factory_players_dict[user] = {"username": user, "accuracy_sum": 0, "time_sum": 0, "rounds_count": 0}
            dc_factory_players_dict[user]["accuracy_sum"] += r["accuracy"]
            dc_factory_players_dict[user]["time_sum"] += r["time"]
            dc_factory_players_dict[user]["rounds_count"] += 1
            
        dc_factory_players = []
        for user, data in dc_factory_players_dict.items():
            avg_accuracy = round(data["accuracy_sum"] / data["rounds_count"], 1)
            avg_time = data["time_sum"] / data["rounds_count"]
            time_str = f"{int(avg_time)}s"
            if avg_time >= 60:
                time_str = f"{int(avg_time // 60)}m {int(avg_time % 60)}s"
            dc_factory_players.append({
                "username": user,
                "avgAccuracy": avg_accuracy,
                "avgTime": avg_time,
                "avgTimeStr": time_str,
                "roundsCount": data["rounds_count"]
            })
        dc_factory_players.sort(key=lambda x: (-x['avgAccuracy'], x['avgTime']))
        
        return jsonify({
            "provinces": {
                "rounds": provinces_rounds,
                "players": provinces_players
            },
            "dc_factory": {
                "rounds": dc_factory_rounds,
                "players": dc_factory_players
            }
        })
    except Exception as e:
        print(f"Error fetching rankings: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

def open_browser():
    webbrowser.open_new(f"http://127.0.0.1:{PORT}")

if __name__ == '__main__':
    Timer(1.5, open_browser).start()
    print(f"\n==========================================")
    print(f"Starting Quiz Server at http://127.0.0.1:{PORT} ...")
    print(f"Opening browser automatically...")
    print(f"==========================================\n")
    app.run(host='127.0.0.1', port=PORT, debug=False)
