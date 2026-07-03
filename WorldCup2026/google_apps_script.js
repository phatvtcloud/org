/**
 * WORLD CUP 2026 PREDICTION SYSTEM - BACKEND API & AUTO SYNC
 * Copy toàn bộ mã này dán vào mục Extensions -> Apps Script trong Google Sheet của bạn.
 * Sau đó bấm "Deploy" -> "New deployment" -> Chọn type "Web app".
 * - Execute as: Me (your email)
 * - Who has access: Anyone
 * Copy lấy URL Web App để cấu hình vào file config của trang web.
 */

const SPREADSHEET_ID = "1YiYTfP1pKri7m_s0Gnv5edP_Q_HVJTxQomCF4Nd5sUk"; // ID của Google Sheet của bạn

// CẤU HÌNH API FOOTBALL-DATA.ORG ĐỂ ĐỒNG BỘ TỰ ĐỘNG KHÔNG CẦN CHẠY PYTHON
const FOOTBALL_DATA_API_KEY = "df420228f4c04224838e20cc1b30d2af"; // Token bạn đã đăng ký
const COMPETITION_CODE = "WC";
const SEASON = 2026;

function getSpreadsheet() {
  return SpreadsheetApp.openById(SPREADSHEET_ID);
}

// ------------------------------------------------------------------
// CẤU HÌNH API ĐẦU VÀO GET (LẤY DỮ LIỆU)
// ------------------------------------------------------------------
function doGet(e) {
  try {
    const action = e.parameter.action;
    const username = e.parameter.username;
    
    if (action === "getInitData") {
      const data = getInitData(username);
      return jsonResponse(data);
    }
    
    return jsonResponse({ error: "Invalid GET action" }, 400);
  } catch (err) {
    return jsonResponse({ error: err.toString() }, 500);
  }
}

// ------------------------------------------------------------------
// CẤU HÌNH API ĐẦU VÀO POST (GỬI DỮ LIỆU)
// ------------------------------------------------------------------
function doPost(e) {
  try {
    let postData;
    if (e.postData && e.postData.contents) {
      postData = JSON.parse(e.postData.contents);
    } else {
      postData = e.parameter;
    }
    
    const action = postData.action;
    
    if (action === "register") {
      return jsonResponse(handleRegister(postData));
    }
    
    if (action === "login") {
      return jsonResponse(handleLogin(postData));
    }
    
    if (action === "predict") {
      return jsonResponse(handlePredict(postData));
    }

    if (action === "predictBatch") {
      return jsonResponse(handlePredictBatch(postData));
    }
    
    return jsonResponse({ error: "Invalid POST action" }, 400);
  } catch (err) {
    return jsonResponse({ error: err.toString() }, 500);
  }
}

// Helper: Trả về JSON với Headers CORS đầy đủ
function jsonResponse(data, statusCode = 200) {
  const output = ContentService.createTextOutput(JSON.stringify(data))
    .setMimeType(ContentService.MimeType.JSON);
  return output;
}

// ------------------------------------------------------------------
// CHỨC NĂNG LẤY DỮ LIỆU ĐẦU VÀO CHO FRONTEND
// ------------------------------------------------------------------
function getInitData(username) {
  const ss = getSpreadsheet();
  
  // 1. Đọc danh sách Trận đấu (Matches)
  const matchesSheet = ss.getSheetByName("Matches");
  const matchesData = matchesSheet.getDataRange().getValues();
  const matchesHeaders = matchesData[0];
  const matches = [];
  
  for (let i = 1; i < matchesData.length; i++) {
    const row = matchesData[i];
    const match = {};
    matchesHeaders.forEach((header, index) => {
      match[header] = row[index];
    });
    matches.push(match);
  }
  
  // 2. Đọc danh sách dự đoán (Predictions) của tất cả mọi người để tính điểm
  const predsSheet = ss.getSheetByName("Predictions");
  const predsData = predsSheet.getDataRange().getValues();
  const predsHeaders = predsData[0];
  const allPredictions = [];
  
  for (let i = 1; i < predsData.length; i++) {
    const row = predsData[i];
    const pred = {};
    predsHeaders.forEach((header, index) => {
      pred[header] = row[index];
    });
    allPredictions.push(pred);
  }
  
  // Lọc riêng dự đoán của User đang đăng nhập
  const userPredictions = allPredictions.filter(p => p.username === username);
  
  // 3. Đọc thông tin Users
  const usersSheet = ss.getSheetByName("Users");
  const usersData = usersSheet.getDataRange().getValues();
  const usersHeaders = usersData[0];
  const users = {};
  
  for (let i = 1; i < usersData.length; i++) {
    const row = usersData[i];
    const user = {};
    usersHeaders.forEach((header, index) => {
      if (header !== "password") { // Bảo mật
        user[header] = row[index];
      }
    });
    users[user.username] = user;
  }
  
  // 4. Tính toán Bảng xếp hạng (Leaderboard) thời gian thực
  const leaderboard = calculateLeaderboard(matches, allPredictions, users);
  
  return {
    matches: matches,
    userPredictions: userPredictions,
    leaderboard: leaderboard,
    serverTime: new Date().toISOString()
  };
}

// Helper: Xác định điểm số theo từng giai đoạn trận đấu
function getStagePoints(roundName) {
  if (!roundName) return 10;
  const r = roundName.toUpperCase();
  if (r.includes("FINAL") && !r.includes("SEMI") && !r.includes("QUARTER") && !r.includes("THIRD")) {
    return 500;
  }
  if (r.includes("THIRD") || r.includes("3RD") || r.includes("BRONZE")) {
    return 200;
  }
  if (r.includes("SEMI")) {
    return 100;
  }
  if (r.includes("QUARTER")) {
    return 50;
  }
  if (r.includes("16") || r.includes("LAST 16") || r.includes("ROUND OF 16")) {
    return 30;
  }
  if (r.includes("32") || r.includes("LAST 32") || r.includes("ROUND OF 32")) {
    return 15;
  }
  return 10; // Mặc định Vòng bảng (Group Stage)
}

// ------------------------------------------------------------------
// THUẬT TOÁN TÍNH ĐIỂM & BẢNG XẾP HẠNG
// ------------------------------------------------------------------
function calculateLeaderboard(matches, predictions, users) {
  const limitDate = new Date("2026-06-22T17:00:00.000Z"); // Chỉ tính trận từ 23/06/2026 00:00:00 giờ Việt Nam
  
  const finishedMatches = matches.filter(m => {
    return (m.status === "FT" || m.status === "Finished") && new Date(m.date) >= limitDate;
  });
  
  const totalNeeded = finishedMatches.length;
  
  // Bản đồ dự đoán: username -> match_id -> prediction
  const predMap = {};
  predictions.forEach(p => {
    const uname = p.username.toLowerCase();
    if (!predMap[uname]) {
      predMap[uname] = {};
    }
    predMap[uname][p.match_id] = p;
  });
  
  const userPoints = {};
  Object.keys(users).forEach(uname => {
    const lowerUname = uname.toLowerCase();
    userPoints[lowerUname] = {
      username: uname,
      fullname: users[uname].fullname || uname,
      department: users[uname].department || "",
      img_url: users[uname].img_url || "",
      totalNeeded: totalNeeded,
      exactMatches: 0,
      wrongMatches: 0,
      totalPoints: 0
    };
  });
  
  finishedMatches.forEach(match => {
    const stagePoints = getStagePoints(match.round);
    const realHome = parseInt(match.home_score);
    const realAway = parseInt(match.away_score);
    if (isNaN(realHome) || isNaN(realAway)) return;
    
    Object.keys(userPoints).forEach(lowerUname => {
      const userStat = userPoints[lowerUname];
      const userPreds = predMap[lowerUname] || {};
      const p = userPreds[match.match_id];
      
      if (p) {
        const predHome = parseInt(p.predicted_home);
        const predAway = parseInt(p.predicted_away);
        if (isNaN(predHome) || isNaN(predAway)) {
          // Lỗi dữ liệu coi như không dự đoán -> Trừ gấp đôi
          userStat.totalPoints -= (2 * stagePoints);
          userStat.wrongMatches += 1;
          return;
        }
        
        if (realHome === predHome && realAway === predAway) {
          // Đoán trúng -> Không bị trừ điểm (0đ)
          userStat.exactMatches += 1;
        } else {
          // Đoán sai -> Trừ số điểm của vòng đấu
          userStat.wrongMatches += 1;
          userStat.totalPoints -= stagePoints;
        }
      } else {
        // Không tham gia dự đoán -> Trừ gấp đôi
        userStat.totalPoints -= (2 * stagePoints);
      }
    });
  });
  
  const rankList = Object.keys(userPoints).map(k => userPoints[k]);
  rankList.sort((a, b) => {
    if (b.totalPoints !== a.totalPoints) {
      return b.totalPoints - a.totalPoints; // Điểm cao hơn (âm ít hơn) xếp trước
    }
    return b.exactMatches - a.exactMatches; // Trúng nhiều hơn xếp trước
  });
  
  return rankList;
}

// ------------------------------------------------------------------
// XỬ LÝ ĐĂNG KÝ THÀNH VIÊN
// ------------------------------------------------------------------
function handleRegister(data) {
  const username = (data.username || "").trim().toLowerCase();
  const password = data.password || "";
  const fullname = (data.fullname || "").trim();
  const department = (data.department || "").trim();
  
  if (!username || !password || !fullname) {
    return { success: false, message: "Vui lòng nhập đầy đủ thông tin đăng ký!" };
  }
  
  if (username.length < 3) {
    return { success: false, message: "Tên đăng nhập phải từ 3 ký tự trở lên!" };
  }
  
  const ss = getSpreadsheet();
  const sheet = ss.getSheetByName("Users");
  const rows = sheet.getDataRange().getValues();
  
  for (let i = 1; i < rows.length; i++) {
    if (rows[i][0].toString().toLowerCase() === username) {
      return { success: false, message: "Tên đăng nhập đã tồn tại trong hệ thống!" };
    }
  }
  
  sheet.appendRow([
    username,
    password,
    fullname,
    department,
    new Date().toISOString()
  ]);
  
  return { success: true, message: "Đăng ký thành công! Bạn có thể đăng nhập ngay." };
}

// ------------------------------------------------------------------
// XỬ LÝ ĐĂNG NHẬP
// ------------------------------------------------------------------
function handleLogin(data) {
  const username = (data.username || "").trim().toLowerCase();
  const password = data.password || "";
  
  if (!username || !password) {
    return { success: false, message: "Vui lòng điền tên đăng nhập và mật khẩu!" };
  }
  
  const ss = getSpreadsheet();
  const sheet = ss.getSheetByName("Users");
  const rows = sheet.getDataRange().getValues();
  
  for (let i = 1; i < rows.length; i++) {
    if (rows[i][0].toString().toLowerCase() === username) {
      if (rows[i][1].toString() === password) {
        return { 
          success: true, 
          message: "Đăng nhập thành công!",
          user: {
            username: username,
            fullname: rows[i][2],
            department: rows[i][3]
          }
        };
      } else {
        return { success: false, message: "Mật khẩu không chính xác!" };
      }
    }
  }
  
  return { success: false, message: "Tài khoản không tồn tại!" };
}

// ------------------------------------------------------------------
// XỬ LÝ GHI DỰ ĐOÁN ĐƠN LẺ
// ------------------------------------------------------------------
function handlePredict(data) {
  const username = (data.username || "").trim().toLowerCase();
  const password = data.password || "";
  const matchId = (data.match_id || "").toString();
  const predHome = parseInt(data.predicted_home);
  const predAway = parseInt(data.predicted_away);
  
  if (isNaN(predHome) || isNaN(predAway)) {
    return { success: false, message: "Tỷ số dự đoán không hợp lệ!" };
  }
  
  const ss = getSpreadsheet();
  
  // 1. Xác thực tài khoản
  const usersSheet = ss.getSheetByName("Users");
  const usersRows = usersSheet.getDataRange().getValues();
  let isAuthenticated = false;
  for (let i = 1; i < usersRows.length; i++) {
    if (usersRows[i][0].toString().toLowerCase() === username && usersRows[i][1].toString() === password) {
      isAuthenticated = true;
      break;
    }
  }
  if (!isAuthenticated) {
    return { success: false, message: "Xác thực tài khoản thất bại!" };
  }
  
  // 2. Kiểm tra xem trận đấu đã bắt đầu chưa (khóa dự đoán trước giờ đá 15 phút)
  const matchesSheet = ss.getSheetByName("Matches");
  const matchesRows = matchesSheet.getDataRange().getValues();
  let matchRow = null;
  for (let i = 1; i < matchesRows.length; i++) {
    if (matchesRows[i][0].toString() === matchId) {
      matchRow = {
        rowNum: i + 1,
        dateStr: matchesRows[i][1],
        status: matchesRows[i][9]
      };
      break;
    }
  }
  
  if (!matchRow) {
    return { success: false, message: "Không tìm thấy trận đấu này!" };
  }
  
  const matchDate = new Date(matchRow.dateStr);
  const now = new Date();
  const timeDifferenceMinutes = (matchDate - now) / (1000 * 60);
  
  if (timeDifferenceMinutes < 15 || matchRow.status === "FT" || matchRow.status === "Live" || matchRow.status === "Finished") {
    return { success: false, message: "Đã đóng cổng dự đoán trận này (15 phút trước giờ đá)!" };
  }
  
  // 3. Ghi dự đoán (Upsert)
  const predsSheet = ss.getSheetByName("Predictions");
  const predsRows = predsSheet.getDataRange().getValues();
  const predictionId = `${username}_${matchId}`;
  let existingRowIndex = -1;
  
  for (let i = 1; i < predsRows.length; i++) {
    if (predsRows[i][0] === predictionId) {
      existingRowIndex = i + 1;
      break;
    }
  }
  
  if (existingRowIndex !== -1) {
    predsSheet.getRange(existingRowIndex, 4, 1, 4).setValues([[
      predHome,
      predAway,
      "",
      new Date().toISOString()
    ]]);
    return { success: true, message: "Đã cập nhật dự đoán!" };
  } else {
    predsSheet.appendRow([
      predictionId,
      username,
      matchId,
      predHome,
      predAway,
      "",
      new Date().toISOString()
    ]);
    return { success: true, message: "Gửi dự đoán thành công!" };
  }
}

// ------------------------------------------------------------------
// XỬ LÝ GHI DỰ ĐOÁN HÀNG LOẠT (BATCH PREDICT)
// ------------------------------------------------------------------
function handlePredictBatch(data) {
  const username = (data.username || "").trim().toLowerCase();
  const password = data.password || "";
  const predictions = data.predictions || [];
  
  if (predictions.length === 0) {
    return { success: false, message: "Không có dự đoán nào để lưu!" };
  }
  
  const ss = getSpreadsheet();
  
  // 1. Xác thực tài khoản
  const usersSheet = ss.getSheetByName("Users");
  const usersRows = usersSheet.getDataRange().getValues();
  let isAuthenticated = false;
  for (let i = 1; i < usersRows.length; i++) {
    if (usersRows[i][0].toString().toLowerCase() === username && usersRows[i][1].toString() === password) {
      isAuthenticated = true;
      break;
    }
  }
  if (!isAuthenticated) {
    return { success: false, message: "Xác thực tài khoản thất bại! Vui lòng đăng nhập lại." };
  }
  
  // 2. Tải lịch thi đấu để kiểm tra thời gian khóa sổ
  const matchesSheet = ss.getSheetByName("Matches");
  const matchesRows = matchesSheet.getDataRange().getValues();
  const matchMap = {};
  for (let i = 1; i < matchesRows.length; i++) {
    matchMap[matchesRows[i][0].toString()] = {
      dateStr: matchesRows[i][1],
      status: matchesRows[i][9]
    };
  }
  
  // 3. Tải danh sách dự đoán cũ để tìm vị trí dòng (Upsert)
  const predsSheet = ss.getSheetByName("Predictions");
  const predsRows = predsSheet.getDataRange().getValues();
  const existingPreds = {}; // predictionId -> row_index (1-based)
  for (let i = 1; i < predsRows.length; i++) {
    existingPreds[predsRows[i][0]] = i + 1;
  }
  
  let successCount = 0;
  let errorMessages = [];
  const now = new Date();
  
  predictions.forEach(p => {
    const matchId = p.match_id.toString();
    const predHome = parseInt(p.predicted_home);
    const predAway = parseInt(p.predicted_away);
    
    if (isNaN(predHome) || isNaN(predAway)) return;
    
    const match = matchMap[matchId];
    if (!match) {
      errorMessages.push(`Không tìm thấy trận đấu ID ${matchId}`);
      return;
    }
    
    // Kiểm tra thời gian (khóa sổ 15 phút trước giờ bóng lăn)
    const matchDate = new Date(match.dateStr);
    const timeDifferenceMinutes = (matchDate - now) / (1000 * 60);
    if (timeDifferenceMinutes < 15 || match.status === "FT" || match.status === "Live" || match.status === "Finished") {
      errorMessages.push(`Trận đấu ID ${matchId} đã đóng cổng dự đoán.`);
      return;
    }
    
    const predictionId = `${username}_${matchId}`;
    const rowData = [
      predictionId,
      username,
      matchId,
      predHome,
      predAway,
      "", // Điểm
      new Date().toISOString()
    ];
    
    if (existingPreds[predictionId]) {
      const rowNum = existingPreds[predictionId];
      predsSheet.getRange(rowNum, 4, 1, 4).setValues([[
        predHome,
        predAway,
        "",
        new Date().toISOString()
      ]]);
    } else {
      predsSheet.appendRow(rowData);
      existingPreds[predictionId] = predsSheet.getLastRow();
    }
    successCount++;
  });
  
  if (successCount === 0) {
    return { success: false, message: "Không lưu được dự đoán nào! " + errorMessages.join(", ") };
  }
  
  let message = `Đã lưu thành công ${successCount} dự đoán!`;
  if (errorMessages.length > 0) {
    message += ` (Có ${errorMessages.length} lỗi do trận đấu đã bắt đầu).`;
  }
  return { success: true, message: message };
}

// ------------------------------------------------------------------
// ĐỒNG BỘ LỊCH THI ĐẤU TỰ ĐỘNG TRÊN CLOUD (KHÔNG CẦN CHẠY PYTHON)
// ------------------------------------------------------------------
function syncMatchesFromAPI() {
  if (!FOOTBALL_DATA_API_KEY || FOOTBALL_DATA_API_KEY === "YOUR_FOOTBALL_DATA_API_KEY_HERE") {
    Logger.log("FOOTBALL_DATA_API_KEY chưa được thiết lập.");
    return;
  }
  
  const url = `https://api.football-data.org/v4/competitions/${COMPETITION_CODE}/matches?season=${SEASON}`;
  const options = {
    headers: {
      "X-Auth-Token": FOOTBALL_DATA_API_KEY
    },
    muteHttpExceptions: true
  };
  
  try {
    const response = UrlFetchApp.fetch(url, options);
    if (response.getResponseCode() !== 200) {
      Logger.log("Lỗi khi kết nối API: " + response.getContentText());
      return;
    }
    
    const data = JSON.parse(response.getContentText());
    if (!data.matches || data.matches.length === 0) {
      Logger.log("Không tìm thấy trận đấu nào từ API.");
      return;
    }
    
    const ss = getSpreadsheet();
    const sheet = ss.getSheetByName("Matches");
    const rows = sheet.getDataRange().getValues();
    const existingMatches = {}; // match_id -> row_index (1-based)
    
    for (let i = 1; i < rows.length; i++) {
      existingMatches[rows[i][0].toString()] = i + 1;
    }
    
    let updateCount = 0;
    let appendCount = 0;
    
    data.matches.forEach(item => {
      const matchId = item.id.toString();
      
      // Map trạng thái
      let status = "NS";
      if (item.status === "FINISHED") status = "FT";
      else if (item.status === "IN_PLAY" || item.status === "PAUSED") status = "Live";
      
      // Lấy tỉ số đúng - cấu trúc API football-data.org:
      // - fullTime    = tổng tích lũy (có cả penalty) -> KHÔNG dùng!
      // - regularTime = tỉ số sau 90p -> luôn lấy cái này
      // - extraTime   = bàn thắng TRONG hiệp phụ (cộng vào regularTime)
      // - penalties   = số bàn luân lưu thuần
      const scoreObj = item.score || {};
      const duration = scoreObj.duration || "REGULAR";
      const scoreRegular = scoreObj.regularTime || {};
      const scoreExtra = scoreObj.extraTime || {};

      let homeScore, awayScore;
      if ((duration === "EXTRA_TIME" || duration === "PENALTY_SHOOTOUT")
          && scoreRegular.home !== null && scoreRegular.home !== undefined
          && scoreExtra.home !== null && scoreExtra.home !== undefined) {
        // Trận có hiệp phụ: cộng regularTime + extraTime
        homeScore = (scoreRegular.home + scoreExtra.home).toString();
        awayScore = (scoreRegular.away + scoreExtra.away).toString();
      } else if (scoreRegular.home !== null && scoreRegular.home !== undefined) {
        // Trận kết thúc sau 90p bình thường
        homeScore = scoreRegular.home.toString();
        awayScore = scoreRegular.away.toString();
      } else {
        // Fallback nếu API không có regularTime (trận chưa đá)
        const scoreFt = scoreObj.fullTime || {};
        homeScore = (scoreFt.home !== null && scoreFt.home !== undefined) ? scoreFt.home.toString() : "";
        awayScore = (scoreFt.away !== null && scoreFt.away !== undefined) ? scoreFt.away.toString() : "";
      }
      
      let roundName = (item.stage || "World Cup").replace(/_/g, " ");
      roundName = roundName.toLowerCase().replace(/\b\w/g, c => c.toUpperCase());
      if (item.group) {
        roundName += " - " + item.group.replace(/_/g, " ").toLowerCase().replace(/\b\w/g, c => c.toUpperCase());
      }
      
      const rowData = [
        matchId,
        item.utcDate,
        roundName,
        item.homeTeam.name,
        item.awayTeam.name,
        item.homeTeam.crest || "",
        item.awayTeam.crest || "",
        homeScore,
        awayScore,
        status
      ];
      
      if (existingMatches[matchId]) {
        const rowNum = existingMatches[matchId];
        const oldRow = rows[rowNum - 1];
        
        // Kiểm tra xem có thay đổi tỉ số hoặc trạng thái không
        if (oldRow[7].toString() !== homeScore || oldRow[8].toString() !== awayScore || oldRow[9] !== status || oldRow[5] === "" && rowData[5] !== "") {
          sheet.getRange(rowNum, 1, 1, 10).setValues([rowData]);
          updateCount++;
        }
      } else {
        sheet.appendRow(rowData);
        appendCount++;
      }
    });
    
    Logger.log(`Đồng bộ hoàn thành. Đã thêm mới: ${appendCount}, Cập nhật: ${updateCount}`);
  } catch (err) {
    Logger.log("Lỗi đồng bộ tự động: " + err.toString());
  }
}
