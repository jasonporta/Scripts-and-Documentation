#!/usr/bin/python

# Start EMhub as a daemonized process

import os
import subprocess

# Configuration:
APP_MODULE = "emhub:create_app()"
LOG_FILE = "emhub_gunicorn.log"
NUM_WORKERS = 2
PORT = 5000

# Gunicorn command:
command = [
        "gunicorn",
        "--workers", str(NUM_WORKERS),
        "--bind", f"0.0.0.0:{PORT}",
        "--log-file", LOG_FILE,
        "--access-logfile", LOG_FILE,
        "--daemon", # Run in the background
        APP_MODULE
]

# Run Gunicorn in the background:
try:
    with open(LOG_FILE, "a") as log:
        subprocess.Popen(command, stdout=log, stderr=log)
    print(f"Gunicorn started in the background. Logs: {LOG_FILE}")
except Exception as e:
    print(f"Error starting at Gunicorn: {e}")
