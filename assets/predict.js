let isRunning = false;
let buffer = [];

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
}

window.addEventListener("devicemotion", function(event) {
    if (!isRunning) return;

    // 1. KEMBALIKAN KE SENSOR TANPA GRAVITASI (Sesuai Dataset Training Anda)
    let acc = event.acceleration || event.accelerationIncludingGravity;
    if (!acc || acc.x === null) return;

    buffer.push({ x: acc.x, y: acc.y, z: acc.z });

    document.getElementById("valX").innerHTML = acc.x.toFixed(2);
    document.getElementById("valY").innerHTML = acc.y.toFixed(2);
    document.getElementById("valZ").innerHTML = acc.z.toFixed(2);
    document.getElementById("count").innerHTML = buffer.length;

    // Jika data sudah 120 baris (~2 detik)
    if (buffer.length >= 120) {
        sendToPredict([...buffer]); 
        
        // 2. UBAH OVERLAP MENJADI 50% (Atau buang bersih)
        // Jika pakai buffer.slice(60), memori hentakan hilang dalam 1 detik.
        // Jika pakai buffer = [], memori hentakan langsung hilang (seperti app lama).
        // Mari kita gunakan slice(60) agar masih ada transisi halus namun tidak nyangkut lama.
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