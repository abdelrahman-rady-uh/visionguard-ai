import json
import logging
import os
from datetime import datetime, timezone
from backend.config import LOG_PATH


class AuditLogger:
    def __init__(self):
        os.makedirs(LOG_PATH, exist_ok=True)
        self.logger = logging.getLogger("audit")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            audit_file = os.path.join(LOG_PATH, "audit.log")
            handler = logging.FileHandler(audit_file, encoding="utf-8")
            handler.setFormatter(logging.Formatter("%(message)s"))
            self.logger.addHandler(handler)

    def log(self, action, user_session="local-session", details=None):
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "user_session": user_session,
            "details": details or {},
        }
        self.logger.info(json.dumps(payload))
