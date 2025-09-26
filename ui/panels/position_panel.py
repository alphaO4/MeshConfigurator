# ui/panels/position_panel.py
from __future__ import annotations
from typing import Dict, Any, Optional

import customtkinter as ctk
from CTkToolTip import CTkToolTip

from models.device_model import DeviceModel
from ui.common import make_collapsible, create_setting_row
from ui.panels.base_panel import BasePanel
from ui.validator import Validator

class PositionPanel(BasePanel):
    section_title = "Position"

    def build(self, parent: ctk.CTkFrame):
        _, self.frame, _ = make_collapsible(parent, self.section_title, open=False)

        # -- Variables --
        self.var_gps_update = ctk.StringVar(value="")
        self.var_use_smart = ctk.BooleanVar(value=True)
        self.var_smart_dist = ctk.StringVar(value="")
        self.var_smart_interval = ctk.StringVar(value="")
        self.var_broadcast_secs = ctk.StringVar(value="")

        # -- Validation --
        validate_numeric_cmd = self.frame.register(Validator.validate_is_numeric)

        # -- Widget Creation --
        create_setting_row(self.frame, "GPS Update (s)", self.var_gps_update, 0,
            validate="key", validatecommand=(validate_numeric_cmd, '%P'))

        chk_use_smart = create_setting_row(self.frame, "Use Smart Position", self.var_use_smart, 1, kind="checkbox")
        
        self.ent_smart_dist = create_setting_row(self.frame, "Smart Min Dist (m)", self.var_smart_dist, 2,
            validate="key", validatecommand=(validate_numeric_cmd, '%P'))
        
        self.ent_smart_interval = create_setting_row(self.frame, "Smart Min Interval (s)", self.var_smart_interval, 3,
            validate="key", validatecommand=(validate_numeric_cmd, '%P'))
        
        create_setting_row(self.frame, "Broadcast (s)", self.var_broadcast_secs, 4,
            validate="key", validatecommand=(validate_numeric_cmd, '%P'))

        # -- Dynamic UI Setup --
        self.tooltip_smart = CTkToolTip(chk_use_smart, message="")
        self._store_default_colors(self.ent_smart_dist)
        self._store_default_colors(self.ent_smart_interval)

        self.var_use_smart.trace_add("write", self._update_smart_controls_state)
        self._update_smart_controls_state()

    def _store_default_colors(self, widget: ctk.CTkEntry):
        """Helper to store a widget's default colors for state changes."""
        widget.default_fg_color = widget.cget("fg_color")
        widget.default_text_color = widget.cget("text_color")

    def _update_smart_controls_state(self, *args):
        """Callback to update smart position fields and tooltip."""
        is_enabled = self.var_use_smart.get()
        
        tooltip_msg = "Disable smart position" if is_enabled else "Enable smart position"
        self.tooltip_smart.configure(message=tooltip_msg)

        for widget in [self.ent_smart_dist, self.ent_smart_interval]:
            if is_enabled:
                widget.configure(
                    state="normal",
                    fg_color=widget.default_fg_color,
                    text_color=widget.default_text_color
                )
            else:
                widget.configure(state="disabled", fg_color="gray25", text_color="gray50")
        
        if not is_enabled:
            self.var_smart_dist.set("")
            self.var_smart_interval.set("")

    def apply_model(self, model: DeviceModel):
        if model.Position:
            self.var_gps_update.set("" if getattr(model.Position, "gpsUpdateInterval", None) is None else str(model.Position.gpsUpdateInterval))
            self.var_use_smart.set(bool(getattr(model.Position, "positionBroadcastSmartEnabled", False)))
            self.var_smart_dist.set("" if getattr(model.Position, "broadcastSmartMinimumDistance", None) is None else str(model.Position.broadcastSmartMinimumDistance))
            self.var_smart_interval.set("" if getattr(model.Position, "broadcastSmartMinimumIntervalSecs", None) is None else str(model.Position.broadcastSmartMinimumIntervalSecs))
            self.var_broadcast_secs.set("" if getattr(model.Position, "positionBroadcastSecs", None) is None else str(model.Position.positionBroadcastSecs))
        
        self._update_smart_controls_state()

    def collect_model_overlay(self, m: DeviceModel) -> DeviceModel:
        def _to_int_or_none(s: str) -> Optional[int]:
            try:
                return None if s is None or str(s).strip() == "" else int(str(s).strip())
            except Exception:
                return None

        try:
            if m.Position:
                gps = _to_int_or_none(self.var_gps_update.get())
                if gps is not None:
                    setattr(m.Position, "gpsUpdateInterval", gps)

                use_smart = bool(self.var_use_smart.get())
                setattr(m.Position, "positionBroadcastSmartEnabled", use_smart)

                dist = _to_int_or_none(self.var_smart_dist.get())
                if dist is not None:
                    setattr(m.Position, "broadcastSmartMinimumDistance", dist)

                inter = _to_int_or_none(self.var_smart_interval.get())
                if inter is not None:
                    setattr(m.Position, "broadcastSmartMinimumIntervalSecs", inter)

                bcast = _to_int_or_none(self.var_broadcast_secs.get())
                if bcast is not None:
                    setattr(m.Position, "positionBroadcastSecs", bcast)
        except Exception:
            pass
        return m

    @property
    def _bindings(self) -> Dict[str, ctk.Variable]:
        return {
            "GPS Update (s)": self.var_gps_update,
            "Use Smart Position": self.var_use_smart,
            "Smart Min Dist (m)": self.var_smart_dist,
            "Smart Min Interval (s)": self.var_smart_interval,
            "Broadcast (s)": self.var_broadcast_secs,
        }

    def preset_bindings(self) -> Dict[str, Dict[str, Any]]:
        return {self.section_title: self._bindings}

    def preset_apply(self, section_fields: Dict[str, Any]):
        pos_fields = section_fields.get(self.section_title, {})
        for label, value in pos_fields.items():
            var = self._bindings.get(label)
            if var:
                try:
                    if isinstance(var, ctk.BooleanVar):
                        var.set(bool(value))
                    else:
                        var.set("" if value is None else str(value))
                except Exception:
                    pass
