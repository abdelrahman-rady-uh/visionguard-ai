"""Gunicorn configuration for production deployment."""
import os
import multiprocessing

# Server socket
bind = f"0.0.0.0:{os.getenv('PORT', 8080)}"
backlog = 2048

# Worker processes
workers = max(2, multiprocessing.cpu_count() - 1)
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 5

# Logging
accesslog = os.path.join(os.getenv('LOG_PATH', 'logs'), 'access.log')
errorlog = os.path.join(os.getenv('LOG_PATH', 'logs'), 'error.log')
loglevel = os.getenv('LOG_LEVEL', 'info')
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'video-analysis-platform'

# Server mechanics
daemon = False
pidfile = os.path.join(os.getenv('LOG_PATH', 'logs'), 'gunicorn.pid')
umask = 0
user = None
group = None
tmp_upload_dir = os.getenv('UPLOAD_DIR', 'uploads')

# SSL (if needed)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"
# ssl_version = "TLSv1_2"

# WSGI
wsgi_app = "backend.app:app"
