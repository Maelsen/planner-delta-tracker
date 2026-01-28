"""
Configuration for Microsoft Planner Delta Tracker

All credentials are read from environment variables.
For local development, set them in your shell or use a .env file.
In GitHub Actions, they are stored as encrypted Secrets.

Schedule settings can be overridden via settings.json (managed by Admin UI).
"""

import os
import json
from pathlib import Path

# Load settings.json if it exists
SETTINGS_FILE = Path(__file__).parent / "settings.json"
_settings = {}
if SETTINGS_FILE.exists():
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            _settings = json.load(f)
    except (json.JSONDecodeError, IOError):
        _settings = {}

# Azure App Registration credentials
TENANT_ID = os.environ.get("TENANT_ID", "")
CLIENT_ID = os.environ.get("CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET", "")

# Microsoft Graph API endpoints
GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"
GRAPH_BETA_URL = "https://graph.microsoft.com/beta"

# Planner Configuration
PLAN_ID = os.environ.get("PLAN_ID", "")
GROUP_ID = os.environ.get("GROUP_ID", "")

# Report Configuration
# Priority: settings.json > environment variable > empty
_settings_recipients = _settings.get("recipients", [])
_env_recipients = os.environ.get("REPORT_RECIPIENTS", "").split(",")
REPORT_RECIPIENTS = _settings_recipients if _settings_recipients else [r for r in _env_recipients if r]
REPORT_SENDER = os.environ.get("REPORT_SENDER", "")

# Schedule Configuration (from settings.json)
SCHEDULE_DAY = _settings.get("schedule_day", "monday").lower()
SCHEDULE_HOUR = _settings.get("schedule_hour", 8)

# Local Storage for snapshots
LOCAL_SNAPSHOT_FILE = os.environ.get("LOCAL_SNAPSHOT_FILE", "snapshots/planner_snapshot.json")
