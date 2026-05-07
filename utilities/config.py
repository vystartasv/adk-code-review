"""
Auto-inject API keys from the credential proxy when not set in environment.
Import this early in any script that needs GOOGLE_API_KEY.
"""
import os
import sys


def _ensure_google_api_key():
    """If GOOGLE_API_KEY is not in the environment, try the credential proxy."""
    if os.environ.get("GOOGLE_API_KEY"):
        return

    try:
        sys.path.insert(0, os.path.expanduser("~/.hermes"))
        from credential_proxy.client import get_credential
        cred = get_credential("Google AI Studio")
        if cred and cred.get("password"):
            os.environ["GOOGLE_API_KEY"] = cred["password"]
    except Exception:
        pass  # Credential proxy unavailable — user must set env manually


def _ensure_google_cloud_project():
    """If GOOGLE_CLOUD_PROJECT is not in the environment, try the credential proxy."""
    if os.environ.get("GOOGLE_CLOUD_PROJECT"):
        return

    try:
        sys.path.insert(0, os.path.expanduser("~/.hermes"))
        from credential_proxy.client import get_credential
        cred = get_credential("Google Cloud Project")
        if cred and cred.get("password"):
            os.environ["GOOGLE_CLOUD_PROJECT"] = cred["password"]
    except Exception:
        pass


_ensure_google_api_key()
_ensure_google_cloud_project()
