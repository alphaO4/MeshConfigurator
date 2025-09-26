# ui/channel_frame.py
from __future__ import annotations
import os
import base64
import customtkinter as ctk
from CTkToolTip import CTkToolTip

from ui.validator import Validator

class ChannelFrame(ctk.CTkFrame):
    """
    Compact channel row with:
      0) Header: "Index n, Primary/Secondary"
      1) Name
      3) PSK textbox (if from device, mask it, generate button displays it unmasked) | Generate
      4) GPS | GPS Precision (precision disabled & set to 0 when GPS unchecked)
      5) Uplink | Downlink
      6) Make Default 'public' channel (sets Name='Default', PSK='AQ==', preview unmasked)
    Keeps legacy attributes: name_var, precision_var, uplink_var, downlink_var, strategy_var, key_var, key_entry
    """

    def __init__(
        self,
        parent: ctk.CTkFrame,
        *,
        index: int,
        is_primary: bool = False,
        delete_callback=None,
    ):
        super().__init__(parent)
        self.index = index
        self.delete_callback = delete_callback
        self._psk_masked = True

        # ---------------- Vars exposed to App ----------------
        self.name_var = ctk.StringVar(value="")
        self.key_var = ctk.StringVar(value="")
        self.strategy_var = ctk.StringVar(value="leave")
        self.gps_var = ctk.BooleanVar(value=False)
        self.precision_var = ctk.StringVar(value="0")
        self.uplink_var = ctk.BooleanVar(value=False)
        self.downlink_var = ctk.BooleanVar(value=False)
        self.default_public_var = ctk.BooleanVar(value=False)
        
        self.key_var.trace_add("write", self._on_key_changed)

        # ---------------- Validation ----------------
        validate_len_cmd = self.register(Validator.validate_string_length)

        # ---------------- Header ----------------
        title_suffix = ", Primary" if is_primary else (", Secondary" if index == 1 else "")
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=6, pady=(8, 2))
        ctk.CTkLabel(hdr, text=f"Index {index}{title_suffix}", font=ctk.CTkFont(weight="bold")).pack(side="left")
        if self.delete_callback is not None:
            ctk.CTkButton(hdr, text="Delete", width=80, command=self._on_delete).pack(side="right", padx=6)

        # ---------------- Row 1: Name ----------------
        r1 = ctk.CTkFrame(self, fg_color="transparent"); r1.pack(fill="x", padx=6, pady=4)
        ctk.CTkLabel(r1, text="Name").pack(side="left", padx=(0, 6))
        name_entry = ctk.CTkEntry(r1, textvariable=self.name_var, width=260,
                                  validate="key",
                                  validatecommand=(validate_len_cmd, '10', '%P'))
        name_entry.pack(side="left")
        CTkToolTip(name_entry, message="10 characters max")


        # ---------------- Row 2: PSK textbox | Show | Generate ----------------
        r2 = ctk.CTkFrame(self, fg_color="transparent"); r2.pack(fill="x", padx=6, pady=4)
        ctk.CTkLabel(r2, text="PSK").pack(side="left", padx=(0, 6))
        
        self.key_entry = ctk.CTkEntry(r2, textvariable=self.key_var, show="•")
        self.key_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        CTkToolTip(self.key_entry, message="Base64-encoded PSK. Leave blank to keep current device PSK.")
        
        self.show_psk_btn = ctk.CTkButton(r2, text="Show", width=60, command=self._on_toggle_psk_visibility)
        self.show_psk_btn.pack(side="left", padx=(0, 6))

        gen_btn = ctk.CTkButton(r2, text="Generate", width=100, command=self._on_generate_psk)
        gen_btn.pack(side="left")
        CTkToolTip(gen_btn, message="Generate a random 32-byte PSK.")

        # ---------------- Row 3: GPS | GPS Precision ----------------
        r3 = ctk.CTkFrame(self, fg_color="transparent"); r3.pack(fill="x", padx=6, pady=4)
        chk_gps = ctk.CTkCheckBox(r3, text="GPS", variable=self.gps_var, command=self._on_gps_toggle)
        chk_gps.pack(side="left", padx=(0, 10))
        self.tooltip_gps = CTkToolTip(chk_gps, message="")
        
        ctk.CTkLabel(r3, text="GPS Precision (0..32)").pack(side="left", padx=(0, 6))
        self.ent_precision = ctk.CTkEntry(r3, textvariable=self.precision_var, width=100)
        self.ent_precision.pack(side="left")
        self.precision_var.trace_add("write", lambda *_: self._precision_changed())
        
        # ---------------- Row 4: Uplink | Downlink ----------------
        r4 = ctk.CTkFrame(self, fg_color="transparent"); r4.pack(fill="x", padx=6, pady=4)
        ctk.CTkCheckBox(r4, text="Uplink", variable=self.uplink_var).pack(side="left", padx=(0, 8))
        ctk.CTkCheckBox(r4, text="Downlink", variable=self.downlink_var).pack(side="left", padx=(0, 8))

        # ---------------- Row 5: Default/Public checkbox ----------------
        r5 = ctk.CTkFrame(self, fg_color="transparent"); r5.pack(fill="x", padx=6, pady=(2, 8))
        ctk.CTkCheckBox(
            r5, text="Make Default (public) channel",
            variable=self.default_public_var,
            command=self._on_default_public_toggle
        ).pack(side="left")
        
        # ---------------- Dynamic UI Setup ----------------
        self.gps_var.trace_add("write", self._update_gps_tooltip)
        self._update_gps_tooltip()
        self._apply_gps_enable_state()

    # ---------------- New Callback for GPS Tooltip ----------------
    def _update_gps_tooltip(self, *args):
        is_enabled = self.gps_var.get()
        message = "Disable GPS" if is_enabled else "Enable GPS"
        self.tooltip_gps.configure(message=message)

    # ---------------- Event handlers ----------------
    def _on_delete(self):
        if callable(self.delete_callback):
            self.delete_callback(self.index)
        try:
            self.destroy()
        except Exception:
            pass

    def _on_generate_psk(self):
        raw = os.urandom(32)
        b64 = base64.b64encode(raw).decode("ascii")
        self.key_var.set(b64)
        self.default_public_var.set(False)
        self._set_psk_visibility(False)

    def _on_toggle_psk_visibility(self):
        self._set_psk_visibility(not self._psk_masked)

    def _on_default_public_toggle(self):
        if self.default_public_var.get():
            self.name_var.set("LongFast")
            self.key_var.set("AQ==")
            self._set_psk_visibility(False)
        else:
            if self.key_var.get():
                self._set_psk_visibility(True)

    def _on_gps_toggle(self):
        if not self.gps_var.get():
            self.precision_var.set("0")
        self._apply_gps_enable_state()

    def _on_key_changed(self, *args):
        if self.key_var.get().strip():
            self.strategy_var.set("explicit")
        else:
            self.strategy_var.set("leave")

    # ---------------- UI/State Helpers ----------------
    def _set_psk_visibility(self, mask: bool):
        self._psk_masked = mask
        if mask:
            self.key_entry.configure(show="•")
            self.show_psk_btn.configure(text="Show")
        else:
            self.key_entry.configure(show="")
            self.show_psk_btn.configure(text="Hide")

    def _apply_gps_enable_state(self):
        try:
            state = "normal" if self.gps_var.get() else "disabled"
            self.ent_precision.configure(state=state)
        except Exception:
            pass
    
    def _precision_changed(self):
        current_text = (self.precision_var.get() or "").strip()
        if not current_text:
            return
        try:
            val = int(current_text)
        except (ValueError, TypeError):
            val = 0

        gps_is_on = self.gps_var.get()
        if val > 0 and not gps_is_on:
            self.gps_var.set(True)
        elif val <= 0 and gps_is_on:
            self.gps_var.set(False)
