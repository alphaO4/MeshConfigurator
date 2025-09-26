# mesh_config/controllers/device_writer_cli.py
from __future__ import annotations

import time
import logging
from typing import Dict, Any, List, Optional

from ._device_common import DeviceBase, CliResult
from .device_reader import DeviceReader
from models.device_model import DeviceModel

log = logging.getLogger(__name__)


def _lower_bool(v) -> str:
    return "true" if bool(v) else "false"


def _norm_text(v: Any) -> Optional[str]:
    """Treat None/''/'   ' as None for diffing so we don't write empty strings."""
    if v is None:
        return None
    if isinstance(v, str):
        s = v.strip()
        return s if s else None
    return str(v)


class DeviceWriterCLI(DeviceBase):
    """
    CLI-backed writer:
    - Diffs original vs edited DeviceModel
    - Builds minimal CLI commands
    - Closes API iface, runs CLI, reconnects, refreshes
    - Returns ApplyReport
    """

    _REBOOT_SUSPECTS = {
        ("device", "role"),
        ("lora", "region"),
        ("lora", "modem_preset"),
        ("bluetooth", "enabled"),
    }

    _REDACT_KEYS = {"psk", "password", "pin", "wifi_psk", "fixed_pin", "wifiPsk", "fixedPin"}

    def __init__(self, port: Optional[str] = None, iface=None):
        super().__init__(port=port, iface=iface)
        self.reader = DeviceReader(iface=self._iface)

    def apply_from_models(self, original: DeviceModel, edited: DeviceModel) -> Dict[str, Any]:
        diff = self._build_diff(original, edited)
        if not any(diff.values()):
            log.info("no changes detected; skipping writes")
            return {"status": "no_change", "sections": {}}

        log.info("detaching API interface for CLI operations")
        self._detach_for_cli()

        report: Dict[str, Any] = {"status": "ok", "sections": {}, "errors": []}
        reboot_expected = self._is_reboot_expected(diff)
        log.info("reboot_expected=%s", reboot_expected)

        execution_plan = [
            ("device", self._exec_device, diff["device"]),
            ("owner", self._exec_owner, diff["owner"]),
            ("lora", self._exec_lora, diff["lora"]),
            ("power", self._exec_power, diff["power"]),
            ("position", self._exec_position, diff["position"]),
            ("display", self._exec_display, diff["display"]),
            ("bluetooth", self._exec_bluetooth, diff["bluetooth"]),
            ("network", self._exec_network, diff["network"]),
            ("channels", self._exec_channels, diff["channels"]),
            ("modules", self._exec_modules, diff["modules"]),
        ]

        any_success = False
        try:
            for section, fn, payload in execution_plan:
                if not payload:
                    continue
                # log.info("%s; changes=%s", section, self._redact(payload))
                sec_res = fn(payload)
                report["sections"][section] = sec_res
                if sec_res.get("status") == "success":
                    any_success = True
                elif sec_res.get("status") != "no_change":
                    report["status"] = "error"
                    report["errors"].append({section: sec_res})
                    log.warning("aborting after section=%s; status=%s", section, sec_res.get("status"))
                    break

            if reboot_expected or any_success:
                log.info("waiting 2.0s before reconnect...")
                time.sleep(2.0)

            try:
                log.info("attempting reconnect...")
                self._reconnect_after_cli(wait_ready_s=15.0)
                post_snapshot = self.reader.snapshot(force_refresh=True)
                report["post_snapshot"] = post_snapshot  # .model_dump()
                log.info("reconnect and post-apply snapshot successful")
            except Exception as e:
                report.setdefault("errors", []).append({"reconnect_or_snapshot": str(e)})
                log.exception("reconnect or post-apply snapshot failed")

        finally:
            self._detach_for_cli()
            log.info("released serial interface")

        return report

    def _build_diff(self, original: DeviceModel, edited: DeviceModel) -> Dict[str, Any]:
        o = original.model_dump()
        e = edited.model_dump()

        def sec_diff(sec: str, mapping: Dict[str, str]) -> Dict[str, Any]:
            out: Dict[str, Any] = {}
            o_sec, e_sec = o.get(sec) or {}, e.get(sec) or {}
            for model_key, cli_key in mapping.items():
                ov, ev = o_sec.get(model_key), e_sec.get(model_key)
                if ev is not None and ov != ev:
                    out[cli_key] = ev
            return out

        DEVICE_MAP = {"role": "device.role"}
        LORA_MAP = {
            "region": "lora.region", "modemPreset": "lora.modem_preset", "channelNum": "lora.channel_num",
            "hopLimit": "lora.hop_limit", "txEnabled": "lora.tx_enabled", "txPower": "lora.tx_power",
        }
        POWER_MAP = {
            "lsSecs": "power.ls_secs", "waitBluetoothSecs": "power.wait_bluetooth_secs",
            "minWakeSecs": "power.min_wake_secs",
        }
        POSITION_MAP = {
            "gpsUpdateInterval": "position.gps_update_interval",
            "positionBroadcastSmartEnabled": "position.position_broadcast_smart_enabled",
            "broadcastSmartMinimumDistance": "position.broadcast_smart_minimum_distance",
            "broadcastSmartMinimumIntervalSecs": "position.broadcast_smart_minimum_interval_secs",
            "positionBroadcastSecs": "position.position_broadcast_secs",
        }
        DISPLAY_MAP = {
            "screenOnSecs": "display.screen_on_secs", "gpsFormat": "display.gps_format",
            "autoScreenCarouselSecs": "display.auto_screen_carousel_secs", "units": "display.units",
            "oled": "display.oled", "displaymode": "display.displaymode", "headingBold": "display.heading_bold",
            "flipScreen": "display.flip_screen", "compassNorthTop": "display.compass_north_top",
            "wakeOnTapOrMotion": "display.wake_on_tap_or_motion", "compassOrientation": "display.compass_orientation",
            "use12hClock": "display.use_12h_clock",
        }
        BLUETOOTH_MAP = {
            "enabled": "bluetooth.enabled", "fixedPin": "bluetooth.fixed_pin", "mode": "bluetooth.mode",
        }
        NETWORK_MAP = {
            "ntpServer": "network.ntp_server", "wifiEnabled": "network.wifi_enabled",
            "wifiSsid": "network.wifi_ssid", "wifiPsk": "network.wifi_psk", "ethEnabled": "network.eth_enabled",
            "rsyslogServer": "network.rsyslog_server",
        }

        MODULE_MAPS = {
            "mqtt": {
                "enabled": "mqtt.enabled", "address": "mqtt.address", "username": "mqtt.username",
                "password": "mqtt.password", "root": "mqtt.root", "json_enabled": "mqtt.json_enabled",
                "tls_enabled": "mqtt.tls_enabled", "proxy_to_client_enabled": "mqtt.proxy_to_client_enabled",
                "map_reporting_enabled": "mqtt.map_reporting_enabled"
            },
            "serial": {
                "enabled": "serial.enabled", "echo": "serial.echo", "rxd": "serial.rxd", "txd": "serial.txd",
                "baud": "serial.baud", "timeout": "serial.timeout", "mode": "serial.mode",
                "override_console_serial_port": "serial.override_console_serial_port"
            },
            "store_forward": {
                "enabled": "store_forward.enabled", "heartbeat": "store_forward.heartbeat", "records": "store_forward.records",
                "history_return_max": "store_forward.history_return_max", "history_return_window": "store_forward.history_return_window",
                "is_server": "store_forward.is_server"
            },
            "range_test": {
                "enabled": "range_test.enabled", "sender": "range_test.sender", "save": "range_test.save"
            },
            "telemetry": {
                "device_update_interval": "telemetry.device_update_interval", "environment_update_interval": "telemetry.environment_update_interval",
                "environment_measurement_enabled": "telemetry.environment_measurement_enabled", "environment_screen_enabled": "telemetry.environment_screen_enabled",
                "environment_display_fahrenheit": "telemetry.environment_display_fahrenheit", "air_quality_enabled": "telemetry.air_quality_enabled",
                "air_quality_interval": "telemetry.air_quality_interval", "power_measurement_enabled": "telemetry.power_measurement_enabled",
                "power_update_interval": "telemetry.power_update_interval", "power_screen_enabled": "telemetry.power_screen_enabled",
                "health_measurement_enabled": "telemetry.health_measurement_enabled", "health_update_interval": "telemetry.health_update_interval",
                "health_screen_enabled": "telemetry.health_screen_enabled"
            },
            "canned_message": {
                "enabled": "canned_message.enabled", "allow_input_source": "canned_message.allow_input_source", "send_bell": "canned_message.send_bell"
            },
            "audio": {
                "codec2_enabled": "audio.codec2_enabled", "ptt_pin": "audio.ptt_pin", "bitrate": "audio.bitrate",
                "i2s_ws": "audio.i2s_ws", "i2s_sd": "audio.i2s_sd", "i2s_din": "audio.i2s_din", "i2s_sck": "audio.i2s_sck"
            },
            "remote_hardware": {"enabled": "remote_hardware.enabled"},
            "neighbor_info": {
                "enabled": "neighbor_info.enabled", "update_interval": "neighbor_info.update_interval",
                "transmit_over_lora": "neighbor_info.transmit_over_lora"
            },
            "ambient_lighting": {
                "led_state": "ambient_lighting.led_state", "current": "ambient_lighting.current", "red": "ambient_lighting.red",
                "green": "ambient_lighting.green", "blue": "ambient_lighting.blue"
            },
            "detection_sensor": {
                "enabled": "detection_sensor.enabled", "minimum_broadcast_secs": "detection_sensor.minimum_broadcast_secs",
                "detection_trigger_type": "detection_sensor.detection_trigger_type", "state_broadcast_secs": "detection_sensor.state_broadcast_secs",
                "send_bell": "detection_sensor.send_bell", "name": "detection_sensor.name", "monitor_pin": "detection_sensor.monitor_pin",
                "use_pullup": "detection_sensor.use_pullup"
            },
            "paxcounter": {
                "enabled": "paxcounter.enabled", "paxcounter_update_interval": "paxcounter.paxcounter_update_interval"
            }
        }

        diff = {
            "device": sec_diff("Device", DEVICE_MAP),
            "owner": {},
            "lora": sec_diff("Lora", LORA_MAP),
            "power": sec_diff("Power", POWER_MAP),
            "position": sec_diff("Position", POSITION_MAP),
            "display": sec_diff("Display", DISPLAY_MAP),
            "bluetooth": sec_diff("BlueTooth", BLUETOOTH_MAP),
            "network": sec_diff("Network", NETWORK_MAP),
            "channels": self._diff_channels(o.get("MeshChannels") or [], e.get("MeshChannels") or []),
            "modules": {},
        }

        # --- Fix bluetooth.fixed_pin: drop empty; coerce numeric string to int ---
        bt_key = "bluetooth.fixed_pin"
        if bt_key in diff["bluetooth"]:
            val = diff["bluetooth"][bt_key]
            if isinstance(val, str):
                s = val.strip()
                if not s:
                    diff["bluetooth"].pop(bt_key, None)  # don't emit empty
                elif s.isdigit():
                    diff["bluetooth"][bt_key] = int(s)   # send as integer

        # --- ModuleConfig diffs with default False suppression & blank normalization ---
        o_mc, e_mc = o.get("ModuleConfig") or {}, e.get("ModuleConfig") or {}

        def _norm(v):
            if isinstance(v, str):
                v = v.strip()
                return v if v else None
            return v

        for module_name, mapping in MODULE_MAPS.items():
            o_sec = o_mc.get(module_name) or {}
            e_sec = e_mc.get(module_name) or {}
            for model_key, cli_key in mapping.items():
                ov, ev = o_sec.get(model_key), e_sec.get(model_key)
                ovn, evn = _norm(ov), _norm(ev)

                if evn is None:
                    continue  # skip blanks entirely

                # avoid writing default False when original lacked a value
                if isinstance(evn, bool) and ov is None and evn is False:
                    continue

                if ovn != evn:
                    diff["modules"][cli_key] = evn

        # Owner names (special CLI)
        o_user, e_user = o.get("UserInfo") or {}, e.get("UserInfo") or {}
        long_o, long_e = o_user.get("longName"), e_user.get("longName")
        short_o, short_e = o_user.get("shortName"), e_user.get("shortName")
        if long_e is not None and long_e != long_o:
            diff["owner"]["owner_long"] = long_e
        if short_e is not None and short_e != short_o:
            diff["owner"]["owner_short"] = short_e
        import json
        log.info("updates: %s\n", json.dumps(self._redact(diff), indent=2, default=str))
        return diff


    def _diff_channels(self, orig: List[Dict[str, Any]], edit: List[Dict[str, Any]]) -> Dict[str, Any]:
        by_idx_o = {c["index"]: c for c in orig}
        by_idx_e = {c["index"]: c for c in edit}

        # Deletions: never delete index 0
        deletes = [idx for idx in by_idx_o if idx != 0 and idx not in by_idx_e]
        upserts: List[Dict[str, Any]] = []

        # Values that are “defaults” commonly injected by UI when no value was set
        suppress_if_none_defaults = {
            "uplink_enabled": False,
            "downlink_enabled": False,
            "position_precision": 0,
        }

        for idx, ed_ch in sorted(by_idx_e.items()):
            fields: Dict[str, Any] = {}
            orig_ch = by_idx_o.get(idx, {})

            # PSK: normalized compare (None/'' treated the same)
            psk_o = _norm_text(orig_ch.get("psk"))
            psk_e = _norm_text(ed_ch.get("psk"))
            if psk_o != psk_e:
                fields["psk"] = psk_e or "default"

            # Name: straight compare, but only if explicitly provided
            name_o, name_e = orig_ch.get("name"), ed_ch.get("name")
            if name_e is not None and name_e != name_o:
                fields["name"] = name_e

            # Other fields (keep them all eligible), but suppress None→default noise
            for model_key, cli_key in [
                ("uplink_enabled", "uplink_enabled"),
                ("downlink_enabled", "downlink_enabled"),
                ("position_precision", "module_settings.position_precision"),
            ]:
                val_o = orig_ch.get(model_key)
                val_e = ed_ch.get(model_key)
                if val_e is None:
                    continue

                # If original was None and edited equals a known default, treat as UI noise
                if model_key in suppress_if_none_defaults and val_o is None and val_e == suppress_if_none_defaults[model_key]:
                    continue

                if val_o != val_e:
                    fields[cli_key] = val_e

            if fields:
                upserts.append({"index": idx, "fields": fields})

        return {"deletes": sorted(deletes, reverse=True), "upserts": upserts}
    

    def _exec_generic(self, section_name: str, changes: Dict[str, Any], bool_keys: List[str] | set = ()) -> Dict[str, Any]:
        if not changes:
            return {"status": "no_change"}

        # support set/list for membership
        bool_keys = set(bool_keys) if not isinstance(bool_keys, set) else bool_keys

        # Stable ordering helps with logs/tests
        args: List[str] = []
        for k in sorted(changes.keys()):
            v = changes[k]
            # Treat as boolean either if key is declared or value is literally a bool
            val = _lower_bool(v) if (k in bool_keys or isinstance(v, bool)) else str(v)
            args.extend(["--set", k, val])

        res = self._run_cli_logged(section_name, args, timeout_s=20.0)
        return self._to_section_result(res, fields=sorted(changes.keys()))
    

    def _exec_device(self, changes: Dict[str, Any]) -> Dict[str, Any]:
        args = ["--set", next(iter(changes.keys())), str(next(iter(changes.values())))]
        res = self._run_cli_logged("device", args, timeout_s=20.0)
        return self._to_section_result(res, fields=list(changes.keys()))

    def _exec_owner(self, changes: Dict[str, Any]) -> Dict[str, Any]:
        args = []
        if "owner_long" in changes:
            args.extend(["--set-owner", str(changes["owner_long"])])
        if "owner_short" in changes:
            args.extend(["--set-owner-short", str(changes["owner_short"])])
        if not args:
            return {"status": "no_change"}
        res = self._run_cli_logged("owner", args, timeout_s=20.0)
        return self._to_section_result(res, fields=list(changes.keys()))

    def _exec_lora(self, changes: Dict[str, Any]) -> Dict[str, Any]:
        return self._exec_generic("lora", changes, bool_keys=["lora.tx_enabled"])

    def _exec_power(self, changes: Dict[str, Any]) -> Dict[str, Any]:
        return self._exec_generic("power", changes)

    def _exec_position(self, changes: Dict[str, Any]) -> Dict[str, Any]:
        return self._exec_generic("position", changes, bool_keys=["position.position_broadcast_smart_enabled"])

    def _exec_display(self, changes: Dict[str, Any]) -> Dict[str, Any]:
        bool_keys = [
            "display.heading_bold", "display.flip_screen", "display.compass_north_top",
            "display.wake_on_tap_or_motion", "display.use_12h_clock"
        ]
        return self._exec_generic("display", changes, bool_keys=bool_keys)

    def _exec_bluetooth(self, changes: Dict[str, Any]) -> Dict[str, Any]:
        return self._exec_generic("bluetooth", changes, bool_keys=["bluetooth.enabled"])

    def _exec_network(self, changes: Dict[str, Any]) -> Dict[str, Any]:
        bool_keys = ["network.wifi_enabled", "network.eth_enabled"]
        return self._exec_generic("network", changes, bool_keys=bool_keys)

    def _exec_channels(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        results = {"deleted": [], "upserts": []}
        overall_status = "no_change"

        for idx in plan.get("deletes", []):
            args = ["--ch-index", str(idx), "--ch-del"]
            res = self._run_cli_logged(f"channels:del[{idx}]", args, timeout_s=20.0)
            results["deleted"].append({"index": idx, **self._to_section_result(res, fields=[])})
            if res.returncode != 0:
                return {"status": "error", **results}
            overall_status = "success"

        for item in plan.get("upserts", []):
            idx, fields = item["index"], item["fields"]
            args = ["--ch-index", str(idx)]
            if idx > 0 and "name" in fields:
                args = ["--ch-add", fields.pop("name")]

            for key, value in fields.items():
                if key == "psk":
                    val = "default" if value == "default" else f"base64:{value}"
                    args.extend(["--ch-set", "psk", val])
                else:
                    val = _lower_bool(value) if isinstance(value, bool) else str(value)
                    args.extend(["--ch-set", key, val])

            res = self._run_cli_logged(f"channels:set[{idx}]", args, timeout_s=25.0)
            results["upserts"].append({"index": idx, **self._to_section_result(res, fields=list(fields.keys()))})
            if res.returncode != 0:
                return {"status": "error", **results}
            overall_status = "success"

        return {"status": overall_status, **results}

    def _exec_modules(self, changes: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute module changes via generic --set calls.
        Keys look like: "mqtt.enabled", "telemetry.device_update_interval", etc.
        """
        bool_keys = {
            "mqtt.enabled", "mqtt.json_enabled", "mqtt.tls_enabled", "mqtt.proxy_to_client_enabled", "mqtt.map_reporting_enabled",
            "serial.enabled", "serial.echo", "serial.override_console_serial_port",
            "store_forward.enabled", "store_forward.heartbeat", "store_forward.is_server",
            "range_test.enabled", "range_test.save",
            "telemetry.environment_measurement_enabled", "telemetry.environment_screen_enabled", "telemetry.environment_display_fahrenheit",
            "telemetry.air_quality_enabled", "telemetry.power_measurement_enabled", "telemetry.power_screen_enabled",
            "telemetry.health_measurement_enabled", "telemetry.health_screen_enabled",
            "canned_message.enabled", "canned_message.send_bell",
            "audio.codec2_enabled",
            "remote_hardware.enabled",
            "neighbor_info.enabled", "neighbor_info.transmit_over_lora",
            "ambient_lighting.led_state",
            "detection_sensor.enabled", "detection_sensor.send_bell", "detection_sensor.use_pullup",
            "paxcounter.enabled",
        }
        return self._exec_generic("modules", changes, bool_keys=bool_keys)

    def _is_reboot_expected(self, diff: Dict[str, Any]) -> bool:
        for sec, key in self._REBOOT_SUSPECTS:
            if diff.get(sec) and any(k.endswith(key) for k in diff[sec].keys()):
                return True
        return False

    def _run_cli_logged(self, section: str, args: List[str], *, timeout_s: float) -> CliResult:
        s_args = self._sanitize_args(args)
        log.info("running command: \n    meshtastic %s", " ".join(s_args))
        res = self._exec_cli(args, timeout_s=timeout_s)
        return res

    def _sanitize_args(self, args: List[str]) -> List[str]:
        out = args[:]
        i = 0
        while i < len(out):
            if out[i] == "--ch-set" and (i + 1 < len(out)) and out[i+1] == "psk":
                if i + 2 < len(out):
                    out[i + 2] = self._redact_value(out[i + 2])
                i += 3
            else:
                i += 1
        return out

    def _redact_value(self, val: str) -> str:
        if isinstance(val, str) and val.startswith("base64:"):
            return "base64:<redacted>"
        return "<redacted>"

    def _redact(self, obj: Any) -> Any:
        """
        Recursively traverses an object to redact specified keys and remove empty values.
        """
        # Base case for non-collection types
        if not isinstance(obj, (dict, list)):
            return obj

        # Handle lists: recurse, then filter out empty items
        if isinstance(obj, list):
            processed_list = [self._redact(item) for item in obj]
            # Keep items that are not considered empty
            return [
                item for item in processed_list
                if item is not None and item != "" and item != [] and item != {}
            ]

        # Handle dictionaries: recurse, then filter out keys with empty values
        if isinstance(obj, dict):
            new_dict = {}
            for k, v in obj.items():
                # Redact keys first
                if k in self._REDACT_KEYS:
                    new_dict[k] = "<redacted>"
                    continue

                # Recurse on the value
                processed_value = self._redact(v)
                
                # Add key-value pair only if the processed value is not empty
                if processed_value is not None and processed_value != "" and processed_value != [] and processed_value != {}:
                    new_dict[k] = processed_value
            return new_dict
        

    def _to_section_result(self, res: CliResult, *, fields: List[str]) -> Dict[str, Any]:
        if res.returncode == 0:
            status = "success"
        elif res.returncode == 124:
            status = "timeout"
        else:
            status = "error"
        return {
            "status": status,
            "fieldsChanged": fields if status == "success" else [],
            "duration_s": round(res.duration_s, 3),
            "stdout": (res.stdout or "").strip()[:400],
            "stderr": (res.stderr or "").strip()[:400],
        }