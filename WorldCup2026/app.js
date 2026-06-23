/**
 * WORLD CUP 2026 PREDICTION SYSTEM - FRONTEND APP
 */

// CẤU HÌNH URL GOOGLE APPS SCRIPT Ở ĐÂY ĐỂ NHÂN VIÊN KHÔNG PHẢI NHẬP LẠI
const DEFAULT_API_URL = "https://script.google.com/macros/s/AKfycbwfVY2LtzMaWSYS53PROoOv46ZoWdPijbC4pamSBiDcK0WnCkdkdwSuIpaR1lJj5WixKQ/exec";
const START_DATE_LIMIT = "2026-06-22T17:00:00.000Z"; // Giờ Việt Nam: 23/06/2026 00:00:00

class WCApp {
    constructor() {
        this.apiUrl = localStorage.getItem("wc_api_url") || DEFAULT_API_URL || "";
        this.currentUser = JSON.parse(localStorage.getItem("wc_user")) || null;
        this.matches = [];
        this.userPredictions = {};
        this.tempPredictions = {}; // Lưu giữ tạm thời tỉ số đang nhập dở
        this.leaderboard = [];

        this.currentSection = "matches"; // matches hoặc leaderboard
        this.matchFilter = "upcoming";   // upcoming hoặc completed

        // Cập nhật giao diện ban đầu
        this.init();
    }

    init() {
        // Cập nhật giá trị vào Input Config
        const configInput = document.getElementById("api-url-input");
        if (configInput) {
            configInput.value = this.apiUrl;
        }

        // Hiện/ẩn banner cấu hình nếu chưa có API URL
        this.updateConfigVisibility();

        // Kiểm tra đăng nhập
        this.updateAuthUI();

        // Tải dữ liệu nếu đã có API
        if (this.apiUrl) {
            this.fetchData();
        }

        // Tự động làm mới dữ liệu mỗi 2 phút nếu đang xem bảng đấu
        setInterval(() => {
            if (this.apiUrl && this.currentUser) {
                this.fetchData(true); // âm thầm tải không hiện loading
            }
        }, 120000);
    }

    // ------------------------------------------------------------------
    // CẤU HÌNH CỔNG KẾT NỐI
    // ------------------------------------------------------------------
    saveConfig() {
        const url = document.getElementById("api-url-input").value.trim();
        if (!url) {
            this.showToast("Vui lòng nhập URL Web App!", "error");
            return;
        }

        if (!url.startsWith("https://script.google.com/")) {
            this.showToast("URL Google Apps Script không đúng định dạng!", "error");
            return;
        }

        this.apiUrl = url;
        localStorage.setItem("wc_api_url", url);
        this.showToast("Đã lưu cấu hình kết nối thành công!", "success");
        this.updateConfigVisibility();
        this.fetchData();
    }

    updateConfigVisibility() {
        const configPanel = document.getElementById("config-panel");
        if (this.apiUrl) {
            // Đã cấu hình, ẩn banner
            configPanel.style.display = "none";
        } else {
            configPanel.style.display = "block";
        }
    }

    // ------------------------------------------------------------------
    // QUẢN LÝ TÀI KHOẢN (AUTH)
    // ------------------------------------------------------------------
    toggleAuthForm(isRegister) {
        document.getElementById("login-form-container").classList.toggle("hidden", isRegister);
        document.getElementById("register-form-container").classList.toggle("hidden", !isRegister);
    }

    updateAuthUI() {
        const authSec = document.getElementById("auth-section");
        const matchSec = document.getElementById("matches-section");
        const userBadge = document.getElementById("user-info-area");
        const usernameDisp = document.getElementById("user-display-name");

        if (this.currentUser) {
            authSec.classList.add("hidden");
            matchSec.classList.remove("hidden");
            userBadge.classList.remove("hidden");
            usernameDisp.textContent = `${this.currentUser.fullname} (${this.currentUser.department})`;

            // Đang xem phần nào thì hiện phần đó
            this.switchSection(this.currentSection);
        } else {
            authSec.classList.remove("hidden");
            matchSec.classList.add("hidden");
            document.getElementById("leaderboard-section").classList.add("hidden");
            userBadge.classList.add("hidden");
        }
    }

    async handleRegister(event) {
        event.preventDefault();
        if (!this.apiUrl) {
            this.showToast("Vui lòng cấu hình URL Web App trước khi đăng ký!", "error");
            return;
        }

        const username = document.getElementById("reg-username").value.trim().toLowerCase();
        const password = document.getElementById("reg-password").value;
        const fullname = document.getElementById("reg-fullname").value.trim();
        const department = document.getElementById("reg-department").value.trim();

        // Simple validation
        if (!/^[a-z0-9_]+$/.test(username)) {
            this.showToast("Tên đăng nhập chỉ chứa chữ thường, số, dấu gạch dưới!", "error");
            return;
        }

        this.showLoadingButton("register-form", true);

        try {
            const res = await this.postAPI({
                action: "register",
                username,
                password,
                fullname,
                department
            });

            if (res.success) {
                this.showToast(res.message, "success");
                
                // Tự động đăng nhập sau khi đăng ký thành công
                this.currentUser = {
                    username: username,
                    fullname: fullname,
                    department: department,
                    password: password
                };
                localStorage.setItem("wc_user", JSON.stringify(this.currentUser));
                this.updateAuthUI();
                
                // Tải dữ liệu ban đầu
                this.fetchData();

                // Reset form đăng ký
                document.getElementById("register-form").reset();
            } else {
                this.showToast(res.message, "error");
            }
        } catch (err) {
            this.showToast("Lỗi kết nối máy chủ đăng ký!", "error");
        } finally {
            this.showLoadingButton("register-form", false);
        }
    }

    async handleLogin(event) {
        event.preventDefault();
        if (!this.apiUrl) {
            this.showToast("Vui lòng cấu hình URL Web App trước khi đăng nhập!", "error");
            return;
        }

        const username = document.getElementById("login-username").value.trim().toLowerCase();
        const password = document.getElementById("login-password").value;

        this.showLoadingButton("login-form", true);

        try {
            const res = await this.postAPI({
                action: "login",
                username,
                password
            });

            if (res.success) {
                this.showToast(res.message, "success");
                // Lưu thông tin đăng nhập kèm mật khẩu để xác thực API dự đoán sau này
                this.currentUser = {
                    username: res.user.username,
                    fullname: res.user.fullname,
                    department: res.user.department,
                    password: password
                };
                localStorage.setItem("wc_user", JSON.stringify(this.currentUser));
                this.updateAuthUI();
                this.fetchData();
            } else {
                this.showToast(res.message, "error");
            }
        } catch (err) {
            this.showToast("Lỗi kết nối xác thực đăng nhập!", "error");
        } finally {
            this.showLoadingButton("login-form", false);
        }
    }

    logout() {
        this.currentUser = null;
        this.tempPredictions = {};
        localStorage.removeItem("wc_user");
        this.updateAuthUI();
        this.showToast("Đã đăng xuất tài khoản.", "info");
    }

    // ------------------------------------------------------------------
    // ĐỒNG BỘ DỮ LIỆU TỪ GOOGLE SHEETS
    // ------------------------------------------------------------------
    async fetchData(silent = false) {
        if (!this.apiUrl) return;

        const container = document.getElementById("matches-list");
        if (!silent) {
            container.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 3rem;"><div class="loading-spinner"></div><p style="margin-top: 1rem; color: var(--text-secondary);">Đang tải dữ liệu từ Google Sheets...</p></div>`;
        }

        const usernameParam = this.currentUser ? this.currentUser.username : "";
        try {
            const response = await fetch(`${this.apiUrl}?action=getInitData&username=${usernameParam}`);
            if (!response.ok) throw new Error("HTTP error " + response.status);

            const data = await response.json();

            this.matches = data.matches || [];
            this.leaderboard = data.leaderboard || [];

            // Lưu dự đoán của user hiện tại dưới dạng Map
            this.userPredictions = {};
            if (data.userPredictions) {
                data.userPredictions.forEach(p => {
                    this.userPredictions[p.match_id] = p;
                });
            }

            this.renderMatches();
            this.renderLeaderboard();

            if (!silent) {
                this.showToast("Đã cập nhật dữ liệu mới nhất!", "success");
            }
        } catch (err) {
            console.error(err);
            if (!silent) {
                container.innerHTML = `<div style="grid-column: 1/-1; text-align: center; color: var(--accent-danger); padding: 3rem;"><i class="fa-solid fa-triangle-exclamation" style="font-size: 2.5rem; margin-bottom: 1rem;"></i><p>Không kết nối được với Google Sheet Database. Kiểm tra cấu hình URL Apps Script!</p></div>`;
                this.showToast("Cập nhật dữ liệu thất bại!", "error");
            }
        }
    }

    // ------------------------------------------------------------------
    // HIỂN THỊ DỮ LIỆU LÊN GIAO DIỆN
    // ------------------------------------------------------------------
    switchSection(section) {
        this.currentSection = section;

        const matchesBtn = document.getElementById("nav-matches");
        const leaderboardBtn = document.getElementById("nav-leaderboard");
        const matchesSec = document.getElementById("matches-section");
        const leaderboardSec = document.getElementById("leaderboard-section");

        if (section === "matches") {
            matchesBtn.classList.add("active");
            leaderboardBtn.classList.remove("active");
            matchesSec.classList.remove("hidden");
            leaderboardSec.classList.add("hidden");
        } else {
            matchesBtn.classList.remove("active");
            leaderboardBtn.classList.add("active");
            matchesSec.classList.add("hidden");
            leaderboardSec.classList.remove("hidden");
        }
    }

    filterMatches(filter) {
        this.matchFilter = filter;
        document.getElementById("tab-upcoming").classList.toggle("active", filter === "upcoming");
        document.getElementById("tab-completed").classList.toggle("active", filter === "completed");
        this.renderMatches();
    }

    renderMatches() {
        const container = document.getElementById("matches-list");
        const msg = document.getElementById("no-matches-msg");
        container.innerHTML = "";

        const now = new Date();
        const twoDaysLater = new Date(now.getTime() + 2 * 24 * 60 * 60 * 1000);

        // Lọc trận đấu
        const filtered = this.matches.filter(m => {
            const matchDate = new Date(m.date);
            const limitDate = new Date(START_DATE_LIMIT);
            if (matchDate < limitDate) return false; // Ẩn trận trước 23/06/2026 VN

            const isFinished = m.status === "FT" || m.status === "Finished";
            if (this.matchFilter === "completed") {
                return isFinished;
            } else {
                // Chỉ hiển thị các trận sắp diễn ra trong vòng 2 ngày (48 giờ) sắp tới
                return !isFinished && matchDate <= twoDaysLater;
            }
        });

        // Sắp xếp: trận sắp đá gần nhất lên trước, trận đã đá xong thì trận mới nhất lên trước
        filtered.sort((a, b) => {
            const dateA = new Date(a.date);
            const dateB = new Date(b.date);
            return this.matchFilter === "completed" ? dateB - dateA : dateA - dateB;
        });

        if (filtered.length === 0) {
            msg.classList.remove("hidden");
            const submitAllContainer = document.getElementById("submit-all-container");
            if (submitAllContainer) submitAllContainer.classList.add("hidden");
            return;
        }
        msg.classList.add("hidden");

        filtered.forEach(m => {
            const matchDate = new Date(m.date);

            // Format thời gian hiển thị theo giờ Việt Nam
            const formattedDate = matchDate.toLocaleDateString("vi-VN", { weekday: 'long', year: 'numeric', month: '2-digit', day: '2-digit' });
            const formattedTime = matchDate.toLocaleTimeString("vi-VN", { hour: '2-digit', minute: '2-digit', hour12: false });

            // Lấy dự đoán cũ của user
            const pred = this.userPredictions[m.match_id];
            const hasPred = pred !== undefined;
            
            // Lấy dự đoán tạm thời đang gõ dở
            const tempPred = this.tempPredictions[m.match_id];
            
            // Giá trị hiển thị trên ô nhập
            let predHome = "";
            let predAway = "";
            
            if (tempPred !== undefined) {
                predHome = tempPred.predicted_home;
                predAway = tempPred.predicted_away;
            } else if (hasPred) {
                predHome = pred.predicted_home;
                predAway = pred.predicted_away;
            }

            // Kiểm tra trạng thái đóng dự đoán (15 phút trước giờ bóng lăn)
            const minutesLeft = (matchDate - now) / (1000 * 60);
            const isLocked = minutesLeft < 15 || m.status === "FT" || m.status === "Finished" || m.status === "Live";

            let footerHTML = "";
            let cardClasses = "match-card";

            if (isLocked) {
                cardClasses += " completed";
                if (m.status === "FT" || m.status === "Finished") {
                    // Trận đấu đã kết thúc -> Hiện điểm kiếm được
                    const points = this.calculateMatchPoints(m, pred);
                    let pointsLabel = "";
                    let pointsClass = "";

                    if (hasPred) {
                        const realHome = parseInt(m.home_score);
                        const realAway = parseInt(m.away_score);
                        const predHome = parseInt(pred.predicted_home);
                        const predAway = parseInt(pred.predicted_away);
                        
                        if (realHome === predHome && realAway === predAway) {
                            pointsLabel = "Chính xác (0đ)";
                            pointsClass = "points-exact";
                        } else {
                            pointsLabel = `${points} Điểm (Đoán sai)`;
                            pointsClass = "points-wrong";
                        }
                    } else {
                        // points mang giá trị âm nhân đôi (-2 * stagePoints)
                        pointsLabel = `${points} Điểm (Không dự đoán)`;
                        pointsClass = "points-wrong";
                    }

                    footerHTML = `
                        <div class="match-footer">
                            <span class="prediction-status">Kết quả: ${m.home_score} - ${m.away_score}</span>
                            <span class="points-earned ${pointsClass}">${pointsLabel}</span>
                        </div>
                    `;
                } else {
                    // Trận đấu đang đá hoặc đã khóa sổ mà chưa có kết quả
                    footerHTML = `
                        <div class="match-footer">
                            <span class="prediction-status" style="color: var(--accent-warning);">
                                <i class="fa-solid fa-lock"></i> Đã đóng cổng dự đoán
                            </span>
                            <span class="points-earned points-pending">Đang đợi tỷ số thực tế</span>
                        </div>
                    `;
                }
            } else {
                // Trận đấu cho phép điền dự đoán
                const lockTimeText = this.getLockCountdown(minutesLeft);
                footerHTML = `
                    <div class="match-footer">
                        <span class="predict-time-limit" title="Đóng cổng 15 phút trước giờ bóng lăn">
                            <i class="fa-regular fa-clock"></i> Còn ${lockTimeText}
                        </span>
                        <span style="color: var(--primary-color); font-size: 0.85rem; font-weight: 600;">
                            <i class="fa-solid fa-pen-to-square"></i> Đang mở cổng
                        </span>
                    </div>
                `;
            }

            // Xác định màu sắc của ô nhập tỉ số dự đoán khi đã kết thúc
            let inputHomeClass = "";
            let inputAwayClass = "";
            const isFinished = m.status === "FT" || m.status === "Finished";
            if (isFinished) {
                if (hasPred) {
                    const realHome = parseInt(m.home_score);
                    const realAway = parseInt(m.away_score);
                    const prHome = parseInt(pred.predicted_home);
                    const prAway = parseInt(pred.predicted_away);
                    if (realHome === prHome && realAway === prAway) {
                        inputHomeClass = "pred-correct";
                        inputAwayClass = "pred-correct";
                    } else {
                        inputHomeClass = "pred-wrong";
                        inputAwayClass = "pred-wrong";
                    }
                } else {
                    inputHomeClass = "pred-wrong";
                    inputAwayClass = "pred-wrong";
                }
            }

            const card = document.createElement("div");
            card.className = cardClasses;
            card.innerHTML = `
                <div class="match-meta">
                    <span class="match-round">${m.round}</span>
                    <span class="match-date"><i class="fa-regular fa-calendar"></i> ${formattedDate} lúc ${formattedTime}</span>
                </div>
                <div class="match-main">
                    <!-- Đội nhà -->
                    <div class="team">
                        <img src="${m.home_logo || 'https://media.api-sports.io/football/teams/95.png'}" class="team-logo" alt="${m.home_team}">
                        <span class="team-name">${m.home_team}</span>
                    </div>

                    <!-- Tỷ số & Trạng thái giữa trận -->
                    <div class="vs-container">
                        ${isLocked && (m.status === "FT" || m.status === "Finished") ?
                    `<span class="score-display">${m.home_score} - ${m.away_score}</span>` :
                    (m.status === "Live" ? `<span class="live-badge">LIVE</span>` : `<span class="vs-text">VS</span>`)
                }
                        
                        <!-- Ô nhập tỉ số dự đoán -->
                        <div class="predict-inputs">
                            <input type="number" id="pred-home-${m.match_id}" class="predict-input ${inputHomeClass}" min="0" max="99" value="${predHome}" ${isLocked ? 'disabled' : ''} placeholder="-" oninput="app.saveTemp('${m.match_id}', 'home', this.value)">
                            <span style="color: var(--text-secondary); font-weight: bold;">:</span>
                            <input type="number" id="pred-away-${m.match_id}" class="predict-input ${inputAwayClass}" min="0" max="99" value="${predAway}" ${isLocked ? 'disabled' : ''} placeholder="-" oninput="app.saveTemp('${m.match_id}', 'away', this.value)">
                        </div>
                        <div style="font-size: 0.75rem; color: var(--text-secondary); text-align: center; margin-top: 0.2rem;">
                            ${hasPred ? '<span style="color: var(--accent-success); font-weight: 600;"><i class="fa-solid fa-check"></i> Đã dự đoán</span>' : 'Chưa dự đoán'}
                        </div>
                    </div>

                    <!-- Đội khách -->
                    <div class="team">
                        <img src="${m.away_logo || 'https://media.api-sports.io/football/teams/96.png'}" class="team-logo" alt="${m.away_team}">
                        <span class="team-name">${m.away_team}</span>
                    </div>
                </div>
                ${footerHTML}
            `;
            container.appendChild(card);
        });

        // Quản lý hiển thị nút gửi dự đoán hàng loạt
        const submitAllContainer = document.getElementById("submit-all-container");
        if (submitAllContainer) {
            const hasEditableMatch = filtered.some(m => {
                const matchDate = new Date(m.date);
                const minutesLeft = (matchDate - now) / (1000 * 60);
                return minutesLeft >= 15 && m.status !== "FT" && m.status !== "Finished" && m.status !== "Live";
            });

            if (this.currentUser && this.matchFilter === "upcoming" && hasEditableMatch) {
                submitAllContainer.classList.remove("hidden");
            } else {
                submitAllContainer.classList.add("hidden");
            }
        }
    }

    async submitAllPredictions() {
        if (!this.apiUrl) {
            this.showToast("Cổng kết nối API chưa được cấu hình!", "error");
            return;
        }

        if (!this.currentUser) {
            this.showToast("Vui lòng đăng nhập để gửi dự đoán!", "error");
            return;
        }

        // Thu thập các giá trị người dùng đã điền
        const predictions = [];
        const matchCards = document.querySelectorAll(".match-card:not(.completed)");

        matchCards.forEach(card => {
            const inputs = card.querySelectorAll(".predict-input");
            if (inputs.length === 2) {
                const homeInput = inputs[0];
                const awayInput = inputs[1];

                const matchId = homeInput.id.replace("pred-home-", "");
                const homeVal = homeInput.value.trim();
                const awayVal = awayInput.value.trim();

                // Chỉ lấy các trận được người dùng điền tỉ số đầy đủ
                if (homeVal !== "" && awayVal !== "") {
                    predictions.push({
                        match_id: matchId,
                        predicted_home: parseInt(homeVal),
                        predicted_away: parseInt(awayVal)
                    });
                }
            }
        });

        if (predictions.length === 0) {
            this.showToast("Vui lòng điền tỷ số cho ít nhất một trận đấu!", "info");
            return;
        }

        // Hiệu ứng loading trên nút
        const btn = document.getElementById("btn-submit-all");
        const originalText = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = `<div class="loading-spinner" style="width: 18px; height: 18px; display: inline-block; vertical-align: middle; margin-right: 5px;"></div> Đang gửi dữ liệu...`;

        try {
            const res = await this.postAPI({
                action: "predictBatch",
                username: this.currentUser.username,
                password: this.currentUser.password,
                predictions: predictions
            });

            if (res.success) {
                this.showToast(res.message, "success");

                // Đồng bộ cục bộ và xóa dự đoán tạm thời
                predictions.forEach(p => {
                    this.userPredictions[p.match_id] = {
                        match_id: p.match_id,
                        predicted_home: p.predicted_home,
                        predicted_away: p.predicted_away
                    };
                    delete this.tempPredictions[p.match_id];
                });

                this.renderMatches();
                this.fetchData(true); // Tải lại ngầm để cập nhật BXH
            } else {
                this.showToast(res.message, "error");
            }
        } catch (err) {
            this.showToast("Lỗi kết nối khi gửi dữ đoán hàng loạt!", "error");
        } finally {
            btn.disabled = false;
            btn.innerHTML = originalText;
        }
    }

    saveTemp(matchId, side, value) {
        if (!this.tempPredictions[matchId]) {
            this.tempPredictions[matchId] = { predicted_home: "", predicted_away: "" };
        }
        if (side === "home") {
            this.tempPredictions[matchId].predicted_home = value;
        } else {
            this.tempPredictions[matchId].predicted_away = value;
        }
    }

    renderLeaderboard() {
        const tbody = document.getElementById("leaderboard-rows");
        const msg = document.getElementById("no-leaderboard-msg");
        tbody.innerHTML = "";

        if (this.leaderboard.length === 0) {
            msg.classList.remove("hidden");
            return;
        }
        msg.classList.add("hidden");

        this.leaderboard.forEach((row, index) => {
            const tr = document.createElement("tr");

            // Đánh dấu dòng của User hiện tại để dễ tìm
            if (this.currentUser && row.username === this.currentUser.username) {
                tr.style.backgroundColor = "rgba(99, 102, 241, 0.12)";
                tr.style.borderLeft = "4px solid var(--primary-color)";
            }

            const rank = index + 1;
            let rankClass = "";
            if (rank === 1) rankClass = "rank-1";
            else if (rank === 2) rankClass = "rank-2";
            else if (rank === 3) rankClass = "rank-3";

            tr.innerHTML = `
                <td class="rank-col ${rankClass}">
                    <span class="rank-badge">${rank}</span>
                </td>
                <td>
                    <div class="fullname-display">${row.fullname}</div>
                    <div class="username-display">@${row.username}</div>
                </td>
                <td>${row.department || "N/A"}</td>
                <td style="text-align: center; font-weight: 600; color: var(--text-secondary);">${row.totalNeeded || 0}</td>
                <td style="text-align: center; font-weight: 600; color: var(--accent-success);">${row.exactMatches || 0}</td>
                <td style="text-align: center; font-weight: 600; color: var(--accent-danger);">${row.wrongMatches || 0}</td>
                <td style="text-align: right; color: #ef4444; font-weight: bold;" class="points-display">${row.totalPoints || 0} đ</td>
            `;
            tbody.appendChild(tr);
        });
    }

    // ------------------------------------------------------------------
    // TÍNH ĐIỂM DỰ ĐOÁN PHỤC VỤ HIỂN THỊ OFFLINE TRÊN GIAO DIỆN
    // ------------------------------------------------------------------
    getStagePoints(roundName) {
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

    calculateMatchPoints(match, prediction) {
        // Nếu trận đấu diễn ra trước ngày giới hạn -> Không tính điểm
        const matchDate = new Date(match.date);
        const limitDate = new Date(START_DATE_LIMIT);
        if (matchDate < limitDate) return 0;

        if (!prediction) {
            // Không tham gia dự đoán -> Trừ gấp đôi điểm của vòng đấu đó
            return -2 * this.getStagePoints(match.round);
        }

        const realHome = parseInt(match.home_score);
        const realAway = parseInt(match.away_score);
        const predHome = parseInt(prediction.predicted_home);
        const predAway = parseInt(prediction.predicted_away);

        if (isNaN(realHome) || isNaN(realAway) || isNaN(predHome) || isNaN(predAway)) {
            // Dự đoán lỗi -> Trừ gấp đôi điểm
            return -2 * this.getStagePoints(match.round);
        }

        // Nếu dự đoán đúng: Không bị trừ điểm (0đ)
        if (realHome === predHome && realAway === predAway) {
            return 0;
        }

        // Nếu dự đoán sai: Trừ số điểm của vòng đấu đó
        return -this.getStagePoints(match.round);
    }

    // Tính thời gian đếm ngược đến lúc khóa sổ
    getLockCountdown(minutesLeft) {
        if (minutesLeft < 60) {
            return `${Math.floor(minutesLeft)} phút`;
        }
        const hours = Math.floor(minutesLeft / 60);
        const days = Math.floor(hours / 24);

        if (days > 0) {
            return `${days} ngày ${hours % 24} giờ`;
        }
        return `${hours} giờ ${Math.floor(minutesLeft % 60)} phút`;
    }

    // ------------------------------------------------------------------
    // GỬI DỰ ĐOÁN LÊN GOOGLE SHEETS
    // ------------------------------------------------------------------
    async submitPrediction(matchId) {
        if (!this.apiUrl) {
            this.showToast("Cổng kết nối API chưa được cấu hình!", "error");
            return;
        }

        if (!this.currentUser) {
            this.showToast("Vui lòng đăng nhập để gửi dự đoán!", "error");
            return;
        }

        const inputHomeVal = document.getElementById(`pred-home-${matchId}`).value;
        const inputAwayVal = document.getElementById(`pred-away-${matchId}`).value;

        if (inputHomeVal === "" || inputAwayVal === "") {
            this.showToast("Vui lòng nhập đầy đủ tỉ số cả 2 đội!", "error");
            return;
        }

        const predicted_home = parseInt(inputHomeVal);
        const predicted_away = parseInt(inputAwayVal);

        if (predicted_home < 0 || predicted_away < 0) {
            this.showToast("Tỷ số dự đoán không thể là số âm!", "error");
            return;
        }

        try {
            const res = await this.postAPI({
                action: "predict",
                username: this.currentUser.username,
                password: this.currentUser.password,
                match_id: matchId,
                predicted_home: predicted_home,
                predicted_away: predicted_away
            });

            if (res.success) {
                this.showToast(res.message, "success");

                // Cập nhật local dự đoán để giao diện đổi màu
                this.userPredictions[matchId] = {
                    match_id: matchId,
                    predicted_home: predicted_home,
                    predicted_away: predicted_away
                };

                this.renderMatches();

                // Tải lại dữ liệu ngầm để cập nhật bảng xếp hạng
                this.fetchData(true);
            } else {
                this.showToast(res.message, "error");
            }
        } catch (err) {
            this.showToast("Lỗi kết nối khi gửi dự đoán!", "error");
        }
    }

    // ------------------------------------------------------------------
    // UTILS & API HELPERS
    // ------------------------------------------------------------------
    async postAPI(data) {
        try {
            const corsResponse = await fetch(this.apiUrl, {
                method: "POST",
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded" // Chuẩn dễ kết nối Apps Script nhất
                },
                body: JSON.stringify(data)
            });
            return await corsResponse.json();
        } catch (e) {
            console.error("POST Error details:", e);
            throw e;
        }
    }

    showLoadingButton(formId, isLoading) {
        const btn = document.querySelector(`#${formId} button[type="submit"]`);
        if (!btn) return;

        if (isLoading) {
            btn.disabled = true;
            btn.innerHTML = `<div class="loading-spinner" style="width: 18px; height: 18px;"></div> Đang xử lý...`;
        } else {
            btn.disabled = false;
            if (formId === "login-form") {
                btn.innerHTML = `<span>Đăng Nhập</span> <i class="fa-solid fa-arrow-right-to-bracket"></i>`;
            } else {
                btn.innerHTML = `<span>Tạo Tài Khoản</span> <i class="fa-solid fa-user-plus"></i>`;
            }
        }
    }

    showToast(message, type = "success") {
        const container = document.getElementById("toast-container");
        const toast = document.createElement("div");
        toast.className = `toast ${type}`;

        let icon = "fa-circle-check";
        if (type === "error") icon = "fa-triangle-exclamation";
        else if (type === "info") icon = "fa-circle-info";

        toast.innerHTML = `
            <i class="fa-solid ${icon}"></i>
            <span>${message}</span>
        `;

        container.appendChild(toast);

        // Tự động xóa toast sau 4 giây
        setTimeout(() => {
            toast.style.animation = "slideUp 0.3s reverse forwards";
            setTimeout(() => {
                toast.remove();
            }, 300);
        }, 4000);
    }
}

// Khởi tạo đối tượng toàn cục
const app = new WCApp();
