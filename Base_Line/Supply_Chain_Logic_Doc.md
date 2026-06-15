# TÀI LIỆU KỸ THUẬT: LOGIC & DATA FLOW MẠNG LƯỚI CHUỖI CUNG ỨNG (SUPPLY CHAIN NETWORK)

Tài liệu này mô tả chi tiết luồng xử lý dữ liệu (Data Flow), các công thức toán học (Formulas) và kiến trúc thuật toán thực tế được triển khai trong script Python `generate_supply_chain_3View.py` để xây dựng Sơ đồ mạng lưới và Bảng phân tích Pivot.

---

## 1. TỔNG QUAN LUỒNG DỮ LIỆU (DATA FLOW)
Hệ thống sử dụng Python (Pandas) để chuẩn hóa (ETL) từ nhiều nguồn dữ liệu rời rạc, tính toán các chỉ số vận hành logistics, sau đó kết xuất ra mô hình dữ liệu quan hệ (`Masterdata.csv`) và hiển thị tương tác trên nền tảng Web (`HTML/JS` kết hợp `Vis.js`).

**Các Sheet Dữ liệu Đầu vào:**
1. **D2C:** Chứa thông tin giao dịch chặng cuối cấp thấp (`Item No`, `DC_Out`, `Customer Number`, `RR 3m`).
2. **Parameter:** Chứa các tham số vĩ mô quy định hệ số lưu kho (`DOH`, `DRP - Stock`) và hằng số trọng tải chuyển đổi thể tích xe (`Values` - Tấn, `Values_2` - M3).
3. **MD06:** Master Data của sản phẩm (Hệ số quy đổi `UOM Conversion / Pallet`, `Pallet chồng đôi` (Y/N), `Tấn/ UOM Conversion`, `M3/ UOM Conversion`, Phân loại `Nặng/Nhẹ`, `Moving Type`).
4. **F2D:** Mapping luồng hàng hóa từ DC_Out + Item No $\rightarrow$ Factory.
5. **D2D:** Mapping luồng hàng hóa từ Factory + DC_Out $\rightarrow$ DC_DRP + các loại xe chuyên chở chặng trung chuyển (`Loại xe F2D`, `Loại xe D2D`).
6. **Shipto:** Master Data của Khách hàng (Tên, Tỉnh thành, Loại xe giao hàng chặng cuối `Loại xe D2C`).
7. **People:** Năng suất nhân sự (`Capacity_Thruput`) theo từng `DC_out`.
8. **Appendix:** Cấu hình thứ tự hiển thị sắp xếp UI (Y-Axis Order) cho Factory, DC và Province.

---

## 2. LOGIC TÍNH TOÁN CÁC CHỈ SỐ CƠ BẢN (BASE METRICS)
Từ bảng `D2C` gốc, dữ liệu được join (Left Join) với `MD06` để tính toán khối lượng, thể tích và số lượng Pallet đầu ra.

*   **Case (Nhu cầu thùng):**
    $$\text{Case} = \text{RR 3m}$$
*   **Tấn (Ton):**
    $$\text{Tấn} = \text{Case} \times \text{Tấn/ UOM Conversion}$$
*   **M3 (Volume):**
    $$\text{M3} = \text{Case} \times \text{M3/ UOM Conversion}$$
*   **Pallet Chặng Cuối (Pallet OB D2C):**
    $$\text{Pallet OB D2C} = \begin{cases} 
    \frac{\text{Case}}{\text{UOM Conversion / Pallet}}, & \text{nếu UOM Conversion / Pallet} \neq 0 \text{ và hợp lệ} \\ 
    0, & \text{ngược lại} 
    \end{cases}$$
*   **Multiplier (Hệ số xếp chồng):**
    $$\text{Multiplier} = \begin{cases} 1, & \text{nếu Pallet chồng đôi} = \text{"Y"} \\ 2, & \text{ngược lại} \end{cases}$$
*   **DOH (Days on Hand):** Được map từ `Moving Type` thông qua cấu hình trong sheet `Parameter` (ví dụ: `Very fast moving`, `Fast moving`, `Normal moving`, `Slow moving`). Nếu rỗng thì mặc định là `0`.
*   **Tồn kho tại DC_Out (Stock Pos):**
    $$\text{Stock Pos} = \text{Pallet OB D2C} \times \text{DOH} \times \text{Multiplier}$$

---

## 3. LOGIC LUỒNG TRUNG CHUYỂN (FLOW METRICS)
Hệ thống định nghĩa luồng hàng hóa qua 3 chặng chính: 
1. **F2D (Factory to DRP):** Factory $\rightarrow$ DC_DRP.
2. **D2D (DRP to Out):** DC_DRP $\rightarrow$ DC_Out.
3. **D2C (Out to Customer):** DC_Out $\rightarrow$ Customer.

*Lưu ý: Nếu không có cấu hình DC_DRP trong bảng D2D cho cặp [Factory, DC_Out], hệ thống tự động gán DC_DRP = DC_Out (không phát sinh trung chuyển chặng D2D).*

*   **D2D (DRP to Out):**
    $$\text{Pallet OB D2D} = \begin{cases} \text{Pallet OB D2C}, & \text{nếu } \text{DC\_DRP} \neq \text{DC\_Out} \\ 0, & \text{nếu } \text{DC\_DRP} = \text{DC\_Out} \end{cases}$$
    $$\text{Pallet IB D2D} = \text{Pallet OB D2D}$$
*   **F2D (Factory to DRP):**
    $$\text{Pallet OB F2D} = \text{Pallet OB D2C}$$
    $$\text{Pallet IB F2D} = \text{Pallet OB D2C}$$

---

## 4. LOGIC TÍNH TOÁN NHU CẦU XE (VEHICLE CAPACITY)
Dựa trên loại xe (`Loại xe F2D`, `Loại xe D2D`, `Loại xe D2C`) và đặc tính hàng hóa (`Nặng/Nhẹ`), hệ thống quy đổi nhu cầu vận tải sang số lượng xe chuyên chở.

**Hàm quy đổi xe tổng quát (`calc_vehicle`):**
Với mỗi loại xe đích $T$ có giới hạn tải trọng $V_1$ (cột `Values` trong Parameter) và giới hạn thể tích $V_2$ (cột `Values_2` trong Parameter):

$$\text{Số lượng xe} = \begin{cases} 
\frac{\text{M3}}{V_2}, & \text{nếu Nặng/Nhẹ} = \text{"Nhẹ"} \\ 
\frac{\text{Tấn}}{V_1}, & \text{nếu Nặng/Nhẹ} = \text{"Nặng"} 
\end{cases}$$
*(Công thức chỉ áp dụng khi Loại xe được cấu hình khớp với loại xe đích $T$, ngược lại trả về 0).*

**Áp dụng cụ thể cho các chặng:**
1.  **F2D Vehicles:**
    *   `F2D Cont bộ` = `calc_vehicle` với `Loại xe F2D` và xe đích `"Cont bộ"`
    *   `F2D Cont biển` = `calc_vehicle` với `Loại xe F2D` và xe đích `"Cont biển"`
    *   `F2D Xe pallet` = `calc_vehicle` với `Loại xe F2D` và xe đích `"Xe pallet"`
    *   `F2D Actual Tấn` = `Tấn` (nếu hàng "Nặng" và có Loại xe F2D), ngược lại là 0.
    *   `F2D Actual M3` = `M3` (nếu hàng "Nhẹ" và có Loại xe F2D), ngược lại là 0.
2.  **D2D Vehicles:** (nhân thêm điều kiện $0$ nếu $\text{DC\_DRP} = \text{DC\_Out}$)
    *   `D2D Cont bộ` = `calc_vehicle` với `Loại xe D2D` và xe đích `"Cont bộ"` $\times$ $\text{d2d\_cond}$
    *   `D2D Cont biển` = `calc_vehicle` với `Loại xe D2D` và xe đích `"Cont biển"` $\times$ $\text{d2d\_cond}$
    *   `D2D Xe pallet` = `calc_vehicle` với `Loại xe D2D` và xe đích `"Xe pallet"` $\times$ $\text{d2d\_cond}$
    *   `D2D Actual Tấn` = `Tấn` (nếu hàng "Nặng", có Loại xe D2D và $\text{DC\_DRP} \neq \text{DC\_Out}$), ngược lại là 0.
    *   `D2D Actual M3` = `M3` (nếu hàng "Nhẹ", có Loại xe D2D và $\text{DC\_DRP} \neq \text{DC\_Out}$), ngược lại là 0.
3.  **D2C Vehicles:** (Giao từ DC_Out đến Khách hàng)
    *   `D2C Truck 15 tấn` = `calc_vehicle` với `Loại xe D2C` và xe đích `"Truck 15 tấn"`
    *   `D2C Truck 2 tấn` = `calc_vehicle` với `Loại xe D2C` và xe đích `"Truck 2 tấn"`
    *   `D2C Actual Tấn` = `Tấn` (nếu hàng "Nặng" và có Loại xe D2C), ngược lại là 0.
    *   `D2C Actual M3` = `M3` (nếu hàng "Nhẹ" và có Loại xe D2C), ngược lại là 0.

---

## 5. LOGIC GOM NHÓM NODE TRÊN SƠ ĐỒ (NODE AGGREGATIONS)
Trên đồ thị (Vis.js), dữ liệu được gom nhóm (Group By) theo các trạm (Nodes) trên luồng chuỗi cung ứng. 

1.  **Factory Nodes (Level 1):**
    *   `pallet_ob_f2d` = $\sum \text{Pallet OB F2D}$
    *   `xe_pallet` = $\sum \text{F2D Xe pallet}$
    *   `cont_bien` = $\sum \text{F2D Cont biển}$
    *   `cont_bo` = $\sum \text{F2D Cont bộ}$
2.  **DC_DRP Nodes (Level 2):**
    *   `pallet_ob_d2d` = $\sum \text{Pallet OB D2D}$
    *   `pallet_ib_f2d` = $\sum \text{Pallet IB F2D}$
    *   `drp_stock` = $\sum \text{Pallet OB D2D} \times \text{DRP - Stock}$
    *   `xe_pallet` = $\sum \text{D2D Xe pallet}$
    *   `cont_bien` = $\sum \text{D2D Cont biển}$
    *   `cont_bo` = $\sum \text{D2D Cont bộ}$
3.  **DC_Out Nodes (Level 3):**
    *   `cases` = $\sum \text{Case}$
    *   `pallet_ob_d2c` = $\sum \text{Pallet OB D2C}$
    *   `stock_pos` = $\sum \text{Stock Pos}$
    *   `pallet_ib_d2d` = $\sum \text{Pallet IB D2D}$
    *   `truck_15_tan` = $\sum \text{D2D Xe pallet}$ *(Lưu lượng đầu vào từ chặng D2D)*
    *   `truck_2_tan` = $\sum \text{D2D Cont biển}$ *(Lưu lượng đầu vào từ chặng D2D)*
4.  **Province Nodes (Level 4):** Group by Tỉnh/Thành phố.
5.  **Customer Nodes (Level 5):** Kết xuất động (Dynamic Render) dựa trên bộ lọc ở Client Side.

---

## 6. LOGIC PIVOT TABLE & RESOURCE PANEL
Cả 2 bảng này đều hiển thị dữ liệu tổng hợp theo **DC (kết hợp cả vai trò DRP và Out)**.

Các cột tính toán chính (Computed Columns):
*   **DRP Stock** = $\sum \text{Pallet OB D2D}$ (tại DC_DRP) $\times$ `DRP - Stock`
*   **Total Stock Pos** = `Stock Pos` (tại DC_Out) + `DRP Stock` (tại DC_DRP)
*   **Diện tích (M2)** = `Total Stock Pos` $\times$ `M2 Per Pallet Pos`
*   **Pallet Thruput (Năng suất luân chuyển)** = `Pallet OB D2C` (Out) + `Pallet IB D2D` (Out) + `Pallet OB D2D` (DRP) + `Pallet IB F2D` (DRP)
*   **Capacity Thruput** = Năng suất nhân sự lấy từ sheet `People` map theo tên DC.
*   **People (Nhân sự)** = `Capacity Thruput` $\times$ `Pallet Thruput`
*   **F2D Xe pallet (Total)** = $\sum \text{F2D Xe pallet}$ (tại DC_DRP)
*   **D2D Xe pallet (Total)** = $\sum \text{D2D Xe pallet}$ (tại DC_DRP)
*   **F2D Cont bộ (Total)** = $\sum \text{F2D Cont bộ}$ (tại DC_DRP)
*   **D2D Cont bộ (Total)** = $\sum \text{D2D Cont bộ}$ (tại DC_DRP)
*   **F2D Cont biển (Total)** = $\sum \text{F2D Cont biển}$ (tại DC_DRP)
*   **D2D Cont biển (Total)** = $\sum \text{D2D Cont biển}$ (tại DC_DRP)
*   **Truck 15 tấn (Total)** = `D2C Truck 15 tấn` (Out) + `D2D Xe pallet` (Out)
*   **Truck 2 tấn (Total)** = `D2C Truck 2 tấn` (Out) + `D2D Cont biển` (Out)

---
*Tài liệu này phản ánh chính xác 100% logic tính toán được lập trình trong script Python dùng cho hệ thống.*
