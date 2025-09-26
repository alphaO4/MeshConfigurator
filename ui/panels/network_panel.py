# ui/panels/network_panel.py
from __future__ import annotations
from typing import Dict, Any

import customtkinter as ctk
from CTkToolTip import CTkToolTip

from models.device_model import DeviceModel
from ui.common import make_collapsible, create_setting_row
from ui.panels.base_panel import BasePanel


ADDRESS_MODES=["DHCP", "STATIC"]
class NetworkPanel(BasePanel):
    section_title = "Network"

    def build(self, parent: ctk.CTkFrame):
        _, self.frame, _ = make_collapsible(parent, self.section_title, open=False)

        # -- Variables --
        self.var_net_ntp = ctk.StringVar(value="")
        self.var_net_wifi_enabled = ctk.BooleanVar(value=False)
        self.var_net_wifi_ssid = ctk.StringVar(value="")
        self.var_net_wifi_psk = ctk.StringVar(value="")
        self.var_net_eth_enabled = ctk.BooleanVar(value=False)
        self.var_address_mode = ctk.StringVar(value="DHCP")
        
        # -- Widget Creation --
        create_setting_row(self.frame, "NTP Server", self.var_net_ntp, 0)
        
        chk_wifi_enabled = create_setting_row(self.frame, "WiFi Enabled", self.var_net_wifi_enabled, 1, kind="checkbox")
        self.ent_wifi_ssid = create_setting_row(self.frame, "WiFi SSID", self.var_net_wifi_ssid, 2)
        self.ent_wifi_psk = create_setting_row(self.frame, "WiFi PSK", self.var_net_wifi_psk, 3, show="•")
        
        chk_eth_enabled = create_setting_row(self.frame, "Ethernet Enabled", self.var_net_eth_enabled, 4, kind="checkbox")
        
        ctk.CTkLabel(self.frame, text="Address Mode").grid(row=5, column=0, sticky="w", padx=6, pady=4)
        ctk.CTkOptionMenu(self.frame, values=ADDRESS_MODES, variable=self.var_address_mode).grid(row=5, column=1, padx=6, pady=4, sticky="ew")

        # -- Dynamic UI Setup --
        self.tooltip_wifi = CTkToolTip(chk_wifi_enabled, message="")
        self.tooltip_eth = CTkToolTip(chk_eth_enabled, message="")
        self._store_default_colors(self.ent_wifi_ssid)
        self._store_default_colors(self.ent_wifi_psk)

        self.var_net_wifi_enabled.trace_add("write", self._update_wifi_controls_state)
        self.var_net_eth_enabled.trace_add("write", self._update_eth_state)
        
        self._update_wifi_controls_state()
        self._update_eth_state()

    def _store_default_colors(self, widget: ctk.CTkEntry):
        """Helper to store a widget's default colors for state changes."""
        widget.default_fg_color = widget.cget("fg_color")
        widget.default_text_color = widget.cget("text_color")

    def _update_wifi_controls_state(self, *args):
        """Callback to update WiFi fields' state and tooltip based on the checkbox."""
        is_enabled = self.var_net_wifi_enabled.get()

        # Update Tooltip
        tooltip_msg = "Disable WiFi" if is_enabled else "Enable WiFi"
        self.tooltip_wifi.configure(message=tooltip_msg)

        # Update SSID and PSK entry fields
        for widget in [self.ent_wifi_ssid, self.ent_wifi_psk]:
            if is_enabled:
                widget.configure(
                    state="normal",
                    fg_color=widget.default_fg_color,
                    text_color=widget.default_text_color
                )
            else:
                widget.configure(state="disabled", fg_color="gray25", text_color="gray50")
        
        if not is_enabled:
            self.var_net_wifi_ssid.set("")
            self.var_net_wifi_psk.set("")
    
    def _update_eth_state(self, *args):
        """Callback to update WiFi fields' state and tooltip based on the checkbox."""
        is_enabled = self.var_net_eth_enabled.get()
        # Update Tooltip
        tooltip_msg = "Disable Ethernet" if is_enabled else "Enable Ethernet"
        self.tooltip_eth.configure(message=tooltip_msg)

    def apply_model(self, model: DeviceModel):
        if model.Network:
            self.var_net_ntp.set(getattr(model.Network, "ntpServer", None) or "")
            self.var_net_wifi_enabled.set(bool(getattr(model.Network, "wifiEnabled", False)))
            self.var_net_wifi_ssid.set(getattr(model.Network, "wifiSsid", None) or "")
            self.var_net_wifi_psk.set(getattr(model.Network, "wifiPsk", None) or "")
            self.var_net_eth_enabled.set(bool(getattr(model.Network, "ethEnabled", False)))
            self.var_address_mode.set(getattr(model.Network, "addressMode", None) or "")
        
        # Ensure the UI state reflects the loaded model
        self._update_wifi_controls_state()
            
    def collect_model_overlay(self, m: DeviceModel) -> DeviceModel:
        try:
            if m.Network:
                setattr(m.Network, "ntpServer", self.var_net_ntp.get() or None)
                setattr(m.Network, "wifiEnabled", bool(self.var_net_wifi_enabled.get()))
                setattr(m.Network, "wifiSsid", self.var_net_wifi_ssid.get() or None)
                setattr(m.Network, "wifiPsk", self.var_net_wifi_psk.get() or None)
                setattr(m.Network, "ethEnabled", bool(self.var_net_eth_enabled.get()))
                setattr(m.Network, "addressMode", self.var_address_mode.get() or None)
        except Exception:
            pass
        return m

    @property
    def _bindings(self) -> Dict[str, ctk.Variable]:
        return {
            "NTP Server": self.var_net_ntp,
            "WiFi Enabled": self.var_net_wifi_enabled,
            "WiFi SSID": self.var_net_wifi_ssid,
            "WiFi PSK": self.var_net_wifi_psk,
            "Ethernet Enabled": self.var_net_eth_enabled,
            "Address Mode": self.var_address_mode,
        }

    def preset_bindings(self) -> Dict[str, Dict[str, Any]]:
        return {self.section_title: self._bindings}

    def preset_apply(self, section_fields: Dict[str, Any]):
        fields = section_fields.get(self.section_title, {})
        for label, value in fields.items():
            var = self._bindings.get(label)
            if var:
                try:
                    if isinstance(var, ctk.BooleanVar):
                        var.set(bool(value))
                    else:
                        var.set("" if value is None else str(value))
                except Exception:
                    pass
