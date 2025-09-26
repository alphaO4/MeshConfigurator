# ui/panels/bluetooth_panel.py
from __future__ import annotations
from typing import Dict, Any, Optional

import customtkinter as ctk
from CTkToolTip import CTkToolTip

from models.device_model import DeviceModel
from ui.common import make_collapsible, create_setting_row
from ui.panels.base_panel import BasePanel
from ui.validator import Validator

BLUETOOTH_MODES = ["RANDOM_PIN", "FIXED_PIN", "NO_PIN"]

class BluetoothPanel(BasePanel):
    section_title = "Bluetooth"
    
    def build(self, parent: ctk.CTkFrame):
        _, self.frame, _ = make_collapsible(parent, self.section_title, open=False)
        self.var_bt_enabled = ctk.BooleanVar(value=False)
        self.var_bt_fixed_pin = ctk.StringVar(value="")
        self.var_bt_mode = ctk.StringVar(value="RANDOM_PIN")

        # Register the validation command with the parent frame
        validate_len_cmd = self.frame.register(Validator.validate_string_length)

        bt_enabled_chk = create_setting_row(self.frame, "Bluetooth Enabled", self.var_bt_enabled, 0, kind="checkbox")
        self.tooltip_bt_enabled = CTkToolTip(bt_enabled_chk, message="")
        # Pass the validation arguments to the helper function
        self.ent_bt_pin = create_setting_row(
            self.frame,
            "PIN",
            self.var_bt_fixed_pin,
            1,
            validate="key",
            validatecommand=(validate_len_cmd, '6', '%P') # Max length of 6
        )
        CTkToolTip(self.ent_bt_pin, message="6 digit fixed pin")

        self._default_pin_fg_color = self.ent_bt_pin.cget("fg_color")
        self._default_pin_text_color = self.ent_bt_pin.cget("text_color")

        ctk.CTkLabel(self.frame, text="Mode").grid(row=2, column=0, sticky="w", padx=6, pady=4)
        self.opt_bt_mode = ctk.CTkOptionMenu(
            self.frame,
            values=BLUETOOTH_MODES,
            variable=self.var_bt_mode,
            width=180
        )
        self.opt_bt_mode.grid(row=2, column=1, padx=6, pady=4, sticky="ew")
        # CTkToolTip(self.opt_bt_mode, message="")

        self.var_bt_enabled.trace_add("write", self._update_pin_entry_state)
        self.var_bt_mode.trace_add("write", self._update_pin_entry_state)
        self.var_bt_enabled.trace_add("write", self._update_bt_tooltip)
        
        self._update_bt_tooltip()
        self._update_pin_entry_state()

    def _update_bt_tooltip(self, *args):
        """Updates the tooltip for the Bluetooth Enabled checkbox."""
        is_enabled = self.var_bt_enabled.get()
        new_message = "Disable Bluetooth" if is_enabled else "Enable Bluetooth"
        self.tooltip_bt_enabled.configure(message=new_message)
        
    def _update_pin_entry_state(self, *args):
        is_enabled = self.var_bt_enabled.get()
        is_fixed_pin_mode = (self.var_bt_mode.get() == "FIXED_PIN")

        if is_enabled and is_fixed_pin_mode:
            self.ent_bt_pin.configure(
                state="normal",
                fg_color=self._default_pin_fg_color,
                text_color=self._default_pin_text_color
            )
        else:
            self.ent_bt_pin.configure(
                state="disabled",
                fg_color="gray25",
                text_color="gray50"
            )
            self.var_bt_fixed_pin.set("")

    def apply_model(self, model: DeviceModel):
        if model.BlueTooth:
            self.var_bt_enabled.set(bool(getattr(model.BlueTooth, "enabled", False)))
            self.var_bt_fixed_pin.set("" if getattr(model.BlueTooth, "fixedPin", None) is None else str(model.BlueTooth.fixedPin))
            
            current_modes = list(self.opt_bt_mode.cget("values"))
            mode_val = getattr(model.BlueTooth, "mode", None) or "RANDOM_PIN"
            if mode_val not in current_modes:
                self.opt_bt_mode.configure(values=current_modes + [mode_val])
            self.var_bt_mode.set(mode_val)
        
        self._update_pin_entry_state()

    def collect_model_overlay(self, m: DeviceModel) -> DeviceModel:
        def _to_int_or_none(s: str) -> Optional[int]:
            try:
                return None if s is None or str(s).strip() == "" else int(str(s).strip())
            except Exception:
                return None
        
        try:
            if m.BlueTooth:
                setattr(m.BlueTooth, "enabled", bool(self.var_bt_enabled.get()))
                setattr(m.BlueTooth, "mode", self.var_bt_mode.get() or "RANDOM_PIN")
                pin_str = self.var_bt_fixed_pin.get()
                setattr(m.BlueTooth, "fixedPin", _to_int_or_none(pin_str) if pin_str.isdigit() else pin_str)

        except Exception:
            pass
        return m

    @property
    def _bindings(self) -> Dict[str, ctk.Variable]:
        return {
            "Bluetooth Enabled": self.var_bt_enabled,
            "PIN": self.var_bt_fixed_pin,
            "Mode": self.var_bt_mode,
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
