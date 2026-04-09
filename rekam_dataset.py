import os
import csv
from datetime import datetime
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS

# ==========================================
# SERVER KHUSUS PEREKAM DATASET (TANPA AI)
# ==========================================
app = Flask(__name__, static_folder="assets")
CORS(app)

@app.route("/")
def home():
    # Mengarahkan user ke UI Perekam Data
    return send_file("sensor.html")

@app.route("/assets/<path:filename>")
def serve_assets(filename):
    return send_from_directory("assets", filename)

# ==========================================
# MESIN PENYIMPAN CSV
# ==========================================
@app.route('/save_csv', methods=['POST'])
def save_csv():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Tidak ada data yang diterima"}), 400

        activity = data.get("activity", "unknown")
        dataset = data.get("dataset", [])

        if not dataset or len(dataset) <= 1:
            return jsonify({"message": "Data kosong, tidak ada yang disimpan."}), 400

        # Buat nama file: dataset_Walking_20260410_103000.csv
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"dataset_{activity}_{timestamp}.csv"
        
        with open(filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(dataset) 

        print(f"\n✅ BERHASIL: Dataset [{activity}] tersimpan! ({len(dataset)-1} baris)")
        return jsonify({"message": f"Berhasil disimpan sebagai {filename}"}), 200

    except Exception as e:
        print(f"\n❌ ERROR Server: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print("🚀 Server Perekam Dataset Aktif di Port 5000")
    print("Buka jalur Ngrok dan akses di HP untuk mulai merekam!")
    app.run(host="0.0.0.0", port=5000, debug=True)