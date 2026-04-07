let isRecording = false;
let dataset = [];
let currentActivity = "";
let countdownInterval;
let autoStopTimeout;

function startSensor() {
    if (typeof DeviceMotionEvent.requestPermission === 'function') {
        DeviceMotionEvent.requestPermission()
            .then(p => { if (p === 'granted') mulaiRekam(); else alert("Izin ditolak!"); })
            .catch(console.error);
    } else {
        mulaiRekam();
    }
}

function mulaiRekam() {
    currentActivity = document.getElementById("activityLabel").value;
    let durationSec = parseInt(document.getElementById("duration").value) || 180; 
    
    dataset = [["timestamp", "activity", "acc_x", "acc_y", "acc_z"]];
    isRecording = true;

    // Ubah UI
    document.getElementById("status").innerHTML = "🔴 Merekam: " + currentActivity;
    document.getElementById("status").className = "status inactive"; 
    
    document.getElementById("startBtn").disabled = true;
    document.getElementById("startBtn").style.opacity = "0.5";
    document.getElementById("stopBtn").disabled = false;
    document.getElementById("stopBtn").style.opacity = "1";
    document.getElementById("cancelBtn").disabled = false;
    document.getElementById("cancelBtn").style.opacity = "1";
    
    document.getElementById("activityLabel").disabled = true;
    document.getElementById("duration").disabled = true;

    // Aktifkan Pocket Lock (Layar Hitam) setelah jeda 3 detik untuk siap-siap masuk kantong
    setTimeout(() => {
        if(isRecording) document.getElementById("pocketLock").style.display = "flex";
    }, 3000);

    // Timer Hitung Mundur
    let timeRemaining = durationSec;
    document.getElementById("timer").innerText = formatTime(timeRemaining);
    
    countdownInterval = setInterval(() => {
        timeRemaining--;
        document.getElementById("timer").innerText = formatTime(timeRemaining);
        if (timeRemaining <= 0) clearInterval(countdownInterval);
    }, 1000);

    // Otomatis Berhenti & Kirim
    autoStopTimeout = setTimeout(() => { stopSensor(); }, durationSec * 1000);
}

// Buka Pocket Lock jika diketuk 2x
function unlockScreen() {
    document.getElementById("pocketLock").style.display = "none";
}

// FORMAT WAKTU
function formatTime(seconds) {
    let m = Math.floor(seconds / 60);
    let s = seconds % 60;
    return (m < 10 ? "0" + m : m) + ":" + (s < 10 ? "0" + s : s);
}

// FUNGSI BERHENTI & KIRIM (SUKSES)
function stopSensor() {
    isRecording = false;
    clearInterval(countdownInterval);
    clearTimeout(autoStopTimeout);
    unlockScreen();

    document.getElementById("status").innerHTML = "⏳ Mengirim...";
    document.getElementById("status").className = "status warning";
    nonaktifkanTombol();
    sendToServer();
}

// FUNGSI BATAL & BUANG DATA (GAGAL/SALAH GERAKAN)
function cancelSensor() {
    isRecording = false;
    clearInterval(countdownInterval);
    clearTimeout(autoStopTimeout);
    unlockScreen();

    dataset = []; // Kosongkan memori
    document.getElementById("status").innerHTML = "⚠️ Dibatalkan. Data dibuang.";
    document.getElementById("status").className = "status warning";
    
    resetFormUI();
}

function nonaktifkanTombol() {
    document.getElementById("stopBtn").disabled = true;
    document.getElementById("stopBtn").style.opacity = "0.5";
    document.getElementById("cancelBtn").disabled = true;
    document.getElementById("cancelBtn").style.opacity = "0.5";
}

window.addEventListener("devicemotion", function(event) {
    if (!isRecording) return;
    let acc =  event.accelerationIncludingGravity ||event.acceleration;
    if (!acc || acc.x === null) return;

    dataset.push([Date.now(), currentActivity, acc.x.toFixed(4), acc.y.toFixed(4), acc.z.toFixed(4)]);
    document.getElementById("valX").innerHTML = acc.x.toFixed(2);
    document.getElementById("valY").innerHTML = acc.y.toFixed(2);
    document.getElementById("valZ").innerHTML = acc.z.toFixed(2);
    document.getElementById("count").innerHTML = dataset.length;
});

function sendToServer() {
    fetch("/save_csv", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ activity: currentActivity, dataset: dataset })
    })
    .then(res => res.json())
    .then(data => {
        document.getElementById("status").innerHTML = "✅ Tersimpan!";
        document.getElementById("status").className = "status active";
        resetFormUI();
    })
    .catch(err => {
        document.getElementById("status").innerHTML = "❌ Gagal Mengirim";
        document.getElementById("status").className = "status inactive";
        document.getElementById("downloadBtn").style.display = "inline-block";
        resetFormUI();
    });
}

function resetFormUI() {
    document.getElementById("startBtn").disabled = false;
    document.getElementById("startBtn").style.opacity = "1";
    document.getElementById("activityLabel").disabled = false;
    document.getElementById("duration").disabled = false;
    document.getElementById("timer").innerText = "00:00";
    nonaktifkanTombol();
}

function downloadCSV() {
    let csvContent = "data:text/csv;charset=utf-8," + dataset.map(e => e.join(",")).join("\n");
    let link = document.createElement("a");
    link.href = encodeURI(csvContent);
    link.download = "dataset_manual_" + currentActivity + "_" + Date.now() + ".csv";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}