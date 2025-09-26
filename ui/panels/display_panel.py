# ui/panels/display_panel.py
from __future__ import annotations
from typing import Dict, Any, Optional

import customtkinter as ctk

from models.device_model import DeviceModel
from ui.common import make_collapsible, create_setting_row
from ui.panels.base_panel import BasePanel
from ui.validator import Validator

# Constants for the OptionMenus
GPS_FORMAT_MAP = {
    "DEC": "Decimal Degrees",
    "DMS": "Degrees Minutes Seconds",
    "UTM": "Universal Transverse Mercator",
    "MGRS": "Military Grid Reference System",
    "OLC": "Open Location Code (Plus Codes)",
    "OSGR": "Ordnance Survey Grid Reference",
}
UNITS_MODES = ["METRIC", "IMPERIAL"]
OLED_MODE_MAP = {
    "OLED_AUTO": "Auto detect display controller",
    "OLED_SSD1306": "Always use SSD1306 driver",
    "OLED_SH1106": "Always use SH1106 driver",
    "OLED_SH1107": "Always use SH1107 driver (Geometry 128x128)",
}
DISPLAY_MODES = ["DEFAULT", "TWOCOLOR", "INVERTED", "COLOR"]


class DisplayPanel(BasePanel):
    section_title = "Display"

    def build(self, parent: ctk.CTkFrame):
        _, self.frame, _ = make_collapsible(parent, self.section_title, open=False)

        # -- Variables --
        self.var_disp_screen_secs = ctk.StringVar(value="")
        self.var_disp_gps_fmt = ctk.StringVar(value="DEC")
        self.var_disp_auto_carousel = ctk.StringVar(value="")
        self.var_disp_units = ctk.StringVar(value="METRIC")
        self.var_disp_oled = ctk.StringVar(value="OLED_AUTO")
        self.var_disp_mode = ctk.StringVar(value="DEFAULT")
        self.var_disp_compass_orientation = ctk.StringVar(value="")
        self.var_disp_heading_bold = ctk.BooleanVar(value=False)
        self.var_disp_flip = ctk.BooleanVar(value=False)
        self.var_disp_north_top = ctk.BooleanVar(value=False)
        self.var_disp_wake_on_motion = ctk.BooleanVar(value=False)
        self.var_disp_use12h = ctk.BooleanVar(value=False)
        
        # -- Validation --
        validate_numeric_cmd = self.frame.register(Validator.validate_is_numeric)

        # -- Widget Creation --
        create_setting_row(self.frame, "Screen On (s)", self.var_disp_screen_secs, 0,
            validate="key", validatecommand=(validate_numeric_cmd, '%P'))
        
        # GPS Format Dropdown & Dynamic Description
        ctk.CTkLabel(self.frame, text="GPS Format").grid(row=1, column=0, sticky="w", padx=6, pady=4)
        ctk.CTkOptionMenu(self.frame, values=list(GPS_FORMAT_MAP.keys()), variable=self.var_disp_gps_fmt).grid(row=1, column=1, padx=6, pady=4, sticky="ew")
        self.lbl_gps_desc = ctk.CTkLabel(self.frame, text="", text_color="gray", font=ctk.CTkFont(size=11))
        self.lbl_gps_desc.grid(row=2, column=1, sticky="w", padx=6, pady=(0, 4))
        
        create_setting_row(self.frame, "Auto Carousel (s)", self.var_disp_auto_carousel, 3,
            validate="key", validatecommand=(validate_numeric_cmd, '%P'))
        
        # Units Dropdown
        ctk.CTkLabel(self.frame, text="Units").grid(row=4, column=0, sticky="w", padx=6, pady=4)
        ctk.CTkOptionMenu(self.frame, values=UNITS_MODES, variable=self.var_disp_units).grid(row=4, column=1, padx=6, pady=4, sticky="ew")

        # OLED Mode Dropdown & Dynamic Description
        ctk.CTkLabel(self.frame, text="OLED Mode").grid(row=5, column=0, sticky="w", padx=6, pady=4)
        ctk.CTkOptionMenu(self.frame, values=list(OLED_MODE_MAP.keys()), variable=self.var_disp_oled).grid(row=5, column=1, padx=6, pady=4, sticky="ew")
        self.lbl_oled_desc = ctk.CTkLabel(self.frame, text="", text_color="gray", font=ctk.CTkFont(size=11))
        self.lbl_oled_desc.grid(row=6, column=1, sticky="w", padx=6, pady=(0, 4))

        # Display Mode Dropdown
        ctk.CTkLabel(self.frame, text="Display Mode").grid(row=7, column=0, sticky="w", padx=6, pady=4)
        ctk.CTkOptionMenu(self.frame, values=DISPLAY_MODES, variable=self.var_disp_mode).grid(row=7, column=1, padx=6, pady=4, sticky="ew")
        
        create_setting_row(self.frame, "Compass Orientation", self.var_disp_compass_orientation, 8)
        
        # Checkboxes (starting at the next available row)
        create_setting_row(self.frame, "Heading Bold", self.var_disp_heading_bold, 9, kind="checkbox")
        create_setting_row(self.frame, "Flip Screen", self.var_disp_flip, 10, kind="checkbox")
        create_setting_row(self.frame, "Compass North Top", self.var_disp_north_top, 11, kind="checkbox")
        create_setting_row(self.frame, "Wake on Tap/Motion", self.var_disp_wake_on_motion, 12, kind="checkbox")
        create_setting_row(self.frame, "Use 12h Clock", self.var_disp_use12h, 13, kind="checkbox")

        # -- Traces for Dynamic Labels --
        self.var_disp_gps_fmt.trace_add("write", self._update_descriptions)
        self.var_disp_oled.trace_add("write", self._update_descriptions)
        self._update_descriptions() # Set initial descriptions

    def _update_descriptions(self, *args):
        """Update descriptive labels based on current selections."""
        selected_gps = self.var_disp_gps_fmt.get()
        self.lbl_gps_desc.configure(text=GPS_FORMAT_MAP.get(selected_gps, ""))
        
        selected_oled = self.var_disp_oled.get()
        self.lbl_oled_desc.configure(text=OLED_MODE_MAP.get(selected_oled, ""))
        
    def apply_model(self, model: DeviceModel):
        if model.Display:
            self.var_disp_screen_secs.set("" if getattr(model.Display, "screenOnSecs", None) is None else str(model.Display.screenOnSecs))
            self.var_disp_gps_fmt.set(getattr(model.Display, "gpsFormat", None) or "DEC")
            self.var_disp_auto_carousel.set("" if getattr(model.Display, "autoScreenCarouselSecs", None) is None else str(model.Display.autoScreenCarouselSecs))
            self.var_disp_units.set(getattr(model.Display, "units", None) or "METRIC")
            self.var_disp_oled.set(getattr(model.Display, "oled", None) or "OLED_AUTO")
            self.var_disp_mode.set(getattr(model.Display, "displaymode", None) or "DEFAULT")
            self.var_disp_heading_bold.set(bool(getattr(model.Display, "headingBold", False)))
            self.var_disp_flip.set(bool(getattr(model.Display, "flipScreen", False)))
            self.var_disp_north_top.set(bool(getattr(model.Display, "compassNorthTop", False)))
            self.var_disp_wake_on_motion.set(bool(getattr(model.Display, "wakeOnTapOrMotion", False)))
            self.var_disp_compass_orientation.set(getattr(model.Display, "compassOrientation", None) or "")
            self.var_disp_use12h.set(bool(getattr(model.Display, "use12hClock", False)))

    def collect_model_overlay(self, m: DeviceModel) -> DeviceModel:
        def _to_int_or_none(s: str) -> Optional[int]:
            try:
                return None if s is None or str(s).strip() == "" else int(str(s).strip())
            except Exception:
                return None

        try:
            if m.Display:
                screen_secs = _to_int_or_none(self.var_disp_screen_secs.get())
                if screen_secs is not None: setattr(m.Display, "screenOnSecs", screen_secs)
                
                carousel_secs = _to_int_or_none(self.var_disp_auto_carousel.get())
                if carousel_secs is not None: setattr(m.Display, "autoScreenCarouselSecs", carousel_secs)
                
                setattr(m.Display, "gpsFormat", self.var_disp_gps_fmt.get() or None)
                setattr(m.Display, "units", self.var_disp_units.get() or None)
                setattr(m.Display, "oled", self.var_disp_oled.get() or None)
                setattr(m.Display, "displaymode", self.var_disp_mode.get() or None)
                setattr(m.Display, "compassOrientation", self.var_disp_compass_orientation.get() or None)
                
                setattr(m.Display, "headingBold", bool(self.var_disp_heading_bold.get()))
                setattr(m.Display, "flipScreen", bool(self.var_disp_flip.get()))
                setattr(m.Display, "compassNorthTop", bool(self.var_disp_north_top.get()))
                setattr(m.Display, "wakeOnTapOrMotion", bool(self.var_disp_wake_on_motion.get()))
                setattr(m.Display, "use12hClock", bool(self.var_disp_use12h.get()))
        except Exception:
            pass # Or log error
        return m
        
    @property
    def _bindings(self) -> Dict[str, ctk.Variable]:
        return {
            "Screen On (s)": self.var_disp_screen_secs,
            "GPS Format": self.var_disp_gps_fmt,
            "Auto Carousel (s)": self.var_disp_auto_carousel,
            "Units": self.var_disp_units,
            "OLED Mode": self.var_disp_oled,
            "Display Mode": self.var_disp_mode,
            "Compass Orientation": self.var_disp_compass_orientation,
            "Heading Bold": self.var_disp_heading_bold,
            "Flip Screen": self.var_disp_flip,
            "Compass North Top": self.var_disp_north_top,
            "Wake on Tap/Motion": self.var_disp_wake_on_motion,
            "Use 12h Clock": self.var_disp_use12h,
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
