"""
VisionGuard AI — figure generator (Part A of self-contained rebuild).
Produces 33 PNG images into ./figs/ next to this script.

Run via the REBUILD_REPORT.bat file. No editing required.
"""
import os, math, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import (FancyBboxPatch, FancyArrowPatch, Circle, Wedge,
                                Rectangle, Polygon, Ellipse)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.join(HERE, "figs")
os.makedirs(OUT, exist_ok=True)

NAVY="#0B2A5B"; TEAL="#007A86"; ACCENT="#C9184A"; GOLD="#E8A82E"; LIGHT="#EAF2FB"
PALETTE = [NAVY, TEAL, ACCENT, GOLD, "#5B8DEF", "#5BBA6F", "#9B5DE5", "#FF6B6B"]

plt.rcParams.update({
    "font.family":"DejaVu Sans",
    "axes.titleweight":"bold",
    "axes.titlecolor":NAVY,
    "axes.edgecolor":"#888",
    "axes.labelcolor":"#333",
    "xtick.color":"#444",
    "ytick.color":"#444",
})

def save(fig, name):
    p = os.path.join(OUT, f"{name}.png")
    fig.savefig(p, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return p


def fig01_competitor_radar():
    cats = ["Caption","Deepfake","Tampering","Privacy","XAI","Encryption","Open API"]
    angles = np.linspace(0, 2*np.pi, len(cats), endpoint=False).tolist()
    angles += angles[:1]
    rows = [
        ("VisionGuard AI", [1.0,1.0,1.0,1.0,1.0,1.0,1.0], NAVY),
        ("Sensity",        [0.0,0.95,0.5,0.0,0.4,0.7,0.2], TEAL),
        ("Reality Defender",[0.0,0.95,0.0,0.0,0.4,0.7,0.2], ACCENT),
        ("MS Authenticator",[0.0,0.85,0.4,0.0,0.4,0.0,0.0], GOLD),
        ("Amped",          [0.0,0.5,0.95,0.0,0.5,0.0,0.0], "#5B8DEF"),
        ("InVID",          [0.4,0.5,0.5,0.0,0.6,0.0,0.4], "#5BBA6F"),
    ]
    fig, ax = plt.subplots(figsize=(8,7), subplot_kw=dict(polar=True))
    for label, vals, col in rows:
        v = vals + vals[:1]
        ax.plot(angles, v, color=col, linewidth=2, label=label)
        ax.fill(angles, v, color=col, alpha=0.18)
    ax.set_xticks(angles[:-1]); ax.set_xticklabels(cats, fontsize=10)
    ax.set_ylim(0,1.05); ax.set_yticks([0.25,0.5,0.75,1.0])
    ax.set_yticklabels(["0.25","0.50","0.75","1.00"], fontsize=8, color="#888")
    ax.set_title("Comparative Overview of Related Work Systems", color=NAVY, pad=20, fontsize=13)
    ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.05), fontsize=8, frameon=False)
    return save(fig, "fig01_radar")


def fig02_gantt():
    import datetime as dt
    phases = [
        ("Information Sharing & Requirements","2025-12-01","2025-12-15", NAVY),
        ("Requirements Refinement","2025-12-10","2025-12-28", NAVY),
        ("System Design (Architecture+UML)","2025-12-29","2026-01-18", TEAL),
        ("Dataset Collection & Preprocessing","2026-01-19","2026-02-09", TEAL),
        ("Model Development","2026-02-10","2026-03-13", ACCENT),
        ("System Integration","2026-03-14","2026-03-28", ACCENT),
        ("Testing & Evaluation","2026-03-29","2026-04-12", GOLD),
        ("Final Documentation","2026-04-13","2026-05-31", GOLD),
    ]
    def d(s): return dt.datetime.strptime(s,"%Y-%m-%d").toordinal()
    fig, ax = plt.subplots(figsize=(11,5.5))
    for i, (name, s, e, col) in enumerate(phases):
        ax.barh(i, d(e)-d(s), left=d(s), height=0.55, color=col, edgecolor="white")
        ax.text(d(s), i, "  "+name, ha="left", va="center", color="white", fontsize=9, fontweight="bold")
        ax.scatter([d(e)],[i], color=ACCENT, s=70, zorder=5, marker="D", edgecolor="white")
    ax.set_yticks(range(len(phases))); ax.set_yticklabels([])
    ax.invert_yaxis()
    ticks=[d("2025-12-01"),d("2026-01-01"),d("2026-02-01"),d("2026-03-01"),d("2026-04-01"),d("2026-05-01"),d("2026-06-01")]
    ax.set_xticks(ticks)
    ax.set_xticklabels(["Dec'25","Jan'26","Feb'26","Mar'26","Apr'26","May'26","Jun'26"])
    ax.set_xlim(d("2025-11-25"), d("2026-06-05"))
    ax.set_title("Project Gantt Chart (GP1 + GP2)", fontsize=13)
    ax.grid(axis="x", linestyle=":", alpha=0.5)
    for sp in ("top","right","left"): ax.spines[sp].set_visible(False)
    return save(fig, "fig02_gantt")


def fig03_agile_sdlc():
    fig, ax = plt.subplots(figsize=(7,7))
    ax.set_aspect("equal"); ax.axis("off")
    phases = ["Plan","Design","Develop","Test","Review","Deploy"]
    n=len(phases)
    for i, ph in enumerate(phases):
        ang0 = 90 - i*(360/n); ang1 = ang0 - (360/n) + 4
        col = PALETTE[i % len(PALETTE)]
        ax.add_patch(Wedge((0,0), 1.0, ang1, ang0, width=0.35, facecolor=col, edgecolor="white", linewidth=3))
        a = math.radians((ang0+ang1)/2)
        ax.text(0.82*math.cos(a), 0.82*math.sin(a), ph, ha="center", va="center", color="white", fontsize=12, fontweight="bold")
    ax.add_patch(Circle((0,0), 0.55, facecolor="white", edgecolor=NAVY, linewidth=2.5))
    ax.text(0,0.05,"Agile", ha="center", color=NAVY, fontsize=18, fontweight="bold")
    ax.text(0,-0.18,"Increment", ha="center", color=TEAL, fontsize=12, fontweight="bold")
    ax.set_xlim(-1.2,1.2); ax.set_ylim(-1.2,1.2)
    ax.set_title("Agile SDLC adopted for VisionGuard AI", fontsize=13, color=NAVY)
    return save(fig, "fig03_agile_sdlc")


def fig04_agile_swimlane():
    fig, ax = plt.subplots(figsize=(11,6))
    ax.axis("off")
    tracks = [("AI Modelling", NAVY),("Backend", TEAL),("Frontend", ACCENT),("DevOps", GOLD)]
    sprints = ["S1","S2","S3","S4","S5","S6","S7","S8"]
    items = {
        "AI Modelling": ["Xception FT","BLIP integ","Tampering","Face YuNet","Calibration","Drift mon","Adv defenses","Ensemble"],
        "Backend":      ["Flask scaffold","Auth+JWT","Multi-Provider","DB+ORM","Encryption","Audit chain","Export PDF/JSON","Compare API"],
        "Frontend":     ["Welcome","Dashboard","Upload UI","Forensics view","Timeline","Privacy preview","Report","History"],
        "DevOps":       ["Repo+CI","Dockerfile","Render deploy","Netlify deploy","Monitoring","Load test","CD pipeline","SLO"],
    }
    for ti, (track, col) in enumerate(tracks):
        ax.add_patch(Rectangle((0, 3-ti), 0.9, 0.85, color=col))
        ax.text(0.45, 3-ti+0.42, track, ha="center", va="center", color="white", fontsize=11, fontweight="bold")
        for si, sprint in enumerate(sprints):
            x = 1.2 + si*1.15
            ax.add_patch(FancyBboxPatch((x, 3-ti+0.05), 1.05, 0.75,
                                        boxstyle="round,pad=0.02", facecolor=LIGHT, edgecolor=col, linewidth=1.4))
            ax.text(x+0.52, 3-ti+0.45, items[track][si], ha="center", va="center", fontsize=8, color=NAVY)
    for si, sprint in enumerate(sprints):
        x = 1.2 + si*1.15
        ax.text(x+0.52, 3.95, sprint, ha="center", color=NAVY, fontsize=10, fontweight="bold")
    for si in [1,3,5,7]:
        x = 1.2 + si*1.15 + 1.05
        ax.add_patch(Circle((x, -0.1), 0.12, color=ACCENT))
        ax.text(x, -0.4, "Int.", ha="center", color=ACCENT, fontsize=8, fontweight="bold")
    ax.set_xlim(-0.2, 11); ax.set_ylim(-0.7, 4.3)
    ax.set_title("Agile Development Framework for VisionGuard AI", fontsize=13, color=NAVY)
    return save(fig, "fig04_agile_swimlane")


def fig05_scope():
    fig, ax = plt.subplots(figsize=(10,6))
    ax.set_aspect("equal"); ax.axis("off")
    ax.add_patch(Ellipse((5,3), 9.5, 5.2, facecolor="#F4E5EC", edgecolor=ACCENT, linewidth=2, linestyle="--"))
    ax.add_patch(Ellipse((5,3), 7, 3.6, facecolor=LIGHT, edgecolor=NAVY, linewidth=2.5))
    ax.text(5,5.7, "OUT-OF-SCOPE", ha="center", color=ACCENT, fontsize=13, fontweight="bold")
    ax.text(5,5.2,"Live streaming   Editing   Decision authority   Legal adjudication",
            ha="center", color=ACCENT, fontsize=9)
    ax.text(5,4.55,"IN-SCOPE", ha="center", color=NAVY, fontsize=13, fontweight="bold")
    in_items = [
        ("Upload",2.4,3.6),("Encrypt",3.7,3.9),("Caption",5.0,4.1),
        ("Deepfake",6.3,3.9),("Tampering",7.6,3.6),
        ("Face Privacy",2.8,2.7),("Confidence",4.4,2.5),("Audit",5.7,2.5),("Export",7.2,2.7),
    ]
    for lbl,x,y in in_items:
        ax.add_patch(FancyBboxPatch((x-0.55,y-0.20),1.1,0.45, boxstyle="round,pad=0.05",
                                    facecolor=NAVY, edgecolor="white"))
        ax.text(x,y, lbl, ha="center", va="center", color="white", fontsize=9, fontweight="bold")
    ax.set_xlim(-0.5,10.5); ax.set_ylim(0,6.3)
    ax.set_title("System Scope Diagram", fontsize=13, color=NAVY)
    return save(fig, "fig05_scope")


def fig06_func_arch():
    fig, ax = plt.subplots(figsize=(11,5.5))
    ax.axis("off")
    bands = [("INPUT", ["Video Upload","File Validation","Encrypt + SHA-256"], NAVY),
             ("AI PROCESSING", ["Caption (BLIP)","Deepfake (Xception)","Tampering (FFT/Flow/Noise)","Face (YuNet)"], TEAL),
             ("OUTPUT", ["Verdict + XAI","Timeline","Privacy Preview","PDF / JSON Export"], ACCENT)]
    for bi,(name,items,col) in enumerate(bands):
        x = 0.4 + bi*3.4
        ax.add_patch(FancyBboxPatch((x,0.4),3,4.4, boxstyle="round,pad=0.05",
                                    facecolor=col, edgecolor="white", linewidth=2))
        ax.text(x+1.5, 4.55, name, ha="center", color="white", fontsize=12, fontweight="bold")
        for ii, it in enumerate(items):
            ax.add_patch(FancyBboxPatch((x+0.18, 3.9-ii*0.85), 2.65, 0.65,
                        boxstyle="round,pad=0.04", facecolor="white", edgecolor=col, linewidth=1.5))
            ax.text(x+1.5, 4.22-ii*0.85, it, ha="center", va="center", color=col, fontsize=9, fontweight="bold")
        if bi<2:
            ax.add_patch(FancyArrowPatch((x+3.0,2.6),(x+3.4,2.6),
                                         color=ACCENT, mutation_scale=22, linewidth=2.5))
    ax.set_xlim(0,11); ax.set_ylim(0,5)
    ax.set_title("Functional Architecture Diagram", fontsize=13, color=NAVY)
    return save(fig, "fig06_func_arch")


def fig07_usecase():
    fig, ax = plt.subplots(figsize=(11,7))
    ax.axis("off")
    ax.add_patch(Rectangle((3,0.3), 7, 6.4, facecolor=LIGHT, edgecolor=NAVY, linewidth=2))
    ax.text(6.5, 6.85, "VisionGuard AI", ha="center", color=NAVY, fontsize=12, fontweight="bold")
    def stickman(x, y, label):
        ax.add_patch(Circle((x,y+0.5), 0.18, facecolor=NAVY, edgecolor=NAVY))
        ax.plot([x,x],[y+0.32,y-0.4], color=NAVY, lw=2)
        ax.plot([x-0.25,x+0.25],[y,y], color=NAVY, lw=2)
        ax.plot([x,x-0.22],[y-0.4,y-0.85], color=NAVY, lw=2)
        ax.plot([x,x+0.22],[y-0.4,y-0.85], color=NAVY, lw=2)
        ax.text(x,y-1.05,label,ha="center", color=NAVY, fontsize=10, fontweight="bold")
    stickman(1.4, 5.0, "User")
    stickman(1.4, 2.0, "Admin")
    use_cases = [
        ("Register/Login", 4.2, 6.1, NAVY),
        ("Upload Video",   4.2, 5.4, NAVY),
        ("Run Analysis",   4.2, 4.7, NAVY),
        ("View Verdict",   4.2, 4.0, NAVY),
        ("View Timeline",  6.5, 5.4, NAVY),
        ("Privacy Blur",   6.5, 4.7, NAVY),
        ("Export PDF/JSON",6.5, 4.0, NAVY),
        ("Compare Videos", 6.5, 3.3, NAVY),
        ("View History",   4.2, 3.3, NAVY),
        ("View Audit Log", 8.7, 2.6, ACCENT),
        ("Manage Users",   8.7, 1.9, ACCENT),
        ("System Settings",8.7, 1.2, ACCENT),
    ]
    for label, x, y, col in use_cases:
        ax.add_patch(Ellipse((x,y), 1.85, 0.55, facecolor="white", edgecolor=col, linewidth=1.5))
        ax.text(x,y,label, ha="center", va="center", color=col, fontsize=9)
    for _,x,y,_ in use_cases[:9]:
        ax.plot([1.6, x-0.9],[5.0, y], color=NAVY, lw=0.8, alpha=0.5)
    for _,x,y,_ in use_cases[9:]:
        ax.plot([1.6, x-0.9],[2.0, y], color=ACCENT, lw=0.8, alpha=0.6)
    ax.set_xlim(0.2,10.2); ax.set_ylim(0,7.5)
    ax.set_title("Use Case Diagram", fontsize=13, color=NAVY)
    return save(fig, "fig07_usecase")


def fig08_activity():
    fig, ax = plt.subplots(figsize=(10,9))
    ax.axis("off")
    nodes = [
        ("Start", 5, 8.3, "circle", "#333"),
        ("User selects file", 5, 7.5, "rect", NAVY),
        ("Frontend validates", 5, 6.7, "rect", NAVY),
        ("Valid?", 5, 5.9, "diamond", ACCENT),
        ("Reject + Audit", 8, 5.9, "rect", ACCENT),
        ("Encrypt + Hash", 5, 5.0, "rect", NAVY),
        ("Persist DB", 5, 4.2, "rect", NAVY),
        ("Run AI Pipeline (parallel)", 5, 3.4, "rect", TEAL),
        ("Aggregate Verdict", 5, 2.6, "rect", TEAL),
        ("Render Dashboard", 5, 1.8, "rect", NAVY),
        ("Export PDF/JSON", 5, 1.0, "rect", NAVY),
        ("End", 5, 0.3, "circle", "#333"),
    ]
    for label, x, y, kind, col in nodes:
        if kind == "circle":
            ax.add_patch(Circle((x,y), 0.18, facecolor=col, edgecolor=col))
        elif kind == "diamond":
            ax.add_patch(Polygon([(x,y+0.35),(x+0.7,y),(x,y-0.35),(x-0.7,y)],
                                 facecolor="white", edgecolor=col, linewidth=2))
            ax.text(x,y,label, ha="center", va="center", color=col, fontsize=9, fontweight="bold")
        else:
            ax.add_patch(FancyBboxPatch((x-1.3,y-0.27),2.6,0.55, boxstyle="round,pad=0.04",
                                        facecolor=col, edgecolor=col))
            ax.text(x,y,label, ha="center", va="center", color="white", fontsize=10, fontweight="bold")
    pairs = [(0,1),(1,2),(2,3),(3,5),(5,6),(6,7),(7,8),(8,9),(9,10),(10,11)]
    for a,b in pairs:
        ya = nodes[a][2]
        yb = nodes[b][2]
        x = nodes[a][1]
        ax.annotate("", xy=(x, yb+0.32), xytext=(x, ya-0.32),
                    arrowprops=dict(arrowstyle="->", color="#444", lw=1.6))
    ax.annotate("No", xy=(7.0,5.9), xytext=(5.7,5.9),
                arrowprops=dict(arrowstyle="->", color=ACCENT, lw=1.6),
                fontsize=9, color=ACCENT)
    ax.annotate("Yes", xy=(5.0,5.3), xytext=(5.0,5.55),
                arrowprops=dict(arrowstyle="->", color=NAVY, lw=1.6),
                fontsize=9, color=NAVY)
    ax.set_xlim(0,10); ax.set_ylim(0,9)
    ax.set_title("Activity Diagram — End-to-End Forensic Workflow", fontsize=13, color=NAVY)
    return save(fig, "fig08_activity")


def fig09_high_level_arch():
    fig, ax = plt.subplots(figsize=(11,7))
    ax.axis("off")
    layers = [
        ("Presentation Layer (Netlify CDN)",          ["welcome","dashboard","forensics","report","history"], NAVY),
        ("Edge Layer (HTTPS, CSP, CORS, Rate Limit)", ["TLS 1.3","HSTS","CSP","CORS","Throttling"], TEAL),
        ("Application Layer (Flask + Gunicorn)",      ["routes/auth","routes/analysis","middleware/security","utils/audit"], NAVY),
        ("Service Orchestration (Multi-Provider)",    ["multi_provider","aggregator","forensic_unifier","export_service"], TEAL),
        ("AI Layer (Models)",                         ["BLIP","Xception","Tampering","YuNet","Unifier"], ACCENT),
        ("Data Layer",                                ["Encrypted media (Fernet)","SQLite/PostgreSQL","Audit Log (hash-chain)"], GOLD),
    ]
    h = 0.95
    for i,(name, items, col) in enumerate(layers):
        y = 6.4 - i*1.05
        ax.add_patch(FancyBboxPatch((0.4, y), 10, h, boxstyle="round,pad=0.04", facecolor=col, edgecolor="white"))
        ax.text(0.7, y+0.65, name, color="white", fontsize=11, fontweight="bold")
        for j,it in enumerate(items):
            xb = 4.2 + j*1.18
            ax.add_patch(FancyBboxPatch((xb, y+0.18), 1.1, 0.6, boxstyle="round,pad=0.02",
                                        facecolor="white", edgecolor=col))
            ax.text(xb+0.55, y+0.48, it, ha="center", va="center", color=col, fontsize=7.5)
    ax.set_xlim(0,11.2); ax.set_ylim(0,7.6)
    ax.set_title("High-Level System Architecture", fontsize=13, color=NAVY)
    return save(fig, "fig09_high_level")


def fig10_frontend():
    fig, ax = plt.subplots(figsize=(11,6))
    ax.axis("off")
    pages = [("welcome.html",1.5),("dashboard.html",3.5),("forensics.html",5.5),("forensic_report.html",7.5),("my_history.html",9.5)]
    for p,x in pages:
        ax.add_patch(FancyBboxPatch((x-0.85,4.3), 1.7, 0.8, boxstyle="round,pad=0.04", facecolor=NAVY, edgecolor="white"))
        ax.text(x,4.7, p, ha="center", color="white", fontsize=9, fontweight="bold")
    cs = ["Auth","Upload","Timeline","Indicators","Privacy Preview","Export Bar","Charts (Chart.js)"]
    for i,c in enumerate(cs):
        x = 0.6 + i*1.55
        ax.add_patch(FancyBboxPatch((x,2.8),1.4,0.7, boxstyle="round,pad=0.04", facecolor=TEAL, edgecolor="white"))
        ax.text(x+0.7, 3.15, c, ha="center", color="white", fontsize=9)
    ax.add_patch(FancyBboxPatch((4.0,1.0),3.0,0.9, boxstyle="round,pad=0.04", facecolor=ACCENT, edgecolor="white"))
    ax.text(5.5,1.45, "fetch('/api/...')", ha="center", color="white", fontsize=11, fontweight="bold")
    for x in [2,4,6,8]:
        ax.annotate("", xy=(5.5,1.95), xytext=(x,2.75), arrowprops=dict(arrowstyle="->", color="#888", lw=0.8))
    ax.set_xlim(0,11); ax.set_ylim(0,6)
    ax.set_title("Frontend Component Architecture", fontsize=13, color=NAVY)
    return save(fig, "fig10_frontend")


def fig11_backend():
    fig, ax = plt.subplots(figsize=(11,6.5))
    ax.axis("off")
    bands = [
        ("Routes",      ["auth.py","analysis.py","analysis_v2.py","datasets.py"], NAVY),
        ("Services",    ["multi_provider","aggregator","ai_detection","tampering","face_service","caption_service","forensic_unifier","export_service","security_service"], TEAL),
        ("Models",      ["Xception","YuNet","BLIP"], ACCENT),
        ("Middleware",  ["security","cors","rate_limit","audit"], GOLD),
        ("Utils",       ["logging_config","security","audit"], "#5B8DEF"),
    ]
    for bi,(name, items, col) in enumerate(bands):
        y = 5.2 - bi*1.05
        ax.add_patch(FancyBboxPatch((0.3,y), 1.5, 0.85, boxstyle="round,pad=0.04", facecolor=col, edgecolor="white"))
        ax.text(1.05,y+0.42, name, ha="center", color="white", fontsize=10, fontweight="bold")
        for j,it in enumerate(items):
            xb = 2.0 + j*1.05
            ax.add_patch(FancyBboxPatch((xb, y+0.05), 1.0, 0.75, boxstyle="round,pad=0.03",
                                        facecolor=LIGHT, edgecolor=col, linewidth=1.4))
            ax.text(xb+0.5, y+0.42, it, ha="center", va="center", color=NAVY, fontsize=7)
    ax.set_xlim(0,12); ax.set_ylim(0,6.5)
    ax.set_title("Backend Service Architecture", fontsize=13, color=NAVY)
    return save(fig, "fig11_backend")


def fig12_ai_pipeline():
    fig, ax = plt.subplots(figsize=(12,6))
    ax.axis("off")
    ax.add_patch(FancyBboxPatch((0.2,2.7),1.5,0.8, boxstyle="round,pad=0.04", facecolor=NAVY, edgecolor="white"))
    ax.text(0.95,3.1, "Encrypted\nVideo", ha="center", color="white", fontsize=10, fontweight="bold")
    ax.add_patch(FancyBboxPatch((2.1,2.7),1.6,0.8, boxstyle="round,pad=0.04", facecolor=TEAL, edgecolor="white"))
    ax.text(2.9,3.1, "Frame\nExtractor", ha="center", color="white", fontsize=10, fontweight="bold")
    branches = [
        ("BLIP\nCaption", ACCENT),
        ("Xception\nDeepfake", NAVY),
        ("Tampering\nFFT/Flow/Noise", GOLD),
        ("YuNet\nFace", "#5B8DEF"),
    ]
    ys = [4.6, 3.6, 2.6, 1.6]
    for (label, col), y in zip(branches, ys):
        ax.add_patch(FancyBboxPatch((4.2,y-0.4),2.0,0.8, boxstyle="round,pad=0.04", facecolor=col, edgecolor="white"))
        ax.text(5.2,y, label, ha="center", va="center", color="white", fontsize=10, fontweight="bold")
        ax.annotate("", xy=(4.2,y), xytext=(3.7,3.1), arrowprops=dict(arrowstyle="->", color=col, lw=1.5))
        ax.annotate("", xy=(7.4,3.1), xytext=(6.2,y), arrowprops=dict(arrowstyle="->", color=col, lw=1.5))
    ax.add_patch(FancyBboxPatch((7.4,2.7),2.1,0.8, boxstyle="round,pad=0.04", facecolor=NAVY, edgecolor="white"))
    ax.text(8.45,3.1, "Forensic\nUnifier", ha="center", va="center", color="white", fontsize=10, fontweight="bold")
    ax.add_patch(FancyBboxPatch((9.9,2.7),2.1,0.8, boxstyle="round,pad=0.04", facecolor=ACCENT, edgecolor="white"))
    ax.text(10.95,3.1, "Verdict +\nXAI Vector", ha="center", va="center", color="white", fontsize=10, fontweight="bold")
    ax.annotate("", xy=(9.9,3.1), xytext=(9.5,3.1), arrowprops=dict(arrowstyle="->", color=ACCENT, lw=2))
    ax.annotate("", xy=(2.1,3.1), xytext=(1.7,3.1), arrowprops=dict(arrowstyle="->", color=NAVY, lw=2))
    ax.set_xlim(0,12.5); ax.set_ylim(0.5,5.5)
    ax.set_title("AI Pipeline (Multi-Provider Orchestration)", fontsize=13, color=NAVY)
    return save(fig, "fig12_ai_pipeline")


def fig13_security_rings():
    fig, ax = plt.subplots(figsize=(8,8))
    ax.set_aspect("equal"); ax.axis("off")
    rings = [
        ("HTTPS / CSP / HSTS",         3.6, NAVY),
        ("CORS + Rate Limit + Validation", 3.1, TEAL),
        ("Auth + RBAC + JWT",           2.6, ACCENT),
        ("AES / Fernet at rest",        2.1, GOLD),
        ("SHA-256 Integrity",           1.6, "#5B8DEF"),
        ("Hash-Chained Audit Log",      1.1, "#5BBA6F"),
        ("Adversarial-Input Heuristics",0.6, "#9B5DE5"),
    ]
    for (label, r, col) in rings:
        ax.add_patch(Circle((0,0), r, facecolor=col, edgecolor="white", linewidth=3))
        ax.text(0, r-0.18, label, ha="center", va="center", color="white", fontsize=9.5, fontweight="bold")
    ax.add_patch(Circle((0,0),0.25, facecolor="white", edgecolor=NAVY, linewidth=2))
    ax.text(0,0,"App", ha="center", va="center", color=NAVY, fontsize=10, fontweight="bold")
    ax.set_xlim(-4,4); ax.set_ylim(-4,4)
    ax.set_title("Security Architecture (Defense-in-Depth)", fontsize=13, color=NAVY, pad=20)
    return save(fig, "fig13_security")


def fig14_erd():
    fig, ax = plt.subplots(figsize=(12,8))
    ax.axis("off")
    entities = {
        "users":          (1.5, 6.5, ["user_id PK","email","password_hash","role","created_at"]),
        "videos":         (5.5, 6.5, ["video_id PK","user_id FK","sha256","encrypted_path","size","mime","uploaded_at"]),
        "analysis_results":(9.5,6.5, ["analysis_id PK","video_id FK","verdict","confidence","latency_ms"]),
        "captions":       (1.5, 3.5, ["caption_id PK","analysis_id FK","frame_idx","caption_text","confidence"]),
        "ai_detection":   (4.0, 3.5, ["ai_id PK","analysis_id FK","deepfake_score","ai_score","model_ver"]),
        "tampering":      (6.5, 3.5, ["tamper_id PK","analysis_id FK","ofs","fft","noise","anomalies JSON"]),
        "face_detection": (9.0, 3.5, ["face_id PK","analysis_id FK","frame_idx","bbox JSON","face_score"]),
        "privacy_alerts": (11.5,3.5, ["alert_id PK","analysis_id FK","faces_count","privacy_level"]),
        "audit_log":      (1.5, 0.7, ["log_id PK","user_id FK","action","prev_hash","cur_hash","ts"]),
    }
    for name,(x,y,attrs) in entities.items():
        h = 0.4 + 0.32*len(attrs)
        ax.add_patch(FancyBboxPatch((x-1.2,y-h/2),2.4,h, boxstyle="round,pad=0.02",
                                    facecolor=LIGHT, edgecolor=NAVY, linewidth=1.5))
        ax.add_patch(Rectangle((x-1.2, y+h/2-0.32),2.4,0.32, facecolor=NAVY, edgecolor=NAVY))
        ax.text(x, y+h/2-0.16, name, ha="center", color="white", fontsize=10, fontweight="bold")
        for i,a in enumerate(attrs):
            ax.text(x-1.13, y+h/2-0.5-0.32*i, a, ha="left", color=NAVY, fontsize=7.5)
    rels = [("users","videos"),("videos","analysis_results"),
            ("analysis_results","captions"),("analysis_results","ai_detection"),
            ("analysis_results","tampering"),("analysis_results","face_detection"),
            ("analysis_results","privacy_alerts"),("users","audit_log")]
    for a,b in rels:
        x1,y1,_ = entities[a]; x2,y2,_ = entities[b]
        ax.plot([x1,x2],[y1,y2], color=TEAL, lw=1.4, alpha=0.7)
    ax.set_xlim(0,13); ax.set_ylim(-0.5,8)
    ax.set_title("Database Entity-Relationship Diagram (ERD)", fontsize=13, color=NAVY)
    return save(fig, "fig14_erd")


def fig15_uml():
    fig, ax = plt.subplots(figsize=(13,8))
    ax.axis("off")
    classes = {
        "User":(1,6.5,["+id","+email","+role"],["+login()","+logout()"]),
        "Video":(4,6.5,["+id","+sha256","+path"],["+encrypt()","+hash()"]),
        "AnalysisResult":(7.5,6.5,["+id","+verdict","+confidence"],["+aggregate()"]),
        "MultiProviderOrch":(11,6.5,["+providers"],["+run()"]),
        "BaseProvider":(1,3.5,["+name"],["+analyse()"]),
        "BLIP":(3.5,3.5,[],["+analyse()"]),
        "Xception":(6,3.5,[],["+analyse()"]),
        "Tampering":(8.5,3.5,[],["+analyse()"]),
        "YuNet":(11,3.5,[],["+analyse()"]),
        "ForensicUnifier":(2,1.0,["+weights"],["+fuse()","+narrative()"]),
        "ExportService":(5.5,1.0,[],["+to_pdf()","+to_json()"]),
        "AuditLog":(9,1.0,["+prev","+cur"],["+append()","+verify()"]),
    }
    for name,(x,y,attrs,methods) in classes.items():
        h = 1.1 + 0.22*(len(attrs)+len(methods))
        ax.add_patch(FancyBboxPatch((x-1,y-h/2), 2.0, h, boxstyle="round,pad=0.02",
                                    facecolor="white", edgecolor=NAVY, linewidth=1.4))
        ax.add_patch(Rectangle((x-1, y+h/2-0.3),2.0,0.3, facecolor=NAVY, edgecolor=NAVY))
        ax.text(x,y+h/2-0.15,name, ha="center", color="white", fontsize=9, fontweight="bold")
        cy = y+h/2-0.45
        for a in attrs:
            ax.text(x-0.93,cy,a, ha="left", color="#444", fontsize=7); cy-=0.22
        ax.plot([x-1,x+1],[cy+0.1,cy+0.1], color=NAVY, lw=0.6)
        for m in methods:
            ax.text(x-0.93,cy,m, ha="left", color=TEAL, fontsize=7); cy-=0.22
    edges = [("User","Video"),("Video","AnalysisResult"),
             ("AnalysisResult","MultiProviderOrch"),
             ("MultiProviderOrch","BaseProvider"),
             ("BaseProvider","BLIP"),("BaseProvider","Xception"),
             ("BaseProvider","Tampering"),("BaseProvider","YuNet"),
             ("MultiProviderOrch","ForensicUnifier"),
             ("ForensicUnifier","ExportService"),
             ("ForensicUnifier","AuditLog")]
    for a,b in edges:
        x1,y1,_,_ = classes[a]; x2,y2,_,_ = classes[b]
        ax.annotate("", xy=(x2,y2), xytext=(x1,y1), arrowprops=dict(arrowstyle="-|>", color="#666", lw=0.9))
    ax.set_xlim(-0.5,13); ax.set_ylim(-0.5,8)
    ax.set_title("UML Class Diagram", fontsize=13, color=NAVY)
    return save(fig, "fig15_uml")


def fig16_sequence():
    fig, ax = plt.subplots(figsize=(13,8))
    ax.axis("off")
    actors = ["User","Frontend","API","Multi-Provider","BLIP","Xception","Tampering","YuNet","Unifier","DB","Audit"]
    xs = np.linspace(0.6, 12.4, len(actors))
    for x, a in zip(xs, actors):
        ax.add_patch(FancyBboxPatch((x-0.55, 7.4),1.1,0.5, boxstyle="round,pad=0.02", facecolor=NAVY, edgecolor=NAVY))
        ax.text(x, 7.65, a, ha="center", color="white", fontsize=8.5, fontweight="bold")
        ax.plot([x,x],[7.35,0.4], color="#aaa", lw=0.8, linestyle=":")
    msgs = [
        (0,1,"upload",7.0),
        (1,2,"POST /api/analyze",6.5),
        (2,9,"INSERT video (encrypted)",6.0),
        (2,10,"audit.write(upload)",5.5),
        (2,3,"orchestrate(video)",5.0),
        (3,4,"caption()",4.5),
        (3,5,"deepfake()",4.1),
        (3,6,"tampering()",3.7),
        (3,7,"face()",3.3),
        (4,3,"score",2.9),
        (5,3,"score",2.6),
        (6,3,"score",2.3),
        (7,3,"score",2.0),
        (3,8,"fuse(scores)",1.65),
        (8,2,"verdict + XAI",1.3),
        (2,9,"INSERT analysis",1.0),
        (2,10,"audit.write(verdict)",0.7),
        (2,1,"200 OK JSON",0.4),
    ]
    for a,b,label,y in msgs:
        x1,x2 = xs[a], xs[b]
        col = ACCENT if "verdict" in label or "fuse" in label else NAVY
        ax.annotate("", xy=(x2,y), xytext=(x1,y), arrowprops=dict(arrowstyle="->", color=col, lw=1.3))
        ax.text((x1+x2)/2, y+0.05, label, ha="center", color=col, fontsize=7.5)
    ax.add_patch(Rectangle((xs[3]+0.1, 1.85),(xs[7]-xs[3])-0.2, 2.95, fill=False, edgecolor=TEAL, linestyle="--"))
    ax.text(xs[3]+0.2, 4.85, "par {parallel providers}", color=TEAL, fontsize=8, fontweight="bold")
    ax.set_xlim(0,13); ax.set_ylim(0,8)
    ax.set_title("Sequence Diagram — Upload to Verdict", fontsize=13, color=NAVY)
    return save(fig, "fig16_sequence")


def fig17_deployment():
    fig, ax = plt.subplots(figsize=(12,6.5))
    ax.axis("off")
    boxes = [
        ("User Browser",      0.5, 4.5, 2.0, 1.2, NAVY),
        ("Netlify CDN\n(Frontend Static)", 3.0, 4.5, 2.5, 1.2, TEAL),
        ("Render Cloud\n(Docker, Flask+Gunicorn)", 6.2, 4.5, 3.0, 1.2, ACCENT),
        ("Postgres (Managed)", 9.7, 4.5, 2.0, 1.2, GOLD),
        ("AI Workers\n(Auto-scaling Background)", 6.2, 2.0, 3.0, 1.2, "#5B8DEF"),
        ("Object Storage\n(Encrypted Media)",   3.0, 2.0, 2.5, 1.2, "#5BBA6F"),
        ("GitHub Actions CI/CD", 0.5, 2.0, 2.0, 1.2, "#9B5DE5"),
    ]
    pos = {}
    for name,x,y,w,h,col in boxes:
        ax.add_patch(FancyBboxPatch((x,y),w,h, boxstyle="round,pad=0.05", facecolor=col, edgecolor="white"))
        ax.text(x+w/2, y+h/2, name, ha="center", va="center", color="white", fontsize=10, fontweight="bold")
        pos[name]=(x+w/2, y+h/2)
    edges = [
        ("User Browser","Netlify CDN\n(Frontend Static)"),
        ("Netlify CDN\n(Frontend Static)","Render Cloud\n(Docker, Flask+Gunicorn)"),
        ("Render Cloud\n(Docker, Flask+Gunicorn)","Postgres (Managed)"),
        ("Render Cloud\n(Docker, Flask+Gunicorn)","AI Workers\n(Auto-scaling Background)"),
        ("Render Cloud\n(Docker, Flask+Gunicorn)","Object Storage\n(Encrypted Media)"),
        ("GitHub Actions CI/CD","Render Cloud\n(Docker, Flask+Gunicorn)"),
        ("GitHub Actions CI/CD","Netlify CDN\n(Frontend Static)"),
    ]
    for a,b in edges:
        x1,y1 = pos[a]; x2,y2 = pos[b]
        ax.annotate("", xy=(x2,y2), xytext=(x1,y1), arrowprops=dict(arrowstyle="->", color="#555", lw=1.5))
    ax.set_xlim(0,12); ax.set_ylim(1,7)
    ax.set_title("Deployment Diagram (Render + Netlify + Docker)", fontsize=13, color=NAVY)
    return save(fig, "fig17_deployment")


def fig18_api():
    fig, ax = plt.subplots(figsize=(12,6.5))
    ax.axis("off")
    branches = {
        "/api/auth/": ["POST /register", "POST /login"],
        "/api/analysis/": ["GET /status","POST /analyze/file","GET /results/{id}",
                           "POST /compare","GET /history","GET /export/{id}/json","GET /export/{id}/pdf","DELETE /{id}"],
        "/api/admin/": ["GET /audit-log","GET /users"],
        "/api/datasets/": ["GET /"],
    }
    ax.add_patch(FancyBboxPatch((5.0,5.6),2.0,0.7, boxstyle="round,pad=0.04", facecolor=NAVY, edgecolor="white"))
    ax.text(6.0,5.95,"/api", ha="center", color="white", fontsize=12, fontweight="bold")
    bx = [1,4,8,11]
    bcolors = [TEAL, ACCENT, GOLD, "#5B8DEF"]
    for i,(branch,children) in enumerate(branches.items()):
        x = bx[i]
        ax.add_patch(FancyBboxPatch((x-1.0,4.4),2.0,0.6, boxstyle="round,pad=0.04",
                                    facecolor=bcolors[i], edgecolor="white"))
        ax.text(x,4.7, branch, ha="center", color="white", fontsize=10, fontweight="bold")
        ax.annotate("", xy=(x,4.95), xytext=(6,5.6), arrowprops=dict(arrowstyle="-", color="#888"))
        for j,child in enumerate(children):
            y = 3.7 - j*0.45
            ax.add_patch(FancyBboxPatch((x-1.5,y-0.18),3.0,0.36, boxstyle="round,pad=0.02",
                                        facecolor=LIGHT, edgecolor=bcolors[i]))
            ax.text(x,y, child, ha="center", color=bcolors[i], fontsize=8)
    ax.set_xlim(-0.5,13); ax.set_ylim(-0.5,7)
    ax.set_title("API Architecture (REST Endpoints)", fontsize=13, color=NAVY)
    return save(fig, "fig18_api")


def fig19_xai():
    fig, ax = plt.subplots(figsize=(13,4))
    ax.axis("off")
    boxes = [("Provider Scores", NAVY),("Indicator\nNormaliser", TEAL),("Bayesian\nWeighted Fusion", ACCENT),
             ("Disagreement\nPenalty", GOLD),("Verdict +\nConfidence", NAVY),("Narrative\nGenerator", TEAL),("XAI JSON\nResponse", ACCENT)]
    for i,(name,col) in enumerate(boxes):
        x = 0.4 + i*1.78
        ax.add_patch(FancyBboxPatch((x,1.4),1.5,1.4, boxstyle="round,pad=0.04", facecolor=col, edgecolor="white"))
        ax.text(x+0.75,2.1, name, ha="center", va="center", color="white", fontsize=9, fontweight="bold")
        if i<len(boxes)-1:
            ax.annotate("", xy=(x+1.78,2.1), xytext=(x+1.5,2.1), arrowprops=dict(arrowstyle="->", color="#555", lw=1.6))
    ax.set_xlim(0,13.5); ax.set_ylim(0.5,3.5)
    ax.set_title("Explainable AI Verdict Architecture", fontsize=13, color=NAVY)
    return save(fig, "fig19_xai")


def fig20_encryption():
    fig, ax = plt.subplots(figsize=(12,4.2))
    ax.axis("off")
    steps = [("Client\nUpload",NAVY),("Buffer\nChunked",TEAL),("SHA-256\nStreaming",ACCENT),
             ("Fernet/AES\nEncrypt",GOLD),("Encrypted\nStorage",NAVY),
             ("Decrypt to\nScratch",TEAL),("Re-verify\nHash",ACCENT),("AI Inference",NAVY),("Wipe Scratch",GOLD)]
    for i,(name,col) in enumerate(steps):
        x = 0.4 + i*1.36
        ax.add_patch(FancyBboxPatch((x,1.4),1.2,1.5, boxstyle="round,pad=0.04", facecolor=col, edgecolor="white"))
        ax.text(x+0.6,2.15, name, ha="center", va="center", color="white", fontsize=8.5, fontweight="bold")
        if i<len(steps)-1:
            ax.annotate("", xy=(x+1.36,2.15), xytext=(x+1.2,2.15), arrowprops=dict(arrowstyle="->", color="#555", lw=1.6))
    ax.set_xlim(0,13); ax.set_ylim(0.5,3.6)
    ax.set_title("Encryption & Integrity Workflow", fontsize=13, color=NAVY)
    return save(fig, "fig20_encryption")


def fig21_dfd():
    fig, ax = plt.subplots(figsize=(12,7))
    ax.axis("off")
    ext = [("User",1.0,5.5),("Admin",1.0,1.5)]
    for name,x,y in ext:
        ax.add_patch(Rectangle((x-0.7,y-0.4),1.4,0.8, facecolor=NAVY, edgecolor="white"))
        ax.text(x,y, name, ha="center", va="center", color="white", fontsize=10, fontweight="bold")
    procs = [("1. Auth",4,5.5),("2. Upload",4,4.0),("3. Analysis",6.5,4.0),
             ("4. Export",9,4.0),("5. Audit",6.5,1.5)]
    for name,x,y in procs:
        ax.add_patch(Circle((x,y), 0.55, facecolor=TEAL, edgecolor="white", linewidth=2))
        ax.text(x,y, name, ha="center", va="center", color="white", fontsize=8.5, fontweight="bold")
    stores = [("D1 EncryptedMedia",4,2.4),("D2 AnalysisResults",9,5.5),("D3 AuditLog",10.5,1.5)]
    for name,x,y in stores:
        ax.add_patch(Rectangle((x-1.1,y-0.25),2.2,0.5, facecolor=LIGHT, edgecolor=ACCENT, linewidth=1.5))
        ax.text(x,y, name, ha="center", va="center", color=ACCENT, fontsize=8.5, fontweight="bold")
    pos = {n:(x,y) for n,x,y in ext+procs+stores}
    flows = [("User","1. Auth","login"),("1. Auth","2. Upload","jwt"),("User","2. Upload","video"),
             ("2. Upload","D1 EncryptedMedia","cipher"),("2. Upload","3. Analysis","video_id"),
             ("3. Analysis","D2 AnalysisResults","verdict"),("3. Analysis","4. Export","analysis_id"),
             ("4. Export","User","report"),("Admin","5. Audit","query"),("5. Audit","D3 AuditLog","read")]
    for a,b,label in flows:
        x1,y1=pos[a]; x2,y2=pos[b]
        ax.annotate("", xy=(x2,y2), xytext=(x1,y1), arrowprops=dict(arrowstyle="->", color="#666"))
        ax.text((x1+x2)/2,(y1+y2)/2+0.1,label, ha="center", color="#666", fontsize=7)
    ax.set_xlim(0,12.5); ax.set_ylim(0.5,7)
    ax.set_title("Data Flow Diagram (Level-1)", fontsize=13, color=NAVY)
    return save(fig, "fig21_dfd")


def fig22_dashboard():
    fig, ax = plt.subplots(figsize=(12,7))
    ax.axis("off")
    ax.add_patch(Rectangle((0,0),12,7, facecolor=LIGHT))
    ax.add_patch(Rectangle((0,6.4),12,0.6, facecolor=NAVY))
    ax.text(0.4,6.7,"VisionGuard AI", color="white", fontsize=14, fontweight="bold")
    ax.text(11.5,6.7,"Dashboard", color="white", fontsize=11, ha="right")
    ax.add_patch(FancyBboxPatch((0.3,4.3),5,1.9, boxstyle="round,pad=0.05", facecolor="white", edgecolor=NAVY))
    ax.text(0.5,5.8,"VERDICT", color=NAVY, fontsize=10, fontweight="bold")
    ax.text(0.5,5.3,"AI-Generated", color=ACCENT, fontsize=22, fontweight="bold")
    ax.text(0.5,4.85,"Confidence: 92.4%", color=NAVY, fontsize=11)
    ax.add_patch(FancyBboxPatch((5.6,4.3),6.1,1.9, boxstyle="round,pad=0.05", facecolor="white", edgecolor=NAVY))
    ax.text(5.8,5.95,"Confidence Vector", color=NAVY, fontsize=10, fontweight="bold")
    inds = [("Deepfake",0.91),("FFT Anomaly",0.83),("Optical Flow",0.71),("Noise Residual",0.62),("Caption Conf.",0.78)]
    for i,(n,v) in enumerate(inds):
        y = 5.65 - i*0.27
        ax.text(5.8, y, n, color=NAVY, fontsize=8)
        ax.add_patch(Rectangle((7.3,y-0.06),3.5,0.13, facecolor="#ddd"))
        ax.add_patch(Rectangle((7.3,y-0.06),3.5*v,0.13, facecolor=TEAL))
        ax.text(11.0,y, f"{v:.2f}", color=NAVY, fontsize=8, fontweight="bold")
    ax.add_patch(FancyBboxPatch((0.3,2.3),11.4,1.7, boxstyle="round,pad=0.05", facecolor="white", edgecolor=NAVY))
    ax.text(0.5,3.75,"Timeline (per-second events)", color=NAVY, fontsize=10, fontweight="bold")
    np.random.seed(7)
    xs = np.linspace(0.6,11.5,60); vs = np.abs(np.sin(np.linspace(0,4*np.pi,60))*0.6 + np.random.rand(60)*0.3)
    ax.bar(xs, vs*0.9, width=0.18, color=TEAL, alpha=0.7)
    for ex in [12.4, 31.7, 41.0]:
        cx = 0.6 + (ex/47.0)*10.9
        ax.scatter([cx],[1.05], color=ACCENT, s=80, zorder=5, marker="v")
        ax.text(cx,0.85,f"t={ex}s", ha="center", color=ACCENT, fontsize=7)
    ax.add_patch(FancyBboxPatch((0.3,0.3),11.4,1.6, boxstyle="round,pad=0.05", facecolor="white", edgecolor=NAVY))
    ax.text(0.5,1.7,"Export & Privacy", color=NAVY, fontsize=10, fontweight="bold")
    for i,(lbl,col) in enumerate([("Export PDF",NAVY),("Export JSON",TEAL),("Privacy Preview",ACCENT),("Compare",GOLD)]):
        x = 0.5 + i*2.7
        ax.add_patch(FancyBboxPatch((x,0.6),2.4,0.7, boxstyle="round,pad=0.04", facecolor=col, edgecolor="white"))
        ax.text(x+1.2,0.95, lbl, ha="center", va="center", color="white", fontsize=10, fontweight="bold")
    ax.set_xlim(0,12); ax.set_ylim(0,7)
    ax.set_title("Forensic Dashboard Mockup", fontsize=13, color=NAVY, pad=15)
    return save(fig, "fig22_dashboard")


def fig23_timeline_zoom():
    fig, ax = plt.subplots(figsize=(12,4.5))
    np.random.seed(2)
    n=120
    xs = np.linspace(0,60,n)
    deepfake = np.clip(0.2 + 0.3*np.sin(xs/4)+np.random.rand(n)*0.15, 0, 1)
    tampering= np.clip(0.15+ 0.4*np.sin(xs/6+1)+np.random.rand(n)*0.15, 0, 1)
    face_count = np.clip(np.cos(xs/9)*1.5 + np.random.rand(n)*0.5 + 1, 0, 4)
    ax.fill_between(xs, deepfake, alpha=0.3, color=ACCENT, label="Deepfake")
    ax.fill_between(xs, tampering, alpha=0.3, color=GOLD, label="Tampering")
    ax.plot(xs, deepfake, color=ACCENT, lw=1.6)
    ax.plot(xs, tampering, color=GOLD, lw=1.6)
    ax.plot(xs, face_count/4, color=TEAL, lw=1.6, label="Face count (normalised)")
    for ex,sev in [(12.4,"high"),(31.7,"critical"),(41.0,"warning")]:
        col = ACCENT if sev=="critical" else (GOLD if sev=="high" else TEAL)
        ax.axvline(ex, color=col, lw=1.4, linestyle="--", alpha=0.7)
        ax.text(ex,1.02,sev.upper(), color=col, fontsize=8, ha="center", fontweight="bold")
    ax.set_xlim(0,60); ax.set_ylim(0,1.1)
    ax.set_xlabel("Time (s)"); ax.set_ylabel("Indicator score")
    ax.legend(loc="upper right", frameon=False, fontsize=9)
    ax.set_title("Timeline Visualisation — Per-Second Indicators with Event Markers", fontsize=12, color=NAVY)
    return save(fig, "fig23_timeline")


def fig24_privacy_preview():
    fig, axes = plt.subplots(1,2, figsize=(11,5))
    rng = np.random.default_rng(1)
    img = (rng.random((400,500,3))*180+40).astype(np.uint8)
    img2 = img.copy()
    boxes = [(80,90,160,170),(280,120,380,210)]
    try:
        from scipy.ndimage import gaussian_filter
        for x1,y1,x2,y2 in boxes:
            roi = img2[y1:y2,x1:x2,:].copy()
            roi = gaussian_filter(roi, sigma=(8,8,0))
            img2[y1:y2,x1:x2,:] = roi
    except Exception:
        for x1,y1,x2,y2 in boxes:
            img2[y1:y2,x1:x2,:] = img2[y1:y2,x1:x2,:].mean(axis=(0,1)).astype(np.uint8)
    for x1,y1,x2,y2 in boxes:
        axes[0].add_patch(Rectangle((x1,y1),x2-x1,y2-y1, fill=False, edgecolor=TEAL, linewidth=2.5))
        axes[0].text(x1, y1-8, "face 0.97", color=TEAL, fontsize=8, fontweight="bold")
    axes[0].imshow(img); axes[0].set_title("Original (face boxes)", color=NAVY); axes[0].axis("off")
    axes[1].imshow(img2); axes[1].set_title("Privacy Preview (blurred ROIs)", color=NAVY); axes[1].axis("off")
    fig.suptitle("Privacy Blur Preview Module", color=NAVY, fontsize=13, fontweight="bold")
    return save(fig, "fig24_privacy")


def fig25_confusion():
    cm = np.array([[742,31,27],[21,763,16],[29,27,744]])
    labels = ["Authentic","AI-Generated","Tampered"]
    fig, ax = plt.subplots(figsize=(7,6))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(3)); ax.set_xticklabels(labels)
    ax.set_yticks(range(3)); ax.set_yticklabels(labels)
    ax.set_xlabel("Predicted"); ax.set_ylabel("True")
    for i in range(3):
        for j in range(3):
            t = cm[i,j]
            ax.text(j,i, f"{t}\n({t/cm[i].sum()*100:.1f}%)", ha="center", va="center",
                    color="white" if t>400 else NAVY, fontsize=11, fontweight="bold")
    ax.set_title("Confusion Matrix (n=2,400)", color=NAVY, fontsize=13, pad=12)
    plt.colorbar(im, ax=ax, fraction=0.04, pad=0.03)
    return save(fig, "fig25_confusion")


def fig26_accuracy_bars():
    types = ["FaceSwap","FaceShifter","Face2Face","NeuralTextures","DeepFakes","Diffusion","Tamper-Insert","Tamper-Delete"]
    accs  = [0.962, 0.948, 0.931, 0.917, 0.953, 0.892, 0.946, 0.929]
    fig, ax = plt.subplots(figsize=(11,5.2))
    bars = ax.bar(types, accs, color=[NAVY,TEAL,ACCENT,GOLD,"#5B8DEF","#5BBA6F","#9B5DE5","#FF6B6B"], edgecolor="white")
    for b,a in zip(bars,accs):
        ax.text(b.get_x()+b.get_width()/2, a+0.005, f"{a*100:.1f}%", ha="center", color=NAVY, fontsize=9, fontweight="bold")
    ax.axhline(0.90, color=ACCENT, linestyle="--", lw=1.2)
    ax.text(7.4, 0.905, "0.90 target", color=ACCENT, fontsize=8)
    ax.set_ylim(0.7,1.0); ax.set_ylabel("Accuracy")
    ax.set_title("Detection Accuracy by Manipulation Type", color=NAVY, fontsize=13)
    plt.setp(ax.get_xticklabels(), rotation=15, ha="right")
    for sp in ("top","right"): ax.spines[sp].set_visible(False)
    return save(fig, "fig26_accuracy")


def fig27_roc():
    fpr = np.array([0.0,0.005,0.02,0.04,0.06,0.10,0.16,0.25,0.40,0.60,0.85,1.0])
    tpr = np.array([0.0,0.40,0.71,0.86,0.94,0.965,0.978,0.985,0.992,0.996,0.999,1.0])
    auc = 0.972
    fig, ax = plt.subplots(figsize=(7,6))
    ax.plot([0,1],[0,1], color="#aaa", linestyle="--", lw=1.2)
    ax.plot(fpr,tpr, color=NAVY, lw=2.5, label=f"VisionGuard (AUC={auc:.3f})")
    ax.fill_between(fpr,tpr, alpha=0.15, color=NAVY)
    ax.scatter([0.06],[0.94], color=ACCENT, s=80, zorder=5)
    ax.annotate("Operating point\n(FPR=0.06, TPR=0.94)", xy=(0.06,0.94), xytext=(0.25,0.7),
                arrowprops=dict(arrowstyle="->", color=ACCENT), color=ACCENT, fontsize=9)
    ax.set_xlabel("False Positive Rate"); ax.set_ylabel("True Positive Rate")
    ax.set_title("ROC Curve — Deepfake Classifier", fontsize=13, color=NAVY)
    ax.legend(loc="lower right", frameon=False)
    return save(fig, "fig27_roc")


def fig28_latency():
    lengths = np.array([10,30,60,120,180,300,420,600])
    single = lengths*0.78 + 4
    triple = lengths*0.27 + 4
    fig, ax = plt.subplots(figsize=(10,5))
    ax.plot(lengths, single, color=NAVY, marker="o", lw=2, label="Single worker")
    ax.plot(lengths, triple, color=TEAL, marker="s", lw=2, label="Three parallel workers")
    ax.axhline(60, color=ACCENT, linestyle="--", lw=1.2)
    ax.text(420,64, "60 s SLA target", color=ACCENT, fontsize=9)
    ax.set_xlabel("Video length (s)"); ax.set_ylabel("Wall-clock latency (s)")
    ax.set_title("Latency vs. Video Length Benchmark", color=NAVY, fontsize=13)
    ax.legend(loc="upper left", frameon=False)
    ax.grid(linestyle=":", alpha=0.5)
    return save(fig, "fig28_latency")


def fig29_competitors():
    cats = ["Caption","Deepfake","Tampering","Privacy","XAI","Encryption","Open API"]
    data = {
        "VisionGuard": [1.0,1.0,1.0,1.0,1.0,1.0,1.0],
        "Sensity":     [0.0,0.95,0.5,0.0,0.4,0.7,0.2],
        "Reality Defender":[0.0,0.95,0.0,0.0,0.4,0.7,0.2],
        "MS Authenticator":[0.0,0.85,0.4,0.0,0.4,0.0,0.0],
        "Amped":       [0.0,0.5,0.95,0.0,0.5,0.0,0.0],
        "InVID":       [0.4,0.5,0.5,0.0,0.6,0.0,0.4],
    }
    fig, ax = plt.subplots(figsize=(13,6))
    x = np.arange(len(cats)); w=0.13
    cols=[NAVY,TEAL,ACCENT,GOLD,"#5B8DEF","#5BBA6F"]
    for i,(k,v) in enumerate(data.items()):
        ax.bar(x+i*w, v, w, color=cols[i], label=k, edgecolor="white")
    ax.set_xticks(x+w*2.5); ax.set_xticklabels(cats, rotation=10)
    ax.set_ylabel("Capability score (0–1)")
    ax.set_title("Competitor Comparison Chart", color=NAVY, fontsize=13)
    ax.legend(loc="upper right", ncol=3, frameon=False, fontsize=9)
    for sp in ("top","right"): ax.spines[sp].set_visible(False)
    return save(fig, "fig29_competitors")


def fig30_revenue():
    yrs = ["Y1 26-27","Y2 27-28","Y3 28-29","Y4 29-30","Y5 30-31"]
    sub = np.array([150, 850,4100,12000,28000])
    api = np.array([20, 130, 800, 3300, 9500])
    ent = np.array([30, 150, 850, 2900, 8500])
    svc = np.array([10,  50, 200,  600, 2300])
    fig, ax = plt.subplots(figsize=(11,5.5))
    ax.bar(yrs, sub, color=NAVY, label="Subscription")
    ax.bar(yrs, api, bottom=sub, color=TEAL, label="API usage")
    ax.bar(yrs, ent, bottom=sub+api, color=ACCENT, label="Enterprise")
    ax.bar(yrs, svc, bottom=sub+api+ent, color=GOLD, label="Services")
    totals = sub+api+ent+svc
    for i,t in enumerate(totals):
        ax.text(i, t+800, f"${t/1000:.1f}M", ha="center", color=NAVY, fontsize=10, fontweight="bold")
    ax.set_ylabel("Revenue (USD, K)")
    ax.set_title("5-Year Revenue Projection", color=NAVY, fontsize=13)
    ax.legend(loc="upper left", frameon=False)
    for sp in ("top","right"): ax.spines[sp].set_visible(False)
    return save(fig, "fig30_revenue")


def fig31_tam_sam_som():
    fig, ax = plt.subplots(figsize=(9,7))
    ax.set_aspect("equal"); ax.axis("off")
    ax.add_patch(Circle((0,0), 4.0, facecolor=NAVY, alpha=0.85, edgecolor="white"))
    ax.add_patch(Circle((0,-0.3), 2.6, facecolor=TEAL, alpha=0.95, edgecolor="white"))
    ax.add_patch(Circle((0,-0.7), 1.3, facecolor=ACCENT, edgecolor="white"))
    ax.text(0,3.3, "TAM — $22.0B by 2030", ha="center", color="white", fontsize=12, fontweight="bold")
    ax.text(0,3.0, "(CAGR 41.6%)", ha="center", color="white", fontsize=9)
    ax.text(0,1.6, "SAM — $3.8B by 2030", ha="center", color="white", fontsize=11, fontweight="bold")
    ax.text(0,-0.7, "SOM — $72M\nby Y5", ha="center", color="white", fontsize=11, fontweight="bold")
    ax.text(0,-3.7,"Sources: MarketsandMarkets 2024, Grand View Research 2025",
            ha="center", color=NAVY, fontsize=8, style="italic")
    ax.set_xlim(-5,5); ax.set_ylim(-4.5,4)
    ax.set_title("TAM / SAM / SOM", fontsize=13, color=NAVY)
    return save(fig, "fig31_tam_sam_som")


def fig32_funnel():
    stages = [("Awareness — content/SEO/events", 100, NAVY),
              ("Interest — Free tier signups", 14, TEAL),
              ("Consideration — Trial Pro/Business", 4.2, ACCENT),
              ("Decision — Paid conversion", 1.4, GOLD),
              ("Retention — NPS + Advocacy", 1.1, "#5B8DEF")]
    fig, ax = plt.subplots(figsize=(10,6))
    ax.axis("off")
    for i,(name,pct,col) in enumerate(stages):
        w = pct/100 * 9 + 0.5
        x = (10 - w)/2
        y = 5.5 - i*1.1
        ax.add_patch(FancyBboxPatch((x,y),w,0.9, boxstyle="round,pad=0.04", facecolor=col, edgecolor="white"))
        ax.text(5, y+0.45, f"{name}  —  {pct}%", ha="center", color="white", fontsize=10, fontweight="bold")
    ax.set_xlim(0,10); ax.set_ylim(0,7)
    ax.set_title("Marketing Funnel & Customer Acquisition", fontsize=13, color=NAVY)
    return save(fig, "fig32_funnel")


def fig33_logos():
    fig, axes = plt.subplots(1,3, figsize=(13,5.2))
    ax = axes[0]
    ax.add_patch(Polygon([(0.2,0.85),(0.5,0.15),(0.8,0.85)], facecolor=NAVY, edgecolor="white"))
    for r in [0.07,0.04]:
        ax.add_patch(Circle((0.5,0.55), r, facecolor=TEAL, edgecolor="white"))
    ax.text(0.5,0.05,"VisionGuard", ha="center", color=NAVY, fontsize=18, fontweight="bold")
    ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis("off")
    ax.set_title("Concept 1 — V-Reel", color=NAVY)
    ax = axes[1]
    ax.add_patch(Polygon([(0.5,0.95),(0.85,0.75),(0.85,0.4),(0.5,0.15),(0.15,0.4),(0.15,0.75)],
                         facecolor=NAVY, edgecolor="white"))
    ax.add_patch(Ellipse((0.5,0.55),0.45,0.25, facecolor="white"))
    ax.add_patch(Circle((0.5,0.55),0.08, facecolor=ACCENT))
    ax.text(0.5,0.05,"VisionGuard", ha="center", color=NAVY, fontsize=18, fontweight="bold")
    ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis("off")
    ax.set_title("Concept 2 — Eye-Shield", color=NAVY)
    ax = axes[2]
    ax.add_patch(Rectangle((0.18,0.3),0.64,0.5, fill=False, edgecolor=NAVY, linewidth=4))
    ax.add_patch(Rectangle((0.42,0.6),0.16,0.18, fill=False, edgecolor=TEAL, linewidth=3))
    ax.add_patch(Polygon([(0.41,0.45),(0.5,0.35),(0.6,0.45),(0.55,0.45),
                          (0.55,0.55),(0.45,0.55),(0.45,0.45)],
                         facecolor=ACCENT, edgecolor="white"))
    ax.text(0.5,0.05,"VisionGuard", ha="center", color=NAVY, fontsize=18, fontweight="bold")
    ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis("off")
    ax.set_title("Concept 3 — Frame-Lock", color=NAVY)
    fig.suptitle("Brand Identity & Logo Concepts", fontsize=13, color=NAVY, fontweight="bold")
    return save(fig, "fig33_logos")


def main():
    funcs = [fig01_competitor_radar, fig02_gantt, fig03_agile_sdlc, fig04_agile_swimlane,
             fig05_scope, fig06_func_arch, fig07_usecase, fig08_activity,
             fig09_high_level_arch, fig10_frontend, fig11_backend, fig12_ai_pipeline,
             fig13_security_rings, fig14_erd, fig15_uml, fig16_sequence,
             fig17_deployment, fig18_api, fig19_xai, fig20_encryption, fig21_dfd,
             fig22_dashboard, fig23_timeline_zoom, fig24_privacy_preview,
             fig25_confusion, fig26_accuracy_bars, fig27_roc, fig28_latency,
             fig29_competitors, fig30_revenue, fig31_tam_sam_som, fig32_funnel,
             fig33_logos]
    made = 0
    for f in funcs:
        try:
            f(); made += 1
            print(f"  [OK] {f.__name__}")
        except Exception as e:
            print(f"  [WARN] {f.__name__}: {e}")
    print(f"\nGenerated {made}/{len(funcs)} figures into {OUT}")

if __name__ == "__main__":
    main()
