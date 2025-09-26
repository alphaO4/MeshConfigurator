# mesh_config/controllers/_device_common.py
from __future__ import annotations

import os
import sys
import time
import shlex
import shutil
import logging
import platform
import subprocess
from dataclasses import dataclass
from typing import Optional, Dict, Any, List

from meshtastic.serial_interface import SerialInterface

log = logging.getLogger(__name__)


def _now() -> float:
    return time.monotonic()


@dataclass
class CliResult:
    cmd: List[str]
    returncode: int
    stdout: str
    stderr: str
    duration_s: float


class DeviceBase:
    """
    Shared base: manages SerialInterface lifecycle and common helpers.
    """

    def __init__(self, port: Optional[str] = None, iface: Optional[SerialInterface] = None):
        if not port and not iface:
            raise ValueError("Device requires either a serial 'port' or an existing 'iface'")
        self._iface = iface or SerialInterface(devPath=port)
        self._owns_iface = iface is None

        # Port path for CLI routing (avoid auto-detect flakiness)
        self._port_path = getattr(self._iface, "port", None) or getattr(self._iface, "devPath", None)

        # Cached executable path for CLI
        self._cli_path = self._resolve_cli_path()
        log.debug("Resolved meshtastic CLI: %s", self._cli_path)

        # Initial warm-up (non-fatal if it times out)
        try:
            self._iface.localNode.waitForConfig()
        except Exception:
            pass

    # ------------- CLI plumbing -------------

    def _resolve_cli_path(self) -> str:
        """
        Finds the 'meshtastic' CLI executable. Resolution order:
        1) MESHTASTIC_CLI env var
        2) If frozen (PyInstaller), look next to the executable
        3) Dev-time: common dist paths relative to repo root
        4) PATH (meshtastic / meshtastic.exe)
        """
        # 1) Explicit override
        env = os.getenv("MESHTASTIC_CLI")
        if env:
            return env

        # 2) Packaged: next to the PyInstaller EXE
        try:
            if getattr(sys, "frozen", False):
                app_dir = os.path.dirname(sys.executable)
                candidates = [
                    os.path.join(app_dir, "meshtastic.exe"),
                    os.path.join(app_dir, "meshtastic"),
                ]
                for p in candidates:
                    if os.path.isfile(p):
                        return p
        except Exception:
            pass

        # 3) Dev-time: try repo-local dist locations
        try:
            here = os.path.dirname(os.path.abspath(__file__))
            # controllers/_device_common.py -> project root
            root = os.path.abspath(os.path.join(here, os.pardir, os.pardir))
            dev_candidates = [
                os.path.join(root, "dist", "release", "meshtastic.exe"),
                os.path.join(root, "dist", "release", "meshtastic"),
                os.path.join(root, "dist", "meshtastic.exe"),
                os.path.join(root, "dist", "meshtastic"),
            ]
            for p in dev_candidates:
                if os.path.isfile(p):
                    return p
        except Exception:
            pass

        # 4) PATH
        cand = shutil.which("meshtastic")
        if cand:
            return cand
        if platform.system().lower().startswith("win"):
            cand = shutil.which("meshtastic.exe")
            if cand:
                return cand

        # Fallback: let subprocess try/err with a clear message
        return "meshtastic"

    def _detach_for_cli(self) -> None:
        """
        Close the SerialInterface before invoking CLI to avoid port contention.
        """
        try:
            if self._iface is not None:
                self._iface.close()
        except Exception:
            log.debug("iface.close() suppressed", exc_info=True)

    def _reconnect_after_cli(self, wait_ready_s: float = 12.0) -> None:
        """
        Recreate the SerialInterface and wait briefly for config to be ready.
        """
        try:
            self._iface = SerialInterface(devPath=self._port_path)  # re-open
        except Exception as e:
            raise RuntimeError(f"Failed to reopen serial interface on {self._port_path}: {e}") from e

        start = _now()
        while _now() - start < wait_ready_s:
            try:
                self._iface.localNode.waitForConfig()
                # best-effort: load channels (non-fatal)
                try:
                    self._iface.localNode.requestChannels()
                except Exception:
                    pass
                return
            except Exception:
                time.sleep(0.2)
        # If we get here, still continue; caller can decide to mark a warning

    def _exec_cli(
        self,
        args: List[str],
        timeout_s: float = 25.0,
        mask_psk: bool = True,
    ) -> CliResult:
        """
        Execute the meshtastic CLI with provided args.
        - Automatically adds --port if we know it
        - Hides console windows on Windows
        - Captures stdout/stderr
        - Enforces timeout
        Returns stdout/stderr text and duration.
        """
        base_cmd = [self._cli_path]
        if self._port_path:
            base_cmd += ["--port", str(self._port_path)]
        cmd = base_cmd + args

        # Redact PSKs in logs
        to_log: List[str] = []
        for a in cmd:
            if mask_psk and (isinstance(a, str) and "base64:" in a):
                to_log.append("base64:<redacted>")
            else:
                to_log.append(a)
        log.debug("CLI exec: %s", " ".join(shlex.quote(x) for x in to_log))

        # Suppress console on Windows
        creationflags = 0
        startupinfo = None
        if os.name == "nt":
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            try:
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 0  # SW_HIDE
            except Exception:
                startupinfo = None

        start = _now()
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_s,
                shell=False,
                creationflags=creationflags,
                startupinfo=startupinfo,
            )
            dur = _now() - start
            return CliResult(
                cmd=cmd,
                returncode=proc.returncode,
                stdout=proc.stdout or "",
                stderr=proc.stderr or "",
                duration_s=dur,
            )
        except subprocess.TimeoutExpired as e:
            dur = _now() - start
            return CliResult(
                cmd=cmd,
                returncode=124,
                stdout=(e.stdout or ""),
                stderr=(e.stderr or "TIMEOUT"),
                duration_s=dur,
            )
        except FileNotFoundError as e:
            dur = _now() - start
            return CliResult(
                cmd=cmd,
                returncode=127,
                stdout="",
                stderr=f"CLI not found: {e}",
                duration_s=dur,
            )
        except Exception as e:
            dur = _now() - start
            return CliResult(
                cmd=cmd,
                returncode=1,
                stdout="",
                stderr=str(e),
                duration_s=dur,
            )

    # ------------- lifecycle -------------

    def close(self) -> None:
        try:
            if self._owns_iface and self._iface is not None:
                self._iface.close()
        except Exception:
            log.debug("close suppressed", exc_info=True)