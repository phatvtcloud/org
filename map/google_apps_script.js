/**
 * BẢN ĐỒ QUIZ - GOOGLE APPS SCRIPT BACKEND
 * 
 * Hướng dẫn cài đặt:
 * 1. Mở file Google Sheet "DC_Quiz_Database" của bạn (hoặc tạo mới nếu chưa có).
 * 2. Chọn mục: Tiện ích mở rộng (Extensions) -> Apps Script.
 * 3. Xóa hết mã code mặc định, copy toàn bộ nội dung file này dán vào.
 * 4. Bấm biểu tượng "Lưu" (Save).
 * 5. Bấm nút "Triển khai" (Deploy) -> "Tối ưu hóa lượt triển khai mới" (New deployment).
 * 6. Chọn loại hình triển khai (Select type) là: Ứng dụng web (Web app).
 * 7. Cấu hình triển khai:
 *    - Thực thi dưới danh nghĩa: Tôi (Execute as: Me / email của bạn).
 *    - Ai có quyền truy cập: Mọi người (Who has access: Anyone).
 * 8. Bấm nút "Triển khai" (Deploy) và cấp quyền truy cập (Authorize access) nếu Google yêu cầu.
 * 9. Copy lấy URL của Web App vừa tạo để dán vào cấu hình `APPS_SCRIPT_URL` trong file `index.html` của game.
 */

// ------------------------------------------------------------------
// API GET REQUEST handler
// ------------------------------------------------------------------
function doGet(e) {
  try {
    const action = e.parameter.action;
    if (action === "getRankings") {
      const data = getRankings();
      return jsonResponse(data);
    }
    return jsonResponse({ error: "Invalid GET action" }, 400);
  } catch (err) {
    return jsonResponse({ error: err.toString() }, 500);
  }
}

// ------------------------------------------------------------------
// API POST REQUEST handler
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
    if (action === "saveRound") {
      const result = handleSaveRound(postData);
      return jsonResponse(result);
    }
    return jsonResponse({ error: "Invalid POST action" }, 400);
  } catch (err) {
    return jsonResponse({ error: err.toString() }, 500);
  }
}

// Helper: Trả về phản hồi JSON với Headers CORS
function jsonResponse(data, statusCode = 200) {
  return ContentService.createTextOutput(JSON.stringify(data))
    .setMimeType(ContentService.MimeType.JSON);
}

// ------------------------------------------------------------------
// XỬ LÝ LƯU TRỮ TRÒ CHƠI THEO LƯỢT (BATCH SAVE)
// ------------------------------------------------------------------
function handleSaveRound(data) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName("Result");
  if (!sheet) {
    sheet = ss.insertSheet("Result");
    sheet.appendRow([
      "Timestamp", "Session ID", "Username", "Game Mode", 
      "Question Number", "Target Name", "Target Type", 
      "Answer Lat", "Answer Lng", "Target Lat", "Target Lng", 
      "Distance Error (km)", "Is Correct", "Response Time (s)"
    ]);
  }
  
  const answers = data.answers || [];
  if (answers.length === 0) {
    return { success: false, message: "Không có dữ liệu câu trả lời để lưu." };
  }
  
  const timestamp = Utilities.formatDate(new Date(), "GMT+7", "yyyy-MM-dd HH:mm:ss");
  const rows = [];
  
  answers.forEach(a => {
    rows.push([
      timestamp,
      data.sessionId || "",
      data.username || "Anonymous",
      data.gameMode || "",
      a.questionNumber || 1,
      a.targetName || "",
      a.targetType || "",
      a.answerLat !== null && a.answerLat !== undefined ? a.answerLat : "",
      a.answerLng !== null && a.answerLng !== undefined ? a.answerLng : "",
      a.targetLat !== null && a.targetLat !== undefined ? a.targetLat : "",
      a.targetLng !== null && a.targetLng !== undefined ? a.targetLng : "",
      a.distanceError !== null && a.distanceError !== undefined ? a.distanceError : "",
      str(a.isCorrect).toUpperCase(),
      a.responseTime || 0
    ]);
  });
  
  // Ghi hàng loạt vào bảng
  const lastRow = sheet.getLastRow();
  const range = sheet.getRange(lastRow + 1, 1, rows.length, 14);
  range.setValues(rows);
  
  return { success: true, count: rows.length };
}

function str(val) {
  return (val === true || val === "true" || val === "TRUE") ? "TRUE" : "FALSE";
}

// ------------------------------------------------------------------
// XỬ LÝ LẤY BẢNG XẾP HẠNG & PIVOT NGƯỜI CHƠI
// ------------------------------------------------------------------
function getRankings() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName("Result");
  if (!sheet) {
    return {
      provinces: { rounds: [], players: [] },
      dc_factory: { rounds: [], players: [] }
    };
  }
  
  const data = sheet.getDataRange().getValues();
  if (data.length <= 1) {
    return {
      provinces: { rounds: [], players: [] },
      dc_factory: { rounds: [], players: [] }
    };
  }
  
  const headers = data[0];
  const records = [];
  
  // Ánh xạ vị trí cột
  const idx = {};
  headers.forEach((h, i) => {
    idx[h] = i;
  });
  
  for (let i = 1; i < data.length; i++) {
    const row = data[i];
    records.push({
      timestamp: row[idx["Timestamp"]],
      sessionId: row[idx["Session ID"]],
      username: row[idx["Username"]],
      gameMode: row[idx["Game Mode"]],
      questionNumber: Number(row[idx["Question Number"]]),
      targetName: row[idx["Target Name"]],
      targetType: row[idx["Target Type"]],
      isCorrect: (row[idx["Is Correct"]] === true || row[idx["Is Correct"]].toString().toUpperCase() === "TRUE"),
      responseTime: Number(row[idx["Response Time (s)"]])
    });
  }
  
  // Nhóm theo Session ID
  const sessions = {};
  records.forEach(r => {
    const key = r.sessionId;
    if (!sessions[key]) {
      sessions[key] = {
        sessionId: r.sessionId,
        gameMode: r.gameMode,
        username: r.username,
        timestamp: r.timestamp,
        correctCount: 0,
        totalCount: 0,
        totalTime: 0
      };
    }
    sessions[key].totalCount += 1;
    if (r.isCorrect) {
      sessions[key].correctCount += 1;
    }
    sessions[key].totalTime += r.responseTime;
  });
  
  // Chuyển đổi thành danh sách vòng chơi
  const rounds = Object.keys(sessions).map(k => {
    const s = sessions[k];
    const acc = s.totalCount > 0 ? Math.round((s.correctCount / s.totalCount) * 1000) / 10 : 0;
    
    // Định dạng chuỗi thời gian
    let timeStr = Math.round(s.totalTime) + "s";
    if (s.totalTime >= 60) {
      timeStr = Math.floor(s.totalTime / 60) + "m " + Math.round(s.totalTime % 60) + "s";
    }
    
    // Định dạng ngày tháng
    let dateStr = "";
    if (s.timestamp) {
      try {
        const d = new Date(s.timestamp);
        dateStr = d.getFullYear() + "-" + 
                  String(d.getMonth() + 1).padStart(2, '0') + "-" + 
                  String(d.getDate()).padStart(2, '0') + " " + 
                  String(d.getHours()).padStart(2, '0') + ":" + 
                  String(d.getMinutes()).padStart(2, '0') + ":" + 
                  String(d.getSeconds()).padStart(2, '0');
      } catch (err) {
        dateStr = s.timestamp.toString();
      }
    }
    
    return {
      sessionId: s.sessionId,
      gameMode: s.gameMode,
      username: s.username,
      total: s.totalCount,
      correct: s.correctCount,
      accuracy: acc,
      time: s.totalTime,
      timeStr: timeStr,
      date: dateStr
    };
  });
  
  const provincesRounds = rounds.filter(r => r.gameMode === "provinces");
  const dcFactoryRounds = rounds.filter(r => r.gameMode === "dc_factory" || r.gameMode === "dc_factory_mode"); // Tương thích cả hai tên mode
  
  // Sắp xếp vòng chơi: độ chính xác giảm dần, thời gian tăng dần
  const sortRounds = (a, b) => {
    if (b.accuracy !== a.accuracy) return b.accuracy - a.accuracy;
    return a.time - b.time;
  };
  provincesRounds.sort(sortRounds);
  dcFactoryRounds.sort(sortRounds);
  
  // Pivot người chơi
  const pivotPlayers = (roundsList) => {
    const playersDict = {};
    roundsList.forEach(r => {
      const user = r.username;
      if (!playersDict[user]) {
        playersDict[user] = {
          username: user,
          accuracySum: 0,
          timeSum: 0,
          roundsCount: 0
        };
      }
      playersDict[user].accuracySum += r.accuracy;
      playersDict[user].timeSum += r.time;
      playersDict[user].roundsCount += 1;
    });
    
    const players = Object.keys(playersDict).map(k => {
      const p = playersDict[k];
      const avgAcc = Math.round((p.accuracySum / p.roundsCount) * 10) / 10;
      const avgTime = p.timeSum / p.roundsCount;
      
      let timeStr = Math.round(avgTime) + "s";
      if (avgTime >= 60) {
        timeStr = Math.floor(avgTime / 60) + "m " + Math.round(avgTime % 60) + "s";
      }
      
      return {
        username: p.username,
        avgAccuracy: avgAcc,
        avgTime: avgTime,
        avgTimeStr: timeStr,
        roundsCount: p.roundsCount
      };
    });
    
    // Sắp xếp người chơi
    players.sort((a, b) => {
      if (b.avgAccuracy !== a.avgAccuracy) return b.avgAccuracy - a.avgAccuracy;
      return a.avgTime - b.avgTime;
    });
    
    return players;
  };
  
  return {
    provinces: {
      rounds: provincesRounds,
      players: pivotPlayers(provincesRounds)
    },
    dc_factory: {
      rounds: dcFactoryRounds,
      players: pivotPlayers(dcFactoryRounds)
    }
  };
}
