# mesh_config/controllers/device_controller.py
from __future__ import annotations

from typing import Optional, List, Dict, Any, Literal

from .device.device_reader import DeviceReader
from .device.device_writer_cli import DeviceWriterCLI
from models.device_model import MeshChannel, DeviceModel


class DeviceController:
    """
    Back-compat facade:
    - Reads via DeviceReader (API)
    - Writes via DeviceWriterCLI (CLI-backed)
    """

    def __init__(self, port: Optional[str]):
        self.reader = DeviceReader(port=port)
        # Writer reuses same port path; it will close/reopen around CLI calls
        self.writer = DeviceWriterCLI(iface=self.reader._iface)

    # --------------- lifecycle ---------------
    def close(self) -> None:
        self.reader.close()

    # --------------- READ API (unchanged) ---------------
    def identity(self, silent: bool = False) -> Dict[str, str]:
        return self.reader.identity(silent=silent)

    def snapshot(self) -> DeviceModel:
        return self.reader.snapshot()

    def list_channels(self) -> List[MeshChannel]:
        return self.reader.list_channels()

    # --------------- WRITE API (CLI-backed UPSERTS) ---------------
    def apply_from_models(self, original: DeviceModel, edited: DeviceModel) -> Dict[str, Any]:
        """
        Main entrypoint for your GUI's 'apply'. Provide the original snapshot and the edited model.
        Performs a diff and issues only the minimal CLI commands needed.
        """
        return self.writer.apply_from_models(original, edited)

    # Optional: maintain single-field upsert shims (map to edited model under the hood)
    def upsert_device_role(self, role: str) -> Dict[str, Any]:
        orig = self.reader.snapshot()
        edited = orig.model_copy(deep=True)
        edited.Device["role"] = role
        return self.writer.apply_from_models(orig, edited)

    def upsert_owner(self, owner_long: Optional[str], owner_short: Optional[str]) -> Dict[str, Any]:
        orig = self.reader.snapshot()
        edited = orig.model_copy(deep=True)
        if owner_long is not None:
            edited.UserInfo["owner"] = owner_long
        if owner_short is not None:
            edited.UserInfo["shortName"] = owner_short
        return self.writer.apply_from_models(orig, edited)

    def upsert_lora(self, *, region, modem_preset, channel_num, hop_limit, tx_enabled, tx_power) -> Dict[str, Any]:
        orig = self.reader.snapshot()
        edited = orig.model_copy(deep=True)
        if region is not None:
            edited.Lora["region"] = region
        if modem_preset is not None:
            edited.Lora["modemPreset"] = modem_preset
        if channel_num is not None:
            edited.Lora["channelNum"] = int(channel_num)
        if hop_limit is not None:
            edited.Lora["hopLimit"] = int(hop_limit)
        if tx_enabled is not None:
            edited.Lora["txEnabled"] = bool(tx_enabled)
        if tx_power is not None:
            edited.Lora["txPower"] = int(tx_power)
        return self.writer.apply_from_models(orig, edited)

    def upsert_power(self, *, light_sleep, wait_bt, min_wake) -> Dict[str, Any]:
        orig = self.reader.snapshot()
        edited = orig.model_copy(deep=True)
        if light_sleep is not None:
            edited.Power["lightSleepSeconds"] = int(light_sleep)
        if wait_bt is not None:
            edited.Power["waitBluetoothSeconds"] = int(wait_bt)
        if min_wake is not None:
            edited.Power["minWakeSeconds"] = int(min_wake)
        return self.writer.apply_from_models(orig, edited)

    def upsert_position(self, *, gps_update_secs, use_smart_position, smart_min_dist_m, smart_min_interval_s, broadcast_secs) -> Dict[str, Any]:
        orig = self.reader.snapshot()
        edited = orig.model_copy(deep=True)
        if gps_update_secs is not None:
            edited.Position["gpsUpdateInterval"] = int(gps_update_secs)
        if use_smart_position is not None:
            edited.Position["useSmartPositioning"] = bool(use_smart_position)
        if smart_min_dist_m is not None:
            edited.Position["smartMinimumDistance"] = int(smart_min_dist_m)
        if smart_min_interval_s is not None:
            edited.Position["smartMinimumInterval"] = int(smart_min_interval_s)
        if broadcast_secs is not None:
            edited.Position["positionBroadcastSecs"] = int(broadcast_secs)
        return self.writer.apply_from_models(orig, edited)

    def upsert_channel(
        self,
        *,
        index: int,
        name: Optional[str],
        gps: Optional[bool],
        precision_bits: int,
        uplink: bool,
        downlink: bool,
        key_b64: Optional[str] = None,
    ) -> Dict[str, Any]:
        orig = self.reader.snapshot()
        edited = orig.model_copy(deep=True)

        # find or append the channel in edited.MeshChannels
        ch = None
        for c in edited.MeshChannels:
            if int(c.index) == int(index):
                ch = c
                break
        if ch is None:
            # Create a new channel entry (secondary by definition)
            ch = MeshChannel(
                index=int(index),
                name=name,
                uplink_enabled=bool(uplink),
                downlink_enabled=bool(downlink),
                position_precision=int(precision_bits),
                psk_present=False,
                psk=key_b64,
                role=None,
            )
            edited.MeshChannels.append(ch)
        else:
            if name is not None:
                ch.name = name
            ch.uplink_enabled = bool(uplink)
            ch.downlink_enabled = bool(downlink)
            ch.position_precision = int(precision_bits)
            ch.psk = key_b64

        return self.writer.apply_from_models(orig, edited)