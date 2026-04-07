import streamlit as st
import joblib
import numpy as np
from collections import Counter
from datetime import datetime
import pandas as pd

# ===============================
# LOAD MODEL
# ===============================
model = joblib.load("model/random_forest_model.pkl")
scaler = joblib.load("model/scaler.pkl")
indices = joblib.load("model/selected_features_indices.pkl")

# ===============================
# LABEL MAPPING
# ===============================
activity_labels = {
    0: "🛌 LAYING",
    1: "🪑 SITTING",
    2: "🧍 STANDING",
    3: "🚶 WALKING",
    4: "⬇️ WALKING_DOWNSTAIRS",
    5: "⬆️ WALKING_UPSTAIRS"
}

# ===============================
# UI
# ===============================
st.set_page_config(page_title="HAR PRO", layout="centered")

st.title("📱 Human Activity Recognition PRO")
st.caption("AI untuk deteksi aktivitas tubuh")

st.divider()

# ===============================
# SESSION STATE
# ===============================
if "history" not in st.session_state:
    st.session_state.history = []

if "log" not in st.session_state:
    st.session_state.log = []

# ===============================
# INPUT
# ===============================
input_data = st.text_area(
    "Masukkan 561 fitur",
    height=150
)

# ===============================
# PREDIKSI
# ===============================
if st.button("🔍 Prediksi"):
    try:
        # ===============================
        # CLEAN INPUT
        # ===============================
        cleaned = input_data.replace("\n", ",").replace("\t", ",").replace(" ", "")
        data_list = [x for x in cleaned.split(",") if x != ""]

        st.write("🔢 Jumlah fitur:", len(data_list))

        if len(data_list) != 561:
            st.error(f"❌ Harus 561 fitur, sekarang: {len(data_list)}")

        else:
            data = np.array([float(x) for x in data_list]).reshape(1, -1)

            # ===============================
            # PIPELINE
            # ===============================
            data_selected = data[:, indices]
            data_scaled = scaler.transform(data_selected)

            pred = model.predict(data_scaled)[0]
            proba = model.predict_proba(data_scaled)
            confidence = float(np.max(proba))

            # ===============================
            # 🔥 SMART SMOOTHING FIX 🔥
            # ===============================
            st.session_state.history.append(pred)

            # batasi history (penting!)
            if len(st.session_state.history) > 5:
                st.session_state.history.pop(0)

            most_common = Counter(st.session_state.history).most_common(1)[0]

            # LOGIKA FINAL (ini kunci fix bug kamu)
            if confidence > 0.90:
                final_pred = pred  # model yakin → langsung pakai
            elif most_common[1] >= 3:
                final_pred = most_common[0]  # cukup stabil → pakai history
            else:
                final_pred = pred  # fallback

            label = activity_labels.get(final_pred, "Unknown")

            # ===============================
            # LOGGING
            # ===============================
            timestamp = datetime.now().strftime("%H:%M:%S")

            st.session_state.log.append({
                "time": timestamp,
                "prediction": label,
                "confidence": round(confidence, 3)
            })

            # ===============================
            # OUTPUT
            # ===============================
            st.divider()
            st.subheader("📊 Hasil Prediksi")

            st.metric("Aktivitas", label)
            st.progress(confidence)
            st.write(f"Confidence: **{round(confidence*100,2)}%**")

            # ===============================
            # TOP 3 (DISARANKAN DI EXPANDER)
            # ===============================
            with st.expander("🔍 Detail Prediksi"):
                sorted_idx = np.argsort(proba[0])[::-1]

                for i in range(3):
                    idx = sorted_idx[i]
                    lbl = activity_labels.get(idx)
                    conf = proba[0][idx]

                    st.write(f"{i+1}. {lbl} ({round(conf*100,2)}%)")

                st.write("History:", st.session_state.history)

    except Exception as e:
        st.error(f"❌ Error: {e}")

# ===============================
# LOG TABLE
# ===============================
st.divider()
st.subheader("📜 Riwayat Lengkap")

if len(st.session_state.log) > 0:
    df = pd.DataFrame(st.session_state.log)
    st.dataframe(df, use_container_width=True)

    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("⬇️ Download Log CSV", csv, "prediction_log.csv")

else:
    st.info("Belum ada data")