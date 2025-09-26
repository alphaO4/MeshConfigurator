# ui/panels/base_panel.py
from __future__ import annotations
import customtkinter as ctk
from typing import Dict, Any

class BasePanel:
    """
    Minimal contract for panels:
    - build(parent_frame): create UI and variables on self
    - apply_model(model): populate variables from DeviceModel
    - collect_model_overlay(base_model): mutate base_model with fields from this panel (same way app.py did)
    - preset_bindings(): mapping { display section -> { label -> ctk.Variable } }
    - preset_apply(section_fields: Dict[str, Any]): set only provided fields
    """
    section_title: str = ""

    def __init__(self, app: "ctk.CTk"):
        self.app = app
        self.frame: ctk.CTkFrame | None = None

    def build(self, parent: ctk.CTkFrame): ...
    def apply_model(self, model): ...
    def collect_model_overlay(self, base_model): ...
    def preset_bindings(self) -> Dict[str, Dict[str, Any]]: ...
    def preset_apply(self, section_fields: Dict[str, Any]): ...
