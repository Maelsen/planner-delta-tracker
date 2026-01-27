"""
Configuration for Microsoft Planner Delta Tracker

All credentials are read from environment variables.
For local development, set them in your shell or use a .env file.
In GitHub Actions, they are stored as encrypted Secrets.
"""

import os

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
REPORT_RECIPIENTS = os.environ.get("REPORT_RECIPIENTS", "").split(",")
REPORT_SENDER = os.environ.get("REPORT_SENDER", "")

# Local Storage for snapshots
LOCAL_SNAPSHOT_FILE = os.environ.get("LOCAL_SNAPSHOT_FILE", "snapshots/planner_snapshot.json")
