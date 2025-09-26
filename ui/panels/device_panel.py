# ui/panels/device_panel.py
from __future__ import annotations
import customtkinter as ctk
from typing import Dict, Any
from CTkToolTip import CTkToolTip


from ui.validator import Validator
from ui.common import make_collapsible, create_setting_row
from .base_panel import BasePanel

class DevicePanel(BasePanel):
    section_title = "Device"

    def build(self, parent: ctk.CTkFrame):
        _, self.frame, _ = make_collapsible(parent, "Device", open=True)

        validate_len_cmd = self.frame.register(Validator.validate_string_length)

        # Vars (names preserved)
        self.var_owner_long = ctk.StringVar()
        self.var_owner_short = ctk.StringVar()
        self.var_role = ctk.StringVar(value="CLIENT")

        # Owner (Long) - Max 39 chars
        ctk.CTkLabel(self.frame, text="Owner (Long)").grid(row=0, column=0, padx=6, pady=4, sticky="w")
        owner_long_entry = ctk.CTkEntry(
            self.frame,
            textvariable=self.var_owner_long,
            validate="key",
            validatecommand=(validate_len_cmd, '39', '%P')
        )
        owner_long_entry.grid(row=0, column=1, padx=6, pady=4, sticky="ew")
        CTkToolTip(owner_long_entry, message="39 character max")
        
        # Owner (Short) - Max 4 chars
        ctk.CTkLabel(self.frame, text="Owner (Short)").grid(row=1, column=0, padx=6, pady=4, sticky="w")
        owner_short_entry = ctk.CTkEntry(
            self.frame,
            textvariable=self.var_owner_short,
            validate="key",
            validatecommand=(validate_len_cmd, '4', '%P')
        )
        owner_short_entry.grid(row=1, column=1, padx=6, pady=4, sticky="ew")
        CTkToolTip(owner_short_entry, message="4 character max")
        # Role (unchanged)
        ctk.CTkLabel(self.frame, text="Role").grid(row=2, column=0, sticky="w", padx=6, pady=4)
        self.opt_role = ctk.CTkOptionMenu(
            self.frame,
            values=[
                "CLIENT", "CLIENT_MUTE", "CLIENT_HIDDEN", "TRACKER", "LOST_AND_FOUND",
                "SENSOR", "TAK", "TAK_TRACKER", "REPEATER", "ROUTER", "ROUTER_LATE"
            ],
            variable=self.var_role,
        )
        self.opt_role.grid(row=2, column=1, padx=6, pady=4, sticky="ew")

    def apply_model(self, model):
        if model.UserInfo:
            self.var_owner_long.set(getattr(model.UserInfo, "longName", "") or "")
            self.var_owner_short.set(getattr(model.UserInfo, "shortName", "") or "")
        if model.Device:
            self.var_role.set(getattr(model.Device, "role", None) or "CLIENT")

    def collect_model_overlay(self, m):
        try:
            if m.Device:
                setattr(m.Device, "role", self.var_role.get().strip() or "CLIENT")
        except Exception:
            pass
        try:
            if m.UserInfo:
                setattr(m.UserInfo, "longName", self.var_owner_long.get().strip() or None)
                setattr(m.UserInfo, "shortName", self.var_owner_short.get().strip() or None)
                if hasattr(m.UserInfo, "owner"):
                    setattr(m.UserInfo, "owner", self.var_owner_long.get().strip() or None)
        except Exception:
            pass
        return m

    @property
    def _bindings(self) -> Dict[str, ctk.Variable]:
        """Helper to map display labels to their variable objects."""
        return {
            "Owner (Long)": self.var_owner_long,
            "Owner (Short)": self.var_owner_short,
            "Role": self.var_role,
        }

    def preset_bindings(self) -> Dict[str, Dict[str, Any]]:
        """Returns a dict mapping display labels to the backing ctk.Variable objects."""
        return {"Device": self._bindings}

    def preset_apply(self, section_fields: Dict[str, Any]):
        """Applies preset values to the UI variables for the 'Device' section."""
        device_fields = section_fields.get("Device", {})
        for label, value in device_fields.items():
            var = self._bindings.get(label)
            if var:
                try:
                    var.set("" if value is None else str(value))
                except Exception:
                    pass # Or log error
