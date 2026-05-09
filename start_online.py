#!/usr/bin/env python3
"""
VisionGuard AI -- Online Launcher
Starts the Flask server AND opens your permanent ngrok link.

FIRST-TIME SETUP (do this once):
  1. Go to https://dashboard.ngrok.com/signup  (free account)
  2. After login, go to https://dashboard.ngrok.com/get-started/your-authtoken
  3. Copy your token and run:
       python start_online.py --setup YOUR_TOKEN_HERE
  4. Then claim your free static domain at:
       https://dashboard.ngrok.com/cloud-edge/domains
     (click "Create domain", copy the domain name)
  5. Save it:
       python start_online.py --domain YOUR-DOMAIN.ngrok-free.app

EVERYDAY USE:
  python start_online.py
"""

import os
import sys
import json
import time
import socket
import threading
import subprocess
import argparse

PORT = 5000
CONFIG_FILE = os.path.join(os.path.dirname(__file__), ".ngrok_config.json")

# Real ngrok binary installed by winget
NGROK_EXE = r"C:\Users\compumarts\AppData\Local\Microsoft\WinGet\Packages\Ngrok.Ngrok_Microsoft.Winget.Source_8wekyb3d8bbwe\ngrok.exe"


# ── Config helpers ────────────────────────────────────────────────

def _load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {}


def _save_config(data):
    cfg = _load_config()
    cfg.update(data)
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)


# ── Flask server ──────────────────────────────────────────────────

def _is_port_open(port, host="127.0.0.1"):
    try:
        with socket.create_connection((host, port), timeout=1.0):
            return True
    except OSError:
        return False


def _flask_thread():
    import logging
    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    from backend.app import app
    app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False)


# ── Main ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="VisionGuard AI Online Launcher")
    parser.add_argument("--setup", metavar="TOKEN",
                        help="Save your ngrok auth token (do this once)")
    parser.add_argument("--domain", metavar="DOMAIN",
                        help="Save your ngrok static domain (do this once)")
    args = parser.parse_args()

    # Handle setup flags
    if args.setup:
        _save_config({"auth_token": args.setup})
        result = subprocess.run(
            [NGROK_EXE, "config", "add-authtoken", args.setup],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print("\n  Auth token saved!")
        else:
            print("\n  Token error:", result.stderr.strip())
        print("  Next: claim your free domain at https://dashboard.ngrok.com/cloud-edge/domains")
        print("  Then run: python start_online.py --domain YOUR-DOMAIN.ngrok-free.app\n")
        return

    if args.domain:
        _save_config({"domain": args.domain})
        print(f"\n  Static domain saved: {args.domain}")
        print("  Run 'python start_online.py' to start.\n")
        return

    # Load saved config
    cfg = _load_config()
    static_domain = cfg.get("domain")
    auth_token = cfg.get("auth_token")

    print()
    print("  VisionGuard AI -- Online Launcher")
    print("  " + "-" * 40)
    print()

    if not auth_token:
        print("  SETUP REQUIRED (free, takes 2 minutes):")
        print()
        print("  1. Create a free account: https://dashboard.ngrok.com/signup")
        print("  2. Copy your auth token:  https://dashboard.ngrok.com/get-started/your-authtoken")
        print("  3. Run: python start_online.py --setup YOUR_TOKEN")
        print("  4. Claim free domain:     https://dashboard.ngrok.com/cloud-edge/domains")
        print("  5. Run: python start_online.py --domain YOUR-DOMAIN.ngrok-free.app")
        print()
        print("  After setup, your link is PERMANENT and works every time.")
        print()
        return

    # ── Start Flask ──────────────────────────────────────────────
    print("  [1/3] Starting VisionGuard AI server...", end="", flush=True)
    t = threading.Thread(target=_flask_thread, daemon=True)
    t.start()

    for _ in range(30):
        if _is_port_open(PORT):
            break
        time.sleep(0.4)
    else:
        print(" FAILED")
        print("  ERROR: Server did not start. Check logs above.")
        sys.exit(1)
    print(" READY", flush=True)

    # ── Open ngrok tunnel ────────────────────────────────────────
    if static_domain:
        print(f"  [2/3] Opening permanent tunnel: {static_domain} ...", flush=True)
        cmd = [NGROK_EXE, "http", str(PORT),
               "--domain", static_domain,
               "--log", "stdout", "--log-format", "json"]
    else:
        print("  [2/3] Opening temporary tunnel (no static domain saved)...", flush=True)
        cmd = [NGROK_EXE, "http", str(PORT),
               "--log", "stdout", "--log-format", "json"]

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
    except FileNotFoundError:
        print("  ERROR: ngrok not found at expected path.")
        sys.exit(1)

    # Read ngrok JSON logs to find the public URL
    tunnel_url = static_domain and f"https://{static_domain}"
    if not tunnel_url:
        import re
        deadline = time.time() + 20
        for line in proc.stdout:
            try:
                entry = json.loads(line)
                url = entry.get("url") or entry.get("public_url") or ""
                if url.startswith("https://"):
                    tunnel_url = url
                    break
                if "started tunnel" in entry.get("msg", ""):
                    url = entry.get("url", "")
                    if url:
                        tunnel_url = url
                        break
            except json.JSONDecodeError:
                pass
            if time.time() > deadline:
                break

    time.sleep(1.5)  # let ngrok fully establish

    # Drain remaining ngrok output so pipe never blocks
    threading.Thread(target=lambda: [proc.stdout.read()], daemon=True).start()

    # ── Print result ─────────────────────────────────────────────
    print(flush=True)
    if tunnel_url:
        print("  [3/3] Your system is ONLINE!", flush=True)
        print(flush=True)
        print("  " + "=" * 54, flush=True)
        print("   PERMANENT LINK -- open on any device, anytime:", flush=True)
        print(flush=True)
        print("   " + tunnel_url, flush=True)
        print(flush=True)
        print("   iPhone, Android, laptop -- any network, anywhere.", flush=True)
        print("  " + "=" * 54, flush=True)
    else:
        print("  Could not get tunnel URL. Check ngrok dashboard.", flush=True)

    print(flush=True)
    print("  Press Ctrl+C to stop the server.", flush=True)
    print(flush=True)

    try:
        proc.wait()
    except KeyboardInterrupt:
        pass

    proc.terminate()
    print("\n  Server stopped.\n")


if __name__ == "__main__":
    main()
