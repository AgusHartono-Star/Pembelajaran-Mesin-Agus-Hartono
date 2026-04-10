import os
import shutil
import pandas as pd
import numpy as np
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import joblib
import json
import collections
import statistics
from statistics import mode
import time

app = Flask(__name__, static_folder="assets")
CORS(app)

# ==========================================
# 1. LOAD MODEL & UTILITIES
# ==========================================
try:
    # Mengambil 'otak' AI, Scaler, dan Label Encoder terbaru
    # Pastikan nama filenya sesuai dengan yang kamu download dari Colab!
    model = joblib.load("model/model_rf_har (2).pkl")
    scaler = joblib.load("model/scaler_rf_har (2).pkl") 
    encoder = joblib.load("model/label_encoder (2).pkl")
    print("✅ Berhasil: Model, Scaler, dan Label Encoder dimuat.")
except Exception as e:
    print(f"❌ Gagal memuat file model: {e}")
    print("⚠️ Pastikan file .pkl sudah ditaruh di dalam folder 'model/'")

# Memori untuk menyimpan 5 prediksi terakhir
prediction_buffer = collections.deque(maxlen=5)
# ==========================================
# 2. ROUTES (NAVIGASI)
# ==========================================
@app.route("/")
def home():
    return send_file("predict.html")

@app.route("/assets/<path:filename>")
def serve_assets(filename):
    return send_from_directory("assets", filename)

# ==========================================
# 3. FEATURE ENGINEERING (LOGIKA AI)
# ==========================================
def extract_features(data):
    # Mengubah data JSON dari HP menjadi Array Numpy
    x = np.array([d["x"] for d in data])
    y = np.array([d["y"] for d in data])
    z = np.array([d["z"] for d in data])
    mag = np.sqrt(x**2 + y**2 + z**2)

    # Ekstraksi 25 Fitur Statistik (Sama persis dengan saat Training di Colab)
    features = {
        'mean_x': np.mean(x), 'mean_y': np.mean(y), 'mean_z': np.mean(z),
        'std_x': np.std(x), 'std_y': np.std(y), 'std_z': np.std(z),
        'max_x': np.max(x), 'max_y': np.max(y), 'max_z': np.max(z),
        'min_x': np.min(x), 'min_y': np.min(y), 'min_z': np.min(z),
        'median_x': np.median(x), 'median_y': np.median(y), 'median_z': np.median(z),
        'rms_x': np.sqrt(np.mean(x**2)), 'rms_y': np.sqrt(np.mean(y**2)), 'rms_z': np.sqrt(np.mean(z**2)),
        'iqr_x': np.percentile(x, 75) - np.percentile(x, 25),
        'iqr_y': np.percentile(y, 75) - np.percentile(y, 25),
        'iqr_z': np.percentile(z, 75) - np.percentile(z, 25),
        'mean_mag': np.mean(mag), 'std_mag': np.std(mag), 'max_mag': np.max(mag), 'min_mag': np.min(mag)
    }
    
    # Membuat DataFrame agar bisa diproses oleh StandardScaler dan Model
    df_feat = pd.DataFrame([features])
    return df_feat

# ==========================================
# 4. PREDICT ENDPOINT (MESIN PREDIKSI)
# ==========================================
@app.route("/predict", methods=["POST"])
def predict():
    try:
        # Terima data sensor dari HP
        data = request.get_json()
        if not data or len(data) < 120:
            return jsonify({"error": "Data kurang dari 120 baris"}), 400

        # Tahap 1: Ekstrak Fitur
        x_features = extract_features(data)
        
        # Tahap 2: Standardisasi (Scaling)
        x_scaled = scaler.transform(x_features)
        
       # Tahap 3: Prediksi Kelas
        pred_idx = model.predict(x_scaled)[0]
        nama_aktivitas_mentah = encoder.inverse_transform([pred_idx])[0]
        
        # --- FILTER STABILIZER (MAJORITY VOTING) ---
        # Masukkan tebakan mentah ke dalam memori
        prediction_buffer.append(nama_aktivitas_mentah)
        
        # Ambil suara terbanyak dari 5 tebakan terakhir
        try:
            nama_aktivitas_stabil = mode(prediction_buffer)
        except statistics.StatisticsError:
            # Jika suara seri (jarang terjadi), ambil tebakan terbaru
            nama_aktivitas_stabil = nama_aktivitas_mentah

        # Tahap 4: Hitung Keyakinan (Confidence)
        if hasattr(model, "predict_proba"):
            confidence = float(np.max(model.predict_proba(x_scaled)[0])) * 100
        else:
            confidence = 100.0

        # Hanya beri keyakinan tinggi jika AI stabil
        if nama_aktivitas_stabil != nama_aktivitas_mentah:
            confidence = confidence * 0.5 # Turunkan skor jika masih labil

        emoji_map = {"Walking": "🚶", "Running": "🏃‍♂️", "Sitting": "🪑", "Standing": "🧍", "Laying": "🛏️"}
        emoji = emoji_map.get(nama_aktivitas_stabil, "🤖")

        result = {
            "prediction": f"{nama_aktivitas_stabil} {emoji}",
            "confidence": f"{confidence:.2f}%",
            "timestamp": time.time()
        }
        
        # --- OPTIMASI ATOMIC WRITE UNTUK STREAMLIT ---
        # Menulis ke file sementara (temp), lalu di-replace agar Streamlit tidak crash
        temp_file = "temp_prediction.json"
        final_file = "last_prediction.json"
        
        with open(temp_file, "w") as f:
            json.dump(result, f)
            
        shutil.move(temp_file, final_file) 
        
        print(f"🔥 AI Mendeteksi: {result['prediction']} ({result['confidence']})")
        
        return jsonify(result)

    except Exception as e:
        print(f"❌ Error Server: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # Menangkap port dari server Render, jika tidak ada pakai 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)