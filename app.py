import os
import threading
import webbrowser
from dotenv import load_dotenv
from backend.app import app

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    def open_ui():
        try:
            webbrowser.open("http://127.0.0.1:5000")
        except Exception:
            pass

    if os.getenv("AUTO_OPEN_BROWSER", "1") == "1":
        threading.Timer(1.5, open_ui).start()
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    app.run(host="127.0.0.1", port=5000, debug=debug_mode)
