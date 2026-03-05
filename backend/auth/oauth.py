import os
from urllib.parse import urlencode

import requests
from flask import current_app


def get_google_auth_url(state: str) -> str:
    """
    Build the Google OAuth 2.0 authorization URL.
    Frontend should redirect the browser to this URL.
    """
    base_url = "https://accounts.google.com/o/oauth2/v2/auth"
    params = {
        "client_id": current_app.config["GOOGLE_CLIENT_ID"],
        "redirect_uri": current_app.config["GOOGLE_OAUTH_REDIRECT_URI"],
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    return f"{base_url}?{urlencode(params)}"


def exchange_google_code_for_userinfo(code: str) -> dict | None:
    """
    Exchange authorization code for tokens and fetch userinfo.
    Returns a dict with at least: {'sub', 'email', 'name'} or None on error.
    """
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": current_app.config["GOOGLE_CLIENT_ID"],
        "client_secret": current_app.config["GOOGLE_CLIENT_SECRET"],
        "redirect_uri": current_app.config["GOOGLE_OAUTH_REDIRECT_URI"],
        "grant_type": "authorization_code",
    }
    token_resp = requests.post(token_url, data=data, timeout=10)
    if not token_resp.ok:
        return None
    tokens = token_resp.json()

    userinfo_resp = requests.get(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
        timeout=10,
    )
    if not userinfo_resp.ok:
        return None
    return userinfo_resp.json()


def get_ms_auth_url(state: str) -> str:
    """
    Build the Microsoft OAuth 2.0 authorization URL.
    """
    tenant = os.environ.get("MS_TENANT_ID", "common")
    base_url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize"
    params = {
        "client_id": current_app.config["MS_CLIENT_ID"],
        "response_type": "code",
        "redirect_uri": current_app.config["MS_OAUTH_REDIRECT_URI"],
        "response_mode": "query",
        "scope": "openid email profile https://graph.microsoft.com/User.Read",
        "state": state,
    }
    return f"{base_url}?{urlencode(params)}"


def exchange_ms_code_for_userinfo(code: str) -> dict | None:
    """
    Exchange Microsoft authorization code for tokens and fetch user profile.
    Returns a dict with: {'id', 'mail' or 'userPrincipalName', 'displayName'} or None.
    """
    tenant = os.environ.get("MS_TENANT_ID", "common")
    token_url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
    data = {
        "client_id": current_app.config["MS_CLIENT_ID"],
        "client_secret": current_app.config["MS_CLIENT_SECRET"],
        "code": code,
        "redirect_uri": current_app.config["MS_OAUTH_REDIRECT_URI"],
        "grant_type": "authorization_code",
        "scope": "openid email profile https://graph.microsoft.com/User.Read",
    }
    token_resp = requests.post(token_url, data=data, timeout=10)
    if not token_resp.ok:
        return None
    tokens = token_resp.json()

    graph_resp = requests.get(
        "https://graph.microsoft.com/v1.0/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
        timeout=10,
    )
    if not graph_resp.ok:
        return None
    return graph_resp.json()

