# controllers/preset_controller.py
from __future__ import annotations

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

log = logging.getLogger(__name__)


class PresetController:
    """
    File-backed preset manager.

    - Creates/uses a hidden directory in the user's HOME (~/.meshtastic_config_presets).
    - Saves presets as readable JSON (*.json, indent=4).
    - Lists available presets (by name, without .json).
    - Loads/saves/deletes presets with defensive error handling.
    - If the directory cannot be created, the controller gracefully disables itself
      (self.preset_dir = None) and returns empty/False from public APIs.

    Also provides optional secure PSK handling via the OS keychain (python-keyring):
      * save_preset_secure(): store PSKs in keyring, write tokens in JSON
      * load_preset_resolved(): read JSON, resolve tokens back to PSKs
    """

    PRESET_DIR_NAME = ".meshtastic_config_presets"

    # ----- Keyring / tokens -----
    _KR_SERVICE = "MeshConfigurator"
    _KR_PREFIX = "keyring://"

    def __init__(self) -> None:
        home = Path.home()
        self.preset_dir: Optional[Path] = home / self.PRESET_DIR_NAME
        self._ensure_preset_dir_exists()

        # Try to import keyring lazily and record availability.
        try:
            import keyring  # noqa: F401
            self._keyring_ok = True
        except Exception:
            self._keyring_ok = False
            log.info("python-keyring not available; presets will store PSKs inline unless you use save_preset_secure().")

    # -------------------------------------------------------------------------
    # Private helpers
    # -------------------------------------------------------------------------
    def _ensure_preset_dir_exists(self) -> None:
        """Attempt to create the preset directory. Disable controller on failure."""
        try:
            if self.preset_dir is None:
                return
            os.makedirs(self.preset_dir, exist_ok=True)
        except OSError as e:
            log.critical("Failed to create preset directory at %s: %s", self.preset_dir, e)
            self.preset_dir = None  # gracefully disable

    @staticmethod
    def _is_safe_name(name: str) -> bool:
        """Reject names with path separators, reserved names, or illegal characters."""
        if not name or name in (".", ".."):
            return False

        # Disallow any path separators for safety (covers POSIX/Windows)
        if os.sep in name or (os.altsep and os.altsep in name):
            return False

        # Disallow characters that are broadly problematic (esp. on Windows)
        invalid_chars = set('<>:"/\\|?*')
        if any(ch in invalid_chars for ch in name):
            return False

        # Windows reserved device names (case-insensitive)
        reserved = {"CON", "PRN", "AUX", "NUL"} | {f"COM{i}" for i in range(1, 10)} | {f"LPT{i}" for i in range(1, 10)}
        if name.upper() in reserved:
            return False

        return True

    def _path_for(self, name: str) -> Optional[Path]:
        """Return full path for the given preset name, or None if disabled/unsafe."""
        if self.preset_dir is None:
            return None
        if not self._is_safe_name(name):
            log.error("Unsafe preset name rejected: %r", name)
            return None
        return self.preset_dir / f"{name}.json"

    def _clean_name(self, name: str) -> str:
        """A little name format and cleaning before it goes through _is_safe_name."""
        try:
            return str(name).title().strip().replace(" ", "")
        except Exception:
            log.error("Could not parse preset name, try a different name.")
            return "Preset"

    # ----- Keyring helpers -----
    def _is_token(self, v: object) -> bool:
        return isinstance(v, str) and v.startswith(self._KR_PREFIX)

    def _make_token(self, label: str) -> str:
        return f"{self._KR_PREFIX}{label}"

    def _label_from_token(self, token: str) -> str:
        return token.split("://", 1)[1]

    def _keyring_save(self, label: str, secret: str) -> Optional[str]:
        """Save secret under label; return token or None if failed/unavailable."""
        if not self._keyring_ok or not secret:
            return None
        try:
            import keyring
            keyring.set_password(self._KR_SERVICE, label, secret)
            return self._make_token(label)
        except Exception as e:
            log.warning("Keyring save failed for label '%s': %s", label, e)
            return None

    def _keyring_fetch(self, token_or_label: str) -> Optional[str]:
        """Fetch secret by token or label; return None if not found/unavailable."""
        if not self._keyring_ok:
            return None
        try:
            import keyring
            label = self._label_from_token(token_or_label) if self._is_token(token_or_label) else token_or_label
            return keyring.get_password(self._KR_SERVICE, label)
        except Exception as e:
            log.warning("Keyring fetch failed for '%s': %s", token_or_label, e)
            return None

    def _keyring_delete(self, token_or_label: str) -> bool:
        """Delete secret by token or label from OS keyring. Returns True if deleted or absent."""
        if not self._keyring_ok:
            return False
        try:
            import keyring
            label = self._label_from_token(token_or_label) if self._is_token(token_or_label) else token_or_label
            # Some backends raise if not present; treat that as success for idempotence
            keyring.delete_password(self._KR_SERVICE, label)
            log.info("[preset] keyring entry removed: %s", label)
            return True
        except keyring.errors.PasswordDeleteError:
            # Already absent
            return True
        except Exception as e:
            log.warning("[preset] failed to remove keyring entry '%s': %s", token_or_label, e)
            return False

    # ----- Secure PSK transforms -----
    def _secure_psks(self, preset_name: str, preset_data: dict) -> dict:
        """Return a copy of preset_data with PSKs moved to keyring and replaced by tokens."""
        out: dict = {}
        for section, fields in (preset_data or {}).items():
            nf: dict = {}
            for label, val in (fields or {}).items():
                if label == "PSK" and isinstance(val, str) and val and not self._is_token(val):
                    label_key = f"{preset_name}:{section}"
                    token = self._keyring_save(label_key, val)
                    if token:
                        nf[label] = token
                    else:
                        # Fallback: keep inline (you can choose to blank instead if you prefer)
                        log.warning("[preset] keyring unavailable; storing PSK inline for section '%s'", section)
                        nf[label] = val
                else:
                    nf[label] = val
            out[section] = nf
        return out

    def _resolve_psks(self, preset_name: str, preset_data: dict) -> dict:
        """Return a copy of preset_data with any keyring tokens replaced by real PSKs."""
        out: dict = {}
        for section, fields in (preset_data or {}).items():
            nf = dict(fields or {})
            psk_val = nf.get("PSK")
            if isinstance(psk_val, str) and self._is_token(psk_val):
                secret = self._keyring_fetch(psk_val)
                if secret is None:
                    log.warning("[preset] PSK for '%s' not found in keyring; leaving field blank.", section)
                    nf["PSK"] = ""
                else:
                    nf["PSK"] = secret
            out[section] = nf
        return out

    @staticmethod
    def _redact_psks_for_log(data: dict) -> dict:
        """Return a shallow-redacted copy for logging (PSK values redacted)."""
        red: dict = {}
        for section, fields in (data or {}).items():
            nf = dict(fields or {})
            if "PSK" in nf and isinstance(nf["PSK"], str) and nf["PSK"]:
                nf["PSK"] = "<redacted>"
            red[section] = nf
        return red

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------
    def get_preset_names(self) -> List[str]:
        """
        Return a list of preset names (without .json).
        Empty list if disabled or an error occurs.
        """
        if self.preset_dir is None:
            return []
        try:
            names: List[str] = []
            for p in self.preset_dir.iterdir():
                if p.is_file() and p.suffix.lower() == ".json":
                    names.append(p.stem)
            return sorted(names)
        except OSError as e:
            log.error("Failed to list preset directory %s: %s", self.preset_dir, e)
            return []

    # ----- Secure variants (recommended) -----
    def save_preset_secure(self, name: str, settings: Dict[str, Any]) -> bool:
        """
        Save settings but move PSKs to OS keychain and write tokens into JSON.
        """
        clean_name = self._clean_name(name=name)
        secured = self._secure_psks(clean_name, settings)
        return self.save_preset(clean_name, secured)

    def load_preset_resolved(self, name: str) -> Dict[str, Any]:
        """
        Load preset then resolve any keyring tokens to plaintext PSKs.
        Returns {} if not found/disabled.
        """
        clean_name = self._clean_name(name=name)
        raw = self.load_preset(clean_name)
        if not raw:
            return {}
        return self._resolve_psks(clean_name, raw)

    def save_preset(self, name: str, settings: Dict[str, Any]) -> bool:
        """
        Save settings to <name>.json. Returns True on success, False otherwise.
        Uses atomic replace where possible to avoid partial writes.
        """
        clean_name = self._clean_name(name=name)
        if self.preset_dir is None:
            log.error("Cannot save preset: preset directory is unavailable.")
            return False

        path = self._path_for(clean_name)
        if path is None:
            return False

        tmp_path = path.with_suffix(".json.tmp")
        try:
            # Ensure directory still exists (it could have been removed externally)
            os.makedirs(self.preset_dir, exist_ok=True)

            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=4, ensure_ascii=False, default=str)
                f.write("\n")

            # Atomic replace (works cross-platform on modern Python)
            os.replace(tmp_path, path)
            log.info("Saved preset '%s' to %s", clean_name, path)
            return True
        except (OSError, TypeError, ValueError) as e:
            log.error("Failed to save preset '%s': %s", clean_name, e)
            # Best-effort cleanup of temp file
            try:
                if tmp_path.exists():
                    tmp_path.unlink(missing_ok=True)  # type: ignore[arg-type]
            except OSError:
                pass
            return False

    def rename_preset(self, old_name: str, new_name: str) -> bool:
        """
        Rename a preset from old_name to new_name. Returns True on success.
        Fails if names are invalid, old_name does not exist, or new_name already exists.
        """
        old = self._clean_name(name=old_name)
        new = self._clean_name(name=new_name)

        old_path = self._path_for(old)
        new_path = self._path_for(new)

        if not old_path or not new_path:
            log.error("Rename failed: one or both preset names are invalid.")
            return False

        if not old_path.exists():
            log.warning("Cannot rename preset '%s'; it does not exist.", old)
            return False

        if new_path.exists():
            log.error("Cannot rename to '%s'; a preset with that name already exists.", new)
            return False

        try:
            os.rename(old_path, new_path)
            log.info("Renamed preset '%s' to '%s'.", old, new)
            return True
        except OSError as e:
            log.error("Failed to rename preset '%s' to '%s': %s", old, new, e)
            return False

    def load_preset(self, name: str) -> Dict[str, Any]:
        """
        Load and return the settings dict for the given preset name.
        Returns {} if disabled, file missing, or on any error/parse failure.
        """
        clean_name = self._clean_name(name=name)
        if self.preset_dir is None:
            return {}

        path = self._path_for(clean_name)
        if path is None:
            return {}

        if not path.exists() or not path.is_file():
            log.warning("Preset not found: %s", path)
            return {}

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                # Redact PSKs in logs
                log_data = self._redact_psks_for_log(data)
                log.info("preset '%s' in use. settings: %s", clean_name, json.dumps(log_data, indent=4))
                return data  # happy path

            log.error("Preset file is not a JSON object: %s", path)
            return {}
        except (OSError, json.JSONDecodeError) as e:
            log.error("Failed to load preset '%s' from %s: %s", clean_name, path, e)
            return {}

    def delete_preset(self, name: str) -> bool:
        """
        Delete the preset file. Returns True on success, False if disabled,
        file missing, or deletion fails.
        """
        clean_name = self._clean_name(name=name)
        if self.preset_dir is None:
            log.error("Cannot delete preset: preset directory is unavailable.")
            return False

        path = self._path_for(clean_name)
        if path is None:
            return False

        if not path.exists():
            log.warning("Cannot delete preset; file does not exist: %s", path)
            return False

        # Attempt to remove any keyring entries referenced by this preset
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                for section, fields in (data or {}).items():
                    try:
                        psk = (fields or {}).get("PSK")
                        if isinstance(psk, str) and self._is_token(psk):
                            # Labels were stored as f"{preset}:{section}"
                            self._keyring_delete(psk)
                    except Exception:
                        pass
        except Exception:
            # Non-fatal; continue with file deletion
            pass

        try:
            os.remove(path)
            log.info("Deleted preset '%s' at %s", clean_name, path)
            return True
        except OSError as e:
            log.error("Failed to delete preset '%s' at %s: %s", clean_name, path, e)
            return False
