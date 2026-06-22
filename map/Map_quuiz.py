from flask import Flask, send_from_directory, render_template_string
import os
import webbrowser
from threading import Timer

app = Flask(__name__)
PORT = 5000

# Get the directory where Map_quuiz.py is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.route('/')
def index():
    # Read and serve the index.html
    html_path = os.path.join(BASE_DIR, 'index.html')
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    return render_template_string(html_content)

@app.route('/diaphantinh.geojson')
def geojson():
    # Serve the GeoJSON map file
    return send_from_directory(BASE_DIR, 'diaphantinh.geojson')

@app.route('/provinces.json')
def provinces():
    # Serve the list of province names
    return send_from_directory(BASE_DIR, 'provinces.json')

@app.route('/dc_factories.json')
def dc_factories():
    # Serve the list of DC/Factory coordinates
    return send_from_directory(BASE_DIR, 'dc_factories.json')

def open_browser():
    webbrowser.open_new(f"http://127.0.0.1:{PORT}")

if __name__ == '__main__':
    # Open the browser after 1.5 seconds once server starts
    Timer(1.5, open_browser).start()
    print(f"\n==========================================")
    print(f"Starting Quiz Server at http://127.0.0.1:{PORT} ...")
    print(f"Opening browser automatically...")
    print(f"==========================================\n")
    app.run(host='127.0.0.1', port=PORT, debug=False)
