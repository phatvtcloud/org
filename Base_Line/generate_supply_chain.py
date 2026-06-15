import pandas as pd
import numpy as np
import json
import urllib.parse
import os

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
        <rect x="1" y="1" width="{width-2}" height="{height-2}" fill="white" stroke="black" stroke-width="1"/>
        <rect x="1" y="1" width="8" height="{height-2}" fill="{border_color}"/>
        <text x="15" y="25" font-family="Segoe UI" font-size="16" font-weight="bold" fill="black">{title}</text>
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

    if 'Loại xe F2D' in master.columns:
        master['F2D Cont bộ'] = calc_vehicle('Loại xe F2D', 'Cont bộ')
        master['F2D Cont biển'] = calc_vehicle('Loại xe F2D', 'Cont biển')
        master['F2D Xe pallet'] = calc_vehicle('Loại xe F2D', 'Xe pallet')
    else:
        master['F2D Cont bộ'] = 0
        master['F2D Cont biển'] = 0
        master['F2D Xe pallet'] = 0
    
    if 'Loại xe D2D' in master.columns:
        d2d_cond = np.where(master['DC_DRP'] == master['DC_Out'], 0, 1)
        master['D2D Cont bộ'] = calc_vehicle('Loại xe D2D', 'Cont bộ', d2d_cond)
        master['D2D Cont biển'] = calc_vehicle('Loại xe D2D', 'Cont biển', d2d_cond)
        master['D2D Xe pallet'] = calc_vehicle('Loại xe D2D', 'Xe pallet', d2d_cond)
    else:
        master['D2D Cont bộ'] = 0
        master['D2D Cont biển'] = 0
        master['D2D Xe pallet'] = 0

    if 'Loại xe D2C' in master.columns:
        master['D2C Truck 15 tấn'] = calc_vehicle('Loại xe D2C', 'Truck 15 tấn')
        master['D2C Truck 2 tấn'] = calc_vehicle('Loại xe D2C', 'Truck 2 tấn')
    else:
        master['D2C Truck 15 tấn'] = 0
        master['D2C Truck 2 tấn'] = 0

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


    # DC_Out Nodes
    dc_out_agg = master.groupby('DC_Out').agg({
        'Case': 'sum',
        'Pallet OB D2C': 'sum',
        'Stock Pos': 'sum',
        'Pallet IB D2D': 'sum',
        'D2D Xe pallet': 'sum',
        'D2D Cont biển': 'sum',
        'D2C Truck 15 tấn': 'sum',
        'D2C Truck 2 tấn': 'sum'
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
    # DC_DRP Nodes
    dc_drp_agg = master.groupby('DC_DRP').agg({
        'Pallet OB D2D': 'sum',
        'Pallet IB F2D': 'sum',
        'F2D Cont bộ': 'sum',
        'F2D Cont biển': 'sum',
        'F2D Xe pallet': 'sum',
        'D2D Cont bộ': 'sum',
        'D2D Cont biển': 'sum',
        'D2D Xe pallet': 'sum'
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
    
    df_pivot['Diện tích'] = df_pivot['Total Stock Pos'] * m2_per_pallet_pos
    df_pivot['Pallet Thruput'] = df_pivot['Pallet OB D2C'] + df_pivot['Pallet IB D2D'] + df_pivot['Pallet OB D2D'] + df_pivot['Pallet IB F2D']
    
    df_pivot['Cont bộ'] = df_pivot['F2D Cont bộ'] + df_pivot['D2D Cont bộ']
    df_pivot['Cont biển'] = df_pivot['F2D Cont biển'] + df_pivot['D2D Cont biển_y']
    df_pivot['Xe pallet'] = df_pivot['F2D Xe pallet'] + df_pivot['D2D Xe pallet_y']
    df_pivot['Truck 15 tấn'] = df_pivot['D2C Truck 15 tấn'] + df_pivot['D2D Xe pallet_x']
    df_pivot['Truck 2 tấn'] = df_pivot['D2C Truck 2 tấn'] + df_pivot['D2D Cont biển_x']
    
    if not df_people.empty:
        df_pivot = pd.merge(df_pivot, df_people, left_on='DC', right_on='DC_out', how='left').fillna(0)
    else:
        df_pivot['Capacity_Thruput'] = 0.0
        
    df_pivot['Capacity_Thruput'] = pd.to_numeric(df_pivot['Capacity_Thruput'], errors='coerce').fillna(0)
    df_pivot['People'] = df_pivot['Capacity_Thruput'] * df_pivot['Pallet Thruput']
    
    df_pivot['order'] = df_pivot['DC'].map(lambda x: dc_order.index(x) if x in dc_order else 1000)
    df_pivot = df_pivot.sort_values(by='order').drop(columns=['order'])
    pivot_data = df_pivot[['DC', 'Case', 'Pallet Thruput', 'Total Stock Pos', 'Diện tích', 'Capacity_Thruput', 'People', 'Xe pallet', 'Cont bộ', 'Cont biển', 'Truck 15 tấn', 'Truck 2 tấn']].to_dict(orient='records')
    pivot_json = json.dumps(pivot_data)
    
    dc_order_json = json.dumps(dc_order)
    
    people_capacity_map = dict(zip(df_people['DC_out'], pd.to_numeric(df_people['Capacity_Thruput'], errors='coerce').fillna(0))) if not df_people.empty else {}
    people_capacity_json = json.dumps(people_capacity_map)
    
    pivot_html = f"""
    <div id="pivot-table-container" style="position: absolute; top: 15px; right: 15px; z-index: 100; background: white; padding: 15px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); max-height: 80vh; overflow-y: auto;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            <h3 style="margin: 0; font-size: 16px; color: #333;">Baseline by DC</h3>
            <div style="position: relative;">
                <button onclick="toggleColumnMenu()" style="background: none; border: 1px solid #ccc; border-radius: 4px; padding: 4px 8px; cursor: pointer; font-size: 12px;">⚙️ Columns</button>
                <div id="column-menu" style="display: none; position: absolute; right: 0; top: 100%; background: white; border: 1px solid #ccc; border-radius: 4px; padding: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); z-index: 101; width: max-content;">
                    <label style="display: block; margin-bottom: 5px; font-size: 13px;"><input type="checkbox" onchange="toggleColumn(2, this.checked)"> Case</label>
                    <label style="display: block; margin-bottom: 5px; font-size: 13px;"><input type="checkbox" onchange="toggleColumn(3, this.checked)"> Pallet Thruput</label>
                    <label style="display: block; margin-bottom: 5px; font-size: 13px;"><input type="checkbox" onchange="toggleColumn(4, this.checked)"> Total Stock Pos</label>
                    <label style="display: block; margin-bottom: 5px; font-size: 13px;"><input type="checkbox" checked onchange="toggleColumn(5, this.checked)"> Diện tích</label>
                    <label style="display: block; margin-bottom: 5px; font-size: 13px;"><input type="checkbox" onchange="toggleColumn(6, this.checked)"> Capacity Thruput</label>
                    <label style="display: block; margin-bottom: 5px; font-size: 13px;"><input type="checkbox" checked onchange="toggleColumn(7, this.checked)"> People</label>
                    <label style="display: block; margin-bottom: 5px; font-size: 13px;"><input type="checkbox" checked onchange="toggleColumn(8, this.checked)"> Xe pallet</label>
                    <label style="display: block; margin-bottom: 5px; font-size: 13px;"><input type="checkbox" checked onchange="toggleColumn(9, this.checked)"> Cont bộ</label>
                    <label style="display: block; margin-bottom: 5px; font-size: 13px;"><input type="checkbox" checked onchange="toggleColumn(10, this.checked)"> Cont biển</label>
                    <label style="display: block; margin-bottom: 5px; font-size: 13px;"><input type="checkbox" checked onchange="toggleColumn(11, this.checked)"> Truck 15 tấn</label>
                    <label style="display: block; font-size: 13px;"><input type="checkbox" checked onchange="toggleColumn(12, this.checked)"> Truck 2 tấn</label>
                </div>
            </div>
        </div>
        <table id="pivot-table" style="width: 100%; border-collapse: collapse; font-size: 13px;">
            <thead style="position: sticky; top: -15px; background: white; z-index: 99;">
                <tr style="border-bottom: 2px solid #ddd;">
                    <th style="padding: 8px; text-align: left;">DC</th>
                    <th style="padding: 8px; text-align: right;">Case</th>
                    <th style="padding: 8px; text-align: right;">Pallet Thruput</th>
                    <th style="padding: 8px; text-align: right;">Total Stock Pos</th>
                    <th style="padding: 8px; text-align: right;">Diện tích</th>
                    <th style="padding: 8px; text-align: right;">Capacity Thruput</th>
                    <th style="padding: 8px; text-align: right;">People</th>
                    <th style="padding: 8px; text-align: right;">Xe pallet</th>
                    <th style="padding: 8px; text-align: right;">Cont bộ</th>
                    <th style="padding: 8px; text-align: right;">Cont biển</th>
                    <th style="padding: 8px; text-align: right;">Truck 15 tấn</th>
                    <th style="padding: 8px; text-align: right;">Truck 2 tấn</th>
                </tr>
            </thead>
            <tbody id="pivot-tbody">
            </tbody>
            <tfoot id="pivot-tfoot" style="position: sticky; bottom: -15px; background: white; z-index: 99;">
            </tfoot>
        </table>
    </div>
    """

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

    print("Preparing Customer Mapping for Filter...")
    customer_mapping = {}
    if 'Customer Number' in master.columns:
        cust_agg = master.groupby(['Customer Number', 'Customer Name', 'Area Service', 'Province', 'DC_Out', 'DC_DRP', 'Factory']).agg({
            'Case': 'sum',
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
            'D2C Truck 2 tấn': 'sum'
        }).reset_index()
        
        for _, row in cust_agg.iterrows():
            cust_id = str(row['Customer Number']).strip()
            if cust_id == 'nan' or not cust_id: continue
            
            if cust_id not in customer_mapping:
                customer_mapping[cust_id] = {
                    'Customer Name': str(row['Customer Name']).replace('nan', ''),
                    'Area Service': str(row['Area Service']).replace('nan', ''),
                    'Province': str(row['Province']).replace('nan', ''),
                    'paths': []
                }
                
            customer_mapping[cust_id]['paths'].append({
                'DC_Out': str(row['DC_Out']).replace('nan', ''),
                'DC_DRP': str(row['DC_DRP']).replace('nan', ''),
                'Factory': str(row['Factory']).replace('nan', ''),
                'Cases': float(row['Case']),
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
                'D2C_Truck_2': float(row['D2C Truck 2 tấn'])
            })
            
    customer_mapping_json = json.dumps(customer_mapping)

    nodes_json = json.dumps(nodes_list)
    edges_json = json.dumps(edges_list)

    # Generate HTML
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Supply Chain Network Diagram</title>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style type="text/css">
        body {{
            margin: 0;
            padding: 0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f5f5f5;
        }}
        #mynetwork {{
            width: 100vw;
            height: 100vh;
            border: none;
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
        }}
    </style>
</head>
<body>
    <button onclick="var el = document.getElementById('filter-wrapper'); el.style.display = el.style.display === 'none' ? 'block' : 'none'" style="position: absolute; top: 15px; left: 15px; z-index: 101; background: white; border: 1px solid #ccc; border-radius: 4px; padding: 8px 12px; cursor: pointer; font-size: 13px; font-weight: bold; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">🔍 Filter Customer</button>
    <div id="filter-wrapper" style="display: none; position: absolute; top: 55px; left: 15px; z-index: 100; background: white; padding: 15px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); width: 300px;">
        <label for="customer-search" style="font-weight: 600; font-size: 14px; margin-bottom: 8px; display: block; color: #333;">Lọc theo Customer Number:</label>
        <input type="text" id="customer-search" list="customer-list" placeholder="Nhập hoặc chọn Customer..." style="padding: 10px; width: 100%; box-sizing: border-box; border: 1px solid #ccc; border-radius: 4px; font-size: 14px;">
        <datalist id="customer-list"></datalist>
        <div style="margin-top: 15px; display: flex; gap: 10px;">
            <button onclick="applyFilter()" style="flex: 1; padding: 10px; background: #1976d2; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: 600; font-size: 14px;">Filter</button>
            <button onclick="clearFilter()" style="flex: 1; padding: 10px; background: #e53935; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: 600; font-size: 14px;">Clear</button>
        </div>
        <div id="filter-error" style="color: #d32f2f; margin-top: 10px; font-size: 13px; display: none; font-weight: 500;">Không tìm thấy Customer này!</div>
    </div>

    <div id="loading">Loading network...</div>
    <div id="mynetwork"></div>
    {pivot_html}

    <script type="text/javascript">
        var originalNodes = {nodes_json};
        var originalEdges = {edges_json};
        var nodes = new vis.DataSet(originalNodes);
        var edges = new vis.DataSet(originalEdges);
        var originalNodeMap = {{}};
        originalNodes.forEach(n => originalNodeMap[n.id] = n);
        var drpStockValue = {drp_stock_value};
        var m2PerPalletPos = {m2_per_pallet_pos};
        var customerMapping = {customer_mapping_json};
        var peopleCapacityMap = {people_capacity_json};
        var originalPivotData = {pivot_json};
        var dcOrder = {dc_order_json};

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

        function renderPivotTable(data) {{
            var tbody = document.getElementById('pivot-tbody');
            var tfoot = document.getElementById('pivot-tfoot');
            tbody.innerHTML = '';
            
            var totalCases = 0;
            var totalStock = 0;
            var totalDienTich = 0;
            var totalPalletThruput = 0;
            var totalPeople = 0;
            var totalContBo = 0;
            var totalContBien = 0;
            var totalXePallet = 0;
            var totalTruck15 = 0;
            var totalTruck2 = 0;
            
            data.sort((a, b) => {{
                var idxA = dcOrder.indexOf(a.DC);
                var idxB = dcOrder.indexOf(b.DC);
                if (idxA === -1) idxA = 1000;
                if (idxB === -1) idxB = 1000;
                return idxA - idxB;
            }});
            
            data.forEach(function(row) {{
                totalCases += Math.round(row.Case || 0);
                totalPalletThruput += Math.round(row['Pallet Thruput'] || 0);
                totalStock += Math.round(row['Total Stock Pos'] || 0);
                totalDienTich += Math.round(row['Diện tích'] || 0);
                totalPeople += Math.round(row['People'] || 0);
                totalContBo += Math.round(row['Cont bộ'] || 0);
                totalContBien += Math.round(row['Cont biển'] || 0);
                totalXePallet += Math.round(row['Xe pallet'] || 0);
                totalTruck15 += Math.round(row['Truck 15 tấn'] || 0);
                totalTruck2 += Math.round(row['Truck 2 tấn'] || 0);
                
                var tr = document.createElement('tr');
                tr.style.borderBottom = '1px solid #eee';
                tr.innerHTML = `
                    <td style="padding: 6px 8px; text-align: left; font-weight: 500;">${{row.DC}}</td>
                    <td style="padding: 6px 8px; text-align: right;">${{Math.round(row.Case).toLocaleString('en-US')}}</td>
                    <td style="padding: 6px 8px; text-align: right;">${{Math.round(row['Pallet Thruput']).toLocaleString('en-US')}}</td>
                    <td style="padding: 6px 8px; text-align: right;">${{Math.round(row['Total Stock Pos']).toLocaleString('en-US')}}</td>
                    <td style="padding: 6px 8px; text-align: right;">${{Math.round(row['Diện tích']).toLocaleString('en-US')}}</td>
                    <td style="padding: 6px 8px; text-align: right;">${{Number(row['Capacity_Thruput']).toLocaleString('en-US', {{maximumFractionDigits: 2}})}}</td>
                    <td style="padding: 6px 8px; text-align: right;">${{Math.round(row['People']).toLocaleString('en-US')}}</td>
                    <td style="padding: 6px 8px; text-align: right;">${{Math.round(row['Xe pallet']||0).toLocaleString('en-US')}}</td>
                    <td style="padding: 6px 8px; text-align: right;">${{Math.round(row['Cont bộ']||0).toLocaleString('en-US')}}</td>
                    <td style="padding: 6px 8px; text-align: right;">${{Math.round(row['Cont biển']||0).toLocaleString('en-US')}}</td>
                    <td style="padding: 6px 8px; text-align: right;">${{Math.round(row['Truck 15 tấn']||0).toLocaleString('en-US')}}</td>
                    <td style="padding: 6px 8px; text-align: right;">${{Math.round(row['Truck 2 tấn']||0).toLocaleString('en-US')}}</td>
                `;
                tbody.appendChild(tr);
            }});
            
            tfoot.innerHTML = `
                <tr style="font-weight: bold; border-top: 2px solid #ddd;">
                    <td style="padding: 8px; text-align: left;">Total</td>
                    <td style="padding: 8px; text-align: right;">${{Math.round(totalCases).toLocaleString('en-US')}}</td>
                    <td style="padding: 8px; text-align: right;">${{Math.round(totalPalletThruput).toLocaleString('en-US')}}</td>
                    <td style="padding: 8px; text-align: right;">${{Math.round(totalStock).toLocaleString('en-US')}}</td>
                    <td style="padding: 8px; text-align: right;">${{Math.round(totalDienTich).toLocaleString('en-US')}}</td>
                    <td style="padding: 8px; text-align: right;"></td>
                    <td style="padding: 8px; text-align: right;">${{Math.round(totalPeople).toLocaleString('en-US')}}</td>
                    <td style="padding: 8px; text-align: right;">${{Math.round(totalXePallet).toLocaleString('en-US')}}</td>
                    <td style="padding: 8px; text-align: right;">${{Math.round(totalContBo).toLocaleString('en-US')}}</td>
                    <td style="padding: 8px; text-align: right;">${{Math.round(totalContBien).toLocaleString('en-US')}}</td>
                    <td style="padding: 8px; text-align: right;">${{Math.round(totalTruck15).toLocaleString('en-US')}}</td>
                    <td style="padding: 8px; text-align: right;">${{Math.round(totalTruck2).toLocaleString('en-US')}}</td>
                </tr>
            `;
            
            applyColumnVisibility();
        }}

        // Column Visibility Logic
        var hiddenColumns = new Set([2, 3, 4, 6]);
        function toggleColumnMenu() {{
            var menu = document.getElementById('column-menu');
            menu.style.display = (menu.style.display === 'none' || menu.style.display === '') ? 'block' : 'none';
        }}
        function toggleColumn(colIndex, isVisible) {{
            if (isVisible) {{
                hiddenColumns.delete(colIndex);
            }} else {{
                hiddenColumns.add(colIndex);
            }}
            applyColumnVisibility();
        }}
        function applyColumnVisibility() {{
            var table = document.getElementById('pivot-table');
            if (!table) return;
            for (var r = 0; r < table.rows.length; r++) {{
                var row = table.rows[r];
                for (var c = 0; c < row.cells.length; c++) {{
                    var cell = row.cells[c];
                    if (hiddenColumns.has(c + 1)) {{
                        cell.style.display = 'none';
                    }} else {{
                        cell.style.display = '';
                    }}
                }}
            }}
        }}

        // Render initial pivot table
        renderPivotTable(originalPivotData);

        // Setup filter dropdown
        var customerList = document.getElementById('customer-list');
        for (var custId in customerMapping) {{
            var option = document.createElement('option');
            option.value = custId;
            option.text = custId + ' - ' + customerMapping[custId]['Customer Name'];
            customerList.appendChild(option);
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
                <rect x="1" y="1" width="${{width-2}}" height="${{height-2}}" fill="white" stroke="black" stroke-width="1"/>
                <rect x="1" y="1" width="8" height="${{height-2}}" fill="${{borderColor}}"/>
                <text x="15" y="25" font-family="Segoe UI" font-size="16" font-weight="bold" fill="black">${{title}}</text>
                ${{statsSvg}}
            </svg>`;
            
            var uri = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(svg);
            var size = 50 * Math.max(175, height) / 175;
            return {{ uri: uri, size: size }};
        }}

        function applyFilter() {{
            var custId = document.getElementById('customer-search').value.trim();
            var errorDiv = document.getElementById('filter-error');
            
            if (custId.indexOf(' - ') > -1) {{
                custId = custId.split(' - ')[0].trim();
            }}
            
            if (!custId || !customerMapping[custId]) {{
                errorDiv.style.display = 'block';
                return;
            }}
            errorDiv.style.display = 'none';
            
            var custData = customerMapping[custId];
            var newNodes = [];
            var newEdges = [];
            var edgesSet = new Set();
            
            var groupColors = {{
                'Country': '#d32f2f',
                'Factory': '#00838f',
                'DC_DRP': '#ef6c00',
                'DC_Out': '#2e7d32',
                'Customer': '#c2185b',
                'Province': '#9c27b0'
            }};

            var totalCases = 0;
            custData.paths.forEach(p => totalCases += p.Cases);
            
            var custImg = generateNodeSvgJs("Cust: " + custId, {{
                customer_name: custData['Customer Name'],
                area_service: custData['Area Service'],
                province: custData['Province'],
                cases: totalCases
            }}, groupColors['Customer']);
            
            newNodes.push({{
                id: "CUST_" + custId,
                level: 5,
                x: 5 * 350,
                y: 0,
                group: 'Customer',
                shape: 'image',
                image: custImg.uri,
                size: custImg.size
            }});

            var nodeAgg = {{ Province: {{}}, DC_Out: {{}}, DC_DRP: {{}}, Factory: {{}} }};

            custData.paths.forEach(p => {{
                var provId = "PROV_" + custData['Province'];
                if (!nodeAgg.Province[provId]) nodeAgg.Province[provId] = {{cases: 0, title: custData['Province']}};
                nodeAgg.Province[provId].cases += p.Cases;
                edgesSet.add(provId + "->CUST_" + custId);

                var outId = "OUT_" + p.DC_Out;
                if (!nodeAgg.DC_Out[outId]) nodeAgg.DC_Out[outId] = {{title: p.DC_Out, cases: 0, pallet_ob_d2c: 0, stock_pos: 0, pallet_ib_d2d: 0, truck_15: 0, truck_2: 0}};
                nodeAgg.DC_Out[outId].cases += p.Cases;
                nodeAgg.DC_Out[outId].pallet_ob_d2c += p.Pallet_OB_D2C;
                nodeAgg.DC_Out[outId].stock_pos += p.Stock_Pos;
                nodeAgg.DC_Out[outId].pallet_ib_d2d += p.Pallet_IB_D2D;
                nodeAgg.DC_Out[outId].truck_15 += p.D2D_Xe_pallet;
                nodeAgg.DC_Out[outId].truck_2 += p.D2D_Cont_bien;
                edgesSet.add(outId + "->" + provId);

                var drpId = "DRP_" + p.DC_DRP;
                if (!nodeAgg.DC_DRP[drpId]) nodeAgg.DC_DRP[drpId] = {{title: p.DC_DRP, pallet_ob_d2d: 0, pallet_ib_f2d: 0, xe_pallet: 0, cont_bien: 0, cont_bo: 0}};
                nodeAgg.DC_DRP[drpId].pallet_ob_d2d += p.Pallet_OB_D2D;
                nodeAgg.DC_DRP[drpId].pallet_ib_f2d += p.Pallet_IB_F2D;
                nodeAgg.DC_DRP[drpId].xe_pallet += p.D2D_Xe_pallet;
                nodeAgg.DC_DRP[drpId].cont_bien += p.D2D_Cont_bien;
                nodeAgg.DC_DRP[drpId].cont_bo += p.D2D_Cont_bo;
                edgesSet.add(drpId + "->" + outId);
                
                var factId = "FACT_" + p.Factory;
                if (!nodeAgg.Factory[factId]) nodeAgg.Factory[factId] = {{title: p.Factory, pallet_ob_f2d: 0, xe_pallet: 0, cont_bien: 0, cont_bo: 0}};
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
            
            // Filter Pivot Table
            var pivotAgg = {{}};
            custData.paths.forEach(p => {{
                var outDC = p.DC_Out;
                if (!pivotAgg[outDC]) pivotAgg[outDC] = {{ DC: outDC, Case: 0, 'Pallet Thruput': 0, 'Total Stock Pos': 0, 'Cont bộ': 0, 'Cont biển': 0, 'Xe pallet': 0, 'Truck 15 tấn': 0, 'Truck 2 tấn': 0 }};
                pivotAgg[outDC].Case += p.Cases;
                pivotAgg[outDC]['Pallet Thruput'] += p.Pallet_OB_D2C;
                pivotAgg[outDC]['Pallet Thruput'] += p.Pallet_IB_D2D;
                pivotAgg[outDC]['Total Stock Pos'] += p.Stock_Pos;

                pivotAgg[outDC]['Truck 15 tấn'] += p.D2C_Truck_15 + p.D2D_Xe_pallet;
                pivotAgg[outDC]['Truck 2 tấn'] += p.D2C_Truck_2 + p.D2D_Cont_bien;
                
                var drpDC = p.DC_DRP;
                if (!pivotAgg[drpDC]) pivotAgg[drpDC] = {{ DC: drpDC, Case: 0, 'Pallet Thruput': 0, 'Total Stock Pos': 0, 'Cont bộ': 0, 'Cont biển': 0, 'Xe pallet': 0, 'Truck 15 tấn': 0, 'Truck 2 tấn': 0 }};
                pivotAgg[drpDC]['Pallet Thruput'] += p.Pallet_OB_D2D;
                pivotAgg[drpDC]['Pallet Thruput'] += p.Pallet_IB_F2D;
                pivotAgg[drpDC]['Total Stock Pos'] += (p.Pallet_IB_F2D * drpStockValue);
                pivotAgg[drpDC]['Cont bộ'] += p.F2D_Cont_bo + p.D2D_Cont_bo;
                pivotAgg[drpDC]['Cont biển'] += p.F2D_Cont_bien + p.D2D_Cont_bien;
                pivotAgg[drpDC]['Xe pallet'] += p.F2D_Xe_pallet + p.D2D_Xe_pallet;
            }});
            
            var filteredPivotData = Object.values(pivotAgg).map(row => {{
                row['Diện tích'] = row['Total Stock Pos'] * m2PerPalletPos;
                row['Capacity_Thruput'] = peopleCapacityMap[row.DC] || 0;
                row['People'] = row['Capacity_Thruput'] * row['Pallet Thruput'];
                return row;
            }});
            renderPivotTable(filteredPivotData);
            
            network.fit();
        }}

        function clearFilter() {{
            document.getElementById('customer-search').value = '';
            document.getElementById('filter-error').style.display = 'none';
            
            nodes.clear();
            edges.clear();
            nodes.add(originalNodes);
            edges.add(originalEdges);
            
            renderPivotTable(originalPivotData);
            
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
    output_file = "c:/Users/phatvt/OneDrive/Image/Hình ảnh/ThanhPhat_Masan/DC FMCG/org/Base_Line/Supply_Chain_Network.html"
    process_supply_chain_data(excel_file, output_file)
