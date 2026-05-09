function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;")
    .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

const raw = localStorage.getItem("analysisResult");
if (!raw) {
  window.location.href = "/";
}

let state = {};
try {
  state = JSON.parse(raw || "{}");
} catch (error) {
  console.error("Failed to parse analysis result from localStorage:", error);
  localStorage.removeItem("analysisResult");
  window.location.href = "/";
}

const result = state.result || {};
let videoDuration = 0;

function clamp(v) {
  return Math.max(0, Math.min(100, Number(v || 0)));
}

function getAiLikelihood() {
  const signals = result.ai_detection?.signals || {};
  return clamp(
    signals.ai_generation_likelihood ??
    signals.combined_ai_signal ??
    result.forensic?.ai_generation_likelihood ??
    result.forensic?.combined_ai_signal ??
    result.ai_detection?.confidence
  );
}

function deriveAiStatus() {
  const signals = result.ai_detection?.signals || {};
  const fas = clamp(
    signals.forensic_authenticity_score ??
    result.forensic?.forensic_authenticity_score ??
    (100 - getAiLikelihood())
  );
  if (fas >= 80) return "Real";
  if (fas >= 55) return "Likely Real";
  if (fas >= 45) return "Inconclusive";
  if (fas >= 25) return "Likely AI-Generated";
  return "AI-Generated";
}

function animateValue(element, start, end, duration) {
  let startTimestamp = null;
  const step = (timestamp) => {
    if (!startTimestamp) startTimestamp = timestamp;
    const progress = Math.min((timestamp - startTimestamp) / duration, 1);
    const easeOut = progress < 0.5 ? 2 * progress * progress : -1 + (4 - 2 * progress) * progress;
    const current = start + (end - start) * easeOut;
    element.textContent = current.toFixed(2) + "%";
    if (progress < 1) {
      requestAnimationFrame(step);
    }
  };
  requestAnimationFrame(step);
}

function addBar(label, value) {
  const wrap = document.getElementById("confidenceWrap");
  const node = document.createElement("div");
  node.className = "bar";
  // Spaces in CSS id selectors are treated as descendant combinators and break
  // querySelector — replace every whitespace run with a hyphen.
  const safeId = "bar-" + label.replace(/\s+/g, "-");

  node.innerHTML = `
    <div class="bar-head"><span>${label}</span><span id="${safeId}">0%</span></div>
    <div class="bar-track"><div class="bar-fill" style="width:${clamp(value)}%"></div></div>
  `;

  wrap.appendChild(node);

  const barPercentageEl = document.getElementById(safeId);
  setTimeout(() => {
    animateValue(barPercentageEl, 0, value, 1200);
  }, 100);
}

function addScoreRing(label, value, tone) {
  const wrap = document.getElementById("scoreRings");
  if (!wrap) return;
  const score = clamp(value);
  const node = document.createElement("div");
  node.className = `score-ring ${tone || ""}`;
  node.style.setProperty("--score", `${score * 3.6}deg`);
  node.innerHTML = `
    <div class="score-orbit">
      <strong>0%</strong>
    </div>
    <span>${label}</span>
  `;
  wrap.appendChild(node);
  setTimeout(() => animateValue(node.querySelector("strong"), 0, score, 1200), 120);
}

function renderAdvancedDashboard() {
  const risk = clamp(result.forensic?.risk_score ?? result.ai_detection?.confidence ?? 50);
  const aiConf = getAiLikelihood();
  const tamper = clamp(result.tampering?.confidence);
  const privacy = result.face_detection?.faces_detected ? Math.min(100, 35 + Number(result.face_detection?.total_faces || 1) * 15) : 8;
  const captionConf = clamp(result.caption?.confidence);
  const authenticity = clamp(100 - Math.max(aiConf, tamper, risk * 0.78));

  const heroRisk = document.getElementById("heroRiskValue");
  if (heroRisk) animateValue(heroRisk, 0, risk, 1000);

  const timestamp = document.getElementById("caseTimestamp");
  if (timestamp) {
    timestamp.textContent = state.analyzedAt
      ? `Analyzed ${new Date(state.analyzedAt).toLocaleString()}`
      : "Analysis metadata loaded";
  }

  addScoreRing("Authenticity", authenticity, "safe");
  addScoreRing("Deepfake Probability", aiConf, aiConf > 60 ? "danger" : "warn");
  addScoreRing("Tampering Risk", tamper, tamper > 55 ? "danger" : "warn");
  addScoreRing("Privacy Risk", privacy, privacy > 45 ? "warn" : "safe");
  addScoreRing("AI Generation", aiConf, aiConf > 60 ? "danger" : "warn");

  const narrative = document.getElementById("reasoningNarrative");
  if (narrative) {
    const verdict = risk > 60 ? "high-risk evidence package" : risk > 30 ? "mixed-risk evidence package" : "low-risk evidence package";
    narrative.innerHTML = `
      <div class="reason-chip">Investigator summary</div>
      <p>This case is currently classified as a <strong>${verdict}</strong>. The system estimated AI generation likelihood at <strong>${aiConf.toFixed(1)}%</strong>, tampering confidence at <strong>${tamper.toFixed(1)}%</strong>, and caption confidence at <strong>${captionConf.toFixed(1)}%</strong>.</p>
      <p>Use the timeline and explainability panels to inspect suspicious timestamps before exporting the forensic brief.</p>
    `;
  }

  const explainability = document.getElementById("explainabilityText");
  if (explainability) {
    explainability.textContent = result.preview_path
      ? "Attention visualization is aligned with generated evidence snapshots and face privacy preview outputs."
      : "Heatmap placeholder generated from available confidence signals. Backend Grad-CAM assets can attach here without changing routes.";
  }

  const focus = document.getElementById("heatmapFocus");
  if (focus) {
    focus.style.left = `${18 + (aiConf % 52)}%`;
    focus.style.top = `${18 + (tamper % 42)}%`;
  }

  const waveform = document.getElementById("waveform");
  if (waveform) {
    waveform.innerHTML = Array.from({ length: 42 }, (_, i) => {
      const h = 18 + Math.abs(Math.sin(i * 0.55 + risk / 20)) * 62;
      return `<span style="height:${h.toFixed(0)}%"></span>`;
    }).join("");
  }

  const voiceScore = document.getElementById("voiceScore");
  if (voiceScore) voiceScore.textContent = result.audio?.voice_authenticity ? `${clamp(result.audio.voice_authenticity).toFixed(1)}%` : "No audio model";
  const lipSync = document.getElementById("lipSyncScore");
  if (lipSync) lipSync.textContent = result.audio?.lip_sync_mismatch ? `${clamp(result.audio.lip_sync_mismatch).toFixed(1)}%` : "Not detected";

  const legend = document.getElementById("objectLegend");
  if (legend) {
    const faceCount = result.face_detection?.total_faces || 0;
    legend.innerHTML = `
      <span><i class="legend-face"></i>${faceCount} face track${faceCount === 1 ? "" : "s"}</span>
      <span><i class="legend-object"></i>Object alerts attach to provider outputs</span>
      <span><i class="legend-alert"></i>${tamper > 55 ? "Suspicious motion/tamper signal" : "No dominant object alert"}</span>
    `;
  }
}

function addForensicDetail(label, value) {
  const wrap = document.getElementById("forensicsWrap");
  const node = document.createElement("div");
  node.className = "forensic-item";
  node.innerHTML = `
    <div class="forensic-label">${label}</div>
    <div class="forensic-value">${value}</div>
  `;
  wrap.appendChild(node);
}

function addSignal(label, value) {
  const wrap = document.getElementById("signalWrap");
  const node = document.createElement("div");
  node.className = "signal";
  node.innerHTML = `<label>${label}</label><strong>${value}</strong>`;
  wrap.appendChild(node);

  const index = wrap.children.length - 1;
  node.style.animationDelay = `${index * 0.1}s`;
}

function formatTime(seconds) {
  const s = Math.max(0, Number(seconds || 0));
  const mm = Math.floor(s / 60).toString().padStart(2, "0");
  const ss = Math.floor(s % 60).toString().padStart(2, "0");
  return `${mm}:${ss}`;
}

function addTimelineItem(item) {
  const wrap = document.getElementById("timelineWrap");
  const node = document.createElement("div");
  node.className = "timeline-item";
  node.innerHTML = `
    <div class="timeline-time">Shot ${item.shot} | ${formatTime(item.start_time)}-${formatTime(item.end_time)}</div>
    <div class="timeline-event">${item.event}</div>
    <div class="timeline-conf">Caption confidence: ${clamp(item.confidence).toFixed(2)}%</div>
  `;
  wrap.appendChild(node);

  const index = wrap.children.length - 1;
  node.style.animationDelay = `${index * 0.08}s`;

  // Click to jump to this timestamp
  node.addEventListener("click", () => {
    const video = document.getElementById("videoPreview");
    video.currentTime = item.start_time;
    video.play();
  });
}

function setupTimelineScrubber() {
  const video = document.getElementById("videoPreview");
  const timelineBar = document.getElementById("timelineBar");
  const eventMarkers = document.getElementById("eventMarkers");
  const timelineScrubber = document.querySelector(".timeline-scrubber");

  const shotEvents = result.shot_events || [];
  const metadata = result.metadata || {};
  videoDuration = metadata.duration || 0;

  // Create event markers
  shotEvents.forEach((event) => {
    if (videoDuration > 0) {
      const marker = document.createElement("div");
      marker.className = "event-marker";
      const percent = (event.start_time / videoDuration) * 100;
      marker.style.left = percent + "%";
      marker.title = event.event;
      marker.addEventListener("click", (e) => {
        e.stopPropagation();
        video.currentTime = event.start_time;
        video.play();
      });
      eventMarkers.appendChild(marker);
    }
  });

  // Update timeline bar on video progress
  video.addEventListener("timeupdate", () => {
    if (videoDuration > 0) {
      const percent = (video.currentTime / videoDuration) * 100;
      timelineBar.style.width = percent + "%";
    }
  });

  // Click on scrubber to seek
  timelineScrubber.addEventListener("click", (e) => {
    const rect = timelineScrubber.getBoundingClientRect();
    const percent = (e.clientX - rect.left) / rect.width;
    video.currentTime = percent * videoDuration;
  });
}

function exportAsJSON() {
  const exportData = {
    metadata: state,
    analysis: result,
    exportedAt: new Date().toISOString(),
  };
  const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `analysis_${new Date().getTime()}.json`;
  link.click();
  URL.revokeObjectURL(url);
}

async function exportAsPDF() {
  try {
    const response = await fetch("/api/export/pdf", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ data: result })
    });
    if (!response.ok) throw new Error("PDF service unavailable");
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `visionguard_report_${new Date().getTime()}.pdf`;
    link.click();
    URL.revokeObjectURL(url);
  } catch (_) {
    const content = `
VISIONGUARD AI - ANALYSIS REPORT
Generated: ${new Date().toISOString()}

VIDEO METADATA
File: ${state.fileName || 'Unknown'}
Size: ${state.fileSize ? (state.fileSize / (1024*1024)).toFixed(2) : 'N/A'} MB
SHA256: ${state.sha256 || 'N/A'}

AI GENERATION RESULTS
Status: ${deriveAiStatus()}
AI Likelihood: ${getAiLikelihood().toFixed(2)}%

FORENSIC SIGNALS
${Object.entries(result.ai_detection?.signals || {}).map(([k, v]) => `${k.replaceAll('_', ' ')}: ${v}`).join('\n')}

TAMPERING ANALYSIS
Type: ${result.tampering?.tampering_type || '-'}
Confidence: ${clamp(result.tampering?.confidence).toFixed(2)}%

FACE DETECTION
Detected: ${result.face_detection?.faces_detected ? 'Yes' : 'No'}
Total Faces: ${result.face_detection?.total_faces || 0}
Alert: ${result.face_detection?.alert || '-'}

CAPTION
${result.caption?.caption || '-'}

EVENT TIMELINE
${(result.shot_events || []).map(e => `Shot ${e.shot} [${formatTime(e.start_time)}-${formatTime(e.end_time)}]: ${e.event}`).join('\n')}
    `.trim();

    const blob = new Blob([content], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `analysis_${new Date().getTime()}.txt`;
    link.click();
    URL.revokeObjectURL(url);
  }
}

function setRiskBadge(riskScore) {
  const badge = document.getElementById("riskBadge");
  badge.classList.remove("risk-low", "risk-mid", "risk-high");
  if (riskScore < 30) {
    badge.classList.add("risk-low");
    badge.textContent = "Overall Risk: Low";
  } else if (riskScore < 60) {
    badge.classList.add("risk-mid");
    badge.textContent = "Overall Risk: Medium";
  } else {
    badge.classList.add("risk-high");
    badge.textContent = "Overall Risk: High";
  }
}

document.getElementById("videoPreview").src = state.videoUrl || "";

// ── Face-privacy canvas overlay ────────────────────────────────────────────
(function setupFaceOverlay() {
  const video   = document.getElementById("videoPreview");
  const canvas  = document.getElementById("faceOverlay");
  const ctx     = canvas.getContext("2d");
  const frames  = (result.face_frames || []).slice().sort((a, b) => a.timestamp - b.timestamp);

  if (!frames.length) return;   // no faces detected — nothing to draw

  function syncCanvas() {
    canvas.width  = video.videoWidth  || video.clientWidth;
    canvas.height = video.videoHeight || video.clientHeight;
  }

  video.addEventListener("loadedmetadata", syncCanvas);
  window.addEventListener("resize", syncCanvas);

  video.addEventListener("timeupdate", () => {
    const t = video.currentTime;

    // Find the face-frame entry whose timestamp is closest to current time.
    let nearest = frames[0];
    let minDiff = Math.abs(frames[0].timestamp - t);
    for (let i = 1; i < frames.length; i++) {
      const d = Math.abs(frames[i].timestamp - t);
      if (d < minDiff) { minDiff = d; nearest = frames[i]; }
    }

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Only draw if the nearest keyframe is within 1 second — avoids
    // drawing stale boxes in parts of the video with no detected faces.
    if (minDiff > 1.0) return;

    ctx.lineWidth = Math.max(2, canvas.width * 0.004);
    ctx.font = `${Math.max(12, canvas.width * 0.022)}px Manrope, sans-serif`;
    for (const f of nearest.faces) {
      const x = f.x_pct * canvas.width;
      const y = f.y_pct * canvas.height;
      const w = f.w_pct * canvas.width;
      const h = f.h_pct * canvas.height;
      ctx.strokeStyle = "rgba(76, 255, 194, 0.95)";
      ctx.fillStyle = "rgba(42, 212, 255, 0.12)";
      ctx.fillRect(x, y, w, h);
      ctx.strokeRect(x, y, w, h);
      ctx.fillStyle = "rgba(2, 10, 18, 0.86)";
      ctx.fillRect(x, Math.max(0, y - 28), Math.max(88, w * 0.6), 24);
      ctx.fillStyle = "#4cffc2";
      ctx.fillText("FACE TRACK", x + 8, Math.max(17, y - 10));
    }
  });

  // Also clear when paused / seeked to a position with no faces
  video.addEventListener("seeking", () => ctx.clearRect(0, 0, canvas.width, canvas.height));
})();
document.getElementById("videoPreview").addEventListener('error', (e) => {
  console.error('Video loading error:', e);
  // Only show the unavailable notice when there is genuinely no URL to load.
  if (!state.videoUrl) {
    const videoElement = document.getElementById("videoPreview");
    const notice = document.createElement("p");
    notice.style.color = "orange";
    notice.textContent = "Video preview unavailable.";
    videoElement.replaceWith(notice);
  }
});
document.getElementById("videoPreview").addEventListener('loadstart', () => {
  console.log('Video loading started');
});
document.getElementById("videoPreview").addEventListener('canplay', () => {
  console.log('Video can play');
});

document.getElementById("captionText").textContent = result.caption?.caption || "-";

const aiStatus = deriveAiStatus();
const aiConf   = getAiLikelihood().toFixed(2);
document.getElementById("aiStatus").textContent = `${aiStatus} (${aiConf}%)`;

// ── Reasons panel ──────────────────────────────────────────────────────────
const reasons = result.ai_detection?.reasons;
if (reasons) {
  document.getElementById("reasonsPanel").style.display = "";
  document.getElementById("reasonsSummary").textContent   = reasons.summary         || "";
  document.getElementById("reasonsAgreement").textContent = reasons.model_agreement || "";
  document.getElementById("reasonsFaceCtx").textContent   = reasons.face_context    || "";

  const makeItems = (list, ulId) => {
    const ul = document.getElementById(ulId);
    ul.innerHTML = (list && list.length)
      ? list.map(t => `<li>${escapeHtml(t)}</li>`).join("")
      : "<li style='color:var(--muted)'>None detected.</li>";
  };
  makeItems(reasons.ai_indicators,   "reasonsAiList");
  makeItems(reasons.real_indicators, "reasonsRealList");

  const topUl = document.getElementById("reasonsTopList");
  topUl.innerHTML = (reasons.top_factors && reasons.top_factors.length)
    ? reasons.top_factors.map(t => `<li>${escapeHtml(t)}</li>`).join("")
    : "<li style='color:var(--muted)'>No data.</li>";
}

document.getElementById("tamperingText").textContent = `${result.tampering?.tampering_type || "-"} (${clamp(result.tampering?.confidence).toFixed(2)}%)`;
document.getElementById("faceText").textContent = result.face_detection?.faces_detected
  ? `Faces detected (${result.face_detection?.total_faces || 0})`
  : "No faces detected";
document.getElementById("privacyAlert").textContent = result.face_detection?.alert || "-";

addBar("Caption", clamp(result.caption?.confidence));
addBar("AI Generation", getAiLikelihood());
addBar("Tampering", clamp(result.tampering?.confidence));
addBar("Face Detection", clamp(result.face_detection?.confidence));

const signals = result.ai_detection?.signals || {};

// Forensic Breakdown (inside Core Findings) is the single source of signal display.
// The standalone "Forensic Signals" panel is a duplicate — hide it.
const signalPanelEl = document.getElementById("signalWrap");
if (signalPanelEl) signalPanelEl.closest("article.panel").style.display = "none";

Object.entries(signals).forEach(([key, value]) => {
  addForensicDetail(key.replaceAll("_", " "), String(value));
});

const shotEvents = result.shot_events || [];
if (shotEvents.length) {
  shotEvents.forEach((s) => addTimelineItem(s));
} else {
  addTimelineItem({ shot: 1, start_time: 0, end_time: 0, event: "No shot events extracted.", confidence: 0 });
}

setRiskBadge(clamp(result.forensic?.risk_score ?? 50));
renderAdvancedDashboard();

if (result.preview_path) {
  const imgName = result.preview_path.split(/[\\/]/).pop();
  document.getElementById("blurPreview").src = `/results/${imgName}`;
}

document.getElementById("exportJSON").addEventListener("click", exportAsJSON);
document.getElementById("exportPDF").addEventListener("click", exportAsPDF);
document.getElementById("fullScreen").addEventListener("click", () => {
  const video = document.getElementById("videoPreview");
  if (video.requestFullscreen) {
    video.requestFullscreen();
  } else if (video.webkitRequestFullscreen) {
    video.webkitRequestFullscreen();
  } else if (video.mozRequestFullScreen) {
    video.mozRequestFullScreen();
  } else if (video.msRequestFullscreen) {
    video.msRequestFullscreen();
  } else {
    const container = video.parentElement;
    if (container.requestFullscreen) container.requestFullscreen();
    else if (container.webkitRequestFullscreen) container.webkitRequestFullscreen();
  }
});

document.getElementById("videoPreview").addEventListener("loadedmetadata", setupTimelineScrubber);

function initParticles() {
  const canvas = document.getElementById("particles");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const dpr = window.devicePixelRatio || 1;
  let stars = [];

  function resize() {
    canvas.width = Math.floor(window.innerWidth * dpr);
    canvas.height = Math.floor(window.innerHeight * dpr);
    canvas.style.width = `${window.innerWidth}px`;
    canvas.style.height = `${window.innerHeight}px`;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    stars = Array.from({ length: Math.max(28, Math.floor(window.innerWidth / 40)) }, () => ({
      x: Math.random() * window.innerWidth,
      y: Math.random() * window.innerHeight,
      s: 0.6 + Math.random() * 1.6,
      a: 0.2 + Math.random() * 0.5,
      t: Math.random() * Math.PI * 2
    }));
  }

  function draw() {
    ctx.clearRect(0, 0, window.innerWidth, window.innerHeight);
    for (const p of stars) {
      p.t += 0.02;
      const alpha = p.a + Math.sin(p.t) * 0.14;
      ctx.beginPath();
      ctx.fillStyle = `rgba(106, 212, 255, ${Math.max(0.1, alpha)})`;
      ctx.arc(p.x, p.y, p.s, 0, Math.PI * 2);
      ctx.fill();
    }
    requestAnimationFrame(draw);
  }

  resize();
  window.addEventListener("resize", resize);
  draw();
}

initParticles();

// ── Topbar user widget ─────────────────────────────────────────────────────
(async function loadTopbarUser() {
  try {
    const res = await fetch("/api/me");
    const data = await res.json();
    if (!data.authenticated) return;

    document.getElementById("historyNavLink").style.display = "";

    const wrap = document.getElementById("topbarUserWrap");
    if (!wrap) return;
    wrap.style.cssText = "display:flex;align-items:center;gap:8px;";

    if (data.picture) {
      const img = document.createElement("img");
      img.src = data.picture;
      img.alt = data.name || "";
      img.style.cssText = "width:28px;height:28px;border-radius:50%;object-fit:cover;border:2px solid var(--primary);";
      img.onerror = () => img.remove();
      wrap.appendChild(img);
    }

    const nameSpan = document.createElement("span");
    nameSpan.textContent = (data.name || data.email || "").split(" ")[0];
    nameSpan.style.cssText = "font-size:0.85rem;font-weight:600;color:var(--ink);max-width:100px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;";
    wrap.appendChild(nameSpan);
  } catch (_) {}
})();
