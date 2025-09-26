# controllers/secret_store.py
from __future__ import annotations
from typing import Optional
import keyring

_SERVICE = "MeshConfigurator"

def _to_token(label: str) -> str:
    return f"keyring://{label}"

def is_token(value: object) -> bool:
    return isinstance(value, str) and value.startswith("keyring://")

def _label_from_token(token: str) -> str:
    return token.split("://", 1)[1]

def save_psk(label: str, secret: str) -> Optional[str]:
    """
    Store secret under (service=_SERVICE, username=label).
    Returns a token like 'keyring://<label>' if stored, else None.
    """
    if not secret:
        return None
    try:
        keyring.set_password(_SERVICE, label, secret)
        return _to_token(label)
    except Exception:
        return None  # backend unavailable, caller decides fallback

def fetch_psk(token_or_label: str) -> Optional[str]:
    """
    Accepts either a token ('keyring://...') or a raw label.
    Returns the secret or None.
    """
    try:
        label = _label_from_token(token_or_label) if is_token(token_or_label) else token_or_label
        return keyring.get_password(_SERVICE, label)
    except Exception:
        return None
