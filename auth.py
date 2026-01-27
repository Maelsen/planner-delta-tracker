"""
Authentication module for Microsoft Graph API

Supports two authentication flows:
1. Client Credentials (App-only) - for automated/scheduled runs
2. Device Code Flow - for interactive authentication (first-time setup)
"""

import msal
import json
import os
from pathlib import Path
from config import TENANT_ID, CLIENT_ID, CLIENT_SECRET

# Token cache file
TOKEN_CACHE_FILE = Path(__file__).parent / "token_cache.json"


def get_msal_app():
    """Create MSAL confidential client application."""
    return msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=f"https://login.microsoftonline.com/{TENANT_ID}",
        client_credential=CLIENT_SECRET,
    )


def get_access_token_client_credentials():
    """
    Get access token using client credentials flow (app-only).
    Best for automated/scheduled runs.

    Note: Requires admin consent for application permissions.
    """
    app = get_msal_app()
    scopes = ["https://graph.microsoft.com/.default"]

    result = app.acquire_token_for_client(scopes=scopes)

    if "access_token" in result:
        return result["access_token"]
    else:
        error_msg = result.get("error_description", result.get("error", "Unknown error"))
        raise Exception(f"Failed to acquire token: {error_msg}")


def get_access_token_device_code():
    """
    Get access token using device code flow (interactive).
    Use this for first-time setup or when delegated permissions are needed.
    """
    app = msal.PublicClientApplication(
        CLIENT_ID,
        authority=f"https://login.microsoftonline.com/{TENANT_ID}",
    )

    scopes = [
        "Tasks.Read",
        "Group.Read.All",
        "Sites.ReadWrite.All",
        "Mail.Send",
        "User.Read"
    ]

    # Try to get token from cache first
    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(scopes, account=accounts[0])
        if result and "access_token" in result:
            return result["access_token"]

    # Need interactive login
    flow = app.initiate_device_flow(scopes=scopes)

    if "user_code" not in flow:
        raise Exception(f"Failed to create device flow: {flow.get('error_description', 'Unknown error')}")

    print(flow["message"])  # Shows: "To sign in, use a web browser to open..."

    result = app.acquire_token_by_device_flow(flow)

    if "access_token" in result:
        return result["access_token"]
    else:
        error_msg = result.get("error_description", result.get("error", "Unknown error"))
        raise Exception(f"Failed to acquire token: {error_msg}")


def get_access_token(interactive=False):
    """
    Get access token for Microsoft Graph API.

    Uses client credentials flow by default (application permissions).
    """
    return get_access_token_client_credentials()


def test_authentication():
    """Test if authentication is working by making a simple API call."""
    import requests

    try:
        token = get_access_token(interactive=True)
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            "https://graph.microsoft.com/v1.0/me",
            headers=headers
        )

        if response.status_code == 200:
            user = response.json()
            print(f"[OK] Authentication successful!")
            print(f"  Logged in as: {user.get('displayName')} ({user.get('mail')})")
            return True
        else:
            print(f"[FEHLER] Authentication test failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False

    except Exception as e:
        print(f"[FEHLER] Authentication failed: {e}")
        return False


if __name__ == "__main__":
    print("Testing authentication...")
    test_authentication()
