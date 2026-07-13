import json
import os
import sys
from typing import Any

import google.auth
from google.oauth2 import service_account


def get_credentials() -> Any:
    """Gets Google Cloud credentials, supporting a JSON string in an env var."""
    # Priority 1: GOOGLE_APPLICATION_CREDENTIALS_JSON environment variable
    creds_json = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")
    if creds_json:
        try:
            info = json.loads(creds_json)
            return service_account.Credentials.from_service_account_info(info)
        except Exception as e:
            print(f"Warning: Failed to load credentials from GOOGLE_APPLICATION_CREDENTIALS_JSON: {e}", file=sys.stderr)

    # Priority 2: Standard ADC (including GOOGLE_APPLICATION_CREDENTIALS file)
    try:
        credentials, _ = google.auth.default()
        return credentials
    except Exception:
        return None
