# ui/panels/modules_panel.py
from __future__ import annotations
from typing import Dict, Any, Optional, List

import customtkinter as ctk
from CTkToolTip import CTkToolTip

from models.device_model import DeviceModel
from ui.common import make_collapsible, create_setting_row
from ui.panels.base_panel import BasePanel
from ui.validator import Validator

# --- Constants for Option Menus ---
AUDIO_BITRATES = ["CODEC2_DEFAULT", "CODEC2_3200", "CODEC2_2400", "CODEC2_1600", "CODEC2_1400", "CODEC2_1300", "CODEC2_1200", "CODEC2_700B", "CODEC2_700"]
CANNED_MSG_SOURCES = ["rotEnc1", "_any", "upDownEnc1", "cardkb"]
SERIAL_MODES = ["DEFAULT", "SIMPLE", "PROTO", "TEXTMSG", "NMEA", "CALTOPO"]
SERIAL_BAUDS = ["BAUD_DEFAULT", "BAUD_110", "BAUD_300", "BAUD_600", "BAUD_1200", "BAUD_2400", "BAUD_4800", "BAUD_9600", "BAUD_19200", "BAUD_38400", "BAUD_57600", "BAUD_115200", "BAUD_230400", "BAUD_460800", "BAUD_576000", "BAUD_921600"]

class ModulesPanel(BasePanel):
    section_title = "Modules"

    def _to_int_or_none(self, s: str) -> Optional[int]:
        try:
            return None if s is None or str(s).strip() == "" else int(str(s).strip())
        except Exception:
            return None

    def build(self, parent: ctk.CTkFrame):
        _, self.frame, _ = make_collapsible(parent, self.section_title, open=False)
        
        self.update_callbacks = []

        # -- Validation Commands --
        validate_numeric_cmd = self.frame.register(Validator.validate_is_numeric)
        validate_range_cmd = self.frame.register(Validator.validate_numeric_range)

        # -- Sub-module frames --
        _, mod_mqtt, _ = make_collapsible(self.frame, "MQTT", open=False)
        _, mod_serial, _ = make_collapsible(self.frame, "Serial", open=False)
        _, mod_sf, _ = make_collapsible(self.frame, "StoreForward", open=False)
        _, mod_rt, _ = make_collapsible(self.frame, "RangeTest", open=False)
        _, mod_tel, _ = make_collapsible(self.frame, "Telemetry", open=False)
        _, mod_cm, _ = make_collapsible(self.frame, "CannedMessage", open=False)
        _, mod_audio, _ = make_collapsible(self.frame, "Audio", open=False)
        _, mod_rh, _ = make_collapsible(self.frame, "RemoteHardware", open=False)
        _, mod_ni, _ = make_collapsible(self.frame, "NeighborInfo", open=False)
        _, mod_al, _ = make_collapsible(self.frame, "AmbientLighting", open=False)
        _, mod_ds, _ = make_collapsible(self.frame, "DetectionSensor", open=False)
        _, mod_px, _ = make_collapsible(self.frame, "Paxcounter", open=False)

        # ==================== MQTT ====================
        self.var_mqtt_enabled = ctk.BooleanVar()
        self.var_mqtt_address = ctk.StringVar()
        self.var_mqtt_username = ctk.StringVar()
        self.var_mqtt_password = ctk.StringVar()
        self.var_mqtt_root = ctk.StringVar()
        self.var_mqtt_json_enabled = ctk.BooleanVar()
        self.var_mqtt_tls_enabled = ctk.BooleanVar()
        self.var_mqtt_proxy_to_client = ctk.BooleanVar()
        self.var_mqtt_map_reporting = ctk.BooleanVar()

        chk_mqtt_enabled = create_setting_row(mod_mqtt, "Enabled", self.var_mqtt_enabled, 0, kind="checkbox")
        self.mqtt_widgets = [
            create_setting_row(mod_mqtt, "Address", self.var_mqtt_address, 1),
            create_setting_row(mod_mqtt, "Username", self.var_mqtt_username, 2),
            create_setting_row(mod_mqtt, "Password", self.var_mqtt_password, 3, show="*"),
            create_setting_row(mod_mqtt, "Root", self.var_mqtt_root, 4),
            create_setting_row(mod_mqtt, "JSON Enabled", self.var_mqtt_json_enabled, 5, kind="checkbox"),
            create_setting_row(mod_mqtt, "TLS Enabled", self.var_mqtt_tls_enabled, 6, kind="checkbox"),
            create_setting_row(mod_mqtt, "Proxy To Client", self.var_mqtt_proxy_to_client, 7, kind="checkbox"),
            create_setting_row(mod_mqtt, "Map Reporting", self.var_mqtt_map_reporting, 8, kind="checkbox"),
        ]
        self._setup_dynamic_section(self.var_mqtt_enabled, self.mqtt_widgets, chk_mqtt_enabled, "Disable MQTT", "Enable MQTT")
        
        # ==================== Serial ====================
        self.var_serial_enabled = ctk.BooleanVar()
        self.var_serial_echo = ctk.BooleanVar()
        self.var_serial_rxd = ctk.StringVar()
        self.var_serial_txd = ctk.StringVar()
        self.var_serial_baud = ctk.StringVar(value="BAUD_DEFAULT")
        self.var_serial_timeout = ctk.StringVar()
        self.var_serial_mode = ctk.StringVar(value="DEFAULT")
        self.var_serial_override_console = ctk.BooleanVar()

        chk_serial_enabled = create_setting_row(mod_serial, "Enabled", self.var_serial_enabled, 0, kind="checkbox")
        self.serial_widgets = [
            create_setting_row(mod_serial, "Echo", self.var_serial_echo, 1, kind="checkbox"),
            create_setting_row(mod_serial, "RXD", self.var_serial_rxd, 2, validate="key", validatecommand=(validate_range_cmd, '0', '39', '%P')),
            create_setting_row(mod_serial, "TXD", self.var_serial_txd, 3, validate="key", validatecommand=(validate_range_cmd, '0', '33', '%P')),
            self._create_option_menu_row(mod_serial, "Baud", self.var_serial_baud, 4, SERIAL_BAUDS),
            create_setting_row(mod_serial, "Timeout", self.var_serial_timeout, 5, validate="key", validatecommand=(validate_numeric_cmd, '%P')),
            self._create_option_menu_row(mod_serial, "Mode", self.var_serial_mode, 6, SERIAL_MODES),
            create_setting_row(mod_serial, "Override Console Port", self.var_serial_override_console, 7, kind="checkbox"),
        ]
        CTkToolTip(self.serial_widgets[4], message="Timeout in milliseconds")
        self._setup_dynamic_section(self.var_serial_enabled, self.serial_widgets, chk_serial_enabled, "Disable Serial", "Enable Serial")
        
        # ==================== StoreForward ====================
        # FIX: use grid (not pack) inside mod_sf to avoid geometry manager conflicts
        ctk.CTkLabel(
            mod_sf,
            text="Only ESP32 devices with PSRAM can be a Store & Forward Server.",
            text_color="gray",
            wraplength=400
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=6, pady=4)

        self.var_sf_enabled = ctk.BooleanVar()
        self.var_sf_heartbeat = ctk.BooleanVar()
        self.var_sf_records = ctk.StringVar()
        self.var_sf_hist_max = ctk.StringVar()
        self.var_sf_hist_window = ctk.StringVar()
        self.var_sf_is_server = ctk.BooleanVar()

        # Shift rows by +1 because row 0 is used by the banner label above
        chk_sf_enabled = create_setting_row(mod_sf, "Enabled", self.var_sf_enabled, 1, kind="checkbox")
        self.sf_widgets = [
            create_setting_row(mod_sf, "Heartbeat", self.var_sf_heartbeat, 2, kind="checkbox"),
            create_setting_row(mod_sf, "Records", self.var_sf_records, 3, validate="key", validatecommand=(validate_numeric_cmd, '%P')),
            create_setting_row(mod_sf, "History Max", self.var_sf_hist_max, 4, validate="key", validatecommand=(validate_numeric_cmd, '%P')),
            create_setting_row(mod_sf, "History Window (m)", self.var_sf_hist_window, 5, validate="key", validatecommand=(validate_numeric_cmd, '%P')),
            create_setting_row(mod_sf, "Is Server", self.var_sf_is_server, 6, kind="checkbox"),
        ]
        CTkToolTip(self.sf_widgets[1], message="Max number of records saved by server")
        CTkToolTip(self.sf_widgets[3], message="Limits the time period (in minutes) a client can request.")
        self._setup_dynamic_section(self.var_sf_enabled, self.sf_widgets, chk_sf_enabled, "Disable Store & Forward", "Enable Store & Forward")

        # ==================== RangeTest ====================
        self.var_rt_enabled = ctk.BooleanVar()
        self.var_rt_sender = ctk.StringVar()
        self.var_rt_save = ctk.BooleanVar()
        self.var_rt_sender.trace_add("write", self._on_rt_sender_change)

        chk_rt_enabled = create_setting_row(mod_rt, "Enabled", self.var_rt_enabled, 0, kind="checkbox")
        self.rt_widgets = [
            create_setting_row(mod_rt, "Sender", self.var_rt_sender, 1, validate="key", validatecommand=(validate_numeric_cmd, '%P')),
            create_setting_row(mod_rt, "Save", self.var_rt_save, 2, kind="checkbox"),
        ]
        CTkToolTip(self.rt_widgets[0], message="Wait seconds between sending test packets. Set to 0 to disable.")
        CTkToolTip(self.rt_widgets[1], message="Android or Apple apps: Leave disabled.")
        self._setup_dynamic_section(self.var_rt_enabled, self.rt_widgets, chk_rt_enabled, "Disable Range Test", "Enable Range Test")

        # ==================== Telemetry ====================
        self.var_tel_dev_int = ctk.StringVar()
        self.var_tel_env_int = ctk.StringVar()
        self.var_tel_env_meas = ctk.BooleanVar()
        self.var_tel_env_screen = ctk.BooleanVar()
        self.var_tel_env_f = ctk.BooleanVar()
        self.var_tel_air_en = ctk.BooleanVar()
        self.var_tel_air_int = ctk.StringVar()
        self.var_tel_pwr_meas = ctk.BooleanVar()
        self.var_tel_pwr_int = ctk.StringVar()
        self.var_tel_pwr_screen = ctk.BooleanVar()
        self.var_tel_health_meas = ctk.BooleanVar()
        self.var_tel_health_int = ctk.StringVar()
        self.var_tel_health_screen = ctk.BooleanVar()

        create_setting_row(mod_tel, "Device Update (s)", self.var_tel_dev_int, 0, validate="key", validatecommand=(validate_numeric_cmd, '%P'))
        create_setting_row(mod_tel, "Env Update (s)", self.var_tel_env_int, 1, validate="key", validatecommand=(validate_numeric_cmd, '%P'))
        create_setting_row(mod_tel, "Env Measure", self.var_tel_env_meas, 2, kind="checkbox")
        create_setting_row(mod_tel, "Env Screen", self.var_tel_env_screen, 3, kind="checkbox")
        chk_tel_env_f = create_setting_row(mod_tel, "Env °F", self.var_tel_env_f, 4, kind="checkbox")
        CTkToolTip(chk_tel_env_f, message="Display Fahrenheit")
        create_setting_row(mod_tel, "Air Quality Enabled", self.var_tel_air_en, 5, kind="checkbox")
        create_setting_row(mod_tel, "Air Interval (s)", self.var_tel_air_int, 6, validate="key", validatecommand=(validate_numeric_cmd, '%P'))
        create_setting_row(mod_tel, "Power Measure", self.var_tel_pwr_meas, 7, kind="checkbox")
        create_setting_row(mod_tel, "Power Interval (s)", self.var_tel_pwr_int, 8, validate="key", validatecommand=(validate_numeric_cmd, '%P'))
        create_setting_row(mod_tel, "Power Screen", self.var_tel_pwr_screen, 9, kind="checkbox")
        create_setting_row(mod_tel, "Health Measure", self.var_tel_health_meas, 10, kind="checkbox")
        create_setting_row(mod_tel, "Health Interval (s)", self.var_tel_health_int, 11, validate="key", validatecommand=(validate_numeric_cmd, '%P'))
        create_setting_row(mod_tel, "Health Screen", self.var_tel_health_screen, 12, kind="checkbox")

        # ==================== CannedMessage ====================
        self.var_cm_enabled = ctk.BooleanVar()
        self.var_cm_allow_src = ctk.StringVar(value="rotEnc1")
        self.var_cm_send_bell = ctk.BooleanVar()
        chk_cm_enabled = create_setting_row(mod_cm, "Enabled", self.var_cm_enabled, 0, kind="checkbox")
        self.cm_widgets = [
            self._create_option_menu_row(mod_cm, "Allow Input Source", self.var_cm_allow_src, 1, CANNED_MSG_SOURCES),
            create_setting_row(mod_cm, "Send Bell", self.var_cm_send_bell, 2, kind="checkbox"),
        ]
        self._setup_dynamic_section(self.var_cm_enabled, self.cm_widgets, chk_cm_enabled, "Disable Canned Message", "Enable Canned Message")
        
        # ==================== Audio ====================
        self.var_audio_codec2 = ctk.BooleanVar()
        self.var_audio_ptt = ctk.StringVar()
        self.var_audio_bitrate = ctk.StringVar(value="CODEC2_DEFAULT")
        self.var_audio_ws = ctk.StringVar()
        self.var_audio_sd = ctk.StringVar()
        self.var_audio_din = ctk.StringVar()
        self.var_audio_sck = ctk.StringVar()
        chk_audio_enabled = create_setting_row(mod_audio, "Codec2 Enabled", self.var_audio_codec2, 0, kind="checkbox")
        self.audio_widgets = [
            create_setting_row(mod_audio, "PTT Pin", self.var_audio_ptt, 1, validate="key", validatecommand=(validate_range_cmd, '0', '39', '%P')),
            self._create_option_menu_row(mod_audio, "Bitrate", self.var_audio_bitrate, 2, AUDIO_BITRATES),
            create_setting_row(mod_audio, "I2S WS", self.var_audio_ws, 3, validate="key", validatecommand=(validate_range_cmd, '0', '34', '%P')),
            create_setting_row(mod_audio, "I2S SD", self.var_audio_sd, 4, validate="key", validatecommand=(validate_range_cmd, '0', '39', '%P')),
            create_setting_row(mod_audio, "I2S DIN", self.var_audio_din, 5, validate="key", validatecommand=(validate_range_cmd, '0', '34', '%P')),
            create_setting_row(mod_audio, "I2S SCK", self.var_audio_sck, 6, validate="key", validatecommand=(validate_range_cmd, '0', '34', '%P')),
        ]
        CTkToolTip(self.audio_widgets[1], message="The bitrate to use for audio")
        self._setup_dynamic_section(self.var_audio_codec2, self.audio_widgets, chk_audio_enabled, "Disable audio module", "Enable audio module")

        # ==================== RemoteHardware ====================
        self.var_rh_enabled = ctk.BooleanVar()
        chk_rh_enabled = create_setting_row(mod_rh, "Enabled", self.var_rh_enabled, 0, kind="checkbox")
        self._setup_dynamic_section(self.var_rh_enabled, [], chk_rh_enabled, "Disable Remote Hardware", "Enable Remote Hardware")

        # ==================== NeighborInfo ====================
        self.var_ni_enabled = ctk.BooleanVar()
        self.var_ni_interval = ctk.StringVar()
        self.var_ni_tx_lora = ctk.BooleanVar()
        chk_ni_enabled = create_setting_row(mod_ni, "Enabled", self.var_ni_enabled, 0, kind="checkbox")
        self.ni_widgets = [
            create_setting_row(mod_ni, "Update Interval (s)", self.var_ni_interval, 1, validate="key", validatecommand=(validate_numeric_cmd, '%P')),
            create_setting_row(mod_ni, "Transmit over LoRa", self.var_ni_tx_lora, 2, kind="checkbox"),
        ]
        self._setup_dynamic_section(self.var_ni_enabled, self.ni_widgets, chk_ni_enabled, "Disable Neighbor Info", "Enable Neighbor Info")

        # ==================== AmbientLighting ====================
        self.var_al_led = ctk.BooleanVar()
        self.var_al_current = ctk.StringVar()
        self.var_al_r = ctk.StringVar()
        self.var_al_g = ctk.StringVar()
        self.var_al_b = ctk.StringVar()
        chk_al_enabled = create_setting_row(mod_al, "LED State", self.var_al_led, 0, kind="checkbox")
        self.al_widgets = [
            create_setting_row(mod_al, "Current", self.var_al_current, 1, validate="key", validatecommand=(validate_numeric_cmd, '%P')),
            create_setting_row(mod_al, "Red", self.var_al_r, 2, validate="key", validatecommand=(validate_range_cmd, '0', '255', '%P')),
            create_setting_row(mod_al, "Green", self.var_al_g, 3, validate="key", validatecommand=(validate_range_cmd, '0', '255', '%P')),
            create_setting_row(mod_al, "Blue", self.var_al_b, 4, validate="key", validatecommand=(validate_range_cmd, '0', '255', '%P')),
        ]
        self._setup_dynamic_section(self.var_al_led, self.al_widgets, chk_al_enabled, "Disable LED", "Enable LED")

        # ==================== DetectionSensor ====================
        self.var_ds_enabled = ctk.BooleanVar()
        self.var_ds_min_bcast = ctk.StringVar()
        self.var_ds_trigger = ctk.StringVar()
        self.var_ds_state_bcast = ctk.StringVar()
        self.var_ds_send_bell = ctk.BooleanVar()
        self.var_ds_name = ctk.StringVar()
        self.var_ds_monitor_pin = ctk.StringVar()
        self.var_ds_pullup = ctk.BooleanVar()
        chk_ds_enabled = create_setting_row(mod_ds, "Enabled", self.var_ds_enabled, 0, kind="checkbox")
        self.ds_widgets = [
            create_setting_row(mod_ds, "Minimum Broadcast (s)", self.var_ds_min_bcast, 1, validate="key", validatecommand=(validate_numeric_cmd, '%P')),
            create_setting_row(mod_ds, "Trigger Type", self.var_ds_trigger, 2),
            create_setting_row(mod_ds, "State Broadcast (s)", self.var_ds_state_bcast, 3),
            create_setting_row(mod_ds, "Send Bell", self.var_ds_send_bell, 4, kind="checkbox"),
            create_setting_row(mod_ds, "Name", self.var_ds_name, 5),
            create_setting_row(mod_ds, "Monitor Pin", self.var_ds_monitor_pin, 6),
            create_setting_row(mod_ds, "Use Pullup", self.var_ds_pullup, 7, kind="checkbox"),
        ]
        self._setup_dynamic_section(self.var_ds_enabled, self.ds_widgets, chk_ds_enabled, "Disable Detection Sensor", "Enable Detection Sensor")

        # ==================== Paxcounter ====================
        self.var_px_enabled = ctk.BooleanVar()
        self.var_px_interval = ctk.StringVar()
        chk_px_enabled = create_setting_row(mod_px, "Enabled", self.var_px_enabled, 0, kind="checkbox")
        self.px_widgets = [
            create_setting_row(mod_px, "Update Interval (s)", self.var_px_interval, 1, validate="key", validatecommand=(validate_numeric_cmd, '%P')),
        ]
        self._setup_dynamic_section(self.var_px_enabled, self.px_widgets, chk_px_enabled, "Disable Paxcounter", "Enable Paxcounter")

    # ==================== Helper Methods for Dynamic UI ====================
    def _store_default_colors(self, widget: ctk.CTkEntry):
        widget.default_fg_color = widget.cget("fg_color")
        widget.default_text_color = widget.cget("text_color")

    def _create_option_menu_row(self, parent, label, var, row, values):
        ctk.CTkLabel(parent, text=label).grid(row=row, column=0, sticky="w", padx=6, pady=4)
        menu = ctk.CTkOptionMenu(parent, variable=var, values=values)
        menu.grid(row=row, column=1, padx=6, pady=4, sticky="ew")
        return menu

    def _setup_dynamic_section(
        self,
        control_var: ctk.BooleanVar,
        widgets: List[ctk.CTkBaseClass],
        tooltip_widget: ctk.CTkBaseClass,
        on_text: str,
        off_text: str,
    ):
        tooltip = CTkToolTip(tooltip_widget, message="")

        # Remember original colors for entries
        for w in widgets:
            if isinstance(w, ctk.CTkEntry):
                w.default_fg_color = w.cget("fg_color")
                w.default_text_color = w.cget("text_color")

        def _update_state(*_):
            is_enabled = bool(control_var.get())
            tooltip.configure(message=on_text if is_enabled else off_text)

            new_state = "normal" if is_enabled else "disabled"
            for w in widgets:
                if not w.winfo_exists():
                    continue
                # flip state
                try:
                    w.configure(state=new_state)
                except Exception:
                    pass

                # dim / restore entry colors and optionally clear text when disabling
                if isinstance(w, ctk.CTkEntry):
                    if is_enabled:
                        w.configure(
                            fg_color=getattr(w, "default_fg_color", w.cget("fg_color")),
                            text_color=getattr(w, "default_text_color", w.cget("text_color")),
                        )
                    else:
                        w.configure(fg_color="gray25", text_color="gray50")
                        # Clear the field when disabling to avoid stale values being written later
                        try:
                            w.delete(0, "end")
                        except Exception:
                            pass

        # bind + store callback
        control_var.trace_add("write", _update_state)
        if not hasattr(self, "update_callbacks"):
            self.update_callbacks = []
        self.update_callbacks.append(_update_state)

        # **Important**: apply current value immediately so UI state is correct on first render
        _update_state()

        control_var.trace_add("write", _update_state)
        self.update_callbacks.append(_update_state)

    def _on_rt_sender_change(self, *args):
        if self.var_rt_sender.get() == "0":
            self.var_rt_enabled.set(False)

    def apply_model(self, model: DeviceModel):
        mc = model.ModuleConfig
        if not mc: return
        
        if getattr(mc, "mqtt", None):
            self.var_mqtt_enabled.set(bool(mc.mqtt.enabled))
            self.var_mqtt_address.set(mc.mqtt.address or "")
            self.var_mqtt_username.set(mc.mqtt.username or "")
            self.var_mqtt_password.set(mc.mqtt.password or "")
            self.var_mqtt_root.set(mc.mqtt.root or "")
            self.var_mqtt_json_enabled.set(bool(mc.mqtt.json_enabled))
            self.var_mqtt_tls_enabled.set(bool(mc.mqtt.tls_enabled))
            self.var_mqtt_proxy_to_client.set(bool(mc.mqtt.proxy_to_client_enabled))
            self.var_mqtt_map_reporting.set(bool(mc.mqtt.map_reporting_enabled))

        if getattr(mc, "serial", None):
            self.var_serial_enabled.set(bool(mc.serial.enabled))
            self.var_serial_echo.set(bool(mc.serial.echo))
            self.var_serial_rxd.set("" if mc.serial.rxd is None else str(mc.serial.rxd))
            self.var_serial_txd.set("" if mc.serial.txd is None else str(mc.serial.txd))
            self.var_serial_baud.set(mc.serial.baud or "")
            self.var_serial_timeout.set("" if mc.serial.timeout is None else str(mc.serial.timeout))
            self.var_serial_mode.set(mc.serial.mode or "")
            self.var_serial_override_console.set(bool(mc.serial.override_console_serial_port))

        if getattr(mc, "store_forward", None):
            self.var_sf_enabled.set(bool(mc.store_forward.enabled))
            self.var_sf_heartbeat.set(bool(mc.store_forward.heartbeat))
            self.var_sf_records.set("" if mc.store_forward.records is None else str(mc.store_forward.records))
            self.var_sf_hist_max.set("" if mc.store_forward.history_return_max is None else str(mc.store_forward.history_return_max))
            self.var_sf_hist_window.set("" if mc.store_forward.history_return_window is None else str(mc.store_forward.history_return_window))
            self.var_sf_is_server.set(bool(mc.store_forward.is_server))

        if getattr(mc, "range_test", None):
            self.var_rt_enabled.set(bool(mc.range_test.enabled))
            self.var_rt_sender.set("" if mc.range_test.sender is None else str(mc.range_test.sender))
            self.var_rt_save.set(bool(mc.range_test.save))

        if getattr(mc, "telemetry", None):
            self.var_tel_dev_int.set("" if mc.telemetry.device_update_interval is None else str(mc.telemetry.device_update_interval))
            self.var_tel_env_int.set("" if mc.telemetry.environment_update_interval is None else str(mc.telemetry.environment_update_interval))
            self.var_tel_env_meas.set(bool(mc.telemetry.environment_measurement_enabled))
            self.var_tel_env_screen.set(bool(mc.telemetry.environment_screen_enabled))
            self.var_tel_env_f.set(bool(mc.telemetry.environment_display_fahrenheit))
            self.var_tel_air_en.set(bool(mc.telemetry.air_quality_enabled))
            self.var_tel_air_int.set("" if mc.telemetry.air_quality_interval is None else str(mc.telemetry.air_quality_interval))
            self.var_tel_pwr_meas.set(bool(mc.telemetry.power_measurement_enabled))
            self.var_tel_pwr_int.set("" if mc.telemetry.power_update_interval is None else str(mc.telemetry.power_update_interval))
            self.var_tel_pwr_screen.set(bool(mc.telemetry.power_screen_enabled))
            self.var_tel_health_meas.set(bool(mc.telemetry.health_measurement_enabled))
            self.var_tel_health_int.set("" if mc.telemetry.health_update_interval is None else str(mc.telemetry.health_update_interval))
            self.var_tel_health_screen.set(bool(mc.telemetry.health_screen_enabled))

        if getattr(mc, "canned_message", None):
            self.var_cm_enabled.set(bool(mc.canned_message.enabled))
            self.var_cm_allow_src.set(mc.canned_message.allow_input_source or "")
            self.var_cm_send_bell.set(bool(mc.canned_message.send_bell))

        if getattr(mc, "audio", None):
            self.var_audio_codec2.set(bool(mc.audio.codec2_enabled))
            self.var_audio_ptt.set("" if mc.audio.ptt_pin is None else str(mc.audio.ptt_pin))
            self.var_audio_bitrate.set(mc.audio.bitrate or "")
            self.var_audio_ws.set("" if mc.audio.i2s_ws is None else str(mc.audio.i2s_ws))
            self.var_audio_sd.set("" if mc.audio.i2s_sd is None else str(mc.audio.i2s_sd))
            self.var_audio_din.set("" if mc.audio.i2s_din is None else str(mc.audio_din))
            self.var_audio_sck.set("" if mc.audio.i2s_sck is None else str(mc.audio.i2s_sck))

        if getattr(mc, "remote_hardware", None):
            self.var_rh_enabled.set(bool(mc.remote_hardware.enabled))

        if getattr(mc, "neighbor_info", None):
            self.var_ni_enabled.set(bool(mc.neighbor_info.enabled))
            self.var_ni_interval.set("" if mc.neighbor_info.update_interval is None else str(mc.neighbor_info.update_interval))
            self.var_ni_tx_lora.set(bool(mc.neighbor_info.transmit_over_lora))

        if getattr(mc, "ambient_lighting", None):
            self.var_al_led.set(bool(mc.ambient_lighting.led_state))
            self.var_al_current.set("" if mc.ambient_lighting.current is None else str(mc.ambient_lighting.current))
            self.var_al_r.set("" if mc.ambient_lighting.red is None else str(mc.ambient_lighting.red))
            self.var_al_g.set("" if mc.ambient_lighting.green is None else str(mc.ambient_lighting.green))
            self.var_al_b.set("" if mc.ambient_lighting.blue is None else str(mc.ambient_lighting.blue))

        if getattr(mc, "detection_sensor", None):
            self.var_ds_enabled.set(bool(mc.detection_sensor.enabled))
            self.var_ds_min_bcast.set("" if mc.detection_sensor.minimum_broadcast_secs is None else str(mc.detection_sensor.minimum_broadcast_secs))
            self.var_ds_trigger.set(mc.detection_sensor.detection_trigger_type or "")
            self.var_ds_state_bcast.set("" if mc.detection_sensor.state_broadcast_secs is None else str(mc.detection_sensor.state_broadcast_secs))
            self.var_ds_send_bell.set(bool(mc.detection_sensor.send_bell))
            self.var_ds_name.set(mc.detection_sensor.name or "")
            self.var_ds_monitor_pin.set("" if mc.detection_sensor.monitor_pin is None else str(mc.detection_sensor.monitor_pin))
            self.var_ds_pullup.set(bool(mc.detection_sensor.use_pullup))

        if getattr(mc, "paxcounter", None):
            self.var_px_enabled.set(bool(mc.paxcounter.enabled))
            self.var_px_interval.set("" if mc.paxcounter.paxcounter_update_interval is None else str(mc.paxcounter.paxcounter_update_interval))

        if hasattr(self, 'update_callbacks'):
            for callback in self.update_callbacks:
                callback()

    def collect_model_overlay(self, m: Optional[DeviceModel]) -> Optional[DeviceModel]:
        """
        Overlay current UI state onto the provided DeviceModel.
        """
        if m is None:
            return None

        mc = getattr(m, "ModuleConfig", None)
        if mc is None:
            return m  # nothing to update

        def _to_int_or_none(s: str) -> Optional[int]:
            try:
                return None if s is None or str(s).strip() == "" else int(str(s).strip())
            except Exception:
                return None

        try:
            if getattr(mc, "mqtt", None):
                mc.mqtt.enabled = bool(self.var_mqtt_enabled.get())
                mc.mqtt.address = self.var_mqtt_address.get() or None
                mc.mqtt.username = self.var_mqtt_username.get() or None
                mc.mqtt.password = self.var_mqtt_password.get() or None
                mc.mqtt.root = self.var_mqtt_root.get() or None
                mc.mqtt.json_enabled = bool(self.var_mqtt_json_enabled.get())
                mc.mqtt.tls_enabled = bool(self.var_mqtt_tls_enabled.get())
                mc.mqtt.proxy_to_client_enabled = bool(self.var_mqtt_proxy_to_client.get())
                mc.mqtt.map_reporting_enabled = bool(self.var_mqtt_map_reporting.get())

            if getattr(mc, "serial", None):
                mc.serial.enabled = bool(self.var_serial_enabled.get())
                mc.serial.echo = bool(self.var_serial_echo.get())
                mc.serial.rxd = _to_int_or_none(self.var_serial_rxd.get())
                mc.serial.txd = _to_int_or_none(self.var_serial_txd.get())
                mc.serial.baud = self.var_serial_baud.get() or None
                mc.serial.timeout = _to_int_or_none(self.var_serial_timeout.get())
                mc.serial.mode = self.var_serial_mode.get() or None
                mc.serial.override_console_serial_port = bool(self.var_serial_override_console.get())

            if getattr(mc, "store_forward", None):
                mc.store_forward.enabled = bool(self.var_sf_enabled.get())
                mc.store_forward.heartbeat = bool(self.var_sf_heartbeat.get())
                mc.store_forward.records = _to_int_or_none(self.var_sf_records.get())
                mc.store_forward.history_return_max = _to_int_or_none(self.var_sf_hist_max.get())
                mc.store_forward.history_return_window = _to_int_or_none(self.var_sf_hist_window.get())
                mc.store_forward.is_server = bool(self.var_sf_is_server.get())

            if getattr(mc, "range_test", None):
                mc.range_test.enabled = bool(self.var_rt_enabled.get())
                mc.range_test.sender = _to_int_or_none(self.var_rt_sender.get())
                mc.range_test.save = bool(self.var_rt_save.get())

            if getattr(mc, "telemetry", None):
                mc.telemetry.device_update_interval = _to_int_or_none(self.var_tel_dev_int.get())
                mc.telemetry.environment_update_interval = _to_int_or_none(self.var_tel_env_int.get())
                mc.telemetry.environment_measurement_enabled = bool(self.var_tel_env_meas.get())
                mc.telemetry.environment_screen_enabled = bool(self.var_tel_env_screen.get())
                mc.telemetry.environment_display_fahrenheit = bool(self.var_tel_env_f.get())
                mc.telemetry.air_quality_enabled = bool(self.var_tel_air_en.get())
                mc.telemetry.air_quality_interval = _to_int_or_none(self.var_tel_air_int.get())
                mc.telemetry.power_measurement_enabled = bool(self.var_tel_pwr_meas.get())
                mc.telemetry.power_update_interval = _to_int_or_none(self.var_tel_pwr_int.get())
                mc.telemetry.power_screen_enabled = bool(self.var_tel_pwr_screen.get())
                mc.telemetry.health_measurement_enabled = bool(self.var_tel_health_meas.get())
                mc.telemetry.health_update_interval = _to_int_or_none(self.var_tel_health_int.get())
                mc.telemetry.health_screen_enabled = bool(self.var_tel_health_screen.get())

            if getattr(mc, "canned_message", None):
                mc.canned_message.enabled = bool(self.var_cm_enabled.get())
                mc.canned_message.allow_input_source = self.var_cm_allow_src.get() or None
                mc.canned_message.send_bell = bool(self.var_cm_send_bell.get())

            if getattr(mc, "audio", None):
                mc.audio.codec2_enabled = bool(self.var_audio_codec2.get())
                mc.audio.ptt_pin = _to_int_or_none(self.var_audio_ptt.get())
                mc.audio.bitrate = self.var_audio_bitrate.get() or None
                mc.audio.i2s_ws = _to_int_or_none(self.var_audio_ws.get())
                mc.audio.i2s_sd = _to_int_or_none(self.var_audio_sd.get())
                mc.audio.i2s_din = _to_int_or_none(self.var_audio_din.get())
                mc.audio.i2s_sck = _to_int_or_none(self.var_audio_sck.get())

            if getattr(mc, "remote_hardware", None):
                mc.remote_hardware.enabled = bool(self.var_rh_enabled.get())

            if getattr(mc, "neighbor_info", None):
                mc.neighbor_info.enabled = bool(self.var_ni_enabled.get())
                mc.neighbor_info.update_interval = _to_int_or_none(self.var_ni_interval.get())
                mc.neighbor_info.transmit_over_lora = bool(self.var_ni_tx_lora.get())

            if getattr(mc, "ambient_lighting", None):
                mc.ambient_lighting.led_state = bool(self.var_al_led.get())
                mc.ambient_lighting.current = _to_int_or_none(self.var_al_current.get())
                mc.ambient_lighting.red = _to_int_or_none(self.var_al_r.get())
                mc.ambient_lighting.green = _to_int_or_none(self.var_al_g.get())
                mc.ambient_lighting.blue = _to_int_or_none(self.var_al_b.get())

            if getattr(mc, "detection_sensor", None):
                mc.detection_sensor.enabled = bool(self.var_ds_enabled.get())
                mc.detection_sensor.minimum_broadcast_secs = _to_int_or_none(self.var_ds_min_bcast.get())
                mc.detection_sensor.detection_trigger_type = self.var_ds_trigger.get() or None
                mc.detection_sensor.state_broadcast_secs = _to_int_or_none(self.var_ds_state_bcast.get())
                mc.detection_sensor.send_bell = bool(self.var_ds_send_bell.get())
                mc.detection_sensor.name = self.var_ds_name.get() or None
                mc.detection_sensor.monitor_pin = _to_int_or_none(self.var_ds_monitor_pin.get())
                mc.detection_sensor.use_pullup = bool(self.var_ds_pullup.get())

            if getattr(mc, "paxcounter", None):
                mc.paxcounter.enabled = bool(self.var_px_enabled.get())
                mc.paxcounter.paxcounter_update_interval = _to_int_or_none(self.var_px_interval.get())

        except Exception:
            # Keep this defensive: never let UI overlay crash the apply path
            pass

        return m

    def preset_bindings(self) -> Dict[str, Dict[str, Any]]:
        return {
            "Modules.MQTT": {
                "Enabled": self.var_mqtt_enabled, "Address": self.var_mqtt_address, "Username": self.var_mqtt_username,
                "Password": self.var_mqtt_password, "Root": self.var_mqtt_root, "JSON Enabled": self.var_mqtt_json_enabled,
                "TLS Enabled": self.var_mqtt_tls_enabled, "Proxy To Client": self.var_mqtt_proxy_to_client,
                "Map Reporting": self.var_mqtt_map_reporting
            },
            "Modules.Serial": {
                "Enabled": self.var_serial_enabled, "Echo": self.var_serial_echo, "RXD": self.var_serial_rxd,
                "TXD": self.var_serial_txd, "Baud": self.var_serial_baud, "Timeout": self.var_serial_timeout,
                "Mode": self.var_serial_mode, "Override Console Port": self.var_serial_override_console
            },
            "Modules.StoreForward": {
                "Enabled": self.var_sf_enabled, "Heartbeat": self.var_sf_heartbeat, "Records": self.var_sf_records,
                "History Max": self.var_sf_hist_max, "History Window (s)": self.var_sf_hist_window,
                "Is Server": self.var_sf_is_server
            },
            "Modules.RangeTest": {
                "Enabled": self.var_rt_enabled, "Sender": self.var_rt_sender, "Save": self.var_rt_save
            },
            "Modules.Telemetry": {
                "Device Update (s)": self.var_tel_dev_int, "Env Update (s)": self.var_tel_env_int,
                "Env Measure": self.var_tel_env_meas, "Env Screen": self.var_tel_env_screen, "Env °F": self.var_tel_env_f,
                "Air Quality Enabled": self.var_tel_air_en, "Air Interval (s)": self.var_tel_air_int,
                "Power Measure": self.var_tel_pwr_meas, "Power Interval (s)": self.var_tel_pwr_int,
                "Power Screen": self.var_tel_pwr_screen, "Health Measure": self.var_tel_health_meas,
                "Health Interval (s)": self.var_tel_health_int, "Health Screen": self.var_tel_health_screen
            },
            "Modules.CannedMessage": {
                "Enabled": self.var_cm_enabled, "Allow Input Source": self.var_cm_allow_src,
                "Send Bell": self.var_cm_send_bell
            },
            "Modules.Audio": {
                "Codec2 Enabled": self.var_audio_codec2, "PTT Pin": self.var_audio_ptt, "Bitrate": self.var_audio_bitrate,
                "I2S WS": self.var_audio_ws, "I2S SD": self.var_audio_sd, "I2S DIN": self.var_audio_din,
                "I2S SCK": self.var_audio_sck
            },
            "Modules.RemoteHardware": {
                "Enabled": self.var_rh_enabled,
            },
            "Modules.NeighborInfo": {
                "Enabled": self.var_ni_enabled, "Update Interval (s)": self.var_ni_interval,
                "Transmit over LoRa": self.var_ni_tx_lora
            },
            "Modules.AmbientLighting": {
                "LED State": self.var_al_led, "Current": self.var_al_current, "Red": self.var_al_r,
                "Green": self.var_al_g, "Blue": self.var_al_b
            },
            "Modules.DetectionSensor": {
                "Enabled": self.var_ds_enabled, "Minimum Broadcast (s)": self.var_ds_min_bcast,
                "Trigger Type": self.var_ds_trigger, "State Broadcast (s)": self.var_ds_state_bcast,
                "Send Bell": self.var_ds_send_bell, "Name": self.var_ds_name, "Monitor Pin": self.var_ds_monitor_pin,
                "Use Pullup": self.var_ds_pullup
            },
            "Modules.Paxcounter": {
                "Enabled": self.var_px_enabled, "Update Interval (s)": self.var_px_interval,
            }
        }

    def preset_apply(self, section_fields: Dict[str, Any]):
        all_bindings = self.preset_bindings()
        for section_key, fields in section_fields.items():
            if section_key in all_bindings:
                module_bindings = all_bindings[section_key]
                for label, value in fields.items():
                    var = module_bindings.get(label)
                    if var:
                        try:
                            if isinstance(var, ctk.BooleanVar):
                                var.set(bool(value))
                            else:
                                var.set("" if value is None else str(value))
                        except Exception:
                            pass
