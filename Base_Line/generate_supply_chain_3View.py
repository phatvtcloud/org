import pandas as pd
import numpy as np
import json
import urllib.parse
import os
import base64

def generate_node_svg(title, cases=None, pallet_ob_d2c=None, stock_pos=None, pallet_ib_d2d=None, pallet_ob_d2d=None, pallet_ib_f2d=None, drp_stock=None, pallet_ob_f2d=None, customer_name=None, area_service=None, province=None, border_color="#2e7d32", xe_pallet=None, cont_bien=None, cont_bo=None, truck_15_tan=None, truck_2_tan=None):
    width = 175
    height = 40
    stats_svg = ""
    y_offset = 70
    
    if area_service is not None and str(area_service) != 'nan':
        stats_svg += f'<text x="15" y="{y_offset}" font-family="Segoe UI" font-size="14" fill="black">Area: {area_service}</text>'
        y_offset += 20

    if province is not None and str(province) != 'nan':
        stats_svg += f'<text x="15" y="{y_offset}" font-family="Segoe UI" font-size="14" fill="black">Prov: {province}</text>'
        y_offset += 20

    if customer_name is not None and str(customer_name) != 'nan':
        stats_svg += f'<text x="15" y="{y_offset}" font-family="Segoe UI" font-size="14" fill="black">Name: {customer_name}</text>'
        y_offset += 20

    if cases is not None:
        stats_svg += f'<text x="15" y="{y_offset}" font-family="Segoe UI" font-size="14" fill="black">Case: {cases:,.0f}</text>'
        y_offset += 20
        
    if pallet_ob_d2c is not None:
        stats_svg += f'<text x="15" y="{y_offset}" font-family="Segoe UI" font-size="14" fill="black">Pallet OB D2C: {pallet_ob_d2c:,.0f}</text>'
        y_offset += 20
        
    if pallet_ib_d2d is not None:
        stats_svg += f'<text x="15" y="{y_offset}" font-family="Segoe UI" font-size="14" fill="black">Pallet IB D2D: {pallet_ib_d2d:,.0f}</text>'
        y_offset += 20
        
    if stock_pos is not None:
        stats_svg += f'<text x="15" y="{y_offset}" font-family="Segoe UI" font-size="14" fill="black">Stock Pos: {stock_pos:,.0f}</text>'
        y_offset += 20
        
    if pallet_ob_f2d is not None:
        stats_svg += f'<text x="15" y="{y_offset}" font-family="Segoe UI" font-size="14" fill="black">Pallet OB F2D: {pallet_ob_f2d:,.0f}</text>'
        y_offset += 20
        
    if pallet_ib_f2d is not None:
        stats_svg += f'<text x="15" y="{y_offset}" font-family="Segoe UI" font-size="14" fill="black">Pallet IB F2D: {pallet_ib_f2d:,.0f}</text>'
        y_offset += 20
        
    if pallet_ob_d2d is not None:
        stats_svg += f'<text x="15" y="{y_offset}" font-family="Segoe UI" font-size="14" fill="black">Pallet OB D2D: {pallet_ob_d2d:,.0f}</text>'
        y_offset += 20
        
    if drp_stock is not None:
        stats_svg += f'<text x="15" y="{y_offset}" font-family="Segoe UI" font-size="14" fill="black">DRP Stock: {drp_stock:,.0f}</text>'
        y_offset += 20
        
    if xe_pallet is not None:
        stats_svg += f'<text x="15" y="{y_offset}" font-family="Segoe UI" font-size="14" fill="black">Xe pallet: {xe_pallet:,.0f}</text>'
        y_offset += 20

    if cont_bien is not None:
        stats_svg += f'<text x="15" y="{y_offset}" font-family="Segoe UI" font-size="14" fill="black">Cont biển: {cont_bien:,.0f}</text>'
        y_offset += 20

    if cont_bo is not None:
        stats_svg += f'<text x="15" y="{y_offset}" font-family="Segoe UI" font-size="14" fill="black">Cont bộ: {cont_bo:,.0f}</text>'
        y_offset += 20

    if truck_15_tan is not None:
        stats_svg += f'<text x="15" y="{y_offset}" font-family="Segoe UI" font-size="14" fill="black">Truck 15 tấn: {truck_15_tan:,.0f}</text>'
        y_offset += 20

    if truck_2_tan is not None:
        stats_svg += f'<text x="15" y="{y_offset}" font-family="Segoe UI" font-size="14" fill="black">Truck 2 tấn: {truck_2_tan:,.0f}</text>'
        y_offset += 20
            
    if y_offset > 50:
        height = y_offset - 10
        
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">
        <rect x="1" y="1" width="{width-2}" height="{height-2}" fill="white" stroke="#ccc" stroke-width="1.5" rx="10" ry="10"/>
        <path d="M 12 1 L 12 {height-1} L 11 {height-1} A 10 10 0 0 1 1 {height-11} L 1 11 A 10 10 0 0 1 11 1 Z" fill="{border_color}"/>
        <text x="20" y="26" font-family="Segoe UI" font-size="16" font-weight="bold" fill="#333">{title}</text>
        {stats_svg}
    </svg>'''
    uri = "data:image/svg+xml;charset=utf-8," + urllib.parse.quote(svg)
    size = 50 * max(175, height) / 175
    return uri, size

def process_supply_chain_data(excel_path, output_html):
    print("Reading data from excel file...")
    try:
        xls = pd.ExcelFile(excel_path)
    except Exception as e:
        print("Error reading excel file. Please ensure the file is closed and not in use.")
        return

    # 1. Process Parameter sheet
    doh_map = {}
    drp_stock_value = 0.0
    m2_per_pallet_pos = 0.0
    veh_params = {}
    if "Parameter" in xls.sheet_names:
        df_param = pd.read_excel(xls, "Parameter")
        for _, row in df_param.iterrows():
            param_name = str(row.get("Parameter")).strip()
            val = row.get("Values")
            val2 = row.get("Values_2")
            if pd.notna(val):
                if param_name in ["Very fast moving", "Fast moving", "Normal moving", "Slow moving"]:
                    doh_map[param_name] = float(val)
                elif param_name == "DRP - Stock":
                    drp_stock_value = float(val)
                elif param_name == "M2 Per Pallet Pos":
                    m2_per_pallet_pos = float(val)
                else:
                    veh_params[param_name] = {
                        'val': float(val) if pd.notna(val) else 0.0,
                        'val2': float(val2) if pd.notna(val2) else 0.0
                    }

    # 2. Process MD06
    if "MD06" in xls.sheet_names:
        df_md06 = pd.read_excel(xls, "MD06")[['Item No', 'UOM Conversion / Pallet', 'Pallet chồng đôi', 'Tấn/ UOM Conversion', 'M3/ UOM Conversion', 'Nặng/Nhẹ', 'Moving Type']].copy()
        df_md06['Item No'] = df_md06['Item No'].astype(str).str.strip()
        df_md06 = df_md06.drop_duplicates(subset=['Item No'])
    else:
        df_md06 = pd.DataFrame(columns=['Item No', 'UOM Conversion / Pallet', 'Pallet chồng đôi', 'Tấn/ UOM Conversion', 'M3/ UOM Conversion', 'Nặng/Nhẹ', 'Moving Type'])

    # 3. Process F2D
    if "F2D" in xls.sheet_names:
        df_f2d = pd.read_excel(xls, "F2D")[['DC_Out', 'Item No', 'Factory']].copy()
        df_f2d['DC_Out'] = df_f2d['DC_Out'].astype(str).str.strip()
        df_f2d['Item No'] = df_f2d['Item No'].astype(str).str.strip()
        df_f2d = df_f2d.drop_duplicates(subset=['DC_Out', 'Item No'])
    else:
        df_f2d = pd.DataFrame(columns=['DC_Out', 'Item No', 'Factory'])

    # 4. Process D2D
    if "D2D" in xls.sheet_names:
        df_d2d = pd.read_excel(xls, "D2D").copy()
        for col in ['Factory', 'DC_Out', 'DC_DRP', 'Loại xe F2D', 'Loại xe D2D']:
            if col not in df_d2d.columns:
                df_d2d[col] = None
        df_d2d = df_d2d[['Factory', 'DC_Out', 'DC_DRP', 'Loại xe F2D', 'Loại xe D2D']].copy()
        df_d2d['Factory'] = df_d2d['Factory'].astype(str).str.strip()
        df_d2d['DC_Out'] = df_d2d['DC_Out'].astype(str).str.strip()
        df_d2d = df_d2d.drop_duplicates(subset=['Factory', 'DC_Out'])
    else:
        df_d2d = pd.DataFrame(columns=['Factory', 'DC_Out', 'DC_DRP', 'Loại xe F2D', 'Loại xe D2D'])

    # 4.5 Process Shipto
    if "Shipto" in xls.sheet_names:
        df_shipto = pd.read_excel(xls, "Shipto")[['Customer Number', 'Customer Name', 'Sales Channel', 'Area Service', 'Province', 'Địa chỉ', 'Tỉnh mới', 'Loại xe D2C']].copy()
        df_shipto['Customer Number'] = df_shipto['Customer Number'].astype(str).str.strip()
        df_shipto = df_shipto.drop_duplicates(subset=['Customer Number'], keep='first')
    else:
        df_shipto = pd.DataFrame(columns=['Customer Number', 'Customer Name', 'Sales Channel', 'Area Service', 'Province', 'Địa chỉ', 'Tỉnh mới', 'Loại xe D2C'])

    # 4.6 Process People
    if "People" in xls.sheet_names:
        df_people = pd.read_excel(xls, "People")[['DC_out', 'Capacity_Thruput']].copy()
        df_people['DC_out'] = df_people['DC_out'].astype(str).str.strip()
        df_people = df_people.drop_duplicates(subset=['DC_out'], keep='first')
    else:
        df_people = pd.DataFrame(columns=['DC_out', 'Capacity_Thruput'])

    if "Ratio" in xls.sheet_names:
        df_ratio = pd.read_excel(xls, "Ratio")[['Day', 'Ratio']].copy()
        df_ratio['Day'] = df_ratio['Day'].astype(str)
        df_ratio['Ratio'] = pd.to_numeric(df_ratio['Ratio'], errors='coerce').fillna(1.0)
        ratio_list = df_ratio.to_dict(orient='records')
    else:
        ratio_list = []
        
    if not ratio_list:
        ratio_list = [{"Day": f"Day {i}", "Ratio": 1.0} for i in range(1, 13)]
        
    ratio_json = json.dumps(ratio_list)

    # 5. Process D2C & Build Master Data
    print("Building Master Data...")
    if "D2C" in xls.sheet_names:
        master = pd.read_excel(xls, "D2C").copy()
    else:
        print("Sheet D2C not found. Cannot build network.")
        return

    #Define Case 3M or 6M 
    master['Case'] = master['RR 3m'] 
     

    # Format Base keys
    master['Item No'] = master['Item No'].astype(str).str.strip()
    master['DC_Out'] = master['DC_Out'].astype(str).str.strip()
    master = master.replace('nan', np.nan).dropna(subset=['DC_Out'])

    # Merge MD06
    master = master.merge(df_md06, on='Item No', how='left')
    
    # Calculate Tấn and M3
    master['Tấn/ UOM Conversion'] = pd.to_numeric(master['Tấn/ UOM Conversion'], errors='coerce').fillna(0)
    master['M3/ UOM Conversion'] = pd.to_numeric(master['M3/ UOM Conversion'], errors='coerce').fillna(0)
    master['Tấn'] = master['Case'] * master['Tấn/ UOM Conversion']
    master['M3'] = master['Case'] * master['M3/ UOM Conversion']
    
    # Calculate Pallet OB D2C & Stock Pos
    master['UOM Conversion / Pallet'] = pd.to_numeric(master['UOM Conversion / Pallet'], errors='coerce')
    master['Pallet OB D2C'] = np.where(
        master['UOM Conversion / Pallet'].notna() & (master['UOM Conversion / Pallet'] != 0),
        master['Case'] / master['UOM Conversion / Pallet'],
        0
    )
    master['Multiplier'] = np.where(master['Pallet chồng đôi'].astype(str).str.strip() == 'Y', 1, 2)
    master['Moving Type'] = master['Moving Type'].astype(str).str.strip()
    master['Moving Type'] = master['Moving Type'].replace(['nan', '', 'None'], 'Normal moving')
    master['DOH'] = master['Moving Type'].map(doh_map).fillna(0)
    master['Stock Pos'] = master['Pallet OB D2C'] * master['DOH'] * master['Multiplier']

    # Merge F2D
    master = master.merge(df_f2d, on=['DC_Out', 'Item No'], how='left')
    
    # Merge D2D
    master['Factory'] = master['Factory'].astype(str).str.strip().replace('nan', np.nan)
    master = master.merge(df_d2d, on=['Factory', 'DC_Out'], how='left')

    # Calculate Pallet OB D2D
    master['DC_DRP'] = master['DC_DRP'].astype(str).str.strip().replace('nan', np.nan)
    # If no DRP mapped, flow goes through a DRP with the same name as DC_Out
    master['DC_DRP'] = master['DC_DRP'].fillna(master['DC_Out'])
    
    master['Pallet OB D2D'] = np.where(
        master['DC_DRP'] != master['DC_Out'],
        master['Pallet OB D2C'],
        0
    )
    master['Pallet IB D2D'] = master['Pallet OB D2D']
    master['Pallet IB F2D'] = master['Pallet OB D2C']
    master['Pallet OB F2D'] = master['Pallet OB D2C']

    # Merge Shipto
    if 'Customer Number' in master.columns:
        master['Customer Number'] = master['Customer Number'].astype(str).str.strip()
        
        # Drop columns from master if they exist to avoid _x/_y suffixes
        cols_to_drop = [col for col in ['Customer Name', 'Sales Channel', 'Area Service', 'Province', 'Địa chỉ', 'Tỉnh mới', 'Loại xe D2C'] if col in master.columns]
        if cols_to_drop:
            master = master.drop(columns=cols_to_drop)
            
        master = master.merge(df_shipto, on='Customer Number', how='left')
    else:
        print("Warning: Customer Number not found in master data.")
        for col in ['Customer Name', 'Area Service', 'Province']:
            master[col] = None

    # Calculate 8 Vehicle columns based on Nặng/Nhẹ
    def calc_vehicle(loai_xe_col, target_xe, multiply_cond=None):
        v = veh_params.get(target_xe, {'val': 1.0, 'val2': 1.0})
        v1 = v['val'] if v['val'] != 0 else 1.0
        v2 = v['val2'] if v['val2'] != 0 else 1.0
        
        res = np.where(
            master[loai_xe_col] == target_xe,
            np.where(
                master['Nặng/Nhẹ'].astype(str).str.strip() == "Nhẹ",
                master['M3'] / v2,
                master['Tấn'] / v1
            ),
            0
        )
        if multiply_cond is not None:
            res = res * multiply_cond
        return res

    def is_valid(col):
        return master[col].notna() & (master[col].astype(str).str.strip() != "") & (master[col].astype(str).str.strip() != "nan")

    if 'Loại xe F2D' in master.columns:
        master['F2D Cont bộ'] = calc_vehicle('Loại xe F2D', 'Cont bộ')
        master['F2D Cont biển'] = calc_vehicle('Loại xe F2D', 'Cont biển')
        master['F2D Xe pallet'] = calc_vehicle('Loại xe F2D', 'Xe pallet')
        master['F2D Actual Tấn'] = np.where((master['Nặng/Nhẹ'].astype(str).str.strip() == "Nặng") & is_valid('Loại xe F2D'), master['Tấn'], 0)
        master['F2D Actual M3'] = np.where((master['Nặng/Nhẹ'].astype(str).str.strip() == "Nhẹ") & is_valid('Loại xe F2D'), master['M3'], 0)
    else:
        master['F2D Cont bộ'] = 0
        master['F2D Cont biển'] = 0
        master['F2D Xe pallet'] = 0
        master['F2D Actual Tấn'] = 0
        master['F2D Actual M3'] = 0
    
    if 'Loại xe D2D' in master.columns:
        d2d_cond = np.where(master['DC_DRP'] == master['DC_Out'], 0, 1)
        master['D2D Cont bộ'] = calc_vehicle('Loại xe D2D', 'Cont bộ', d2d_cond)
        master['D2D Cont biển'] = calc_vehicle('Loại xe D2D', 'Cont biển', d2d_cond)
        master['D2D Xe pallet'] = calc_vehicle('Loại xe D2D', 'Xe pallet', d2d_cond)
        master['D2D Actual Tấn'] = np.where((master['Nặng/Nhẹ'].astype(str).str.strip() == "Nặng") & is_valid('Loại xe D2D') & (master['DC_Out'] != master['DC_DRP']), master['Tấn'], 0)
        master['D2D Actual M3'] = np.where((master['Nặng/Nhẹ'].astype(str).str.strip() == "Nhẹ") & is_valid('Loại xe D2D') & (master['DC_Out'] != master['DC_DRP']), master['M3'], 0)
    else:
        master['D2D Cont bộ'] = 0
        master['D2D Cont biển'] = 0
        master['D2D Xe pallet'] = 0
        master['D2D Actual Tấn'] = 0
        master['D2D Actual M3'] = 0

    if 'Loại xe D2C' in master.columns:
        master['D2C Truck 15 tấn'] = calc_vehicle('Loại xe D2C', 'Truck 15 tấn')
        master['D2C Truck 2 tấn'] = calc_vehicle('Loại xe D2C', 'Truck 2 tấn')
        master['D2C Actual Tấn'] = np.where((master['Nặng/Nhẹ'].astype(str).str.strip() == "Nặng") & is_valid('Loại xe D2C'), master['Tấn'], 0)
        master['D2C Actual M3'] = np.where((master['Nặng/Nhẹ'].astype(str).str.strip() == "Nhẹ") & is_valid('Loại xe D2C'), master['M3'], 0)
    else:
        master['D2C Truck 15 tấn'] = 0
        master['D2C Truck 2 tấn'] = 0
        master['D2C Actual Tấn'] = 0
        master['D2C Actual M3'] = 0

    # Export Master Data
    master_csv_path = os.path.join(os.path.dirname(output_html), "Masterdata.csv")
    master.to_csv(master_csv_path, index=False, encoding='utf-8-sig')

    # Process Appendix for ordering
    fact_order = []
    dc_order = []
    prov_order = []
    if "Appendix" in xls.sheet_names:
        df_app = pd.read_excel(xls, "Appendix")
        if 'Factory' in df_app.columns:
            fact_order = df_app['Factory'].dropna().astype(str).str.strip().tolist()
        if 'DC' in df_app.columns:
            dc_order = df_app['DC'].dropna().astype(str).str.strip().tolist()
        if 'Province' in df_app.columns:
            prov_order = df_app['Province'].dropna().astype(str).str.strip().tolist()

    def get_order_y(name, order_list, y_spacing=80, default_idx=1000):
        try:
            return order_list.index(name) * y_spacing
        except ValueError:
            return default_idx * y_spacing
            
    x_spacing = 350
    y_spacing = 130

    # 6. Aggregate Nodes & Edges
    print("Aggregating Nodes and Edges...")
    nodes_list = []
    edges_set = set()
    
    group_colors = {
        'Country': '#d32f2f',
        'Factory': '#00838f',
        'DC_DRP': '#ef6c00',
        'DC_Out': '#2e7d32',
        'Customer': '#c2185b'
    }

    # Province Nodes
    if 'Province' in master.columns and 'Customer Number' in master.columns:
        prov_agg = master.groupby('Province').agg({'Case': 'sum', 'Customer Number': 'nunique'}).reset_index()
        for _, row in prov_agg.iterrows():
            prov = str(row['Province']).strip()
            if prov and prov != 'nan' and prov != 'None':
                prov_id = f"PROV_{prov}"
                uri, size = generate_node_svg(
                    title=f"{prov}",
                    customer_name=f"{row['Customer Number']} Customers",
                    cases=row['Case'],
                    border_color="#9c27b0"
                )
                nodes_list.append({
                    "id": prov_id,
                    "level": 4,
                    "x": 4 * x_spacing,
                    "y": get_order_y(prov, prov_order, y_spacing),
                    "group": "Province",
                    "shape": "image",
                    "image": uri,
                    "size": size
                })


    dc_out_agg = master.groupby('DC_Out').agg({
        'Case': 'sum',
        'Tấn': 'sum',
        'M3': 'sum',
        'Pallet OB D2C': 'sum',
        'Stock Pos': 'sum',
        'Pallet IB D2D': 'sum',
        'D2D Xe pallet': 'sum',
        'D2D Cont biển': 'sum',
        'D2C Truck 15 tấn': 'sum',
        'D2C Truck 2 tấn': 'sum',
        'D2C Actual Tấn': 'sum',
        'D2C Actual M3': 'sum'
    }).reset_index()
    
    for _, row in dc_out_agg.iterrows():
        out_name = row['DC_Out']
        out_id = f"OUT_{out_name}"
        uri, size = generate_node_svg(
            title=out_name,
            cases=row['Case'],
            pallet_ob_d2c=row['Pallet OB D2C'],
            stock_pos=row['Stock Pos'],
            pallet_ib_d2d=row['Pallet IB D2D'],
            truck_15_tan=row['D2D Xe pallet'],
            truck_2_tan=row['D2D Cont biển'],
            border_color=group_colors['DC_Out']
        )
        nodes_list.append({
            "id": out_id,
            "level": 3,
            "x": 3 * x_spacing,
            "y": get_order_y(out_name, dc_order, y_spacing),
            "group": "DC_Out",
            "shape": "image",
            "image": uri,
            "size": size
        })
    dc_drp_agg = master.groupby('DC_DRP').agg({
        'Pallet OB D2D': 'sum',
        'Pallet IB F2D': 'sum',
        'F2D Cont bộ': 'sum',
        'F2D Cont biển': 'sum',
        'F2D Xe pallet': 'sum',
        'D2D Cont bộ': 'sum',
        'D2D Cont biển': 'sum',
        'D2D Xe pallet': 'sum',
        'F2D Actual Tấn': 'sum',
        'F2D Actual M3': 'sum',
        'D2D Actual Tấn': 'sum',
        'D2D Actual M3': 'sum'
    }).reset_index()
    
    for _, row in dc_drp_agg.iterrows():
        drp_name = row['DC_DRP']
        drp_id = f"DRP_{drp_name}"
        
        pallet_ob_d2d = row['Pallet OB D2D']
        pallet_ib_f2d = row['Pallet IB F2D']
        drp_stock = pallet_ob_d2d * drp_stock_value
        
        uri, size = generate_node_svg(
            title=drp_name,
            pallet_ob_d2d=pallet_ob_d2d,
            pallet_ib_f2d=pallet_ib_f2d,
            drp_stock=drp_stock,
            xe_pallet=row['D2D Xe pallet'],
            cont_bien=row['D2D Cont biển'],
            cont_bo=row['D2D Cont bộ'],
            border_color=group_colors['DC_DRP']
        )
        nodes_list.append({
            "id": drp_id,
            "level": 2,
            "x": 2 * x_spacing,
            "y": get_order_y(drp_name, dc_order, y_spacing),
            "group": "DC_DRP",
            "shape": "image",
            "image": uri,
            "size": size
        })

    # Factory Nodes
    fact_agg = master.groupby('Factory').agg({
        'Pallet OB F2D': 'sum',
        'F2D Xe pallet': 'sum',
        'F2D Cont biển': 'sum',
        'F2D Cont bộ': 'sum'
    }).reset_index()
    
    for _, row in fact_agg.iterrows():
        fact = row['Factory']
        fact_id = f"FACT_{fact}"
        uri, size = generate_node_svg(
            title=fact, 
            pallet_ob_f2d=row['Pallet OB F2D'], 
            xe_pallet=row['F2D Xe pallet'],
            cont_bien=row['F2D Cont biển'],
            cont_bo=row['F2D Cont bộ'],
            border_color=group_colors['Factory']
        )
        nodes_list.append({
            "id": fact_id,
            "level": 1,
            "x": 1 * x_spacing,
            "y": get_order_y(fact, fact_order, y_spacing),
            "group": "Factory",
            "shape": "image",
            "image": uri,
            "size": size
        })

    # Pivot Table Data
    pivot_out = dc_out_agg.rename(columns={'DC_Out': 'DC'})
    pivot_drp = dc_drp_agg.rename(columns={'DC_DRP': 'DC'})
    df_pivot = pd.merge(pivot_out, pivot_drp, on='DC', how='outer').fillna(0)
    
    df_pivot['DRP Stock'] = df_pivot['Pallet OB D2D'] * drp_stock_value
    df_pivot['Total Stock Pos'] = df_pivot['Stock Pos'] + df_pivot['DRP Stock']
    
    df_pivot['Tấn'] = df_pivot['Tấn']
    df_pivot['M3'] = df_pivot['M3']
    df_pivot['Pallet'] = df_pivot['Pallet OB D2C']
    
    df_pivot['Diện tích'] = df_pivot['Total Stock Pos'] * m2_per_pallet_pos
    df_pivot['Pallet Thruput'] = df_pivot['Pallet OB D2C'] + df_pivot['Pallet IB D2D'] + df_pivot['Pallet OB D2D'] + df_pivot['Pallet IB F2D']
    
    df_pivot['F2D Cont bộ'] = df_pivot['F2D Cont bộ']
    df_pivot['D2D Cont bộ'] = df_pivot['D2D Cont bộ']
    df_pivot['F2D Cont biển'] = df_pivot['F2D Cont biển']
    df_pivot['D2D Cont biển'] = df_pivot['D2D Cont biển_y']
    df_pivot['F2D Xe pallet'] = df_pivot['F2D Xe pallet']
    df_pivot['D2D Xe pallet'] = df_pivot['D2D Xe pallet_y']
    df_pivot['Truck 15 tấn'] = df_pivot['D2C Truck 15 tấn'] + df_pivot['D2D Xe pallet_x']
    df_pivot['Truck 2 tấn'] = df_pivot['D2C Truck 2 tấn'] + df_pivot['D2D Cont biển_x']
    
    df_pivot['F2D Actual Tấn'] = df_pivot['F2D Actual Tấn']
    df_pivot['F2D Actual M3'] = df_pivot['F2D Actual M3']
    df_pivot['D2D Actual Tấn'] = df_pivot['D2D Actual Tấn']
    df_pivot['D2D Actual M3'] = df_pivot['D2D Actual M3']
    df_pivot['D2C Actual Tấn'] = df_pivot['D2C Actual Tấn']
    df_pivot['D2C Actual M3'] = df_pivot['D2C Actual M3']
    
    if not df_people.empty:
        df_pivot = pd.merge(df_pivot, df_people, left_on='DC', right_on='DC_out', how='left').fillna(0)
    else:
        df_pivot['Capacity_Thruput'] = 0.0
        
    df_pivot['Capacity_Thruput'] = pd.to_numeric(df_pivot['Capacity_Thruput'], errors='coerce').fillna(0)
    df_pivot['People'] = df_pivot['Capacity_Thruput'] * df_pivot['Pallet Thruput']
    
    df_pivot['order'] = df_pivot['DC'].map(lambda x: dc_order.index(x) if x in dc_order else 1000)
    df_pivot = df_pivot.sort_values(by='order').drop(columns=['order'])
    pivot_data = df_pivot[['DC', 'Case', 'Tấn', 'M3', 'Pallet', 'Pallet Thruput', 'Total Stock Pos', 'Diện tích', 'Capacity_Thruput', 'People', 'F2D Xe pallet', 'D2D Xe pallet', 'F2D Cont bộ', 'D2D Cont bộ', 'F2D Cont biển', 'D2D Cont biển', 'Truck 15 tấn', 'Truck 2 tấn', 'F2D Actual Tấn', 'F2D Actual M3', 'D2D Actual Tấn', 'D2D Actual M3', 'D2C Actual Tấn', 'D2C Actual M3']].to_dict(orient='records')
    pivot_json = json.dumps(pivot_data)
    
    dc_order_json = json.dumps(dc_order)
    
    people_capacity_map = dict(zip(df_people['DC_out'], pd.to_numeric(df_people['Capacity_Thruput'], errors='coerce').fillna(0))) if not df_people.empty else {}
    people_capacity_json = json.dumps(people_capacity_map)
    
    day_headers = "".join([f'<th style="padding: 8px; text-align: right; border-bottom: 2px solid #ddd; min-width: 60px;">{r["Day"]}</th>' for r in ratio_list])
    
    pivot_html = f"""
    <div id="pivot-table-container" style="background: white; padding: 15px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); overflow-y: auto; overflow-x: auto; height: 100%;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; position: sticky; left: -15px; z-index: 101;">
            <h3 style="margin: 0; font-size: 18px; color: #333;">Baseline by Day (Digital Twin Summary)</h3>
            <div style="position: relative; display: flex; gap: 8px;">
                <button onclick="document.getElementById('filter-modal').style.display='flex'" style="padding: 6px 12px; font-size: 13px; cursor: pointer; border: 1px solid #1976d2; color: #1976d2; background: white; border-radius: 4px; font-weight: bold;">🔍 Filter Data</button>
                <button onclick="exportTableToExcel('pivot-table', 'Baseline_By_Day')" style="padding: 6px 12px; font-size: 13px; cursor: pointer; border: 1px solid #28a745; color: #28a745; background: white; border-radius: 4px; font-weight: bold;">📥 Xuất Excel</button>
                <button onclick="toggleRowConfigMenu()" style="padding: 6px 12px; font-size: 13px; cursor: pointer; border: 1px solid #ccc; background: #eee; border-radius: 4px; font-weight: bold;">⚙️ Tùy chỉnh dòng</button>
                <div id="row-config-menu" style="display: none; position: absolute; top: 35px; right: 0; background: white; border: 1px solid #ccc; border-radius: 4px; padding: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); width: 250px; z-index: 200; max-height: 400px; overflow-y: auto;">
                    <ul id="row-config-list" style="list-style: none; padding: 0; margin: 0; font-size: 13px;"></ul>
                </div>
            </div>
        </div>
        <table id="pivot-table" style="width: max-content; border-collapse: separate; border-spacing: 0; font-size: 13px;">
            <thead style="position: sticky; top: -15px; background: white; z-index: 99;">
                <tr>
                    <th style="padding: 8px; text-align: left; position: sticky; left: -15px; background: white; z-index: 100; border-bottom: 2px solid #ddd;">Metric</th>
                    <th style="padding: 8px; text-align: left; background: white; border-bottom: 2px solid #ddd; min-width: 50px;">UoM</th>
                    <th style="padding: 8px; text-align: right; background: white; border-bottom: 2px solid #ddd; min-width: 60px;">Max</th>
                    <th style="padding: 8px; text-align: right; background: white; border-bottom: 2px solid #ddd; min-width: 60px;">Average</th>
                    {day_headers}
                </tr>
            </thead>
            <tbody id="pivot-tbody">
            </tbody>
        </table>
    </div>
    """
    
    docx_path = os.path.join(os.path.dirname(output_html), "Từ Điển Công Thức.docx")
    docx_base64 = ""
    if os.path.exists(docx_path):
        with open(docx_path, "rb") as f:
            docx_base64 = base64.b64encode(f.read()).decode('utf-8')
    
    logic_html = f'''
    <div id="logic-container" style="background: white; padding: 25px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); overflow-y: auto; height: 100%; max-width: 900px; margin: 0 auto; line-height: 1.6;">
        <style>
            #docx-output {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #333; }}
            #docx-output h1 {{ font-size: 24px; color: #007bff; border-bottom: 2px solid #007bff; padding-bottom: 5px; }}
            #docx-output h2 {{ font-size: 20px; color: #0056b3; margin-top: 20px; }}
            #docx-output h3 {{ font-size: 16px; color: #0056b3; margin-top: 15px; }}
            #docx-output table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
            #docx-output th, #docx-output td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            #docx-output th {{ background-color: #f2f2f2; }}
            #docx-output p {{ margin: 10px 0; }}
            #docx-output ul, #docx-output ol {{ margin-top: 5px; margin-bottom: 5px; }}
        </style>
        <div id="docx-output" style="text-align: center; color: #666; font-style: italic; padding-top: 20px;">
            Đang tải và xử lý dữ liệu từ file "Từ Điển Công Thức.docx"...
        </div>
    </div>
    
    <script src="https://cdnjs.cloudflare.com/ajax/libs/mammoth/1.4.21/mammoth.browser.min.js"></script>
    <script>
    (function() {{
        var docxBase64 = "{docx_base64}";
        var outDiv = document.getElementById('docx-output');
        
        if (docxBase64) {{
            function base64ToArrayBuffer(base64) {{
                var binary_string = window.atob(base64);
                var len = binary_string.length;
                var bytes = new Uint8Array(len);
                for (var i = 0; i < len; i++) {{
                    bytes[i] = binary_string.charCodeAt(i);
                }}
                return bytes.buffer;
            }}
            
            mammoth.convertToHtml({{arrayBuffer: base64ToArrayBuffer(docxBase64)}})
                .then(function(result) {{
                    outDiv.style.textAlign = 'left';
                    outDiv.style.fontStyle = 'normal';
                    outDiv.innerHTML = result.value;
                }})
                .catch(function(err) {{
                    outDiv.innerHTML = "Lỗi khi đọc file DOCX: " + err;
                }});
        }} else {{
            outDiv.innerHTML = "Không tìm thấy file 'Từ Điển Công Thức.docx' trong thư mục. Vui lòng tạo file này và chạy lại lệnh Python để cập nhật.";
        }}
    }})();
    </script>
    '''

    # Edges (F2D and D2D)
    flows = master[['Factory', 'DC_DRP', 'DC_Out']].dropna(subset=['Factory'])
    for _, row in flows.iterrows():
        fact_id = f"FACT_{row['Factory']}"
        drp_id = f"DRP_{row['DC_DRP']}"
        out_id = f"OUT_{row['DC_Out']}"
        
        edges_set.add((fact_id, drp_id))
        edges_set.add((drp_id, out_id))

    # Edges (Out and Province)
    if 'Province' in master.columns:
        out_prov_flows = master[['DC_Out', 'Province']].dropna().drop_duplicates()
        for _, row in out_prov_flows.iterrows():
            prov = str(row['Province']).strip()
            if prov and prov != 'nan' and prov != 'None':
                out_id = f"OUT_{row['DC_Out']}"
                prov_id = f"PROV_{prov}"
                edges_set.add((out_id, prov_id))

    edges_list = [{"from": src, "to": dst} for src, dst in edges_set]

    print(f"Total Nodes: {len(nodes_list)}")
    print(f"Total Edges: {len(edges_list)}")

    print("Preparing Unified Path Mapping for Filter...")
    path_mapping = []
    
    group_cols = ['Customer Number', 'Customer Name', 'Item No', 'Area Service', 'Province', 'DC_Out', 'DC_DRP', 'Factory']
    actual_cols = [c for c in group_cols if c in master.columns]
    
    if len(actual_cols) > 0:
        path_agg = master.groupby(actual_cols).agg({
            'Case': 'sum',
            'Tấn': 'sum',
            'M3': 'sum',
            'Pallet OB D2C': 'sum',
            'Stock Pos': 'sum',
            'Pallet OB D2D': 'sum',
            'Pallet IB D2D': 'sum',
            'Pallet OB F2D': 'sum',
            'Pallet IB F2D': 'sum',
            'F2D Cont bộ': 'sum',
            'F2D Cont biển': 'sum',
            'F2D Xe pallet': 'sum',
            'D2D Cont bộ': 'sum',
            'D2D Cont biển': 'sum',
            'D2D Xe pallet': 'sum',
            'D2C Truck 15 tấn': 'sum',
            'D2C Truck 2 tấn': 'sum',
            'F2D Actual Tấn': 'sum',
            'F2D Actual M3': 'sum',
            'D2D Actual Tấn': 'sum',
            'D2D Actual M3': 'sum',
            'D2C Actual Tấn': 'sum',
            'D2C Actual M3': 'sum'
        }).reset_index()
        
        for _, row in path_agg.iterrows():
            path_mapping.append({
                'Cust': str(row.get('Customer Number', '')).strip().replace('nan', ''),
                'CustName': str(row.get('Customer Name', '')).strip().replace('nan', ''),
                'Item': str(row.get('Item No', '')).strip().replace('nan', ''),
                'Area': str(row.get('Area Service', '')).strip().replace('nan', ''),
                'Prov': str(row.get('Province', '')).strip().replace('nan', ''),
                'DC_Out': str(row.get('DC_Out', '')).strip().replace('nan', ''),
                'DC_DRP': str(row.get('DC_DRP', '')).strip().replace('nan', ''),
                'Fact': str(row.get('Factory', '')).strip().replace('nan', ''),
                'Cases': float(row['Case']),
                'Tan': float(row['Tấn']),
                'M3': float(row['M3']),
                'Pallet_OB_D2C': float(row['Pallet OB D2C']),
                'Stock_Pos': float(row['Stock Pos']),
                'Pallet_OB_D2D': float(row['Pallet OB D2D']),
                'Pallet_IB_D2D': float(row['Pallet IB D2D']),
                'Pallet_OB_F2D': float(row['Pallet OB F2D']),
                'Pallet_IB_F2D': float(row['Pallet IB F2D']),
                'F2D_Cont_bo': float(row['F2D Cont bộ']),
                'F2D_Cont_bien': float(row['F2D Cont biển']),
                'F2D_Xe_pallet': float(row['F2D Xe pallet']),
                'D2D_Cont_bo': float(row['D2D Cont bộ']),
                'D2D_Cont_bien': float(row['D2D Cont biển']),
                'D2D_Xe_pallet': float(row['D2D Xe pallet']),
                'D2C_Truck_15': float(row['D2C Truck 15 tấn']),
                'D2C_Truck_2': float(row['D2C Truck 2 tấn']),
                'F2D_Actual_Tan': float(row['F2D Actual Tấn']),
                'F2D_Actual_M3': float(row['F2D Actual M3']),
                'D2D_Actual_Tan': float(row['D2D Actual Tấn']),
                'D2D_Actual_M3': float(row['D2D Actual M3']),
                'D2C_Actual_Tan': float(row['D2C Actual Tấn']),
                'D2C_Actual_M3': float(row['D2C Actual M3'])
            })
            
    path_mapping_json = json.dumps(path_mapping)

    nodes_json = json.dumps(nodes_list)
    edges_json = json.dumps(edges_list)

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Supply Chain End-to-End Baseline</title>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style type="text/css">
        body {{
            margin: 0;
            padding: 0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f5f5f5;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }}
        
        /* Tab CSS */
        .tab {{
            overflow: hidden;
            background-color: #2c3e50;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            flex-shrink: 0;
        }}
        .tab button {{
            background-color: inherit;
            color: #ecf0f1;
            float: left;
            border: none;
            outline: none;
            cursor: pointer;
            padding: 14px 20px;
            transition: 0.3s;
            font-size: 15px;
            font-weight: 600;
            border-bottom: 3px solid transparent;
        }}
        .tab button:hover {{
            background-color: #34495e;
        }}
        .tab button.active {{
            background-color: #1abc9c;
            color: white;
            border-bottom: 3px solid #16a085;
        }}
        .tabcontent {{
            display: none;
            padding: 20px;
            flex-grow: 1;
            overflow: hidden;
            box-sizing: border-box;
            height: calc(100vh - 50px);
        }}
        
        #mynetwork {{
            width: 100%;
            height: 100%;
            border: 1px solid #ddd;
            border-radius: 8px;
            background: white;
        }}
        #loading {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 20px;
            color: #666;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            z-index: 1000;
        }}
        #filter-wrapper {{
            position: absolute;
            top: 15px;
            left: 15px;
            z-index: 100;
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            width: 300px;
        }}
    </style>
    <script>
        function openTab(evt, tabName) {{
            var i, tabcontent, tablinks;
            tabcontent = document.getElementsByClassName("tabcontent");
            for (i = 0; i < tabcontent.length; i++) {{
                tabcontent[i].style.display = "none";
            }}
            tablinks = document.getElementsByClassName("tablinks");
            for (i = 0; i < tablinks.length; i++) {{
                tablinks[i].className = tablinks[i].className.replace(" active", "");
            }}
            document.getElementById(tabName).style.display = "block";
            evt.currentTarget.className += " active";
        }}
    </script>
</head>
<body>
    <div class="tab">
      <button class="tablinks active" onclick="openTab(event, 'SummaryTab')">1. Summary (Baseline Pivot)</button>
      <button class="tablinks" onclick="openTab(event, 'DetailTab')">2. Detail by Route (Network)</button>
      <button class="tablinks" onclick="openTab(event, 'LogicTab')">3. Logic Dictionary</button>
    </div>

    <!-- TAB 1: SUMMARY -->
    <div id="SummaryTab" class="tabcontent" style="display: block;">
        {pivot_html}
    </div>

    <!-- TAB 2: DETAIL BY ROUTE -->
    <div id="DetailTab" class="tabcontent" style="padding: 15px; height: calc(100vh - 50px); box-sizing: border-box;">
        <div style="display: flex; flex-direction: row; height: 100%; width: 100%;">
            <!-- Left Side: Network -->
            <div style="flex-grow: 1; position: relative; height: 100%; display: flex; flex-direction: column; min-width: 0; padding-right: 5px;">
                <div style="margin-bottom: 10px; display: flex; gap: 10px; flex-shrink: 0;">
                    <button onclick="document.getElementById('filter-modal').style.display='flex'" style="background: white; border: 1px solid #1976d2; color: #1976d2; border-radius: 4px; padding: 8px 12px; cursor: pointer; font-size: 13px; font-weight: bold; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">🔍 Filter Data</button>
                    <button onclick="toggleResourcePanel()" style="background: #ff9800; border: none; color: white; border-radius: 4px; padding: 8px 12px; cursor: pointer; font-size: 13px; font-weight: bold; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">📊 Resource Panel</button>
                </div>
                <div style="position: relative; flex-grow: 1; min-height: 0;">
                    <div id="loading">Loading network...</div>
                    <div id="mynetwork" style="width: 100%; height: 100%; border: 1px solid #ddd; border-radius: 8px; background: white;"></div>
                </div>
            </div>
            
            <!-- Drag Handle / Resizer -->
            <div id="resize-handle" style="width: 6px; cursor: col-resize; background: #ddd; height: 100%; transition: background 0.2s; flex-shrink: 0; margin: 0 5px; border-radius: 3px; z-index: 102;" onmouseover="this.style.background='#ff9800'" onmouseout="this.style.background='#ddd'"></div>
            
            <!-- Right Side: Resource Panel -->
            <div id="resource-panel" style="width: 500px; background: white; border: 1px solid #ddd; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); padding: 15px; display: flex; flex-direction: column; height: 100%; box-sizing: border-box; flex-shrink: 0; min-width: 0; padding-left: 15px;">
                <h4 style="margin-top: 0; margin-bottom: 15px; color: #333; font-size: 16px; border-bottom: 2px solid #ff9800; padding-bottom: 8px; display: flex; justify-content: space-between; align-items: center; flex-shrink: 0;">
                    <span>📊 Phân bổ Resource theo DC</span>
                    <button onclick="toggleResourcePanel()" style="border: none; background: transparent; font-size: 16px; cursor: pointer; color: #999;">✖</button>
                </h4>
                
                <div style="flex-grow: 1; overflow: auto;">
                    <table style="width: 100%; border-collapse: collapse; font-size: 12px;">
                        <thead style="position: sticky; top: 0; z-index: 100;">
                            <tr id="resource-thead-tr">
                            </tr>
                        </thead>
                        <tbody id="resource-tbody">
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <!-- TAB 3: LOGIC -->
    <div id="LogicTab" class="tabcontent">
        {logic_html}
    </div>

    <!-- FILTER MODAL -->
    <div id="filter-modal" style="display: none; position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(0,0,0,0.5); z-index: 2000; align-items: center; justify-content: center;">
        <div style="background: white; padding: 25px; border-radius: 8px; width: 450px; max-width: 90%; position: relative; box-shadow: 0 10px 25px rgba(0,0,0,0.2); max-height: 90vh; overflow-y: auto;">
            <button onclick="document.getElementById('filter-modal').style.display='none'" style="position: absolute; top: 15px; right: 15px; border: none; background: transparent; font-size: 18px; cursor: pointer; color: #666;">✖</button>
            <h4 style="margin-top: 0; margin-bottom: 20px; color: #333; font-size: 18px; border-bottom: 2px solid #1976d2; padding-bottom: 10px;">🔍 Lọc Dữ Liệu</h4>
            
            <p style="font-size: 12px; color: #666; margin-top: -10px; margin-bottom: 15px;"><i>Hỗ trợ tìm nhiều giá trị bằng cách ngăn cách bởi dấu phẩy (,). Có thể kết hợp lọc nhiều tiêu chí cùng lúc.</i></p>

            <label for="customer-search" style="font-weight: 600; font-size: 13px; margin-bottom: 6px; display: block; color: #555;">Lọc theo Customer Number:</label>
            <input type="text" id="customer-search" list="customer-list" placeholder="VD: 1001, 1002..." style="padding: 10px; width: 100%; box-sizing: border-box; border: 1px solid #ccc; border-radius: 4px; font-size: 13px;">
            <datalist id="customer-list"></datalist>

            <label for="item-search" style="font-weight: 600; font-size: 13px; margin-top: 15px; margin-bottom: 6px; display: block; color: #555;">Lọc theo Item No:</label>
            <input type="text" id="item-search" list="item-list" placeholder="VD: ITEM1, ITEM2..." style="padding: 10px; width: 100%; box-sizing: border-box; border: 1px solid #ccc; border-radius: 4px; font-size: 13px;">
            <datalist id="item-list"></datalist>

            <label for="province-search" style="font-weight: 600; font-size: 13px; margin-top: 15px; margin-bottom: 6px; display: block; color: #555;">Lọc theo Province:</label>
            <input type="text" id="province-search" list="province-list" placeholder="VD: Hà Nội, Hồ Chí Minh..." style="padding: 10px; width: 100%; box-sizing: border-box; border: 1px solid #ccc; border-radius: 4px; font-size: 13px;">
            <datalist id="province-list"></datalist>

            <label for="dc-search" style="font-weight: 600; font-size: 13px; margin-top: 15px; margin-bottom: 6px; display: block; color: #555;">Lọc theo DC_Out:</label>
            <input type="text" id="dc-search" list="dc-list" placeholder="VD: DC1, DC2..." style="padding: 10px; width: 100%; box-sizing: border-box; border: 1px solid #ccc; border-radius: 4px; font-size: 13px;">
            <datalist id="dc-list"></datalist>

            <div style="margin-top: 20px; display: flex; gap: 10px;">
                <button onclick="applyFilter(); document.getElementById('filter-modal').style.display='none';" style="flex: 1; padding: 10px; background: #1976d2; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; font-size: 14px;">Xác nhận (Filter)</button>
                <button onclick="clearFilter(); document.getElementById('filter-modal').style.display='none';" style="flex: 1; padding: 10px; background: #e53935; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; font-size: 14px;">Xóa Filter</button>
            </div>
            <div id="filter-error" style="color: #d32f2f; margin-top: 15px; font-size: 13px; display: none; font-weight: bold; text-align: center;">Không tìm thấy kết quả!</div>
        </div>
    </div>

    <script type="text/javascript">
        var originalNodes = {nodes_json};
        var originalEdges = {edges_json};
        var nodes = new vis.DataSet(originalNodes);
        var edges = new vis.DataSet(originalEdges);
        var originalNodeMap = {{}};
        originalNodes.forEach(n => originalNodeMap[n.id] = n);
        var drpStockValue = {drp_stock_value};
        var m2PerPalletPos = {m2_per_pallet_pos};
        var pathMapping = {path_mapping_json};
        var peopleCapacityMap = {people_capacity_json};
        var originalPivotData = {pivot_json};
        var dcOrder = {dc_order_json};
        var ratioData = {ratio_json};

        var container = document.getElementById('mynetwork');
        var data = {{
            nodes: nodes,
            edges: edges
        }};
        var options = {{
            layout: {{
                randomSeed: 2
            }},
            nodes: {{
                borderWidth: 0,
                borderWidthSelected: 0,
                shapeProperties: {{
                    useBorderWithImage: false
                }},
                shadow: false
            }},
            edges: {{
                width: 1,
                color: {{
                    color: '#9e9e9e',
                    highlight: '#f44336',
                    hover: '#f44336'
                }},
                smooth: {{
                    type: 'cubicBezier',
                    forceDirection: 'horizontal',
                    roundness: 0.4
                }},
                arrows: {{
                    to: {{
                        enabled: true,
                        scaleFactor: 0.5
                    }}
                }},
                shadow: false
            }},
            physics: false,
            interaction: {{
                hover: false,
                selectConnectedEdges: true,
                zoomView: true,
                dragView: true
            }}
        }};

        var network = new vis.Network(container, data, options);
        
        network.once('stabilizationIterationsDone', function() {{
            document.getElementById('loading').style.display = 'none';
        }});
        network.once('afterDrawing', function() {{
            document.getElementById('loading').style.display = 'none';
        }});

        window.rowConfig = [
            {{ name: 'Case', visible: true, isDecimal: false, group: 'Sell in', tooltip: 'Lấy từ [RR 3m]', uom: 'Thùng' }},
            {{ name: 'Tấn', visible: true, isDecimal: false, group: 'Sell in', tooltip: 'Lấy từ Masterdata[Tấn]', uom: 'Tấn' }},
            {{ name: 'M3', visible: true, isDecimal: false, group: 'Sell in', tooltip: 'Lấy từ Masterdata[M3]', uom: 'M3' }},
            {{ name: 'Pallet', visible: true, isDecimal: false, group: 'Sell in', tooltip: 'Lấy từ Masterdata[Pallet OB D2C]', uom: 'Pallet' }},
            {{ name: 'Pallet Thruput', visible: false, isDecimal: false, group: 'Operation', tooltip: 'Tổng các nhánh Pallet (IB/OB) của F2D, D2D, D2C', uom: 'Pallet' }},
            {{ name: 'Total Stock Pos', displayName: 'Pallet Position', visible: false, isDecimal: false, group: 'Operation', tooltip: 'Stock Pos (D2C) + DRP Stock (D2D)', uom: 'Pallet' }},
            {{ name: 'Diện tích', visible: true, isDecimal: false, group: 'Operation', tooltip: 'Total Stock Pos × Hệ số m2', uom: 'M2' }},
            {{ name: 'Capacity Thruput', visible: false, isDecimal: true, group: 'Operation', tooltip: 'Lấy từ sheet People', uom: '' }},
            {{ name: 'People', visible: true, isDecimal: false, group: 'Operation', tooltip: 'Capacity Thruput × Pallet Thruput', uom: 'Người' }},
            {{ name: 'F2D Xe pallet', displayName: 'Xe pallet', visible: true, isDecimal: false, group: 'Transportation', subGroup: 'F2D', tooltip: 'Tính từ Tấn/M3 (Nặng/Nhẹ) cho Loại xe F2D', uom: 'Xe' }},
            {{ name: 'F2D Cont bộ', displayName: 'Cont bộ', visible: true, isDecimal: false, group: 'Transportation', subGroup: 'F2D', tooltip: 'Tính từ Tấn/M3 (Nặng/Nhẹ) cho Loại xe F2D', uom: 'Cont' }},
            {{ name: 'F2D Cont biển', displayName: 'Cont biển', visible: true, isDecimal: false, group: 'Transportation', subGroup: 'F2D', tooltip: 'Tính từ Tấn/M3 (Nặng/Nhẹ) cho Loại xe F2D', uom: 'Cont' }},
            {{ name: 'F2D Actual Tấn', displayName: 'Actual Tấn', visible: true, isDecimal: false, group: 'Transportation', subGroup: 'F2D', tooltip: 'Tấn (nếu Nặng) cho Loại xe F2D', uom: 'Tấn' }},
            {{ name: 'F2D Actual M3', displayName: 'Actual M3', visible: true, isDecimal: false, group: 'Transportation', subGroup: 'F2D', tooltip: 'M3 (nếu Nhẹ) cho Loại xe F2D', uom: 'M3' }},
            {{ name: 'D2D Xe pallet', displayName: 'Xe pallet', visible: false, isDecimal: false, group: 'Transportation', subGroup: 'D2D', tooltip: 'Tính từ Tấn/M3 (Nặng/Nhẹ) cho Loại xe D2D', uom: 'Xe' }},
            {{ name: 'D2D Cont bộ', displayName: 'Cont bộ', visible: true, isDecimal: false, group: 'Transportation', subGroup: 'D2D', tooltip: 'Tính từ Tấn/M3 (Nặng/Nhẹ) cho Loại xe D2D', uom: 'Cont' }},
            {{ name: 'D2D Cont biển', displayName: 'Cont biển', visible: true, isDecimal: false, group: 'Transportation', subGroup: 'D2D', tooltip: 'Tính từ Tấn/M3 (Nặng/Nhẹ) cho Loại xe D2D', uom: 'Cont' }},
            {{ name: 'D2D Actual Tấn', displayName: 'Actual Tấn', visible: true, isDecimal: false, group: 'Transportation', subGroup: 'D2D', tooltip: 'Tấn (nếu Nặng) cho Loại xe D2D và có điều chuyển kho', uom: 'Tấn' }},
            {{ name: 'D2D Actual M3', displayName: 'Actual M3', visible: true, isDecimal: false, group: 'Transportation', subGroup: 'D2D', tooltip: 'M3 (nếu Nhẹ) cho Loại xe D2D và có điều chuyển kho', uom: 'M3' }},
            {{ name: 'Truck 15 tấn', visible: true, isDecimal: false, group: 'Transportation', subGroup: 'D2C', tooltip: 'Tính từ Tấn/M3 (Nặng/Nhẹ) cho Loại xe D2C', uom: 'Xe' }},
            {{ name: 'Truck 2 tấn', visible: true, isDecimal: false, group: 'Transportation', subGroup: 'D2C', tooltip: 'Tính từ Tấn/M3 (Nặng/Nhẹ) cho Loại xe D2C', uom: 'Xe' }},
            {{ name: 'D2C Actual Tấn', displayName: 'Actual Tấn', visible: true, isDecimal: false, group: 'Transportation', subGroup: 'D2C', tooltip: 'Tấn (nếu Nặng) cho Loại xe D2C', uom: 'Tấn' }},
            {{ name: 'D2C Actual M3', displayName: 'Actual M3', visible: true, isDecimal: false, group: 'Transportation', subGroup: 'D2C', tooltip: 'M3 (nếu Nhẹ) cho Loại xe D2C', uom: 'M3' }}
        ];

        function renderRowConfigMenu() {{
            var ul = document.getElementById('row-config-list');
            if (!ul) return;
            ul.innerHTML = '';
            
            var currentGroup = '';
            var currentSubGroup = '';
            
            window.rowConfig.forEach((cfg, index) => {{
                if (cfg.group !== currentGroup) {{
                    currentGroup = cfg.group;
                    currentSubGroup = '';
                    var groupLi = document.createElement('li');
                    groupLi.style.padding = '4px 6px';
                    groupLi.style.fontWeight = 'bold';
                    groupLi.style.color = '#333';
                    groupLi.style.background = '#e3f2fd';
                    groupLi.style.marginTop = '4px';
                    groupLi.innerText = currentGroup;
                    ul.appendChild(groupLi);
                }}
                
                if (cfg.subGroup && cfg.subGroup !== currentSubGroup) {{
                    currentSubGroup = cfg.subGroup;
                    var subGroupLi = document.createElement('li');
                    subGroupLi.style.padding = '4px 6px 4px 15px';
                    subGroupLi.style.fontWeight = '600';
                    subGroupLi.style.color = '#555';
                    subGroupLi.style.background = '#f5f5f5';
                    subGroupLi.innerText = currentSubGroup;
                    ul.appendChild(subGroupLi);
                }}

                var li = document.createElement('li');
                var paddingLeft = cfg.subGroup ? '25px' : '15px';
                li.style.padding = '4px 6px 4px ' + paddingLeft;
                li.style.display = 'flex';
                li.style.alignItems = 'center';
                
                var cb = document.createElement('input');
                cb.type = 'checkbox';
                cb.checked = cfg.visible;
                cb.style.marginRight = '8px';
                cb.onchange = function() {{
                    window.rowConfig[index].visible = cb.checked;
                    renderPivotTable(window.currentData || originalPivotData);
                }};
                
                var span = document.createElement('span');
                span.innerText = cfg.displayName || cfg.name;
                
                li.appendChild(cb);
                li.appendChild(span);
                ul.appendChild(li);
            }});
        }}

        function toggleRowConfigMenu() {{
            var menu = document.getElementById('row-config-menu');
            menu.style.display = menu.style.display === 'none' ? 'block' : 'none';
        }}

        function toggleResourcePanel() {{
            var panel = document.getElementById('resource-panel');
            var handle = document.getElementById('resize-handle');
            if (!panel) return;
            if (panel.style.display === 'none') {{
                panel.style.display = 'flex';
                if (handle) handle.style.display = 'block';
            }} else {{
                panel.style.display = 'none';
                if (handle) handle.style.display = 'none';
            }}
            if (network) network.fit();
        }}

        function renderResourcePivotTable(data) {{
            var theadTr = document.getElementById('resource-thead-tr');
            var tbody = document.getElementById('resource-tbody');
            if (!theadTr || !tbody) return;
            theadTr.innerHTML = '';
            tbody.innerHTML = '';
            
            if (data.length === 0) return;
            
            data.sort((a, b) => {{
                var idxA = dcOrder.indexOf(a.DC);
                var idxB = dcOrder.indexOf(b.DC);
                if (idxA === -1) idxA = 1000;
                if (idxB === -1) idxB = 1000;
                return idxA - idxB;
            }});
            
            theadTr.innerHTML += `<th style="padding: 8px; text-align: left; background: #ff9800; color: white; border-bottom: 2px solid #ddd; min-width: 150px; position: sticky; top: 0; left: 0; z-index: 99;">Metric</th>`;
            theadTr.innerHTML += `<th style="padding: 8px; text-align: left; background: #ff9800; color: white; border-bottom: 2px solid #ddd; min-width: 50px; position: sticky; top: 0; z-index: 98;">UoM</th>`;
            theadTr.innerHTML += `<th style="padding: 8px; text-align: right; background: #ff9800; color: white; border-bottom: 2px solid #ddd; min-width: 80px; position: sticky; top: 0; z-index: 98;">Tổng</th>`;
            
            data.forEach(row => {{
                theadTr.innerHTML += `<th style="padding: 8px; text-align: right; background: #ff9800; color: white; border-bottom: 2px solid #ddd; min-width: 80px; position: sticky; top: 0; z-index: 98;">${{row.DC}}</th>`;
            }});
            
            var currentGroup = '';
            var currentSubGroup = '';

            window.rowConfig.forEach(function(cfg) {{
                if (!cfg.visible) return;
                
                if (cfg.group !== currentGroup) {{
                    currentGroup = cfg.group;
                    currentSubGroup = '';
                    var groupTr = document.createElement('tr');
                    var colsCount = 3 + data.length;
                    groupTr.innerHTML = `<td style="padding: 6px 8px; text-align: left; font-weight: bold; background: #fff3e0; position: sticky; left: 0; z-index: 97;">${{currentGroup}}</td><td colspan="${{colsCount - 1}}" style="background: #fff3e0; border-bottom: 1px solid #ddd;"></td>`;
                    tbody.appendChild(groupTr);
                }}
                
                if (cfg.subGroup && cfg.subGroup !== currentSubGroup) {{
                    currentSubGroup = cfg.subGroup;
                    var subGroupTr = document.createElement('tr');
                    var colsCount = 3 + data.length;
                    subGroupTr.innerHTML = `<td style="padding: 6px 8px 6px 20px; text-align: left; font-weight: bold; color: #555; background: #fafafa; position: sticky; left: 0; z-index: 97; font-style: italic;">${{currentSubGroup}}</td><td colspan="${{colsCount - 1}}" style="background: #fafafa; border-bottom: 1px solid #eee;"></td>`;
                    tbody.appendChild(subGroupTr);
                }}
                
                var formatVal = function(val, dec, unit) {{
                    if (val === undefined || val === null || val === 0) return '-';
                    // Force 0 decimals
                    var numStr = val.toLocaleString('en-US', {{minimumFractionDigits: 0, maximumFractionDigits: 0}});
                    return numStr + (unit ? ' ' + unit : '');
                }};

                var totalVal = 0;
                data.forEach(row => {{
                    var val = Number(row[cfg.name] || 0);
                    if (cfg.name !== 'Capacity_Thruput') {{
                        totalVal += val;
                    }}
                }});

                var tr = document.createElement('tr');
                tr.style.borderBottom = '1px solid #eee';
                
                var paddingLeft = cfg.subGroup ? '30px' : '15px';
                var tdName = `<td style="padding: 6px 8px 6px ${{paddingLeft}}; text-align: left; position: sticky; left: 0; background: white; z-index: 97; box-shadow: 2px 0 5px rgba(0,0,0,0.05);">${{cfg.displayName || cfg.name}}</td>`;
                var tdUom = `<td style="padding: 6px 8px; text-align: left; color: #666;">${{cfg.uom}}</td>`;
                var tdTotal = `<td style="padding: 6px 8px; text-align: right; font-weight: bold; color: #1976d2;">${{cfg.name === 'Capacity_Thruput' ? '-' : formatVal(totalVal, 0, '')}}</td>`;
                
                tr.innerHTML = tdName + tdUom + tdTotal;
                
                data.forEach(row => {{
                    var val = Number(row[cfg.name] || 0);
                    tr.innerHTML += `<td style="padding: 6px 8px; text-align: right;">${{formatVal(val, 0, '')}}</td>`;
                }});
                
                tbody.appendChild(tr);
            }});
        }}

        function renderPivotTable(data) {{
            window.currentData = data;
            var tbody = document.getElementById('pivot-tbody');
            var tfoot = document.getElementById('pivot-tfoot');
            if (tbody) tbody.innerHTML = '';
            
            var totalCases = 0;
            var totalTan = 0;
            var totalM3 = 0;
            var totalPallet = 0;
            var totalStock = 0;
            var totalDienTich = 0;
            var totalPalletThruput = 0;
            var totalCapacityThruput = 0;
            var totalPeople = 0;
            var totalF2DContBo = 0;
            var totalD2DContBo = 0;
            var totalF2DContBien = 0;
            var totalD2DContBien = 0;
            var totalF2DXePallet = 0;
            var totalD2DXePallet = 0;
            var totalTruck15 = 0;
            var totalTruck2 = 0;
            var totalF2DActualTan = 0;
            var totalF2DActualM3 = 0;
            var totalD2DActualTan = 0;
            var totalD2DActualM3 = 0;
            var totalD2CActualTan = 0;
            var totalD2CActualM3 = 0;
            
            if (data.length > 0) {{
                data.sort((a, b) => {{
                    var idxA = dcOrder.indexOf(a.DC);
                    var idxB = dcOrder.indexOf(b.DC);
                    if (idxA === -1) idxA = 1000;
                    if (idxB === -1) idxB = 1000;
                    return idxA - idxB;
                }});
                
                data.forEach(function(row) {{
                    totalCases += Math.round(row.Case || 0);
                    totalTan += Number(row['Tấn'] || 0);
                    totalM3 += Number(row['M3'] || 0);
                    totalPallet += Math.round(row['Pallet'] || 0);
                    totalPalletThruput += Math.round(row['Pallet Thruput'] || 0);
                    totalStock += Math.round(row['Total Stock Pos'] || 0);
                    totalDienTich += Math.round(row['Diện tích'] || 0);
                    totalCapacityThruput += Number(row['Capacity_Thruput'] || 0);
                    totalPeople += Math.round(row['People'] || 0);
                    totalF2DContBo += Math.round(row['F2D Cont bộ'] || 0);
                    totalD2DContBo += Math.round(row['D2D Cont bộ'] || 0);
                    totalF2DContBien += Math.round(row['F2D Cont biển'] || 0);
                    totalD2DContBien += Math.round(row['D2D Cont biển'] || 0);
                    totalF2DXePallet += Math.round(row['F2D Xe pallet'] || 0);
                    totalD2DXePallet += Math.round(row['D2D Xe pallet'] || 0);
                    totalTruck15 += Math.round(row['Truck 15 tấn'] || 0);
                    totalTruck2 += Math.round(row['Truck 2 tấn'] || 0);
                    totalF2DActualTan += Number(row['F2D Actual Tấn'] || 0);
                    totalF2DActualM3 += Number(row['F2D Actual M3'] || 0);
                    totalD2DActualTan += Number(row['D2D Actual Tấn'] || 0);
                    totalD2DActualM3 += Number(row['D2D Actual M3'] || 0);
                    totalD2CActualTan += Number(row['D2C Actual Tấn'] || 0);
                    totalD2CActualM3 += Number(row['D2C Actual M3'] || 0);
                }});
            }}
            
            var computedTotals = {{
                'Case': totalCases,
                'Tấn': totalTan,
                'M3': totalM3,
                'Pallet': totalPallet,
                'Pallet Thruput': totalPalletThruput,
                'Total Stock Pos': totalStock,
                'Diện tích': totalDienTich,
                'Capacity Thruput': totalCapacityThruput,
                'People': totalPeople,
                'F2D Xe pallet': totalF2DXePallet,
                'F2D Cont bộ': totalF2DContBo,
                'F2D Cont biển': totalF2DContBien,
                'F2D Actual Tấn': totalF2DActualTan,
                'F2D Actual M3': totalF2DActualM3,
                'D2D Xe pallet': totalD2DXePallet,
                'D2D Cont bộ': totalD2DContBo,
                'D2D Cont biển': totalD2DContBien,
                'D2D Actual Tấn': totalD2DActualTan,
                'D2D Actual M3': totalD2DActualM3,
                'Truck 15 tấn': totalTruck15,
                'Truck 2 tấn': totalTruck2,
                'D2C Actual Tấn': totalD2CActualTan,
                'D2C Actual M3': totalD2CActualM3
            }};

            var currentGroup = '';
            var currentSubGroup = '';

            window.rowConfig.forEach(function(cfg) {{
                if (!cfg.visible) return;
                
                if (cfg.group !== currentGroup) {{
                    currentGroup = cfg.group;
                    currentSubGroup = '';
                    var groupTr = document.createElement('tr');
                    var groupTd = `<td style="padding: 6px 8px; text-align: left; font-weight: bold; background: #e3f2fd; position: sticky; left: -15px; z-index: 98;">${{currentGroup}}</td><td colspan="${{ratioData.length + 3}}" style="background: #e3f2fd; border-bottom: 1px solid #ddd;"></td>`;
                    groupTr.innerHTML = groupTd;
                    if (tbody) tbody.appendChild(groupTr);
                }}
                
                if (cfg.subGroup && cfg.subGroup !== currentSubGroup) {{
                    currentSubGroup = cfg.subGroup;
                    var subGroupTr = document.createElement('tr');
                    var subGroupTd = `<td style="padding: 6px 8px 6px 20px; text-align: left; font-weight: 600; background: #f5f5f5; color: #555; font-style: italic; position: sticky; left: -15px; z-index: 98;">${{currentSubGroup}}</td><td colspan="${{ratioData.length + 3}}" style="background: #f5f5f5; border-bottom: 1px solid #eee;"></td>`;
                    subGroupTr.innerHTML = subGroupTd;
                    if (tbody) tbody.appendChild(subGroupTr);
                }}
                
                var paddingLeft = cfg.subGroup ? '35px' : '20px';
                var tr = document.createElement('tr');
                var displayName = cfg.displayName || cfg.name;
                var tooltipHtml = cfg.tooltip ? `<span title="${{cfg.tooltip}}" style="cursor: help; color: #888; font-size: 11px; margin-left: 6px; border: 1px solid #ccc; border-radius: 50%; padding: 0 4px; display: inline-block;">?</span>` : '';
                var uomText = cfg.uom || '';
                var tdHtml = `<td style="padding: 6px 8px 6px ${{paddingLeft}}; text-align: left; font-weight: 500; position: sticky; left: -15px; background: white; z-index: 98; border-bottom: 1px solid #eee; white-space: nowrap;">${{displayName}}${{tooltipHtml}}</td>
                              <td style="padding: 6px 8px; text-align: left; border-bottom: 1px solid #eee; font-style: italic; color: #666;">${{uomText}}</td>`;
                
                var maxVal = 0;
                var sumVal = 0;
                var dailyVals = [];
                ratioData.forEach(function(r) {{
                    var val = computedTotals[cfg.name] * r.Ratio;
                    dailyVals.push(val);
                    if (val > maxVal) maxVal = val;
                    sumVal += val;
                }});
                var avgVal = dailyVals.length > 0 ? sumVal / dailyVals.length : 0;
                
                var maxStr = cfg.isDecimal ? Number(maxVal).toLocaleString('en-US', {{maximumFractionDigits: 2}}) : Math.round(maxVal).toLocaleString('en-US');
                var avgStr = cfg.isDecimal ? Number(avgVal).toLocaleString('en-US', {{maximumFractionDigits: 2}}) : Math.round(avgVal).toLocaleString('en-US');
                
                tdHtml += `<td style="padding: 6px 8px; text-align: right; border-bottom: 1px solid #eee; font-weight: 600; color: #d32f2f;">${{maxStr}}</td>`;
                tdHtml += `<td style="padding: 6px 8px; text-align: right; border-bottom: 1px solid #eee; font-weight: 600; color: #1976d2;">${{avgStr}}</td>`;

                dailyVals.forEach(function(val) {{
                    var displayStr = cfg.isDecimal ? Number(val).toLocaleString('en-US', {{maximumFractionDigits: 2}}) : Math.round(val).toLocaleString('en-US');
                    tdHtml += `<td style="padding: 6px 8px; text-align: right; border-bottom: 1px solid #eee;">${{displayStr}}</td>`;
                }});
                
                tr.innerHTML = tdHtml;
                if (tbody) tbody.appendChild(tr);
            }});
        }}

        // Setup filter dropdown
        var custSet = new Set();
        var itemSet = new Set();
        var provSet = new Set();
        var dcSet = new Set();
        
        pathMapping.forEach(p => {{
            if (p.Cust) custSet.add(p.Cust + ' - ' + p.CustName);
            if (p.Item) itemSet.add(p.Item);
            if (p.Prov) provSet.add(p.Prov);
            if (p.DC_Out) dcSet.add(p.DC_Out);
        }});

        var customerList = document.getElementById('customer-list');
        Array.from(custSet).sort().forEach(c => {{
            var option = document.createElement('option');
            option.value = c;
            customerList.appendChild(option);
        }});

        var itemList = document.getElementById('item-list');
        Array.from(itemSet).sort().forEach(i => {{
            var option = document.createElement('option');
            option.value = i;
            itemList.appendChild(option);
        }});

        var provinceList = document.getElementById('province-list');
        Array.from(provSet).sort().forEach(p => {{
            var option = document.createElement('option');
            option.value = p;
            provinceList.appendChild(option);
        }});

        var dcList = document.getElementById('dc-list');
        Array.from(dcSet).sort().forEach(d => {{
            var option = document.createElement('option');
            option.value = d;
            dcList.appendChild(option);
        }});
        
        // Initial render for Resource Panel
        renderResourcePivotTable(originalPivotData);

        // Resizable panel logic
        (function() {{
            var handle = document.getElementById('resize-handle');
            var panel = document.getElementById('resource-panel');
            var isResizing = false;
            
            if (handle && panel) {{
                handle.addEventListener('mousedown', function(e) {{
                    isResizing = true;
                    document.body.style.cursor = 'col-resize';
                    document.body.style.userSelect = 'none';
                }});
                
                document.addEventListener('mousemove', function(e) {{
                    if (!isResizing) return;
                    var container = document.getElementById('DetailTab');
                    if (container) {{
                        var containerRect = container.getBoundingClientRect();
                        var newWidth = containerRect.right - e.clientX - 15;
                        if (newWidth > 200 && newWidth < containerRect.width * 0.7) {{
                            panel.style.width = newWidth + 'px';
                        }}
                    }}
                }});
                
                document.addEventListener('mouseup', function(e) {{
                    if (isResizing) {{
                        isResizing = false;
                        document.body.style.cursor = '';
                        document.body.style.userSelect = '';
                        if (network) network.fit();
                    }}
                }});
            }}
        }})();

        function exportTableToExcel(tableID, filename = '') {{
            var tableSelect = document.getElementById(tableID);
            var html = tableSelect.outerHTML;
            var blob = new Blob(['\\ufeff' + html], {{ type: 'application/vnd.ms-excel' }});
            var url = URL.createObjectURL(blob);
            var a = document.createElement('a');
            a.href = url;
            a.download = filename ? filename + '.xls' : 'PivotTable.xls';
            a.click();
            URL.revokeObjectURL(url);
        }}

        function generateNodeSvgJs(title, data, borderColor) {{
            var width = 175;
            var height = 40;
            var statsSvg = "";
            var yOffset = 50;

            function addText(label, value) {{
                if (value !== undefined && value !== null && value !== 'nan' && value !== '') {{
                    var displayVal = (typeof value === 'number') ? Math.round(value).toLocaleString('en-US') : value;
                    statsSvg += `<text x="15" y="${{yOffset}}" font-family="Segoe UI" font-size="14" fill="black">${{label}}: ${{displayVal}}</text>`;
                    yOffset += 20;
                }}
            }}

            addText("Area", data.area_service);
            addText("Prov", data.province);
            addText("Name", data.customer_name);
            addText("Case", data.cases);
            addText("Pallet OB D2C", data.pallet_ob_d2c);
            addText("Pallet IB D2D", data.pallet_ib_d2d);
            addText("Stock Pos", data.stock_pos);
            addText("Pallet OB F2D", data.pallet_ob_f2d);
            addText("Pallet IB F2D", data.pallet_ib_f2d);
            addText("Pallet OB D2D", data.pallet_ob_d2d);
            addText("DRP Stock", data.drp_stock);
            addText("Xe pallet", data.xe_pallet);
            addText("Cont biển", data.cont_bien);
            addText("Cont bộ", data.cont_bo);
            addText("Truck 15 tấn", data.truck_15_tan);
            addText("Truck 2 tấn", data.truck_2_tan);

            if (yOffset > 50) {{
                height = yOffset - 10;
            }}

            var svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${{width}}" height="${{height}}">
                <rect x="1" y="1" width="${{width-2}}" height="${{height-2}}" fill="white" stroke="#ccc" stroke-width="1.5" rx="10" ry="10"/>
                <path d="M 12 1 L 12 ${{height-1}} L 11 ${{height-1}} A 10 10 0 0 1 1 ${{height-11}} L 1 11 A 10 10 0 0 1 11 1 Z" fill="${{borderColor}}"/>
                <text x="20" y="26" font-family="Segoe UI" font-size="16" font-weight="bold" fill="#333">${{title}}</text>
                ${{statsSvg}}
            </svg>`;
            
            var uri = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(svg);
            var size = 50 * Math.max(175, height) / 175;
            return {{ uri: uri, size: size }};
        }}

        function applyFilter() {{
            var getList = (id) => document.getElementById(id).value.split(',').map(s => s.trim().split(' - ')[0]).filter(s => s);
            
            var custIds = getList('customer-search');
            var itemIds = getList('item-search');
            var provs = getList('province-search');
            var dcs = getList('dc-search');
            
            var errorDiv = document.getElementById('filter-error');
            
            if (custIds.length === 0 && itemIds.length === 0 && provs.length === 0 && dcs.length === 0) {{
                errorDiv.innerText = "Vui lòng nhập ít nhất 1 điều kiện lọc!";
                errorDiv.style.display = 'block';
                return;
            }}
            
            var filteredPaths = pathMapping.filter(p => {{
                var matchCust = custIds.length === 0 || custIds.includes(p.Cust);
                var matchItem = itemIds.length === 0 || itemIds.includes(p.Item);
                var matchProv = provs.length === 0 || provs.includes(p.Prov);
                var matchDc = dcs.length === 0 || dcs.includes(p.DC_Out);
                return matchCust && matchItem && matchProv && matchDc;
            }});
            
            if (filteredPaths.length === 0) {{
                errorDiv.innerText = "Không tìm thấy kết quả phù hợp!";
                errorDiv.style.display = 'block';
                return;
            }}
            
            errorDiv.style.display = 'none';
            
            var newNodes = [];
            var newEdges = [];
            var edgesSet = new Set();
            
            var groupColors = {{
                'Country': '#d32f2f',
                'Factory': '#00838f',
                'DC_DRP': '#ef6c00',
                'DC_Out': '#2e7d32',
                'Customer': '#c2185b',
                'Item': '#1976d2',
                'Province': '#9c27b0'
            }};

            var nodeAgg = {{ Customer: {{}}, Item: {{}}, Province: {{}}, DC_Out: {{}}, DC_DRP: {{}}, Factory: {{}} }};

            filteredPaths.forEach(p => {{
                if (custIds.length > 0 && p.Cust) {{
                    var custId = "CUST_" + p.Cust;
                    if (!nodeAgg.Customer[custId]) nodeAgg.Customer[custId] = {{ title: p.Cust, name: p.CustName, area: p.Area, prov: p.Prov, cases: 0 }};
                    nodeAgg.Customer[custId].cases += p.Cases;
                }}
                
                if (itemIds.length > 0 && p.Item) {{
                    var itemId = "ITEM_" + p.Item;
                    if (!nodeAgg.Item[itemId]) nodeAgg.Item[itemId] = {{ title: p.Item, cases: 0 }};
                    nodeAgg.Item[itemId].cases += p.Cases;
                }}

                if (p.Prov && p.Prov !== 'None' && p.Prov !== 'nan') {{
                    var provId = "PROV_" + p.Prov;
                    if (!nodeAgg.Province[provId]) nodeAgg.Province[provId] = {{cases: 0, title: p.Prov}};
                    nodeAgg.Province[provId].cases += p.Cases;
                    
                    if (custIds.length > 0 && p.Cust) edgesSet.add(provId + "->CUST_" + p.Cust);
                    if (itemIds.length > 0 && p.Item) edgesSet.add(provId + "->ITEM_" + p.Item);
                    
                    var outId = "OUT_" + p.DC_Out;
                    if (!nodeAgg.DC_Out[outId]) nodeAgg.DC_Out[outId] = {{title: p.DC_Out, cases: 0, pallet_ob_d2c: 0, stock_pos: 0, pallet_ib_d2d: 0, truck_15: 0, truck_2: 0}};
                    nodeAgg.DC_Out[outId].cases += p.Cases;
                    nodeAgg.DC_Out[outId].pallet_ob_d2c += p.Pallet_OB_D2C;
                    nodeAgg.DC_Out[outId].stock_pos += p.Stock_Pos;
                    nodeAgg.DC_Out[outId].pallet_ib_d2d += p.Pallet_IB_D2D;
                    nodeAgg.DC_Out[outId].truck_15 += p.D2D_Xe_pallet;
                    nodeAgg.DC_Out[outId].truck_2 += p.D2D_Cont_bien;
                    edgesSet.add(outId + "->" + provId);
                }} else {{
                    var outId = "OUT_" + p.DC_Out;
                    if (!nodeAgg.DC_Out[outId]) nodeAgg.DC_Out[outId] = {{title: p.DC_Out, cases: 0, pallet_ob_d2c: 0, stock_pos: 0, pallet_ib_d2d: 0, truck_15: 0, truck_2: 0}};
                    nodeAgg.DC_Out[outId].cases += p.Cases;
                    nodeAgg.DC_Out[outId].pallet_ob_d2c += p.Pallet_OB_D2C;
                    nodeAgg.DC_Out[outId].stock_pos += p.Stock_Pos;
                    nodeAgg.DC_Out[outId].pallet_ib_d2d += p.Pallet_IB_D2D;
                    nodeAgg.DC_Out[outId].truck_15 += p.D2D_Xe_pallet;
                    nodeAgg.DC_Out[outId].truck_2 += p.D2D_Cont_bien;
                    
                    if (custIds.length > 0 && p.Cust) edgesSet.add(outId + "->CUST_" + p.Cust);
                    if (itemIds.length > 0 && p.Item) edgesSet.add(outId + "->ITEM_" + p.Item);
                }}

                var drpId = "DRP_" + p.DC_DRP;
                if (!nodeAgg.DC_DRP[drpId]) nodeAgg.DC_DRP[drpId] = {{title: p.DC_DRP, pallet_ob_d2d: 0, pallet_ib_f2d: 0, xe_pallet: 0, cont_bien: 0, cont_bo: 0}};
                nodeAgg.DC_DRP[drpId].pallet_ob_d2d += p.Pallet_OB_D2D;
                nodeAgg.DC_DRP[drpId].pallet_ib_f2d += p.Pallet_IB_F2D;
                nodeAgg.DC_DRP[drpId].xe_pallet += p.D2D_Xe_pallet;
                nodeAgg.DC_DRP[drpId].cont_bien += p.D2D_Cont_bien;
                nodeAgg.DC_DRP[drpId].cont_bo += p.D2D_Cont_bo;
                edgesSet.add(drpId + "->" + outId);
                
                var factId = "FACT_" + p.Fact;
                if (!nodeAgg.Factory[factId]) nodeAgg.Factory[factId] = {{title: p.Fact, pallet_ob_f2d: 0, xe_pallet: 0, cont_bien: 0, cont_bo: 0}};
                nodeAgg.Factory[factId].pallet_ob_f2d += p.Pallet_OB_F2D;
                nodeAgg.Factory[factId].xe_pallet += p.F2D_Xe_pallet;
                nodeAgg.Factory[factId].cont_bien += p.F2D_Cont_bien;
                nodeAgg.Factory[factId].cont_bo += p.F2D_Cont_bo;
                edgesSet.add(factId + "->" + drpId);
            }});
            
            var dynamicYSpacing = 160;
            
            function addGroupNodes(groupObj, level, groupName, generateSvgFunc) {{
                var items = [];
                for (var id in groupObj) {{
                    var origY = originalNodeMap[id] ? originalNodeMap[id].y : 0;
                    items.push({{id: id, n: groupObj[id], origY: origY}});
                }}
                items.sort((a, b) => a.origY - b.origY);
                
                items.forEach((item, index) => {{
                    var img = generateSvgFunc(item.n);
                    newNodes.push({{
                        id: item.id,
                        level: level,
                        x: originalNodeMap[item.id] ? originalNodeMap[item.id].x : level * 350,
                        y: index * dynamicYSpacing,
                        group: groupName,
                        shape: 'image',
                        image: img.uri,
                        size: img.size
                    }});
                }});
            }}

            addGroupNodes(nodeAgg.Customer, 5, 'Customer', function(n) {{
                return generateNodeSvgJs("Cust: " + n.title, {{
                    customer_name: n.name,
                    area_service: n.area,
                    province: n.prov,
                    cases: n.cases
                }}, groupColors['Customer']);
            }});
            
            addGroupNodes(nodeAgg.Item, 5, 'Item', function(n) {{
                return generateNodeSvgJs("Item: " + n.title, {{
                    cases: n.cases
                }}, groupColors['Item']);
            }});

            addGroupNodes(nodeAgg.Province, 4, 'Province', function(n) {{
                return generateNodeSvgJs(n.title, {{ cases: n.cases }}, groupColors['Province']);
            }});

            addGroupNodes(nodeAgg.DC_Out, 3, 'DC_Out', function(n) {{
                return generateNodeSvgJs(n.title, {{ 
                    cases: n.cases, 
                    pallet_ob_d2c: n.pallet_ob_d2c, 
                    stock_pos: n.stock_pos,
                    pallet_ib_d2d: n.pallet_ib_d2d,
                    truck_15_tan: n.truck_15,
                    truck_2_tan: n.truck_2
                }}, groupColors['DC_Out']);
            }});

            addGroupNodes(nodeAgg.DC_DRP, 2, 'DC_DRP', function(n) {{
                return generateNodeSvgJs(n.title, {{ 
                    pallet_ob_d2d: n.pallet_ob_d2d,
                    pallet_ib_f2d: n.pallet_ib_f2d,
                    drp_stock: n.pallet_ib_f2d * drpStockValue,
                    xe_pallet: n.xe_pallet,
                    cont_bien: n.cont_bien,
                    cont_bo: n.cont_bo
                }}, groupColors['DC_DRP']);
            }});

            addGroupNodes(nodeAgg.Factory, 1, 'Factory', function(n) {{
                return generateNodeSvgJs(n.title, {{ 
                    pallet_ob_f2d: n.pallet_ob_f2d,
                    xe_pallet: n.xe_pallet,
                    cont_bien: n.cont_bien,
                    cont_bo: n.cont_bo
                }}, groupColors['Factory']);
            }});

            edgesSet.forEach(e => {{
                var parts = e.split('->');
                newEdges.push({{from: parts[0], to: parts[1]}});
            }});

            nodes.clear();
            edges.clear();
            nodes.add(newNodes);
            edges.add(newEdges);
            
            var pivotAgg = {{}};
            filteredPaths.forEach(p => {{
                var outDC = p.DC_Out;
                if (!pivotAgg[outDC]) pivotAgg[outDC] = {{ DC: outDC, Case: 0, 'Tấn': 0, 'M3': 0, 'Pallet': 0, 'Pallet Thruput': 0, 'Total Stock Pos': 0, 'F2D Cont bộ': 0, 'D2D Cont bộ': 0, 'F2D Cont biển': 0, 'D2D Cont biển': 0, 'F2D Xe pallet': 0, 'D2D Xe pallet': 0, 'Truck 15 tấn': 0, 'Truck 2 tấn': 0, 'F2D Actual Tấn': 0, 'F2D Actual M3': 0, 'D2D Actual Tấn': 0, 'D2D Actual M3': 0, 'D2C Actual Tấn': 0, 'D2C Actual M3': 0 }};
                pivotAgg[outDC].Case += p.Cases;
                pivotAgg[outDC]['Tấn'] += p.Tan;
                pivotAgg[outDC]['M3'] += p.M3;
                pivotAgg[outDC]['Pallet'] += p.Pallet_OB_D2C;
                pivotAgg[outDC]['Pallet Thruput'] += p.Pallet_OB_D2C;
                pivotAgg[outDC]['Pallet Thruput'] += p.Pallet_IB_D2D;
                pivotAgg[outDC]['Total Stock Pos'] += p.Stock_Pos;

                pivotAgg[outDC]['Truck 15 tấn'] += p.D2C_Truck_15 + p.D2D_Xe_pallet;
                pivotAgg[outDC]['Truck 2 tấn'] += p.D2C_Truck_2 + p.D2D_Cont_bien;
                pivotAgg[outDC]['D2C Actual Tấn'] += p.D2C_Actual_Tan;
                pivotAgg[outDC]['D2C Actual M3'] += p.D2C_Actual_M3;
                
                var drpDC = p.DC_DRP;
                if (!pivotAgg[drpDC]) pivotAgg[drpDC] = {{ DC: drpDC, Case: 0, 'Tấn': 0, 'M3': 0, 'Pallet': 0, 'Pallet Thruput': 0, 'Total Stock Pos': 0, 'F2D Cont bộ': 0, 'D2D Cont bộ': 0, 'F2D Cont biển': 0, 'D2D Cont biển': 0, 'F2D Xe pallet': 0, 'D2D Xe pallet': 0, 'Truck 15 tấn': 0, 'Truck 2 tấn': 0, 'F2D Actual Tấn': 0, 'F2D Actual M3': 0, 'D2D Actual Tấn': 0, 'D2D Actual M3': 0, 'D2C Actual Tấn': 0, 'D2C Actual M3': 0 }};
                pivotAgg[drpDC]['Pallet Thruput'] += p.Pallet_OB_D2D;
                pivotAgg[drpDC]['Pallet Thruput'] += p.Pallet_IB_F2D;
                pivotAgg[drpDC]['Total Stock Pos'] += (p.Pallet_IB_F2D * drpStockValue);
                pivotAgg[drpDC]['F2D Cont bộ'] += p.F2D_Cont_bo;
                pivotAgg[drpDC]['D2D Cont bộ'] += p.D2D_Cont_bo;
                pivotAgg[drpDC]['F2D Cont biển'] += p.F2D_Cont_bien;
                pivotAgg[drpDC]['D2D Cont biển'] += p.D2D_Cont_bien;
                pivotAgg[drpDC]['F2D Xe pallet'] += p.F2D_Xe_pallet;
                pivotAgg[drpDC]['D2D Xe pallet'] += p.D2D_Xe_pallet;
                pivotAgg[drpDC]['F2D Actual Tấn'] += p.F2D_Actual_Tan;
                pivotAgg[drpDC]['F2D Actual M3'] += p.F2D_Actual_M3;
                pivotAgg[drpDC]['D2D Actual Tấn'] += p.D2D_Actual_Tan;
                pivotAgg[drpDC]['D2D Actual M3'] += p.D2D_Actual_M3;
            }});
            
            var filteredPivotData = Object.values(pivotAgg).map(row => {{
                row['Diện tích'] = row['Total Stock Pos'] * m2PerPalletPos;
                row['Capacity_Thruput'] = peopleCapacityMap[row.DC] || 0;
                row['People'] = row['Capacity_Thruput'] * row['Pallet Thruput'];
                return row;
            }});
            renderPivotTable(filteredPivotData);
            renderResourcePivotTable(filteredPivotData);
            
            network.fit();
        }}

        function clearFilter() {{
            document.getElementById('customer-search').value = '';
            document.getElementById('item-search').value = '';
            document.getElementById('province-search').value = '';
            document.getElementById('dc-search').value = '';
            document.getElementById('filter-error').style.display = 'none';
            
            nodes.clear();
            edges.clear();
            nodes.add(originalNodes);
            edges.add(originalEdges);
            
            renderPivotTable(originalPivotData);
            renderResourcePivotTable(originalPivotData);
            
            network.fit();
        }}
    </script>
</body>
</html>"""

    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print("Successfully generated network diagram!")

if __name__ == "__main__":
    excel_file = "c:/Users/phatvt/OneDrive/Image/Hình ảnh/ThanhPhat_Masan/DC FMCG/org/Base_Line/base line Supra.xlsx"
    output_file = "c:/Users/phatvt/OneDrive/Image/Hình ảnh/ThanhPhat_Masan/DC FMCG/org/Base_Line/Supply_Chain_Network_3Views.html"
    process_supply_chain_data(excel_file, output_file)
