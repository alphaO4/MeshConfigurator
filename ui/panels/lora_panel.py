# ui/panels/lora_panel.py
from __future__ import annotations
import customtkinter as ctk
from typing import Dict, Any, Optional
from CTkToolTip import CTkToolTip

from ui.validator import Validator 
from ui.common import make_collapsible, create_setting_row
from .base_panel import BasePanel

REGION_NAMES=['BR_902', 'LORA_24', 'PH_915', 'EU_433', 'RU', 'MY_919', 'NP_865', 'PH_868', 'NZ_865', 'UA_433', 'UNSET', 'PH_433', 'SG_923', 'ANZ', 'KZ_433', 'TH', 'TW', 'EU_868', 'US', 'JP', 'IN', 'ANZ_433', 'CN', 'KR', 'KZ_863', 'UA_868', 'MY_433']
MODEM_PRESET_NAMES=['MEDIUM_FAST', 'LONG_SLOW', 'MEDIUM_SLOW', 'SHORT_FAST', 'SHORT_TURBO', 'VERY_LONG_SLOW', 'LONG_FAST', 'SHORT_SLOW', 'LONG_MODERATE']
class LoRaPanel(BasePanel):
    section_title = "LoRa"

    def build(self, parent: ctk.CTkFrame):
        _, self.frame, _ = make_collapsible(parent, "LoRa", open=False)
        
        # Vars (names preserved)
        self.var_region = ctk.StringVar(value="US")
        self.var_modem = ctk.StringVar(value="LONG_FAST")
        self.var_channel_num = ctk.StringVar(value="20")
        self.var_hop_limit = ctk.StringVar(value="")
        self.var_tx_enabled = ctk.BooleanVar(value=True)
        self.var_tx_power = ctk.StringVar(value="")

        # 1. Register the numeric range validation command
        validate_range_cmd = self.frame.register(Validator.validate_numeric_range)

        # Region and Modem Preset Option Menus
        ctk.CTkLabel(self.frame, text="Region").grid(row=0, column=0, padx=6, pady=4, sticky="w")
        region_menu = ctk.CTkOptionMenu(
            self.frame,
            values=REGION_NAMES,
            variable=self.var_region,
            width=180
        )
        region_menu.grid(row=0, column=1, padx=6, pady=4, sticky="ew")

        ctk.CTkLabel(self.frame, text="Modem Preset").grid(row=1, column=0, padx=6, pady=4, sticky="w")
        modem_menu = ctk.CTkOptionMenu(
            self.frame,
            values=MODEM_PRESET_NAMES,
            variable=self.var_modem,
            width=180
        )
        modem_menu.grid(row=1, column=1, padx=6, pady=4, sticky="ew")
        
        channel_num=create_setting_row(self.frame, "Channel Num", self.var_channel_num, 2)
        CTkToolTip(channel_num, message="20 is the default for LongFast")
        # 2. Apply validation for Hop Limit (0-7)
        hop_limit=create_setting_row(
            self.frame, 
            "Hop Limit", 
            self.var_hop_limit, 
            3,
            validate="key",
            validatecommand=(validate_range_cmd, '0', '7', '%P')
        )
        CTkToolTip(hop_limit, message="1-7 hops allowed, default is 3.")
        # 3. Apply validation for TX Power (0-30)
        create_setting_row(
            self.frame, 
            "TX Power (0..30)", 
            self.var_tx_power, 
            4,
            validate="key",
            validatecommand=(validate_range_cmd, '0', '30', '%P')
        )
        
        create_setting_row(self.frame, "TX Enabled", self.var_tx_enabled, 5, kind="checkbox")

    def apply_model(self, model):
        if model.Lora:
            self.var_region.set(getattr(model.Lora, "region", None) or "US")
            self.var_modem.set(getattr(model.Lora, "modemPreset", None) or "")
            self.var_channel_num.set("" if getattr(model.Lora, "channelNum", None) is None else str(model.Lora.channelNum))
            self.var_hop_limit.set("" if getattr(model.Lora, "hopLimit", None) is None else str(model.Lora.hopLimit))
            self.var_tx_power.set("" if getattr(model.Lora, "txPower", None) is None else str(model.Lora.txPower))
            self.var_tx_enabled.set(bool(getattr(model.Lora, "txEnabled", True)))

    def _to_int_or_none(self, s: str) -> Optional[int]:
        try:
            return None if s is None or str(s).strip() == "" else int(str(s).strip())
        except Exception:
            return None

    def collect_model_overlay(self, m):
        try:
            if m.Lora:
                setattr(m.Lora, "region", self.var_region.get().strip() or None)
                setattr(m.Lora, "modemPreset", self.var_modem.get().strip() or None)
                chn = self._to_int_or_none(self.var_channel_num.get())
                if chn is not None: setattr(m.Lora, "channelNum", int(chn))
                hl = self._to_int_or_none(self.var_hop_limit.get())
                if hl is not None: setattr(m.Lora, "hopLimit", int(hl))
                tp = self._to_int_or_none(self.var_tx_power.get())
                if tp is not None: setattr(m.Lora, "txPower", int(tp))
                setattr(m.Lora, "txEnabled", bool(self.var_tx_enabled.get()))
        except Exception:
            pass
        return m
    
    @property
    def _bindings(self) -> Dict[str, ctk.Variable]:
        """Helper to map display labels to their variable objects."""
        return {
            "Region": self.var_region,
            "Modem Preset": self.var_modem,
            "Channel Num": self.var_channel_num,
            "Hop Limit": self.var_hop_limit,
            "TX Power (0..30)": self.var_tx_power,
            "TX Enabled": self.var_tx_enabled,
        }

    def preset_bindings(self) -> Dict[str, Dict[str, Any]]:
        """Returns a dict mapping display labels to the backing ctk.Variable objects."""
        return {"LoRa": self._bindings}

    def preset_apply(self, section_fields: Dict[str, Any]):
        """Applies preset values to the UI variables for the 'LoRa' section."""
        lora_fields = section_fields.get("LoRa", {})
        for label, value in lora_fields.items():
            var = self._bindings.get(label)
            if var:
                try:
                    if isinstance(var, ctk.BooleanVar):
                        var.set(bool(value))
                    else:
                        var.set("" if value is None else str(value))
                except Exception:
                    pass
