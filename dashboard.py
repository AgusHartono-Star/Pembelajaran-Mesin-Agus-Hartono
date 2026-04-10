import streamlit as st
import json
import time
import os
import pandas as pd
import numpy as np
import joblib
from datetime import datetime

# ==========================================
# 1. KONFIGURASI HALAMAN
# ==========================================
st.set_page_config(
    page_title="HAR Real-Time Analytics",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. KUSTOMISASI CSS (ULTRA MODERN UI)
# ==========================================
st.markdown("""
    <style>
    .stApp { background-color: #0f172a; color: #f8fafc; }
    [data-testid="stHeader"] { background: rgba(0,0,0,0); }
    h1, h2, h3 { font-family: 'Inter', sans-serif; font-weight: 800; color: #f1f5f9; }
    [data-testid="stMetricValue"] { font-size: 45px !important; color: #38bdf8 !important; text-shadow: 0 0 15px rgba(56, 189, 248, 0.3); }
    [data-testid="stMetricLabel"] { font-size: 16px !important; color: #94a3b8 !important; letter-spacing: 1.5px; }
    .css-1r6slb0, .css-12w0qpk { background-color: #1e293b; padding: 20px; border-radius: 15px; border: 1px solid #334155; box-shadow: 0 10px 20px rgba(0,0,0,0.2); }
    .stProgress > div > div > div > div { background-image: linear-gradient(to right, #3b82f6, #2dd4bf); height: 15px; border-radius: 10px;}
    .pulse-online {
        display: inline-block; width: 12px; height: 12px; border-radius: 50%;
        background-color: #10b981; margin-right: 8px;
        box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
        animation: pulse-green 1.5s infinite;
    }
    @keyframes pulse-green {
        0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(16, 185, 129, 0); }
        100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }
    .status-offline { color: #f43f5e; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 3. FUNGSI FEATURE ENGINEERING (BARU DITAMBAHKAN)
# ==========================================
def extract_features(window_data):
    """Mengekstrak 25 fitur statistik dari data mentah X, Y, Z"""
    # Sesuaikan nama kolom jika data mentahmu berbeda (misal: 'x', 'y', 'z')
    # Di sini diasumsikan kolom bernama 'acc_x', 'acc_y', 'acc_z'
    x = window_data['acc_x'].values
    y = window_data['acc_y'].values
    z = window_data['acc_z'].values
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
    return features

# ==========================================
# 4. INITIALIZATION & SIDEBAR
# ==========================================
if 'history' not in st.session_state:
    st.session_state.history = []

with st.sidebar:
    st.title("⚙️ Control Panel")
    
    st.write("### 🧭 Pilih Mode Operasi")
    app_mode = st.radio("Pilih Mode:", ["⚡ Real-Time Sensor", "📁 Uji Data CSV (Mentah)"])
    
    st.divider()
    
    if app_mode == "⚡ Real-Time Sensor":
        st.info("Dashboard menerima aliran data dari HP dengan interval 1 detik.")
        if st.button("🗑️ Clear Activity Log", use_container_width=True):
            st.session_state.history = []

# ==========================================
# 5. HEADER UTAMA
# ==========================================
st.markdown("<h1>⚡ Human Activity Recognition</h1>", unsafe_allow_html=True)
if app_mode == "⚡ Real-Time Sensor":
    st.markdown("<p style='color:#94a3b8; font-size:18px;'>Real-Time AI Classification Dashboard</p>", unsafe_allow_html=True)
else:
    st.markdown("<p style='color:#94a3b8; font-size:18px;'>Raw Data Feature Engineering & Batch Prediction Tool</p>", unsafe_allow_html=True)
st.markdown("---")


# ==========================================
# MODE 1: REAL-TIME ENGINE (SENSOR HP)
# ==========================================
# ==========================================
# MODE 1: REAL-TIME ENGINE (SENSOR HP)
# ==========================================
if app_mode == "⚡ Real-Time Sensor":
    import requests
    
    # URL API dari PythonAnywhere milikmu
    API_URL = "https://agushartono.pythonanywhere.com/get_live_status"
    
    # Membuat wadah (placeholder) agar UI bisa di-refresh tanpa berkedip
    status_placeholder = st.empty()
    content_placeholder = st.empty()
    
    with status_placeholder.container():
        st.markdown(f"**Status:** 🟡 <span style='color:#facc15; font-weight:bold;'>MENYAMBUNGKAN KE SENSOR...</span>", unsafe_allow_html=True)
    
    try:
        # Meminta data dari server PythonAnywhere
        response = requests.get(API_URL, timeout=3)
        
        if response.status_code == 200:
            data = response.json()
            current_act = data.get('prediction', 'Unknown')
            conf_str = data.get('confidence', '0%')
            
            # Update status jadi hijau (Online)
            with status_placeholder.container():
                st.markdown(f"**Status:** <div class='pulse-online'></div> <span style='color:#10b981; font-weight:bold;'>SENSOR ONLINE</span> &nbsp;&nbsp;|&nbsp;&nbsp; **Sync:** {datetime.now().strftime('%H:%M:%S')}", unsafe_allow_html=True)
            
            with content_placeholder.container():
                # Catat ke history jika aktivitas berubah atau history masih kosong
                if not st.session_state.history or st.session_state.history[0]['Activity'] != current_act:
                    st.session_state.history.insert(0, {
                        "Time": datetime.now().strftime("%H:%M:%S"),
                        "Activity": current_act,
                        "Confidence": conf_str
                    })
                    st.session_state.history = st.session_state.history[:8] # Simpan 8 history terakhir
                
                # Tampilkan Angka Besar
                m1, m2 = st.columns(2)
                with m1:
                    st.metric(label="🎯 ACTIVITY DETECTED", value=current_act)
                with m2:
                    st.metric(label="🤖 AI CONFIDENCE SCORE", value=conf_str)
                
                # Tampilkan Progress Bar
                try:
                    conf_val = float(conf_str.replace('%', '')) / 100
                except ValueError:
                    conf_val = 0.0
                    
                st.write("### ⚡ Probability Strength")
                st.progress(conf_val)

                # Tampilkan History
                st.write("### 📜 Recent Activity Log")
                if st.session_state.history:
                    df_hist = pd.DataFrame(st.session_state.history)
                    st.dataframe(df_hist, use_container_width=True, hide_index=True)
                    
        else:
            with status_placeholder.container():
                st.markdown(f"**Status:** 🔴 <span class='status-offline'>SENSOR OFFLINE</span>", unsafe_allow_html=True)
            with content_placeholder.container():
                st.warning("⚠️ Menunggu aliran data sensor dari HP...")
                st.info("Buka link PythonAnywhere di HP-mu dan tekan 'Mulai Deteksi'.")

    except requests.exceptions.RequestException as e:
        with status_placeholder.container():
            st.markdown(f"**Status:** 🔴 <span class='status-offline'>GAGAL TERHUBUNG</span>", unsafe_allow_html=True)
        with content_placeholder.container():
            st.error(f"Gagal terhubung ke API: {e}")

    # Rerun otomatis setiap 1.5 detik
    time.sleep(1.5)
    try:
        st.rerun()
    except AttributeError:
        st.experimental_rerun()


# ==========================================
# MODE 2: UJI DATA MENTAH CSV & FEATURE ENGINEERING
# ==========================================
elif app_mode == "📁 Uji Data CSV (Mentah)":
    st.subheader("⚙️ Proses Data Mentah & Prediksi")
    st.write("Upload file CSV berisi data sensor **mentah** (acc_x, acc_y, acc_z). Sistem akan otomatis melakukan *sliding window* dan ekstraksi fitur sebelum diprediksi.")
    
    try:
        # Pastikan nama model sudah sesuai
        model = joblib.load("model/model_rf_har.pkl")
        scaler = joblib.load("model/scaler_rf_har.pkl")
        encoder = joblib.load("model/label_encoder.pkl")
        model_ready = True
    except Exception as e:
        model_ready = False
        st.error(f"❌ Gagal memuat model (.pkl). Pastikan file model ada di folder 'model/'. Error: {e}")

    if model_ready:
        uploaded_file = st.file_uploader("Upload File CSV Data Mentah", type=["csv"])
        
        if uploaded_file is not None:
            raw_data = pd.read_csv(uploaded_file)
            
            # Cek apakah kolom yang dibutuhkan ada. 
            # Jika dataset mentah dari HP bernama x, y, z, ubah baris di bawah ini.
            required_cols = ['acc_x', 'acc_y', 'acc_z']
            if not all(col in raw_data.columns for col in required_cols):
                st.error(f"❌ Error: Dataset mentah harus memiliki kolom: {required_cols}. Kolom terdeteksi: {list(raw_data.columns)}")
            else:
                st.success(f"✅ Data mentah diterima: {len(raw_data)} baris.")
                with st.expander("Lihat Sampel Data Mentah"):
                    st.dataframe(raw_data.head())

                # Meminta user memasukkan window size
                col_w1, col_w2 = st.columns(2)
                with col_w1:
                    window_size = st.number_input("Tentukan Ukuran Window (Data per prediksi)", min_value=10, value=50, step=10)
                with col_w2:
                    st.info(f"💡 Info: Jika sensor diset 50Hz, maka window size 50 = 1 detik data. Hasilnya akan menghasilkan {len(raw_data) // window_size} prediksi.")

                if st.button("🛠️ Ekstrak Fitur & Prediksi", type="primary"):
                    with st.spinner('Mengekstrak 25 fitur statistik dan mengklasifikasikan...'):
                        try:
                            # 1. PROSES SLIDING WINDOW
                            extracted_features_list = []
                            for i in range(0, len(raw_data) - window_size + 1, window_size):
                                window_data = raw_data.iloc[i : i + window_size]
                                features = extract_features(window_data)
                                extracted_features_list.append(features)
                            
                            df_features = pd.DataFrame(extracted_features_list)
                            
                            st.write("### 📊 Hasil Ekstraksi Fitur (Siap Prediksi)")
                            st.write(f"Terekstrak menjadi {len(df_features)} baris (window) dan {df_features.shape[1]} kolom fitur.")
                            with st.expander("Lihat Data Setelah Diekstrak"):
                                st.dataframe(df_features.head())

                            # 2. PROSES PREDIKSI
                            # Scaling
                            x_scaled = scaler.transform(df_features)
                            # Prediksi
                            pred_idx = model.predict(x_scaled)
                            pred_labels = encoder.inverse_transform(pred_idx)
                            
                            # Buat dataframe untuk hasil akhir
                            df_result = pd.DataFrame({
                                'Window_Index': range(1, len(pred_labels) + 1),
                                'PREDIKSI_AI': pred_labels
                            })
                            
                            st.write("### 🎯 Hasil Klasifikasi Aktivitas")
                            col_res1, col_res2 = st.columns([1, 2])
                            with col_res1:
                                st.dataframe(df_result, height=300, use_container_width=True)
                            with col_res2:
                                activity_counts = df_result['PREDIKSI_AI'].value_counts()
                                st.bar_chart(activity_counts)
                            
                            # Tombol Download
                            csv_result = df_result.to_csv(index=False).encode('utf-8')
                            st.download_button(
                                label="⬇️ Download Hasil Prediksi (CSV)",
                                data=csv_result,
                                file_name=f"hasil_prediksi_mentah.csv",
                                mime="text/csv",
                            )
                        except Exception as e:
                            st.error(f"❌ Terjadi kesalahan saat ekstraksi/prediksi: {e}")