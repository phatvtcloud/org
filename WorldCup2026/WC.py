import os
import json
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# 1. Load configuration from config.json
base_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(base_dir, "config.json")

try:
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
except Exception as e:
    config = {
        "api_key": "YOUR_API_KEY_HERE",
        "api_provider": "football-data",
        "league_id": "WC",
        "season": 2026
    }

# 2. Connect to Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials_path = os.path.join(base_dir, "credentials.json")
creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)
client = gspread.authorize(creds)
spreadsheet = client.open("WorldCup2026_Database")
matches_sheet = spreadsheet.worksheet("Matches")

# 3. Mock data (used when API Key is missing or API errors)
MOCK_MATCHES = [
    {
        "match_id": "990001",
        "date": "2026-06-11T17:00:00Z",
        "round": "Group Stage - Group A",
        "home_team": "USA",
        "away_team": "Mexico",
        "home_logo": "https://media.api-sports.io/football/teams/95.png",
        "away_logo": "https://media.api-sports.io/football/teams/96.png",
        "home_score": "2",
        "away_score": "1",
        "status": "FT"
    },
    {
        "match_id": "990002",
        "date": "2026-06-12T15:00:00Z",
        "round": "Group Stage - Group B",
        "home_team": "Argentina",
        "away_team": "France",
        "home_logo": "https://media.api-sports.io/football/teams/26.png",
        "away_logo": "https://media.api-sports.io/football/teams/2.png",
        "home_score": "2",
        "away_score": "2",
        "status": "FT"
    },
    {
        "match_id": "990003",
        "date": "2026-06-13T19:00:00Z",
        "round": "Group Stage - Group C",
        "home_team": "Brazil",
        "away_team": "England",
        "home_logo": "https://media.api-sports.io/football/teams/6.png",
        "away_logo": "https://media.api-sports.io/football/teams/10.png",
        "home_score": "0",
        "away_score": "1",
        "status": "FT"
    },
    {
        "match_id": "990004",
        "date": "2026-07-15T18:00:00Z",
        "round": "Group Stage - Group D",
        "home_team": "Spain",
        "away_team": "Germany",
        "home_logo": "https://media.api-sports.io/football/teams/9.png",
        "away_logo": "https://media.api-sports.io/football/teams/25.png",
        "home_score": "",
        "away_score": "",
        "status": "NS"
    },
    {
        "match_id": "990005",
        "date": "2026-07-16T20:00:00Z",
        "round": "Group Stage - Group E",
        "home_team": "Japan",
        "away_team": "Vietnam",
        "home_logo": "https://media.api-sports.io/football/teams/12.png",
        "away_logo": "https://media.api-sports.io/football/teams/18.png",
        "home_score": "",
        "away_score": "",
        "status": "NS"
    }
]

def get_live_fixtures(api_key, provider, league_id, season):
    """Retrieve fixture data from API provider"""
    if not api_key or api_key == "YOUR_API_KEY_HERE":
        print("API Key not set. Using local mock data...")
        return MOCK_MATCHES

    # --- PROVIDER: football-data.org ---
    if provider == "football-data":
        print(f"Calling football-data.org for League: {league_id}, Season: {season}...")
        url = f"https://api.football-data.org/v4/competitions/{league_id}/matches"
        headers = {
            "X-Auth-Token": api_key
        }
        params = {
            "season": season
        }
        try:
            response = requests.get(url, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if "matches" not in data or not data["matches"]:
                print("No matches returned from football-data.org. Using mock data...")
                return MOCK_MATCHES
                
            fixtures = []
            for item in data["matches"]:
                status_raw = item.get("status", "SCHEDULED")
                if status_raw == "FINISHED":
                    status = "FT"
                elif status_raw in ["IN_PLAY", "PAUSED"]:
                    status = "Live"
                else:
                    status = "NS"
                
                # Lấy tỉ số đúng - cấu trúc API football-data.org:
                # - fullTime   = tổng tích lũy (có cả penalty) -> KHÔNG dùng!
                # - regularTime = tỉ số sau 90p -> luôn lấy cái này
                # - extraTime   = bàn thắng TRONG hiệp phụ (cộng vào regularTime)
                # - penalties   = số bàn luân lưu thuần
                score_obj = item.get("score", {})
                duration = score_obj.get("duration", "REGULAR")
                score_regular = score_obj.get("regularTime") or {}
                score_extra = score_obj.get("extraTime") or {}

                if duration in ("EXTRA_TIME", "PENALTY_SHOOTOUT") and score_regular.get("home") is not None and score_extra.get("home") is not None:
                    # Trận có hiệp phụ: cộng regularTime + extraTime
                    home_score = str(score_regular.get("home", 0) + score_extra.get("home", 0))
                    away_score = str(score_regular.get("away", 0) + score_extra.get("away", 0))
                elif score_regular.get("home") is not None:
                    # Trận kết thúc sau 90p bình thường
                    home_score = str(score_regular.get("home"))
                    away_score = str(score_regular.get("away"))
                else:
                    # Fallback nếu API không có regularTime (trận chưa đá)
                    score_ft = score_obj.get("fullTime") or {}
                    home_score = str(score_ft.get("home")) if score_ft.get("home") is not None else ""
                    away_score = str(score_ft.get("away")) if score_ft.get("away") is not None else ""
                
                stage_raw = item.get("stage", "World Cup")
                round_name = stage_raw.replace("_", " ").title()
                group_name = item.get("group")
                if group_name:
                    round_name += f" - {group_name.replace('_', ' ').title()}"

                fixtures.append({
                    "match_id": str(item["id"]),
                    "date": item["utcDate"],
                    "round": round_name,
                    "home_team": item["homeTeam"]["name"],
                    "away_team": item["awayTeam"]["name"],
                    "home_logo": item["homeTeam"].get("crest", ""),
                    "away_logo": item["awayTeam"].get("crest", ""),
                    "home_score": home_score,
                    "away_score": away_score,
                    "status": status
                })
            return fixtures
        except Exception as e:
            print(f"Error calling football-data.org: {e}. Using mock data...")
            return MOCK_MATCHES

    # --- PROVIDER: api-football.com (api-sports) ---
    else:
        print(f"Calling api-football.com for League ID: {league_id}, Season: {season}...")
        url = "https://v3.football.api-sports.io/fixtures"
        headers = {
            "x-apisports-key": api_key
        }
        params = {
            "league": league_id,
            "season": season
        }
        
        if provider == "rapidapi":
            url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
            headers = {
                "x-rapidapi-key": api_key,
                "x-rapidapi-host": "api-football-v1.p.rapidapi.com"
            }

        try:
            response = requests.get(url, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if "errors" in data and data["errors"]:
                print(f"API-Sports errors: {data['errors']}. Using mock data...")
                return MOCK_MATCHES

            if "response" not in data or not data["response"]:
                print("No matches returned from API-Sports. Using mock data...")
                return MOCK_MATCHES
                
            fixtures = []
            for item in data["response"]:
                fix = item["fixture"]
                league = item["league"]
                teams = item["teams"]
                goals = item["goals"]
                
                home_score = str(goals["home"]) if goals["home"] is not None else ""
                away_score = str(goals["away"]) if goals["away"] is not None else ""
                
                fixtures.append({
                    "match_id": str(fix["id"]),
                    "date": fix["date"],
                    "round": league.get("round", "World Cup"),
                    "home_team": teams["home"]["name"],
                    "away_team": teams["away"]["name"],
                    "home_logo": teams["home"]["logo"],
                    "away_logo": teams["away"]["logo"],
                    "home_score": home_score,
                    "away_score": away_score,
                    "status": fix["status"]["short"]
                })
            return fixtures
        except Exception as e:
            print(f"Error calling API-Football: {e}. Using mock data...")
            return MOCK_MATCHES

def update_google_sheets(fixtures):
    """Update matches data in Google Sheet"""
    all_rows = matches_sheet.get_all_records()
    existing_matches = {str(row["match_id"]): (i + 2, row) for i, row in enumerate(all_rows)}
    
    updates = []
    appends = []
    
    for f in fixtures:
        m_id = f["match_id"]
        row_data = [
            f["match_id"], f["date"], f["round"], 
            f["home_team"], f["away_team"], 
            f["home_logo"], f["away_logo"], 
            f["home_score"], f["away_score"], 
            f["status"]
        ]
        
        if m_id in existing_matches:
            row_num, existing_data = existing_matches[m_id]
            if (str(existing_data.get("home_score")) != f["home_score"] or 
                str(existing_data.get("away_score")) != f["away_score"] or 
                existing_data.get("status") != f["status"] or
                existing_data.get("home_logo") == "" and f["home_logo"] != ""):
                
                range_label = f"A{row_num}:J{row_num}"
                updates.append({
                    "range": range_label,
                    "values": [row_data]
                })
        else:
            appends.append(row_data)

    if updates:
        matches_sheet.batch_update(updates)
        print(f"Updated score/status for {len(updates)} matches.")
        
    if appends:
        matches_sheet.append_rows(appends, value_input_option="USER_ENTERED")
        print(f"Appended {len(appends)} new matches to Sheet.")
        
    if not updates and not appends:
        print("All matches are up-to-date. No changes made.")

if __name__ == "__main__":
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting World Cup data sync...")
    
    provider = config.get("api_provider", "football-data")
    api_key = config.get("api_key")
    season = config.get("season", 2026)
    league_id = config.get("league_id", "WC") if provider == "football-data" else config.get("league_id", 1)
    
    fixtures_data = get_live_fixtures(api_key, provider, league_id, season)
    update_google_sheets(fixtures_data)
    print("Sync completed successfully.")
