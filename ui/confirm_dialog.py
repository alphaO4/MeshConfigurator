# ui/confirm_dialog.py
import customtkinter as ctk

class ConfirmationDialog(ctk.CTkToplevel):
    """A simple dialog to get True/False confirmation from the user."""
    def __init__(self, parent, title: str, message: str):
        super().__init__(parent)
        self.title(title)
        self.transient(parent)
        self.grab_set()
        self.result = False

        ctk.CTkLabel(self, text=message, wraplength=300).pack(padx=20, pady=20)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(padx=20, pady=(0, 20))

        ctk.CTkButton(btn_frame, text="Yes", command=self._on_yes).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="No", command=self._on_no).pack(side="left", padx=10)
        
        # Center the window
        self.after(50, self._center_window)

    def _center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = self.master.winfo_x() + (self.master.winfo_width() // 2) - (width // 2)
        y = self.master.winfo_y() + (self.master.winfo_height() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _on_yes(self):
        self.result = True
        self.destroy()

    def _on_no(self):
        self.result = False
        self.destroy()

    @classmethod
    def ask(cls, parent, title: str, message: str) -> bool:
        dialog = cls(parent, title, message)
        parent.wait_window(dialog)
        return dialog.result