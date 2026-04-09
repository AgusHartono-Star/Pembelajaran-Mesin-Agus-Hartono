let isRunning = false;
let buffer = [];

// ==========================================
// FITUR WAKE LOCK & SCREEN LOCK
// ==========================================
let wakeLock = null;
let lastTapTime = 0;
const lockOverlay = document.getElementById('lockOverlay');

// Mencegah layar mati
async function requestWakeLock() {
    try {
        if ('wakeLock' in navigator) {
            wakeLock = await navigator.wakeLock.request('screen');
            console.log('Wake Lock Aktif: Layar tidak akan mati.');
        }
    } catch (err) {
        console.error(`Wake Lock gagal: ${err.message}`);
    }
}

// Melepas pencegah layar mati
function releaseWakeLock() {
    if (wakeLock !== null) {
        wakeLock.release().then(() => { wakeLock = null; });
    }
}

// Logika Buka Kunci dengan Double Tap
lockOverlay.addEventListener('touchend', function(e) {
    let currentTime = new Date().getTime();
    let tapLength = currentTime - lastTapTime;
    
    // Jika jarak antar tap kurang dari 500ms (Double Tap)
    if (tapLength < 500 && tapLength > 0) {
        lockOverlay.style.display = 'none'; // Sembunyikan layar kunci
        e.preventDefault(); // Cegah klik tembus ke bawah
    }
    lastTapTime = currentTime;
});

// Fallback jika ditest pakai mouse di PC
lockOverlay.addEventListener('dblclick', function() {
    lockOverlay.style.display = 'none';
});

// ==========================================
// LOGIKA SENSOR UTAMA
// ==========================================
function startSensor() {
    if (typeof DeviceMotionEvent.requestPermission === 'function') {
        DeviceMotionEvent.requestPermission()
            .then(p => { if (p === 'granted') mulai(); else alert("Izin ditolak!"); })
            .catch(console.error);
    } else {
        mulai();
    }
}

function mulai() {
    isRunning = true;
    buffer = [];
    
    // Aktifkan UI State
    document.getElementById("status").innerHTML = "🟢 SENSOR ON (Mendeteksi...)";
    document.getElementById("status").className = "status active"; 
    document.getElementById("startBtn").disabled = true;
    document.getElementById("startBtn").style.opacity = "0.5";
    document.getElementById("stopBtn").disabled = false;
    document.getElementById("stopBtn").style.opacity = "1";
    document.getElementById("hasil_prediksi").innerText = "Mengumpulkan data...";

    // AKTIFKAN FITUR PENGAMAN SAAT MASUK SAKU
    requestWakeLock();
    lockOverlay.style.display = 'flex'; // Tampilkan layar kunci
}

function stopSensor() {
    isRunning = false;
    buffer = [];
    
    // Matikan UI State
    document.getElementById("status").innerHTML = "🔴 SENSOR OFF";
    document.getElementById("status").className = "status inactive";
    document.getElementById("startBtn").disabled = false;
    document.getElementById("startBtn").style.opacity = "1";
    document.getElementById("stopBtn").disabled = true;
    document.getElementById("stopBtn").style.opacity = "0.5";
    
    document.getElementById("hasil_prediksi").innerText = "-";
    document.getElementById("hasil_conf").innerText = "-";
    document.getElementById("count").innerHTML = "0";

    // MATIKAN PENCEGAH LAYAR MATI
    releaseWakeLock();
}

window.addEventListener("devicemotion", function(event) {
    if (!isRunning) return;

    // 1. PRIORITASKAN SENSOR DENGAN GRAVITASI
    let acc = event.accelerationIncludingGravity || event.acceleration;
    
    if (!acc || acc.x === null) return;

    buffer.push({ x: acc.x, y: acc.y, z: acc.z });

    document.getElementById("valX").innerHTML = acc.x.toFixed(2);
    document.getElementById("valY").innerHTML = acc.y.toFixed(2);
    document.getElementById("valZ").innerHTML = acc.z.toFixed(2);
    document.getElementById("count").innerHTML = buffer.length;

    // Jika data sudah 120 baris (~2 detik)
    if (buffer.length >= 120) {
        sendToPredict([...buffer]); 
        
        // Transisi Overlap 50%
        buffer = buffer.slice(60); 
    }
});

function sendToPredict(data) {
    fetch("/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
    })
    .then(res => res.json())
    .then(res => {
        if(res.prediction) {
            document.getElementById("hasil_prediksi").innerText = res.prediction;
            document.getElementById("hasil_conf").innerText = res.confidence;
        }
    })
    .catch(err => console.error("Gagal prediksi:", err));
}