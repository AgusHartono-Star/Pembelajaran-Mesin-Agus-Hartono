import streamlit as st
import json
import time
import os
import pandas as pd
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
    /* Tema Dasar */
    .stApp { background-color: #0f172a; color: #f8fafc; }
    
    /* Hilangkan Header bawaan Streamlit yang mengganggu */
    [data-testid="stHeader"] { background: rgba(0,0,0,0); }
    
    /* Tipografi */
    h1, h2, h3 { font-family: 'Inter', sans-serif; font-weight: 800; color: #f1f5f9; }
    
    /* Styling Kartu Metrik */
    [data-testid="stMetricValue"] { font-size: 45px !important; color: #38bdf8 !important; text-shadow: 0 0 15px rgba(56, 189, 248, 0.3); }
    [data-testid="stMetricLabel"] { font-size: 16px !important; color: #94a3b8 !important; letter-spacing: 1.5px; }
    
    /* Kartu UI Background */
    .css-1r6slb0, .css-12w0qpk { background-color: #1e293b; padding: 20px; border-radius: 15px; border: 1px solid #334155; box-shadow: 0 10px 20px rgba(0,0,0,0.2); }
    
    /* Progress Bar Gradient */
    .stProgress > div > div > div > div { background-image: linear-gradient(to right, #3b82f6, #2dd4bf); height: 15px; border-radius: 10px;}
    
    /* Animasi Status Online */
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
# 3. INITIALIZATION (STATE MANAGEMENT)
# ==========================================
if 'history' not in st.session_state:
    st.session_state.history = []

# Sidebar
with st.sidebar:
    st.title("⚙️ Control Panel")
    st.info("Dashboard menerima aliran data dari Infinix Note 40 dengan interval prediksi 0.5 detik.")
    if st.button("🗑️ Clear Activity Log", use_container_width=True):
        st.session_state.history = []

# Header Dashboard
st.markdown("<h1>⚡ Human Activity Recognition</h1>", unsafe_allow_html=True)
st.markdown("<p style='color:#94a3b8; font-size:18px;'>Real-Time AI Classification Dashboard</p>", unsafe_allow_html=True)
st.markdown("---")

# ==========================================
# 4. MAIN LOOP (REAL-TIME ENGINE)
# ==========================================
placeholder = st.empty()

while True:
    with placeholder.container():
        file_path = "last_prediction.json"
        file_exists = os.path.exists(file_path)
        
        # Validasi Koneksi (diperketat menjadi 5 detik karena data masuk tiap 0.5 detik)
        if file_exists:
            last_update_time = os.path.getmtime(file_path)
            is_online = (time.time() - last_update_time) < 5 
        else:
            is_online = False

        # Status Bar Rendering
        if is_online:
            st.markdown(f"**Status:** <div class='pulse-online'></div> <span style='color:#10b981; font-weight:bold;'>SENSOR ONLINE</span> &nbsp;&nbsp;|&nbsp;&nbsp; **Sync:** {datetime.now().strftime('%H:%M:%S')}", unsafe_allow_html=True)
        else:
            st.markdown(f"**Status:** 🔴 <span class='status-offline'>SENSOR OFFLINE</span> &nbsp;&nbsp;|&nbsp;&nbsp; **Sync:** {datetime.now().strftime('%H:%M:%S')}", unsafe_allow_html=True)

        st.write("") # Spacing

        if file_exists and is_online:
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                
                current_act = data['prediction']
                conf_str = data['confidence']
                
                # Update History Log (Hanya rekam jika aktivitas berubah agar log tidak penuh spam)
                if not st.session_state.history or st.session_state.history[0]['Activity'] != current_act:
                    st.session_state.history.insert(0, {
                        "Time": datetime.now().strftime("%H:%M:%S"),
                        "Activity": current_act,
                        "Confidence": conf_str
                    })
                    st.session_state.history = st.session_state.history[:8] # Simpan 8 data terakhir saja

                # --- RENDER KARTU METRIK ---
                m1, m2 = st.columns(2)
                with m1:
                    st.metric(label="🎯 ACTIVITY DETECTED", value=current_act)
                with m2:
                    st.metric(label="🤖 AI CONFIDENCE SCORE", value=conf_str)
                
                # --- RENDER PROGRESS BAR ---
                conf_val = float(conf_str.replace('%', '')) / 100
                st.write("### ⚡ Probability Strength")
                st.progress(conf_val)

                # --- RENDER TABEL HISTORY ---
                st.write("### 📜 Recent Activity Log")
                if st.session_state.history:
                    df_hist = pd.DataFrame(st.session_state.history)
                    # Menggunakan st.dataframe untuk tampilan tabel yang lebih interaktif dan modern
                    st.dataframe(df_hist, use_container_width=True, hide_index=True)
            
            except json.JSONDecodeError:
                # PERBAIKAN KRITIS: Jika Flask sedang menimpa file, lewati loop ini agar UI tidak crash
                pass
            except Exception as e:
                st.error(f"Error sistem: {e}")

        else:
            # Tampilan saat sensor mati / belum dikoneksikan
            st.warning("⚠️ Menunggu aliran data sensor dari Infinix Note 40...")
            st.info("Buka aplikasi di HP, tekan 'Mulai Deteksi', dan pastikan koneksi Ngrok stabil.")

    # PERCEPATAN REFRESH RATE: Turun dari 2 detik menjadi 0.5 detik
    # Ini menyesuaikan dengan Overlap Sliding Window kita (Step Size 30 = 0.5 detik)
    time.sleep(1)