// ==========================================
// SISTEM AUTO-GENERATE TOKEN
// ==========================================
let myToken = localStorage.getItem("har_pairing_token");

if (!myToken) {
    let randomPin = Math.floor(1000 + Math.random() * 9000);
    myToken = "HAR-" + randomPin;
    localStorage.setItem("har_pairing_token", myToken);
}

document.addEventListener("DOMContentLoaded", function() {
    let displayEl = document.getElementById("tokenDisplay");
    if(displayEl) {
        displayEl.innerText = myToken;
    }
});

let isRunning = false;
let buffer = [];

// ==========================================
// FITUR WAKE LOCK & SCREEN LOCK
// ==========================================
let wakeLock = null;
let lastTapTime = 0;
const lockOverlay = document.getElementById('lockOverlay');

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

function releaseWakeLock() {
    if (wakeLock !== null) {
        wakeLock.release().then(() => { wakeLock = null; });
    }
}

if(lockOverlay) {
    lockOverlay.addEventListener('touchend', function(e) {
        let currentTime = new Date().getTime();
        let tapLength = currentTime - lastTapTime;

        if (tapLength < 500 && tapLength > 0) {
            lockOverlay.style.display = 'none';
            e.preventDefault();
        }
        lastTapTime = currentTime;
    });

    lockOverlay.addEventListener('dblclick', function() {
        lockOverlay.style.display = 'none';
    });
}

// ==========================================
// LOGIKA SENSOR UTAMA & UI
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

    document.getElementById("status").innerHTML = "🟢 SENSOR ON (Mendeteksi...)";
    document.getElementById("status").className = "status active";
    document.getElementById("startBtn").disabled = true;
    document.getElementById("startBtn").style.opacity = "0.5";
    document.getElementById("stopBtn").disabled = false;
    document.getElementById("stopBtn").style.opacity = "1";
    document.getElementById("hasil_prediksi").innerText = "Mengumpulkan data...";

    requestWakeLock();
    if(lockOverlay) lockOverlay.style.display = 'flex';
}

function stopSensor() {
    isRunning = false;
    buffer = [];

    document.getElementById("status").innerHTML = "🔴 SENSOR OFF";
    document.getElementById("status").className = "status inactive";
    document.getElementById("startBtn").disabled = false;
    document.getElementById("startBtn").style.opacity = "1";
    document.getElementById("stopBtn").disabled = true;
    document.getElementById("stopBtn").style.opacity = "0.5";

    document.getElementById("hasil_prediksi").innerText = "-";
    document.getElementById("hasil_conf").innerText = "-";
    document.getElementById("count").innerHTML = "0";

    releaseWakeLock();
}

// ==========================================
// PENGIRIMAN DATA DENGAN SISTEM ANTI-SPAM (LAMPU LALU LINTAS)
// ==========================================
let isPredicting = false; // Tambahkan variabel ini untuk menahan pengiriman

window.addEventListener("devicemotion", function(event) {
    if (!isRunning) return;

    let acc = event.accelerationIncludingGravity || event.acceleration;

    if (!acc || acc.x === null) return;

    buffer.push({ x: acc.x, y: acc.y, z: acc.z });

    document.getElementById("valX").innerHTML = acc.x.toFixed(2);
    document.getElementById("valY").innerHTML = acc.y.toFixed(2);
    document.getElementById("valZ").innerHTML = acc.z.toFixed(2);
    document.getElementById("count").innerHTML = buffer.length;

    // Jika data sudah 120 baris
    if (buffer.length >= 120) {
        // HANYA KIRIM JIKA SERVER SEDANG TIDAK SIBUK
        if (!isPredicting) {
            sendToPredict([...buffer]);
        }

        // Tetap potong buffer agar memori HP tidak penuh
        buffer = buffer.slice(60);
    }
});

function sendToPredict(data) {
    isPredicting = true; // Nyalakan Lampu Merah (Kunci pengiriman baru)

    let payload = {
        "token": myToken,
        "sensor_data": data
    };

    fetch("https://agushartono.pythonanywhere.com", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    })
    .then(res => {
        if (!res.ok) {
            throw new Error('Network response was not ok');
        }
        return res.json();
    })
    .then(res => {
        if(res.prediction) {
            document.getElementById("hasil_prediksi").innerText = res.prediction;
            document.getElementById("hasil_conf").innerText = res.confidence;
        } else if (res.error) {
             document.getElementById("hasil_prediksi").innerText = "Error: " + res.error;
        }
    })
    .catch(err => {
        console.error("Gagal prediksi:", err);
        // Jangan langsung bilang gagal ke user kalau cuma telat, biarkan AI memulihkan diri di siklus berikutnya
        document.getElementById("hasil_prediksi").innerText = "Menunggu respons server...";
    })
    .finally(() => {
        // INI PALING PENTING: Nyalakan Lampu Hijau kembali (Buka kunci)
        // Entah berhasil atau gagal, izinkan HP mengirim data lagi.
        isPredicting = false;
    });
}