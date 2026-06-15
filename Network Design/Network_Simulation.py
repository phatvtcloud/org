import sys
import os
import time
import random
import simpy
import pandas as pd
import numpy as np

# --- AUTO-LAUNCH STREAMLIT LOGIC ---
try:
    from streamlit.runtime.scriptrunner import get_script_run_ctx
    is_streamlit = get_script_run_ctx() is not None
except ImportError:
    is_streamlit = False

if not is_streamlit:
    import subprocess
    print("--------------------------------------------------")
    print("Masan DC Operations Simulator - Auto Launcher")
    print("--------------------------------------------------")
    print("Detecting run outside Streamlit environment.")
    print("Launching Streamlit dashboard automatically...")
    script_path = os.path.abspath(__file__)
    try:
        # Launching streamlit module using sys.executable (Anaconda python)
        subprocess.run([sys.executable, "-m", "streamlit", "run", script_path])
    except Exception as e:
        print(f"Error launching Streamlit automatically: {e}")
        print("Please run manually using: streamlit run Network_Simulation.py")
    sys.exit(0)

# --- STREAMLIT DASHBOARD CODE ---
import streamlit as st
import streamlit.components.v1 as components

# Set page config for wide layout and dark style
st.set_page_config(
    page_title="Masan DC Operations Simulator",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Premium CSS Styling (Masan Red Accent, Slate Dark Background)
st.markdown("""
<style>
    /* Global Fonts & Styling */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700;800&display=swap');
    
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
        font-family: 'Outfit', sans-serif;
    }
    
    h1, h2, h3, h4 {
        color: #ffffff !important;
        font-family: 'Outfit', sans-serif;
        font-weight: 700 !important;
    }
    
    /* Header decoration */
    .title-container {
        border-bottom: 2px solid #e31837;
        padding-bottom: 10px;
        margin-bottom: 25px;
    }
    .title-main {
        font-size: 2.5rem;
        font-weight: 800;
        color: #ffffff;
        margin: 0;
    }
    .title-sub {
        font-size: 1.1rem;
        color: #8b949e;
        margin: 5px 0 0 0;
    }
    
    /* Custom Sidebar Card styling */
    section[data-testid="stSidebar"] {
        background-color: #161b22 !important;
        border-right: 1px solid #30363d;
    }
    
    /* Make all text elements inside the sidebar bright white */
    section[data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    
    /* Revert text inside input boxes, dropdowns, and textareas to black so they are legible on white fields */
    section[data-testid="stSidebar"] input,
    section[data-testid="stSidebar"] select,
    section[data-testid="stSidebar"] textarea {
        color: #11151c !important;
    }
    
    /* Target tabs text inside sidebar (active vs inactive state) */
    section[data-testid="stSidebar"] div[data-baseweb="tab"] * {
        color: #8b949e !important;
    }
    section[data-testid="stSidebar"] div[data-baseweb="tab"][aria-selected="true"] * {
        color: #ffffff !important;
    }
    
    /* Custom Metric Cards */
    .metric-card {
        background: #1f242c;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        transition: transform 0.2s ease, border-color 0.2s;
    }
    .metric-card:hover {
        transform: translateY(-3px);
        border-color: #e31837;
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: 800;
        color: #e31837;
        margin-bottom: 4px;
        line-height: 1.1;
    }
    .metric-value-green {
        color: #2ea043;
    }
    .metric-value-blue {
        color: #58a6ff;
    }
    .metric-value-orange {
        color: #f0883e;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #8b949e;
        text-transform: uppercase;
        font-weight: 600;
        letter-spacing: 0.8px;
    }
    
    /* Recommendations Box */
    .rec-box {
        background: rgba(227, 24, 55, 0.05);
        border-left: 4px solid #e31837;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
    }
    
    .rec-box-green {
        background: rgba(46, 160, 67, 0.05);
        border-left: 4px solid #2ea043;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
    }
    
    /* Styled tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #161b22;
        padding: 8px;
        border-radius: 10px;
        border: 1px solid #30363d;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 42px;
        background-color: transparent;
        border-radius: 6px;
        color: #8b949e;
        font-weight: 600;
        padding: 0 16px;
        transition: all 0.2s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        color: #ffffff;
        background-color: rgba(255, 255, 255, 0.05);
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #e31837 !important;
        color: #ffffff !important;
        box-shadow: 0 4px 10px rgba(227, 24, 55, 0.25);
    }
</style>
""", unsafe_allow_html=True)

# Main Header
st.markdown("""
<div class="title-container">
    <div class="title-main">🏭 Masan DC Operations Simulator</div>
    <div class="title-sub">SimPy Discrete-Event Simulation & Yard-Warehouse Bottleneck Analysis</div>
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR CONFIGURATION ---
st.sidebar.markdown("### 🎛️ Simulation Parameters")

# Sidebar tabs for neat layout
side_tabs = st.sidebar.tabs(["🚛 Yard & Docks", "📦 Storage", "⚙️ Speed"])

with side_tabs[0]:
    st.markdown("**Inbound Gate & Docks**")
    inbound_docks_cap = st.slider("Inbound Docks (EAST)", 5, 50, 30, help="Number of physical doors for unloading")
    inbound_crews_cap = st.slider("Unloading Crews", 2, 30, 10, help="Labor crews dedicated to unloading")
    crew_unload_rate = st.slider("Unloading Rate (plt/hr/crew)", 10, 50, 24)
    yard_queue_cap = st.slider("West Yard Queue Cap (Trucks)", 5, 40, 20, help="Capacity of Gate 1 Inbound Queue Lane")
    ib_interval = st.slider("Inbound Arrival Interval (mean min)", 5.0, 45.0, 15.0, step=1.0)
    
    st.markdown("---")
    st.markdown("**Outbound Gate & Docks**")
    outbound_docks_cap = st.slider("Outbound Docks (NORTH)", 10, 60, 40, help="Number of physical doors for loading")
    outbound_crews_cap = st.slider("Loading Crews", 5, 40, 16, help="Labor crews dedicated to loading")
    crew_load_rate = st.slider("Loading Rate (plt/hr/crew)", 10, 50, 20)
    ob_interval = st.slider("Outbound Arrival Interval (mean min)", 5.0, 45.0, 12.0, step=1.0)

with side_tabs[1]:
    st.markdown("**ASRS Storage**")
    asrs_cap = st.number_input("ASRS Capacity (Pallets)", value=23300)
    asrs_initial = st.number_input("ASRS Initial Stock (Pallets)", value=15000)
    
    st.markdown("**Selective Rack Storage (Fast)**")
    selective_cap = st.number_input("Selective Capacity (Pallets)", value=8600)
    selective_initial = st.number_input("Selective Initial Stock (Pallets)", value=5000)
    
    st.markdown("**Floor / Campaign Storage**")
    floor_cap = st.number_input("Floor Capacity (Pallets)", value=2200)
    floor_initial = st.number_input("Floor Initial Stock (Pallets)", value=1000)
    
    st.markdown("---")
    st.markdown("**Manning & Handling Speed**")
    putaway_forklifts = st.slider("Putaway Forklifts", 1, 20, 8)
    putaway_time = st.slider("Putaway Time / Pallet (min)", 0.5, 5.0, 2.0)
    picking_forklifts = st.slider("Picking Forklifts", 1, 30, 12)
    picking_time = st.slider("Picking Time / Pallet (min)", 0.5, 5.0, 2.5)

with side_tabs[2]:
    st.markdown("**Simulation Execution Settings**")
    duration_days = st.slider("Simulation Duration (Days)", 1, 14, 2, help="Number of operational days to simulate")
    sim_seed = st.number_input("Random Seed (for reproducibility)", value=42, min_value=1)

# Compile params dictionary
params = {
    'inbound_docks_cap': inbound_docks_cap,
    'inbound_crews_cap': inbound_crews_cap,
    'crew_unload_rate_pallets_per_hr': crew_unload_rate,
    'yard_queue_cap': yard_queue_cap,
    'inbound_truck_interval': ib_interval,
    'min_inbound_pallets': 15,
    'max_inbound_pallets': 25,
    
    'outbound_docks_cap': outbound_docks_cap,
    'outbound_crews_cap': outbound_crews_cap,
    'crew_load_rate_pallets_per_hr': crew_load_rate,
    'outbound_truck_interval': ob_interval,
    'min_outbound_pallets': 20,
    'max_outbound_pallets': 30,
    
    'asrs_cap': asrs_cap,
    'asrs_initial': asrs_initial,
    'selective_cap': selective_cap,
    'selective_initial': selective_initial,
    'floor_cap': floor_cap,
    'floor_initial': floor_initial,
    
    'putaway_forklifts': putaway_forklifts,
    'putaway_time_per_pallet': putaway_time,
    'picking_forklifts': picking_forklifts,
    'picking_time_per_pallet': picking_time,
    
    'duration_hrs': duration_days * 24.0,
    'seed': sim_seed
}

# --- SIMULATION CLASS ---
class DCSimulation:
    def __init__(self, env, params):
        self.env = env
        self.params = params
        
        # Resources
        self.inbound_docks = simpy.Resource(env, capacity=params['inbound_docks_cap'])
        self.outbound_docks = simpy.Resource(env, capacity=params['outbound_docks_cap'])
        
        self.inbound_crews = simpy.Resource(env, capacity=params['inbound_crews_cap'])
        self.outbound_crews = simpy.Resource(env, capacity=params['outbound_crews_cap'])
        
        self.putaway_resource = simpy.Resource(env, capacity=params['putaway_forklifts'])
        self.picking_resource = simpy.Resource(env, capacity=params['picking_forklifts'])
        
        # Storage (Containers)
        self.asrs_container = simpy.Container(env, init=params['asrs_initial'], capacity=params['asrs_cap'])
        self.selective_container = simpy.Container(env, init=params['selective_initial'], capacity=params['selective_cap'])
        self.floor_container = simpy.Container(env, init=params['floor_initial'], capacity=params['floor_cap'])
        
        self.inbound_buffer_container = simpy.Container(env, init=0, capacity=100000)
        self.outbound_staging_container = simpy.Container(env, init=0, capacity=100000)
        
        # Picking requests queue
        self.pick_queue = []
        
        # State tracking
        self.yard_inbound_queue = 0
        self.gate_overflows = 0
        self.total_inbound_trucks = 0
        self.total_outbound_trucks = 0
        self.total_pallets_received = 0
        self.total_pallets_dispatched = 0
        
        # Metrics logs
        self.inbound_truck_times = []
        self.outbound_truck_times = []
        self.log_data = []
        
        # Run background processes
        env.process(self.inbound_truck_generator())
        env.process(self.outbound_truck_generator())
        env.process(self.putaway_process())
        env.process(self.picking_process())
        env.process(self.logger_process())
        
    def inbound_truck_generator(self):
        truck_id = 0
        while True:
            # Exponential arrival pattern
            yield self.env.timeout(random.expovariate(1.0 / self.params['inbound_truck_interval']))
            self.env.process(self.inbound_truck(f"IB_TRUCK_{truck_id}"))
            truck_id += 1
            
    def outbound_truck_generator(self):
        truck_id = 0
        while True:
            yield self.env.timeout(random.expovariate(1.0 / self.params['outbound_truck_interval']))
            self.env.process(self.outbound_truck(f"OB_TRUCK_{truck_id}"))
            truck_id += 1
            
    def inbound_truck(self, truck_id):
        arrival_time = self.env.now
        
        # Check yard queue limit (Gate 1 perimeter road)
        if self.yard_inbound_queue >= self.params['yard_queue_cap']:
            self.gate_overflows += 1
            return
            
        self.yard_inbound_queue += 1
        
        # Request inbound dock
        dock_req = self.inbound_docks.request()
        yield dock_req
        
        # Dock assigned, exit yard queue
        self.yard_inbound_queue -= 1
        
        # Docking maneuver (5 minutes)
        yield self.env.timeout(5.0)
        
        # Unloading process
        pallets_to_unload = random.randint(self.params['min_inbound_pallets'], self.params['max_inbound_pallets'])
        crew_req = self.inbound_crews.request()
        yield crew_req
        
        unload_time_min = (pallets_to_unload / self.params['crew_unload_rate_pallets_per_hr']) * 60.0
        yield self.env.timeout(unload_time_min)
        
        # Deposit to buffer
        yield self.inbound_buffer_container.put(pallets_to_unload)
        self.total_pallets_received += pallets_to_unload
        
        # Release crew
        self.inbound_crews.release(crew_req)
        
        # Undocking maneuver (5 minutes)
        yield self.env.timeout(5.0)
        self.inbound_docks.release(dock_req)
        
        # Log duration
        self.inbound_truck_times.append(self.env.now - arrival_time)
        self.total_inbound_trucks += 1
        
    def outbound_truck(self, truck_id):
        arrival_time = self.env.now
        pallets_to_load = random.randint(self.params['min_outbound_pallets'], self.params['max_outbound_pallets'])
        
        # Request outbound dock
        dock_req = self.outbound_docks.request()
        yield dock_req
        
        # Docking maneuver (5 minutes)
        yield self.env.timeout(5.0)
        
        # Submit pick request to staging
        pick_done = self.env.event()
        self.pick_queue.append({
            'truck_id': truck_id,
            'pallets_needed': pallets_to_load,
            'done_event': pick_done
        })
        
        # Wait until picking process places items in staging
        yield pick_done
        
        # Request loading crew
        crew_req = self.outbound_crews.request()
        yield crew_req
        
        # Retrieve from staging buffer
        yield self.outbound_staging_container.get(pallets_to_load)
        
        load_time_min = (pallets_to_load / self.params['crew_load_rate_pallets_per_hr']) * 60.0
        yield self.env.timeout(load_time_min)
        
        self.total_pallets_dispatched += pallets_to_load
        
        # Release crew & dock
        self.outbound_crews.release(crew_req)
        
        # Undocking maneuver (5 minutes)
        yield self.env.timeout(5.0)
        self.outbound_docks.release(dock_req)
        
        # Log duration
        self.outbound_truck_times.append(self.env.now - arrival_time)
        self.total_outbound_trucks += 1
        
    def putaway_process(self):
        while True:
            # Wait for inventory in inbound buffer
            if self.inbound_buffer_container.level == 0:
                yield self.env.timeout(5.0)
                continue
                
            batch = min(5, self.inbound_buffer_container.level)
            if batch == 0:
                yield self.env.timeout(5.0)
                continue
                
            # Request forklift
            with self.putaway_resource.request() as req:
                yield req
                
                # Fetch from buffer
                yield self.inbound_buffer_container.get(batch)
                
                # Travel/putaway time
                yield self.env.timeout(batch * self.params['putaway_time_per_pallet'])
                
                # Distribute pallets into storage (60% ASRS, 30% Selective, 10% Floor)
                for _ in range(batch):
                    placed = False
                    while not placed:
                        r = random.random()
                        zones = []
                        if r < 0.60:
                            zones = [('asrs', self.asrs_container), ('selective', self.selective_container), ('floor', self.floor_container)]
                        elif r < 0.90:
                            zones = [('selective', self.selective_container), ('asrs', self.asrs_container), ('floor', self.floor_container)]
                        else:
                            zones = [('floor', self.floor_container), ('selective', self.selective_container), ('asrs', self.asrs_container)]
                            
                        # Put in first available zone
                        for name, container in zones:
                            if container.level < container.capacity:
                                yield container.put(1)
                                placed = True
                                break
                                
                        if not placed:
                            # Warehouse completely saturated! Sleep before trying again
                            yield self.env.timeout(10.0)
                            
    def picking_process(self):
        while True:
            if not self.pick_queue:
                yield self.env.timeout(2.0)
                continue
                
            # Pull first order from FIFO picking queue
            req = self.pick_queue.pop(0)
            needed = req['pallets_needed']
            done = req['done_event']
            
            picked = 0
            while picked < needed:
                container = None
                
                # Prioritize: Selective (fast picks) -> ASRS -> Floor
                if self.selective_container.level > 0:
                    container = self.selective_container
                elif self.asrs_container.level > 0:
                    container = self.asrs_container
                elif self.floor_container.level > 0:
                    container = self.floor_container
                    
                if container is None:
                    # Stockout! Wait for putaway/inbound replenishment
                    yield self.env.timeout(5.0)
                    continue
                    
                batch = min(5, needed - picked, container.level)
                
                # Request picking forklift
                with self.picking_resource.request() as pick_req:
                    yield pick_req
                    
                    yield container.get(batch)
                    yield self.env.timeout(batch * self.params['picking_time_per_pallet'])
                    yield self.outbound_staging_container.put(batch)
                    picked += batch
                    
            done.succeed()
            
    def logger_process(self):
        while True:
            self.log_data.append({
                'Time (Hr)': self.env.now / 60.0,
                'ASRS Inventory': self.asrs_container.level,
                'Selective Inventory': self.selective_container.level,
                'Floor Inventory': self.floor_container.level,
                'Inbound Buffer': self.inbound_buffer_container.level,
                'Outbound Staging': self.outbound_staging_container.level,
                'Yard Queue': self.yard_inbound_queue,
                'Inbound Docks Util (%)': (self.inbound_docks.count / self.inbound_docks.capacity) * 100,
                'Outbound Docks Util (%)': (self.outbound_docks.count / self.outbound_docks.capacity) * 100,
                'Total Received (Plt)': self.total_pallets_received,
                'Total Dispatched (Plt)': self.total_pallets_dispatched,
                'Inbound Docks Busy': self.inbound_docks.count,
                'Outbound Docks Busy': self.outbound_docks.count
            })
            yield self.env.timeout(10.0) # Log states every 10 minutes of simulation time

# --- DYNAMIC 2D SVG MAP GENERATION FUNCTION ---
def generate_svg_map(state, params):
    # Cast variables to standard Python float/int to prevent numpy/pandas types causing issues in range()
    asrs_level = float(state['asrs_level'])
    selective_level = float(state['selective_level'])
    floor_level = float(state['floor_level'])
    ib_buffer = int(state['ib_buffer'])
    ob_staging = int(state['ob_staging'])
    yard_q = int(state['yard_q'])
    ib_busy = int(state['ib_busy'])
    ob_busy = int(state['ob_busy'])
    time_hr = float(state['time_hr'])

    # Calculate storage fill levels (percentage)
    asrs_pct = min(100.0, (asrs_level / params['asrs_cap']) * 100) if params['asrs_cap'] > 0 else 0
    selective_pct = min(100.0, (selective_level / params['selective_cap']) * 100) if params['selective_cap'] > 0 else 0
    floor_pct = min(100.0, (floor_level / params['floor_cap']) * 100) if params['floor_cap'] > 0 else 0
    
    # Calculate widths for SVG fill bars
    asrs_fill_width = int(asrs_pct * 1.4)  # max width 140px
    selective_fill_width = int(selective_pct * 1.4)
    floor_fill_width = int(floor_pct * 1.4)
    
    # Yard queue trucks (lined up on West side: x=175, y from 430 down)
    yard_trucks_svg = ""
    for i in range(min(8, yard_q)):
        y_pos = 430 - (i * 32)
        yard_trucks_svg += f'<rect x="175" y="{y_pos}" width="16" height="26" rx="2" fill="#f0883e" stroke="#ffffff" stroke-width="0.5"/>'
        yard_trucks_svg += f'<rect x="179" y="{y_pos-3}" width="8" height="5" rx="1" fill="#2d3748"/>' # cabin
        
    # Inbound docks occupied trucks (parked on the east side: x=860, y spaced between 160 and 420)
    ib_trucks_svg = ""
    for i in range(min(10, ib_busy)):
        y_pos = 160 + (i * 28)
        ib_trucks_svg += f'<rect x="860" y="{y_pos}" width="28" height="14" rx="2" fill="#e31837" stroke="#ffffff" stroke-width="0.5"/>'
        ib_trucks_svg += f'<rect x="888" y="{y_pos+3}" width="4" height="8" rx="1" fill="#2d3748"/>' # cabin
        
    # Outbound docks occupied trucks (parked on the north side: y=52, x spaced between 320 and 780)
    ob_trucks_svg = ""
    for i in range(min(15, ob_busy)):
        x_pos = 320 + (i * 30)
        ob_trucks_svg += f'<rect x="{x_pos}" y="52" width="14" height="28" rx="2" fill="#58a6ff" stroke="#ffffff" stroke-width="0.5"/>'
        ob_trucks_svg += f'<rect x="{x_pos+3}" y="48" width="8" height="4" rx="1" fill="#2d3748"/>' # cabin

    # Forklifts moving around (yellow dots)
    forklifts_svg = ""
    # Putaway forklifts moving from buffer to storage
    if ib_buffer > 0:
        for i in range(min(4, int(ib_buffer // 5) + 1)):
            x_pos = random.randint(750, 775)
            y_pos = random.randint(200, 420)
            forklifts_svg += f'<circle cx="{x_pos}" cy="{y_pos}" r="5" fill="#f1c40f" stroke="#000000" stroke-width="0.5"/>'
            forklifts_svg += f'<line x1="{x_pos-5}" y1="{y_pos}" x2="{x_pos-8}" y2="{y_pos}" stroke="#000000" stroke-width="1.5"/>' # fork
            
    # Picking forklifts moving in storage/main aisle/staging
    if ob_staging > 0 or asrs_level > 0 or selective_level > 0:
        for i in range(min(5, int(ob_staging // 10) + 1)):
            x_pos = random.randint(300, 750)
            y_pos = random.randint(140, 180)
            forklifts_svg += f'<circle cx="{x_pos}" cy="{y_pos}" r="5" fill="#f1c40f" stroke="#000000" stroke-width="0.5"/>'
            forklifts_svg += f'<line x1="{x_pos}" y1="{y_pos-5}" x2="{x_pos}" y2="{y_pos-8}" stroke="#000000" stroke-width="1.5"/>' # fork

    svg_map = f"""
    <svg viewBox="0 0 1000 600" width="100%" height="100%" style="background-color: #11151c; border-radius: 12px; border: 1px solid #30363d;">
        <!-- Define SVG Markers and Gradients -->
        <defs>
            <marker id="arrow-red" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                <path d="M 0 0 L 10 5 L 0 10 z" fill="#e31837"/>
            </marker>
            <marker id="arrow-blue" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                <path d="M 0 0 L 10 5 L 0 10 z" fill="#58a6ff"/>
            </marker>
            <marker id="arrow-gray" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                <path d="M 0 0 L 10 5 L 0 10 z" fill="#8b949e"/>
            </marker>
            
            <linearGradient id="asrsGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stop-color="#113e3d"/>
                <stop offset="100%" stop-color="#1b7875"/>
            </linearGradient>
            <linearGradient id="selectiveGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stop-color="#592b0c"/>
                <stop offset="100%" stop-color="#b85f14"/>
            </linearGradient>
            <linearGradient id="floorGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stop-color="#0c2d59"/>
                <stop offset="100%" stop-color="#1b5ba6"/>
            </linearGradient>
        </defs>

        <!-- Yard Boundary -->
        <rect x="10" y="10" width="980" height="580" rx="15" fill="#161b22" stroke="#30363d" stroke-width="2"/>
        
        <!-- Main Building Footprint (28,000 sqm footprint representation) -->
        <rect x="250" y="100" width="600" height="400" rx="12" fill="#21262d" stroke="#484f58" stroke-width="3"/>
        <text x="550" y="125" fill="#ffffff" font-size="15" font-weight="bold" text-anchor="middle">Masan Distribution Center (28,000 m²)</text>
        <text x="550" y="142" fill="#8b949e" font-size="11" text-anchor="middle">Simulation Time: {time_hr:.1f} Hours</text>
        
        <!-- Gate 1 (IN) - Inbound Entry -->
        <rect x="30" y="450" width="110" height="60" rx="6" fill="#e31837" fill-opacity="0.1" stroke="#e31837" stroke-width="2"/>
        <text x="85" y="485" fill="#e31837" font-size="13" font-weight="bold" text-anchor="middle">Gate 1 (IN)</text>
        
        <!-- Gate 2A (OUT) - Outbound Northwest -->
        <rect x="150" y="20" width="110" height="50" rx="6" fill="#2ea043" fill-opacity="0.1" stroke="#2ea043" stroke-width="2"/>
        <text x="205" y="50" fill="#2ea043" font-size="12" font-weight="bold" text-anchor="middle">Gate 2A (OUT)</text>
        
        <!-- Gate 2B (OUT) - Outbound Northeast -->
        <rect x="750" y="20" width="110" height="50" rx="6" fill="#2ea043" fill-opacity="0.1" stroke="#2ea043" stroke-width="2"/>
        <text x="805" y="50" fill="#2ea043" font-size="12" font-weight="bold" text-anchor="middle">Gate 2B (OUT)</text>
        
        <!-- Roads / Yard Lanes -->
        <!-- Flow line from Gate 1 to Inbound Docks -->
        <path d="M 140 480 L 190 480 L 190 540 L 900 540 L 900 300 L 860 300" fill="none" stroke="#30363d" stroke-width="4" stroke-dasharray="10, 5"/>
        <text x="545" y="560" fill="#8b949e" font-size="11" text-anchor="middle">West-East Perimeter Ring Road (Inbound Flow)</text>
        
        <!-- Render queued trucks dynamically -->
        {yard_trucks_svg}
        
        <!-- Inbound Docks (EAST - Nhập Hàng) -->
        <rect x="830" y="150" width="30" height="300" rx="6" fill="#e31837" fill-opacity="0.25" stroke="#e31837" stroke-width="2"/>
        <text x="846" y="300" fill="#ffffff" font-size="12" font-weight="bold" writing-mode="vertical-rl" text-anchor="middle">EAST INBOUND DOCKS ({params['inbound_docks_cap']} Doors)</text>
        <!-- Busy docks count display -->
        <circle cx="845" cy="180" r="10" fill="#e31837"/>
        <text x="845" y="184" fill="#ffffff" font-size="10" font-weight="bold" text-anchor="middle">{ib_busy}</text>
        
        <!-- Render Inbound Docks parked trucks -->
        {ib_trucks_svg}
        
        <!-- Outbound Docks (NORTH - Xuất Hàng) -->
        <rect x="300" y="85" width="500" height="30" rx="6" fill="#58a6ff" fill-opacity="0.25" stroke="#58a6ff" stroke-width="2"/>
        <text x="550" y="105" fill="#ffffff" font-size="12" font-weight="bold" text-anchor="middle">NORTH OUTBOUND DOCKS ({params['outbound_docks_cap']} Doors)</text>
        <!-- Busy docks count display -->
        <circle cx="780" cy="100" r="10" fill="#58a6ff"/>
        <text x="780" y="104" fill="#ffffff" font-size="10" font-weight="bold" text-anchor="middle">{ob_busy}</text>
        
        <!-- Render Outbound Docks parked trucks -->
        {ob_trucks_svg}
        
        <!-- Storage Area: ASRS Reserve -->
        <rect x="380" y="190" width="180" height="130" rx="8" fill="#161b22" stroke="#30363d" stroke-width="1.5"/>
        <text x="470" y="215" fill="#ffffff" font-size="13" font-weight="bold" text-anchor="middle">ASRS Reserve (35m)</text>
        <text x="470" y="235" fill="#8b949e" font-size="10.5" text-anchor="middle">{asrs_level:,.0f} / {params['asrs_cap']:,} Plt</text>
        <!-- Fill status bar -->
        <rect x="400" y="270" width="140" height="15" rx="3" fill="#30363d"/>
        <rect x="400" y="270" width="{asrs_fill_width}" height="15" rx="3" fill="url(#asrsGrad)"/>
        <text x="470" y="282" fill="#ffffff" font-size="10.5" font-weight="bold" text-anchor="middle">{asrs_pct:.1f}% Fill</text>
        
        <!-- Storage Area: Selective Racks -->
        <rect x="580" y="190" width="180" height="130" rx="8" fill="#161b22" stroke="#30363d" stroke-width="1.5"/>
        <text x="670" y="215" fill="#ffffff" font-size="13" font-weight="bold" text-anchor="middle">Selective Rack (Fast)</text>
        <text x="670" y="235" fill="#8b949e" font-size="10.5" text-anchor="middle">{selective_level:,.0f} / {params['selective_cap']:,} Plt</text>
        <!-- Fill status bar -->
        <rect x="600" y="270" width="140" height="15" rx="3" fill="#30363d"/>
        <rect x="600" y="270" width="{selective_fill_width}" height="15" rx="3" fill="url(#selectiveGrad)"/>
        <text x="670" y="282" fill="#ffffff" font-size="10.5" font-weight="bold" text-anchor="middle">{selective_pct:.1f}% Fill</text>
        
        <!-- Storage Area: Floor / Campaign -->
        <rect x="380" y="340" width="180" height="120" rx="8" fill="#161b22" stroke="#30363d" stroke-width="1.5"/>
        <text x="470" y="365" fill="#ffffff" font-size="13" font-weight="bold" text-anchor="middle">Floor / Campaign</text>
        <text x="470" y="385" fill="#8b949e" font-size="10.5" text-anchor="middle">{floor_level:,.0f} / {params['floor_cap']:,} Plt</text>
        <!-- Fill status bar -->
        <rect x="400" y="420" width="140" height="15" rx="3" fill="#30363d"/>
        <rect x="400" y="420" width="{floor_fill_width}" height="15" rx="3" fill="url(#floorGrad)"/>
        <text x="470" y="432" fill="#ffffff" font-size="10.5" font-weight="bold" text-anchor="middle">{floor_pct:.1f}% Fill</text>
        
        <!-- Inbound Buffer & Receiving Stage (East side) -->
        <rect x="780" y="200" width="40" height="200" rx="5" fill="#e31837" fill-opacity="0.1" stroke="#e31837" stroke-dasharray="4,4" stroke-width="1.5"/>
        <text x="800" y="300" fill="#ff7b72" font-size="11" font-weight="bold" writing-mode="vertical-rl" text-anchor="middle">Inbound Buffer: {ib_buffer} Plt</text>
        
        <!-- Outbound Staging Stage (North side) -->
        <rect x="300" y="130" width="500" height="40" rx="5" fill="#58a6ff" fill-opacity="0.1" stroke="#58a6ff" stroke-dasharray="4,4" stroke-width="1.5"/>
        <text x="550" y="155" fill="#79c0ff" font-size="11" font-weight="bold" text-anchor="middle">Outbound Staging: {ob_staging} Pallets Staged</text>
        
        <!-- Gate 1 Yard Queue Display (West side) -->
        <rect x="155" y="440" width="80" height="50" rx="6" fill="#e31837" fill-opacity="0.15" stroke="#e31837" stroke-width="1.5"/>
        <text x="195" y="460" fill="#ff7b72" font-size="11.5" text-anchor="middle">Yard Queue</text>
        <text x="195" y="482" fill="#ffffff" font-size="16" font-weight="bold" text-anchor="middle">{yard_q} Trucks</text>
        
        <!-- Render Forklifts dynamically -->
        {forklifts_svg}
        
        <!-- Arrows showing internal flow -->
        <!-- Inbound to Buffer -->
        <path d="M 830 300 L 822 300" fill="none" stroke="#e31837" stroke-width="2" marker-end="url(#arrow-red)"/>
        <!-- Buffer to Storage -->
        <path d="M 780 300 L 766 300" fill="none" stroke="#8b949e" stroke-width="2" marker-end="url(#arrow-gray)"/>
        <!-- Staging to Outbound Dock -->
        <path d="M 550 130 L 550 117" fill="none" stroke="#58a6ff" stroke-width="2" marker-end="url(#arrow-blue)"/>
    </svg>
    """
    return svg_map

# --- INITIALIZE AND RUN RUNNER ---
def run_simulation(params):
    random.seed(params['seed'])
    env = simpy.Environment()
    sim = DCSimulation(env, params)
    env.run(until=params['duration_hrs'] * 60.0)
    return sim

# --- SIMULATION CONTROL INTERFACE ---
run_mode = st.radio("🎬 Choose Run Mode", ["⚡ Fast Run (Full Analytics & Summary)", "🎬 Live 2D Animated Simulation (Watch Vehicles & Forklifts)"], horizontal=True)

# Define variables that we need to maintain
sim = None
df_log = None

if run_mode == "⚡ Fast Run (Full Analytics & Summary)":
    if 'sim_results' not in st.session_state or st.sidebar.button("🚀 Regenerate Model", type="primary"):
        with st.spinner("Simulating operations..."):
            st.session_state['sim_results'] = run_simulation(params)
            st.session_state['params'] = params
            st.success("Simulation Run Complete!")
            
    sim = st.session_state['sim_results']
    df_log = pd.DataFrame(sim.log_data)
    
    # Render final state
    final_state_data = {
        'asrs_level': df_log.iloc[-1]['ASRS Inventory'],
        'selective_level': df_log.iloc[-1]['Selective Inventory'],
        'floor_level': df_log.iloc[-1]['Floor Inventory'],
        'ib_buffer': df_log.iloc[-1]['Inbound Buffer'],
        'ob_staging': df_log.iloc[-1]['Outbound Staging'],
        'yard_q': df_log.iloc[-1]['Yard Queue'],
        'ib_busy': df_log.iloc[-1]['Inbound Docks Busy'],
        'ob_busy': df_log.iloc[-1]['Outbound Docks Busy'],
        'time_hr': params['duration_hrs']
    }
    
    # SVG Map
    svg_map = generate_svg_map(final_state_data, params)
    
    # Layout rendering
    col_left, col_right = st.columns([5, 5])
    with col_left:
        st.markdown("### 🗺️ Final Operation State Layout")
        components.html(svg_map, height=520, scrolling=False)
        
    with col_right:
        st.markdown("### 📊 Operational Turnaround Time")
        avg_ib_truck_time = np.mean(sim.inbound_truck_times) if sim.inbound_truck_times else 0.0
        avg_ob_truck_time = np.mean(sim.outbound_truck_times) if sim.outbound_truck_times else 0.0
        
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value-blue metric-value">{avg_ib_truck_time:.1f} min</div>
                <div class="metric-label">Avg Inbound Truck Time</div>
            </div>
            """, unsafe_allow_html=True)
        with col_t2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value-blue metric-value">{avg_ob_truck_time:.1f} min</div>
                <div class="metric-label">Avg Outbound Truck Time</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("##### Cumulative Pallet Flows")
        df_throughput = df_log[['Time (Hr)', 'Total Received (Plt)', 'Total Dispatched (Plt)']].set_index('Time (Hr)')
        st.line_chart(df_throughput, color=["#e31837", "#2ea043"])
        
        st.markdown("##### Yard Queue Length (Gate 1)")
        df_queue = df_log[['Time (Hr)', 'Yard Queue']].set_index('Time (Hr)')
        st.line_chart(df_queue, color=["#f0883e"])

else:
    # Live 2D Animated Simulation
    st.markdown("### 🎬 Real-time 2D Simulation Visualizer")
    col_ctrl, col_spacing = st.columns([2, 8])
    start_sim = col_ctrl.button("▶️ Start Simulation Animation", type="primary")
    
    # Placeholder for the visual map
    map_placeholder = st.empty()
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Initial Map State before run
    initial_state_data = {
        'asrs_level': params['asrs_initial'],
        'selective_level': params['selective_initial'],
        'floor_level': params['floor_initial'],
        'ib_buffer': 0,
        'ob_staging': 0,
        'yard_q': 0,
        'ib_busy': 0,
        'ob_busy': 0,
        'time_hr': 0.0
    }
    with map_placeholder.container():
        components.html(generate_svg_map(initial_state_data, params), height=520, scrolling=False)
        
    if start_sim:
        random.seed(params['seed'])
        env = simpy.Environment()
        sim = DCSimulation(env, params)
        
        # Advance simulation in 15 minute intervals (steps)
        step_size_min = 15.0
        total_steps = int(params['duration_hrs'] * 60 / step_size_min)
        
        for step in range(total_steps):
            target_time = (step + 1) * step_size_min
            env.run(until=target_time)
            
            # Extract live state
            live_state = {
                'asrs_level': sim.asrs_container.level,
                'selective_level': sim.selective_container.level,
                'floor_level': sim.floor_container.level,
                'ib_buffer': sim.inbound_buffer_container.level,
                'ob_staging': sim.outbound_staging_container.level,
                'yard_q': sim.yard_inbound_queue,
                'ib_busy': sim.inbound_docks.count,
                'ob_busy': sim.outbound_docks.count,
                'time_hr': target_time / 60.0
            }
            
            # Redraw SVG map
            with map_placeholder.container():
                components.html(generate_svg_map(live_state, params), height=520, scrolling=False)
                
            # Update indicators
            progress_bar.progress((step + 1) / total_steps)
            status_text.markdown(f"**⏰ Time**: {target_time/60.0:.1f} hrs | **📥 Received**: {sim.total_pallets_received} Plt | **📤 Dispatched**: {sim.total_pallets_dispatched} Plt | **⚠️ Overflows**: {sim.gate_overflows}")
            
            # Animation sleep time
            time.sleep(0.08)
            
        st.success("Animation Finished! Scroll down to inspect the detailed analytics and reports.")
        # Store in session state for tabs rendering
        st.session_state['sim_results'] = sim
        st.session_state['params'] = params
        df_log = pd.DataFrame(sim.log_data)

# --- RUN DETAILED TABS AT THE END ---
if 'sim_results' in st.session_state:
    sim = st.session_state['sim_results']
    df_log = pd.DataFrame(sim.log_data)
    
    avg_ib_dock_util = df_log['Inbound Docks Util (%)'].mean()
    avg_ob_dock_util = df_log['Outbound Docks Util (%)'].mean()
    avg_ib_truck_time = np.mean(sim.inbound_truck_times) if sim.inbound_truck_times else 0.0
    avg_ob_truck_time = np.mean(sim.outbound_truck_times) if sim.outbound_truck_times else 0.0

    st.markdown("---")
    # KPI metrics row (for summary)
    st.markdown("### 📊 Operational KPI Summary Dashboard")
    col_m1, col_m2, col_m3, col_m4, col_m5, col_m6 = st.columns(6)
    with col_m1:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value">{sim.total_inbound_trucks}</div>
            <div class="metric-label">Inbound Trucks</div>
        </div>""", unsafe_allow_html=True)
    with col_m2:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value">{sim.total_outbound_trucks}</div>
            <div class="metric-label">Outbound Trucks</div>
        </div>""", unsafe_allow_html=True)
    with col_m3:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value-green metric-value">{sim.total_pallets_dispatched:,}</div>
            <div class="metric-label">Dispatched Pallets</div>
        </div>""", unsafe_allow_html=True)
    with col_m4:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value-blue metric-value">{avg_ib_dock_util:.1f}%</div>
            <div class="metric-label">Inbound Docks Util</div>
        </div>""", unsafe_allow_html=True)
    with col_m5:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value-blue metric-value">{avg_ob_dock_util:.1f}%</div>
            <div class="metric-label">Outbound Docks Util</div>
        </div>""", unsafe_allow_html=True)
    with col_m6:
        overflow_class = "metric-value-orange" if sim.gate_overflows > 0 else "metric-value-green"
        st.markdown(f"""<div class="metric-card">
            <div class="{overflow_class} metric-value">{sim.gate_overflows}</div>
            <div class="metric-label">Gate Overflows</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    tabs = st.tabs(["📦 Warehouse Inventory Profile", "🚛 Dock & Yard Analysis", "⚠️ Bottleneck Diagnostic Report"])

    with tabs[0]:
        st.markdown("### 📦 Detailed Storage Profiling")
        col_tab_left, col_tab_right = st.columns([7, 3])
        
        with col_tab_left:
            st.markdown("##### Storage Area Inventory Levels (Stacked Profile)")
            df_inventory = df_log[['Time (Hr)', 'ASRS Inventory', 'Selective Inventory', 'Floor Inventory']].set_index('Time (Hr)')
            st.area_chart(df_inventory, color=["#1b7875", "#b85f14", "#1b5ba6"])
            
        with col_tab_right:
            st.markdown("##### Stage Buffer Levels (Queues)")
            df_buffers = df_log[['Time (Hr)', 'Inbound Buffer', 'Outbound Staging']].set_index('Time (Hr)')
            st.line_chart(df_buffers, color=["#ff7b72", "#79c0ff"])

    with tabs[1]:
        st.markdown("### 🚛 Dock Utilization & Gate Analysis")
        col_d1, col_d2 = st.columns(2)
        
        with col_d1:
            st.markdown("##### Dock Door Occupancy Level (%)")
            df_docks = df_log[['Time (Hr)', 'Inbound Docks Util (%)', 'Outbound Docks Util (%)']].set_index('Time (Hr)')
            st.line_chart(df_docks, color=["#e31837", "#58a6ff"])
            
        with col_d2:
            st.markdown("##### Operational Metrics Summary Table")
            metrics_summary = pd.DataFrame({
                "KPI Metric": [
                    "Total Inbound Trucks Arrived",
                    "Total Outbound Trucks Arrived",
                    "Total Gate Overflows",
                    "Total Pallets Unloaded",
                    "Total Pallets Dispatched",
                    "Average Inbound Dock Occupancy (%)",
                    "Average Outbound Dock Occupancy (%)",
                    "Inbound Truck Average Cycle Time (min)",
                    "Outbound Truck Average Cycle Time (min)"
                ],
                "Value": [
                    sim.total_inbound_trucks + sim.gate_overflows,
                    sim.total_outbound_trucks,
                    sim.gate_overflows,
                    f"{sim.total_pallets_received:,}",
                    f"{sim.total_pallets_dispatched:,}",
                    f"{avg_ib_dock_util:.2f}%",
                    f"{avg_ob_dock_util:.2f}%",
                    f"{avg_ib_truck_time:.2f} min",
                    f"{avg_ob_truck_time:.2f} min"
                ]
            })
            st.dataframe(metrics_summary, use_container_width=True, hide_index=True)

    with tabs[2]:
        st.markdown("### ⚠️ Bottleneck Diagnostic & Optimization Advice")
        
        # Calculate resource constraints
        inbound_docks_busy_avg = df_log['Inbound Docks Busy'].mean()
        outbound_docks_busy_avg = df_log['Outbound Docks Busy'].mean()
        
        # Normalize utilization scores to find constraints (0 - 100)
        scores = {
            "Yard Queue Congestion": min(100.0, (df_log['Yard Queue'].mean() / params['yard_queue_cap']) * 100),
            "Inbound Dock Doors Saturated": avg_ib_dock_util,
            "Outbound Dock Doors Saturated": avg_ob_dock_util,
            "Inbound Buffer Congestion": min(100.0, (df_log['Inbound Buffer'].mean() / 200.0) * 100),
            "Outbound Staging Congestion": min(100.0, (df_log['Outbound Staging'].mean() / 400.0) * 100)
        }
        
        col_b1, col_b2 = st.columns([4, 6])
        
        with col_b1:
            st.markdown("##### Resource Congestion Scores")
            df_scores = pd.DataFrame(list(scores.items()), columns=["Resource Area", "Congestion Score (%)"]).set_index("Resource Area")
            st.bar_chart(df_scores, color="#e31837")
            
        with col_b2:
            st.markdown("##### 💡 Simulation Recommendations")
            
            # Rule 1: Yard Overflows
            if sim.gate_overflows > 0:
                st.markdown(f"""
                <div class="rec-box">
                    <strong>🚨 CRITICAL: Inbound Gate Overflow ({sim.gate_overflows} Trucks Rejected)</strong><br>
                    Your West yard queue capacity ({params['yard_queue_cap']} trucks) was exceeded. 
                    <br><em>Remedies:</em> 
                    1. Increase <strong>Yard Queue Capacity</strong>.
                    2. Increase <strong>Inbound Docks</strong> to clear trucks faster.
                    3. Speed up unloading by increasing <strong>Unloading Crews</strong>.
                </div>
                """, unsafe_allow_html=True)
                
            # Rule 2: Inbound Docks Saturation
            if avg_ib_dock_util > 80.0:
                st.markdown(f"""
                <div class="rec-box">
                    <strong>⚠️ Inbound Dock Doors Saturated ({avg_ib_dock_util:.1f}% Avg Utilization)</strong><br>
                    Inbound docks are running at near-maximum capacity, causing incoming trucks to queue.
                    <br><em>Remedies:</em> Add more <strong>Inbound Docks</strong> on the East side (currently {params['inbound_docks_cap']}).
                </div>
                """, unsafe_allow_html=True)
                
            # Rule 3: Outbound Docks Saturation
            if avg_ob_dock_util > 80.0:
                st.markdown(f"""
                <div class="rec-box">
                    <strong>⚠️ Outbound Dock Doors Saturated ({avg_ob_dock_util:.1f}% Avg Utilization)</strong><br>
                    Outbound docks are highly congested.
                    <br><em>Remedies:</em> Increase <strong>Outbound Docks</strong> on the North side (currently {params['outbound_docks_cap']}).
                </div>
                """, unsafe_allow_html=True)
                
            # Rule 4: Buffer issues
            max_ib_buffer = df_log['Inbound Buffer'].max()
            if max_ib_buffer > 200:
                st.markdown(f"""
                <div class="rec-box">
                    <strong>⚠️ Inbound Buffer Bottleneck (Max: {max_ib_buffer} Pallets)</strong><br>
                    Pallets are accumulating in the inbound buffer faster than forklifts can store them.
                    <br><em>Remedies:</em> Increase <strong>Putaway Forklifts</strong> (currently {params['putaway_forklifts']}) or reduce <strong>Putaway Time / Pallet</strong>.
                </div>
                """, unsafe_allow_html=True)
                
            # Rule 5: Staging Issues
            max_ob_staging = df_log['Outbound Staging'].max()
            if max_ob_staging > 400:
                st.markdown(f"""
                <div class="rec-box">
                    <strong>⚠️ Outbound Staging Saturated (Max: {max_ob_staging} Pallets)</strong><br>
                    Goods are being picked and staged but not loaded onto outbound trucks fast enough.
                    <br><em>Remedies:</em> Increase <strong>Loading Crews</strong> (currently {params['outbound_crews_cap']}) or increase <strong>Outbound Trucks</strong> arrival rate.
                </div>
                """, unsafe_allow_html=True)
                
            # Healthy status
            if sim.gate_overflows == 0 and avg_ib_dock_util < 75.0 and avg_ob_dock_util < 75.0 and max_ib_buffer < 150:
                st.markdown(f"""
                <div class="rec-box-green">
                    <strong>✅ System Healthy & Balanced</strong><br>
                    All queue levels, dock utilizations, and worker assignments are running smoothly with no active bottlenecks.
                </div>
                """, unsafe_allow_html=True)
