import os
import csv
from datetime import datetime
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import numpy as np
import joblib

# ===============================
# INIT APP
# ===============================
app = Flask(__name__, static_folder="assets")
CORS(app)

# ===============================
# LOAD MODEL (DIBIARKAN JIKA NANTI DIBUTUHKAN)
# ===============================
try:
    model = joblib.load("model/random_forest_model.pkl")
    scaler = joblib.load("model/scaler.pkl")
    indices = joblib.load("model/selected_features_indices.pkl")
    print("✅ Model berhasil dimuat.")
except Exception as e:
    print(f"⚠️ Peringatan: Model belum dimuat sempurna. Error: {e}")

# ===============================
# LABEL
# ===============================
labels = {
    0: "LAYING",
    1: "SITTING",
    2: "STANDING",
    3: "WALKING",
    4: "WALKING_DOWNSTAIRS",
    5: "WALKING_UPSTAIRS"
}

# ===============================
# ROUTE HOME (WAJIB ADA)
# ===============================
@app.route("/")
def home():
    # Pastikan file sensor.html ada di folder yang sama dengan flask_api.py
    return send_file("sensor.html")

# ===============================
# ROUTE ASSETS (CSS & JS)
# ===============================
@app.route("/assets/<path:filename>")
def serve_assets(filename):
    return send_from_directory("assets", filename)

# =================================================================
# [BARU] ROUTE UNTUK MENYIMPAN DATASET DARI HP KE LAPTOP
# =================================================================
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

        # Buat nama file unik berdasarkan waktu (misal: dataset_Walking_20260404_193000.csv)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"dataset_{activity}_{timestamp}.csv"
        
        # Simpan file CSV ke dalam folder proyekmu (sejajar dengan flask_api.py)
        with open(filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(dataset) 

        print(f"\n✅ BERHASIL: File {filename} telah tersimpan di laptop dengan {len(dataset)-1} baris data.")
        return jsonify({"message": f"Berhasil disimpan sebagai {filename}"}), 200

    except Exception as e:
        print(f"\n❌ ERROR: Gagal menyimpan CSV - {e}")
        return jsonify({"error": str(e)}), 500

# ===============================
# FEATURE ENGINEERING
# ===============================
def extract_features(data):
    x = np.array([d["x"] for d in data])
    y = np.array([d["y"] for d in data])
    z = np.array([d["z"] for d in data])

    features = []

    # BASIC STATS
    features.extend([
        np.mean(x), np.mean(y), np.mean(z),
        np.std(x), np.std(y), np.std(z),
        np.max(x), np.max(y), np.max(z),
        np.min(x), np.min(y), np.min(z),
        np.var(x), np.var(y), np.var(z)
    ])

    # ENERGY (FIXED)
    features.extend([
        np.mean(x**2),
        np.mean(y**2),
        np.mean(z**2)
    ])

    # MAGNITUDE (PENTING BANGET)
    magnitude = np.sqrt(x**2 + y**2 + z**2)

    features.extend([
        np.mean(magnitude),
        np.std(magnitude),
        np.max(magnitude),
        np.min(magnitude)
    ])

    # PADDING KE 561
    full = np.zeros(561)
    full[:len(features)] = features

    return full.reshape(1, -1)

# ===============================
# ROUTE PREDICT
# ===============================
@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "no data"}), 400

        # CASE 1: SENSOR (list of dict)
        if isinstance(data, list):
            x = extract_features(data)

        # CASE 2: STREAMLIT (561 fitur)
        elif isinstance(data, dict) and "features" in data:
            features = data["features"]

            if len(features) != 561:
                return jsonify({"error": "harus 561 fitur"}), 400

            x = np.array(features).reshape(1, -1)

        else:
            return jsonify({"error": "format data tidak dikenali"}), 400

        # PIPELINE MODEL
        x_selected = x[:, indices]
        x_scaled = scaler.transform(x_selected)

        pred = model.predict(x_scaled)[0]
        proba = model.predict_proba(x_scaled)[0]

        result = {
            "prediction": labels[pred],
            "confidence": float(np.max(proba))
        }

        print("🔥 HASIL PREDIKSI:", result)

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ===============================
# RUN
# ===============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)