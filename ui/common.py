# ui/common.py
from __future__ import annotations
import base64
from typing import Optional, Tuple
import customtkinter as ctk

# ---------- Utilities moved from app.py (no behavior change) ----------
def is_base64ish(s: str) -> bool:
    try:
        if not s or len(s) % 4 != 0:
            return False
        base64.b64decode(s, validate=True)
        return True
    except Exception:
        return False

def make_collapsible(parent: ctk.CTkFrame, title: str, open: bool = False):
    """
    Returns (header_frame, content_frame, toggle_fn).
    Uses pack() for the content and hides via pack_forget().
    """
    wrapper = ctk.CTkFrame(parent)
    wrapper.pack(fill="x", padx=6, pady=(6, 0))

    header = ctk.CTkFrame(wrapper)
    header.pack(fill="x")

    chevron = ctk.CTkLabel(header, text=("▼" if open else "▶"), width=12)
    chevron.pack(side="left", padx=(6, 6))
    title_lbl = ctk.CTkLabel(header, text=title, font=ctk.CTkFont(size=14, weight="bold"))
    title_lbl.pack(side="left", pady=4)

    content = ctk.CTkFrame(wrapper)
    pack_args = dict(fill="x", padx=6, pady=(4, 6))
    if open:
        content.pack(**pack_args)

    state = {"open": open}

    def toggle():
        state["open"] = not state["open"]
        if state["open"]:
            chevron.configure(text="▼")
            content.pack(**pack_args)
        else:
            chevron.configure(text="▶")
            content.pack_forget()
        wrapper.update_idletasks()

    for w in (header, chevron, title_lbl):
        w.bind("<Button-1>", lambda _e: toggle())

    return header, content, toggle

def create_setting_row(
    parent: ctk.CTkFrame,
    label_text: str,
    variable: ctk.Variable,
    row_index: int,
    *,
    kind: str = "entry",
    show: Optional[str] = None,
    validate: Optional[str] = None,
    validatecommand: Optional[Tuple] = None,
):
    """
    Standardized two-column layout:
      - Column 0: Label
      - Column 1: Entry or CheckBox (kind='entry'|'checkbox')
    Returns the created widget (Entry or CheckBox).
    """
    parent.grid_columnconfigure(0, weight=0)
    parent.grid_columnconfigure(1, weight=1)

    lbl = ctk.CTkLabel(parent, text=label_text)
    lbl.grid(row=row_index, column=0, padx=6, pady=4, sticky="w")

    if kind == "checkbox":
        widget = ctk.CTkCheckBox(parent, text="", variable=variable)
        widget.grid(row=row_index, column=1, padx=6, pady=4, sticky="w")
    else:
        # Pass the new validation arguments directly to the CTkEntry
        widget = ctk.CTkEntry(
            parent,
            textvariable=variable,
            show=show,
            validate=validate,
            validatecommand=validatecommand,
        )
        widget.grid(row=row_index, column=1, padx=6, pady=4, sticky="ew")

    return widget
