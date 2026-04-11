import os
import json
import time
import pandas as pd
import numpy as np
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import joblib
import collections
from statistics import mode

app = Flask(__name__, static_folder="assets")
CORS(app)

# ==========================================
# 1. LOAD MODEL (VERSI ABSOLUTE PATH)
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.path.join(BASE_DIR, "model", "model_rf_har (1).pkl")
SCALER_PATH = os.path.join(BASE_DIR, "model", "scaler_rf_har.pkl")
ENCODER_PATH = os.path.join(BASE_DIR, "model", "label_encoder.pkl")

try:
    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    encoder = joblib.load(ENCODER_PATH)
    print("✅ Model RF Ready")
except Exception as e:
    print(f"❌ Load Error: {e}")
    model, scaler, encoder = None, None, None

# ... (lanjutkan dengan sisa kodenya, tidak perlu diubah) ...

prediction_buffer = collections.deque(maxlen=5)

def extract_features(data):
    x = np.array([d["x"] for d in data])
    y = np.array([d["y"] for d in data])
    z = np.array([d["z"] for d in data])
    mag = np.sqrt(x**2 + y**2 + z**2)
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
    return pd.DataFrame([features])

@app.route("/")
def home():
    return send_file("predict.html")

@app.route("/predict", methods=["POST"])
def predict():
    if model is None:
        return jsonify({"error": "Model Server Sedang Rusak"}), 500
    try:
        data = request.get_json()
        token = data.get("token", "default")
        sensor_data = data.get("sensor_data", [])

        if len(sensor_data) < 120:
            return jsonify({"error": "Waiting for data..."}), 400

        feat = extract_features(sensor_data)
        scaled = scaler.transform(feat)
        pred_idx = model.predict(scaled)[0]
        label = encoder.inverse_transform([pred_idx])[0]

        prediction_buffer.append(label)
        try:
            final_label = mode(prediction_buffer)
        except:
            final_label = label

        conf = float(np.max(model.predict_proba(scaled)[0])) * 100
        emoji = {"Walking":"🚶","Running":"🏃‍♂️","Sitting":"🪑","Standing":"🧍","Laying":"🛏️"}.get(final_label, "🤖")

        result = {
            "prediction": f"{final_label} {emoji}",
            "confidence": f"{conf:.2f}%",
            "timestamp": time.time()
        }

        path = os.path.join(os.path.dirname(__file__), f"last_{token}.json")
        with open(path, "w") as f:
            json.dump(result, f)

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/get_live_status")
def get_live_status():
    token = request.args.get('token')
    path = os.path.join(os.path.dirname(__file__), f"last_{token}.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            return jsonify(json.load(f)), 200
    return jsonify({"prediction": "Offline", "confidence": "0%"}), 202

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)