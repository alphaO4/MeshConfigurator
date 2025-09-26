# ui/save_preset_dialog.py
from __future__ import annotations
from typing import Dict, Any, Tuple, Optional, List
import customtkinter as ctk

class SavePresetDialog(ctk.CTkToplevel):
    """
    Modal dialog to collect a preset name and a subset of settings.
    Allows editing the values of the settings to be saved.
    """

    def __init__(self, parent, all_settings: Dict[str, Dict[str, Any]], existing_names: List[str]) -> None:
        super().__init__(master=parent)
        self.title("Save Preset")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()

        self.result: Optional[Tuple[str, Dict[str, Any]]] = None
        self._all_settings = all_settings or {}
        self._existing_lc = {s.lower() for s in (existing_names or [])}
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # -------------------------------
        # Row 0: Name Entry
        # -------------------------------
        name_row = ctk.CTkFrame(self)
        name_row.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 6))
        name_row.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(name_row, text="Preset Name:").grid(row=0, column=0, padx=(8, 6), pady=6, sticky="w")
        self._name_var = ctk.StringVar()
        self._name_var.trace_add("write", lambda *_: self._validate_name())
        self.name_entry = ctk.CTkEntry(name_row, textvariable=self._name_var)
        self.name_entry.grid(row=0, column=1, padx=(0, 8), pady=6, sticky="ew")
        self.name_entry.focus_set()
        self._name_msg = ctk.CTkLabel(name_row, text="", text_color="gray60")
        self._name_msg.grid(row=1, column=0, columnspan=2, sticky="w", padx=(8, 6), pady=(0, 2))

        # -------------------------------
        # Row 1: Scrollable Settings Checklist
        # -------------------------------
        self.settings_frame = ctk.CTkScrollableFrame(self)
        self.settings_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=6)
        self.settings_frame.grid_columnconfigure(1, weight=1) # Allow entry widgets to expand

        # NEW: Store widgets and data for each row in a list of dictionaries
        self.settings_rows: List[Dict[str, Any]] = []
        self._populate_checklist()

        # -------------------------------
        # Row 2: Actions
        # -------------------------------
        actions = ctk.CTkFrame(self)
        actions.grid(row=2, column=0, sticky="ew", padx=10, pady=(6, 10))
        actions.grid_columnconfigure(0, weight=1)
        btn_wrap = ctk.CTkFrame(actions)
        btn_wrap.grid(row=0, column=0, sticky="e")
        self.save_button = ctk.CTkButton(btn_wrap, text="Save", command=self._on_save, state="disabled")
        self.save_button.pack(side="right", padx=(6, 0))
        cancel_button = ctk.CTkButton(btn_wrap, text="Cancel", command=self._on_cancel)
        cancel_button.pack(side="right")

        self.bind("<Return>", lambda _e: self._on_save() if self.save_button.cget("state") == "normal" else None)
        self.bind("<Escape>", lambda _e: self._on_cancel())
        self._center_over_parent(parent, width=520, height=580)

    def _populate_checklist(self) -> None:
        """NEW: Populates the list with a checkbox and a hidden, editable entry for each setting."""
        for section, settings in self._all_settings.items():
            # Section header
            header = ctk.CTkLabel(self.settings_frame, text=str(section), font=ctk.CTkFont(size=14, weight="bold"))
            header.pack(fill="x", padx=8, pady=(8, 4))

            for display_name, value in settings.items():
                # Frame to hold the checkbox and entry for alignment
                row_frame = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
                row_frame.pack(fill="x", padx=18, pady=2)
                row_frame.grid_columnconfigure(1, weight=1)

                # Create the entry widget first, so the checkbox can control it
                value_var = ctk.StringVar(value=str(value))
                entry = ctk.CTkEntry(row_frame, textvariable=value_var)
                # Note: The entry is NOT packed or gridded here; it starts hidden.

                # Create the checkbox and link its command to toggle the entry's visibility
                cb = ctk.CTkCheckBox(row_frame, text=str(display_name))
                cb.configure(command=lambda checked=cb, e=entry: self._on_checkbox_toggled(checked, e))
                cb.grid(row=0, column=0, sticky="w")

                # Store all relevant parts for this setting
                self.settings_rows.append({
                    "cb": cb,
                    "var": value_var,
                    "entry": entry,
                    "section": section,
                    "name": display_name,
                })

    def _on_checkbox_toggled(self, checkbox: ctk.CTkCheckBox, entry: ctk.CTkEntry):
        """Shows or hides the entry widget based on the checkbox state."""
        if checkbox.get():
            # Place the entry to the right of the checkbox, expanding to fill space
            entry.grid(row=0, column=1, sticky="ew", padx=(10, 0))
        else:
            # Remove the entry from the grid, hiding it
            entry.grid_forget()

    def _on_save(self) -> None:
        """NEW: Collects data from the visible and enabled entry fields."""
        name = (self._name_var.get() or "").strip()
        if not name or name.lower() in self._existing_lc:
            return

        selected_settings: Dict[str, Dict[str, Any]] = {}
        for row in self.settings_rows:
            if row["cb"].get():
                # Get the potentially edited value from the StringVar
                edited_value = row["var"].get()
                section = row["section"]
                setting_name = row["name"]
                selected_settings.setdefault(section, {})[setting_name] = edited_value

        self.result = (name, selected_settings)
        self.destroy()
        
    # --- Other methods (_on_cancel, _validate_name, _center_over_parent, get_preset_data) remain the same ---
    def _on_cancel(self) -> None:
        self.result = None
        self.destroy()

    def _validate_name(self) -> None:
        raw = self._name_var.get() or ""
        name = raw.strip()
        msg = ""
        enable = True

        if not name:
            msg = "Enter a preset name."
            enable = False
        elif name.lower() in self._existing_lc:
            msg = "That name already exists."
            enable = False

        self.save_button.configure(state=("normal" if enable else "disabled"))
        self._name_msg.configure(text=msg)
        
    def _center_over_parent(self, parent, width: int = 520, height: int = 580) -> None:
        try:
            self.update_idletasks()
            px = parent.winfo_rootx()
            py = parent.winfo_rooty()
            pw = parent.winfo_width()
            ph = parent.winfo_height()
            x = px + (pw // 2) - (width // 2)
            y = py + (ph // 2) - (height // 2)
            self.geometry(f"{width}x{height}+{max(0, x)}+{max(0, y)}")
        except Exception:
            self.geometry(f"{width}x{height}")
            
    @staticmethod
    def get_preset_data(parent, all_settings: Dict[str, Dict[str, Any]], existing_names: List[str]) -> Optional[Tuple[str, Dict[str, Any]]]:
        dlg = SavePresetDialog(parent, all_settings=all_settings, existing_names=existing_names)
        parent.wait_window(dlg)
        return dlg.result
