let selectedFile = null;
const dropzone = document.getElementById("dropzone");
const input = document.getElementById("videoInput");
const browseBtn = document.getElementById("browseBtn");
const analyzeBtn = document.getElementById("analyzeBtn");
const statusEl = document.getElementById("status");
const allowed = ["mp4", "avi", "mov"];

function setStatus(msg) {
  statusEl.textContent = msg;
}

function validateFile(file) {
  if (!file || !file.name.includes(".")) return false;
  const ext = file.name.split(".").pop().toLowerCase();
  return allowed.includes(ext);
}

function setFile(file) {
  const fileInfoEl = document.getElementById("fileInfo");
  const fileInfoName = document.getElementById("fileInfoName");
  const fileInfoSize = document.getElementById("fileInfoSize");

  if (!validateFile(file)) {
    selectedFile = null;
    analyzeBtn.disabled = true;
    statusEl.className = "status status-error";
    setStatus("Invalid format. Please upload MP4, AVI, or MOV.");
    if (fileInfoEl) fileInfoEl.style.display = "none";
    return;
  }
  selectedFile = file;
  analyzeBtn.disabled = false;
  statusEl.className = "status status-ok";
  setStatus("File ready - click Run Full Analysis to begin.");
  if (fileInfoEl) {
    fileInfoEl.style.display = "flex";
    fileInfoName.textContent = file.name;
    fileInfoSize.textContent = (file.size / (1024 * 1024)).toFixed(2) + " MB";
  }
}

dropzone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropzone.classList.add("dragover");
});

dropzone.addEventListener("dragleave", () => {
  dropzone.classList.remove("dragover");
});

dropzone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropzone.classList.remove("dragover");
  setFile(e.dataTransfer.files[0]);
});

browseBtn.addEventListener("click", () => input.click());
input.addEventListener("change", (e) => setFile(e.target.files[0]));

analyzeBtn.addEventListener("click", async () => {
  if (!selectedFile) return;
  analyzeBtn.disabled = true;
  statusEl.className = "status";
  dropzone.classList.add("is-scanning");
  setStatus("Uploading video securely...");

  try {
    const data = new FormData();
    data.append("video", selectedFile);
    const uploadRes = await fetch("/api/upload", { method: "POST", body: data });
    const uploadJson = await uploadRes.json();
    if (!uploadRes.ok) throw new Error(uploadJson.error || "Upload failed");

    setStatus("Running captioning, forensic AI detection, tampering checks, face privacy review, and timeline extraction...");
    const analyzeRes = await fetch(`/api/analyze/${uploadJson.video_id}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({})
    });
    const analyzeJson = await analyzeRes.json();
    if (!analyzeRes.ok) throw new Error(analyzeJson.error || "Analysis failed");

    localStorage.setItem(
      "analysisResult",
      JSON.stringify({
        fileName: selectedFile.name,
        fileSize: selectedFile.size,
        videoUrl: `/api/video/${uploadJson.video_id}`,
        result: analyzeJson,
        sha256: uploadJson.sha256,
        analyzedAt: new Date().toISOString()
      })
    );
    setStatus("Analysis complete - opening intelligence dashboard...");
    window.location.href = "/dashboard";
  } catch (err) {
    dropzone.classList.remove("is-scanning");
    statusEl.className = "status status-error";
    setStatus(`Error: ${err.message}`);
    analyzeBtn.disabled = false;
  }
});

function initParticles() {
  const canvas = document.getElementById("particles");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const dpr = window.devicePixelRatio || 1;
  let particles = [];

  function resize() {
    canvas.width = Math.floor(window.innerWidth * dpr);
    canvas.height = Math.floor(window.innerHeight * dpr);
    canvas.style.width = `${window.innerWidth}px`;
    canvas.style.height = `${window.innerHeight}px`;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    particles = Array.from({ length: Math.max(24, Math.floor(window.innerWidth / 45)) }, () => ({
      x: Math.random() * window.innerWidth,
      y: Math.random() * window.innerHeight,
      r: 0.7 + Math.random() * 2.2,
      v: 0.15 + Math.random() * 0.5
    }));
  }

  function tick() {
    ctx.clearRect(0, 0, window.innerWidth, window.innerHeight);
    for (const p of particles) {
      p.y -= p.v;
      if (p.y < -8) {
        p.y = window.innerHeight + 8;
        p.x = Math.random() * window.innerWidth;
      }
      ctx.beginPath();
      ctx.fillStyle = "rgba(120, 214, 255, 0.35)";
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fill();
    }
    requestAnimationFrame(tick);
  }

  resize();
  window.addEventListener("resize", resize);
  tick();
}

initParticles();
