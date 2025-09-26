# ui/panels/power_panel.py
from __future__ import annotations
from typing import Dict, Any, Optional

import customtkinter as ctk

from models.device_model import DeviceModel
from ui.common import make_collapsible, create_setting_row
from ui.panels.base_panel import BasePanel
from ui.validator import Validator

class PowerPanel(BasePanel):
    section_title = "Power"

    def build(self, parent: ctk.CTkFrame):
        _, self.frame, _ = make_collapsible(parent, self.section_title, open=False)

        # -- Variables --
        self.var_light_sleep = ctk.StringVar(value="")
        self.var_wait_bt = ctk.StringVar(value="")
        self.var_min_wake = ctk.StringVar(value="")

        # -- Validation --
        validate_numeric_cmd = self.frame.register(Validator.validate_is_numeric)

        # -- Widget Creation --
        create_setting_row(self.frame, "Light Sleep (s)", self.var_light_sleep, 0,
            validate="key", validatecommand=(validate_numeric_cmd, '%P'))
        
        create_setting_row(self.frame, "Wait Bluetooth (s)", self.var_wait_bt, 1,
            validate="key", validatecommand=(validate_numeric_cmd, '%P'))
        
        create_setting_row(self.frame, "Min Wake (s)", self.var_min_wake, 2,
            validate="key", validatecommand=(validate_numeric_cmd, '%P'))

    def apply_model(self, model: DeviceModel):
        if model.Power:
            ls = getattr(model.Power, "lsSecs", None)
            self.var_light_sleep.set("" if ls is None else str(ls))
            self.var_wait_bt.set("" if getattr(model.Power, "waitBluetoothSecs", None) is None else str(model.Power.waitBluetoothSecs))
            self.var_min_wake.set("" if getattr(model.Power, "minWakeSecs", None) is None else str(model.Power.minWakeSecs))

    def collect_model_overlay(self, m: DeviceModel) -> DeviceModel:
        def _to_int_or_none(s: str) -> Optional[int]:
            try:
                return None if s is None or str(s).strip() == "" else int(str(s).strip())
            except Exception:
                return None
                
        try:
            if m.Power:
                ls = _to_int_or_none(self.var_light_sleep.get())
                wb = _to_int_or_none(self.var_wait_bt.get())
                mw = _to_int_or_none(self.var_min_wake.get())
                if ls is not None:
                    if hasattr(m.Power, "lsSecs"): setattr(m.Power, "lsSecs", ls)
                if wb is not None:
                    if hasattr(m.Power, "waitBluetoothSecs"): setattr(m.Power, "waitBluetoothSecs", wb)
                if mw is not None:
                    if hasattr(m.Power, "minWakeSecs"): setattr(m.Power, "minWakeSecs", mw)
        except Exception:
            pass
        return m

    @property
    def _bindings(self) -> Dict[str, ctk.Variable]:
        return {
            "Light Sleep (s)": self.var_light_sleep,
            "Wait Bluetooth (s)": self.var_wait_bt,
            "Min Wake (s)": self.var_min_wake,
        }

    def preset_bindings(self) -> Dict[str, Dict[str, Any]]:
        return {self.section_title: self._bindings}

    def preset_apply(self, section_fields: Dict[str, Any]):
        power_fields = section_fields.get(self.section_title, {})
        for label, value in power_fields.items():
            var = self._bindings.get(label)
            if var:
                try:
                    var.set("" if value is None else str(value))
                except Exception:
                    pass
