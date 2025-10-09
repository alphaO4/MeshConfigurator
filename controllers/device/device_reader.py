# mesh_config/controllers/device_reader.py
from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional

from ._device_common import DeviceBase
from models.device_model import DeviceModel, MeshChannel
from google.protobuf.json_format import MessageToDict


log = logging.getLogger(__name__)


def _safe_getattr(obj, name, default=None):
    try:
        return getattr(obj, name, default)
    except Exception:
        return default

def _pb_to_dict(pb, always_print_fields_with_no_presence: bool = True) -> Dict[str, Any]:
    return (
        MessageToDict(message=pb, always_print_fields_with_no_presence=always_print_fields_with_no_presence)
        if pb is not None
        else {}
    )

def _read_position_precision(ch_like: Any) -> int:
    """
    Accepts either a protobuf Channel/Settings object or a dict produced by MessageToDict.
    Tries moduleSettings.positionPrecision first (newer firmwares), then positionPrecision.
    """
    # dict path
    if isinstance(ch_like, dict):
        try:
            ms = ch_like.get("moduleSettings") or {}
            if "positionPrecision" in ms:
                return int(ms.get("positionPrecision"))
        except Exception:
            pass
        try:
            if "positionPrecision" in ch_like:
                return int(ch_like.get("positionPrecision"))
        except Exception:
            pass
        return 0

    # object path
    try:
        return int(getattr(ch_like.moduleSettings, "positionPrecision"))  # type: ignore[attr-defined]
    except Exception:
        pass
    try:
        return int(getattr(ch_like, "positionPrecision"))
    except Exception:
        pass
    return 0

class DeviceReader(DeviceBase):
    """
    Read-only ops (unchanged logic). Uses the Python API to fetch complete state.
    """

    def identity(self, silent: bool = False) -> Dict[str, str]:
        mi = _safe_getattr(self._iface, "myInfo")
        m = _safe_getattr(self._iface, "metadata")
        port = _safe_getattr(self._iface, "port") or _safe_getattr(self._iface, "devPath") or ""
        out = {
            "deviceId": str(_safe_getattr(mi, "deviceId", "") or ""),
            "hwModel": str(_safe_getattr(m, "hwModel", "") or _safe_getattr(mi, "hwModel", "") or ""),
            "firmwareVersion": str(_safe_getattr(m, "firmwareVersion", "") or ""),
            "port": port,
        }
        if not silent:
            log.info("identity: %s", out)
        return out


    def _get_owner(self, field: str):
        try:
            u = self._iface.getMyUser()
            if isinstance(u, dict):
                return u.get(field)
            # some custom wrappers expose attributes
            return getattr(u, field, None)
        except Exception:
            return None

    def snapshot(self, force_refresh: bool = False) -> DeviceModel:
        iface = self._iface
        if not iface:
            raise RuntimeError("Serial interface not initialized")

        ln = iface.localNode

        try:
            cfg_loaded = bool(getattr(getattr(ln, "localConfig", None), "device", None))
        except Exception:
            cfg_loaded = False

        ch_list = getattr(ln, "channels", None)
        channels_loaded = isinstance(ch_list, list) and len(ch_list) > 0


        if force_refresh or not cfg_loaded:
            try:
                log.info("Requesting fresh config from device...")
                ln.waitForConfig()
            except Exception:
                pass

        if force_refresh or not channels_loaded:
            try:
                log.info("Requesting fresh channel list from device...")
                ln.requestChannels()
            except Exception:
                pass
            # Wait briefly for channels to populate (API is async)
            import time as _time
            def _ready(lst):
                try:
                    if not (isinstance(lst, list) and len(lst) > 0):
                        return False
                    # Ready if we have primary or any non-disabled with settings
                    for _ch in lst:
                        d = _pb_to_dict(_ch)
                        if int(d.get("index", 0)) == 0:
                            return True
                        s = d.get("settings") or {}
                        if s and str(d.get("role")).upper() != 'DISABLED':
                            return True
                except Exception:
                    pass
                return False

            deadline = _time.monotonic() + 6.0
            while _time.monotonic() < deadline:
                ch_list = getattr(ln, "channels", None)
                if _ready(ch_list):
                    break
                _time.sleep(0.2)
            else:
                ch_list = getattr(ln, "channels", None)

        user = iface.getMyUser() or {}
        metadata = _pb_to_dict(iface.metadata)
        my_info = _pb_to_dict(iface.myInfo)
        metadata["port"] = getattr(iface, "port", None) or getattr(iface, "devPath", None) or ""

        local_cfg = _pb_to_dict(ln.localConfig)
        module_cfg = _pb_to_dict(ln.moduleConfig)
        mesh_channels: List[MeshChannel] = []
        for ch in (ch_list or []):
            chd = _pb_to_dict(ch)
            settings = chd.get("settings") or {}
            
            # Skip channels that are explicitly disabled or have no settings
            if not settings or str(chd.get("role")).upper() == 'DISABLED':
                continue

            psk = settings.get("psk")
            mesh_channels.append(
                MeshChannel(
                    index=int(chd.get("index", 0)),
                    name=(settings.get("name") or None),
                    uplink_enabled=bool(settings.get("uplinkEnabled", False)),
                    downlink_enabled=bool(settings.get("downlinkEnabled", False)),
                    position_precision=_read_position_precision(settings),
                    psk=psk,
                    psk_present=bool(psk),
                    role=chd.get("role"),
                )
            )

        return DeviceModel(
            UserInfo=user,
            MetaData=metadata,
            MyInfo=my_info,
            Device=local_cfg.get("device") or {},
            Power=local_cfg.get("power") or {},
            Lora=local_cfg.get("lora") or {},
            Position=local_cfg.get("position") or {},
            Display=local_cfg.get("display") or {},
            BlueTooth=local_cfg.get("bluetooth") or {},
            Network=local_cfg.get("network") or {},
            MeshChannels=mesh_channels,
            ModuleConfig=module_cfg,
        )


    def list_channels(self) -> List[MeshChannel]:
        # fixed to return MeshChannels from DeviceModel
        return self.snapshot().MeshChannels
