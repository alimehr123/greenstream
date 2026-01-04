# server/server_manager/server_manager.py
import tkinter as tk
from tkinter import ttk
import subprocess
import sys
from pathlib import Path


class ServerManagerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("GreenStream – Server Manager")
        self.geometry("500x300")
        self.resizable(False, False)

        self._build_ui()

    def _build_ui(self):
        title = ttk.Label(
            self,
            text="GreenStream Server Manager",
            font=("Segoe UI", 16, "bold")
        )
        title.pack(pady=20)

        tools_frame = ttk.Frame(self)
        tools_frame.pack(fill="both", expand=True, padx=20)

        layout_btn = ttk.Button(
            tools_frame,
            text="Layout Editor",
            command=self.launch_layout_editor
        )
        layout_btn.pack(pady=15, ipadx=20, ipady=10)

        footer = ttk.Label(
            self,
            text="Version 0.1 – Admin Tools",
            font=("Segoe UI", 9)
        )
        footer.pack(side="bottom", pady=10)

    def launch_layout_editor(self):
        editor_path = Path(__file__).parent / "layout_editor" / "layout_editor.py"

        if not editor_path.exists():
            tk.messagebox.showerror(
                "Error",
                "layout_editor.py not found"
            )
            return

        subprocess.Popen([sys.executable, str(editor_path)])


if __name__ == "__main__":
    app = ServerManagerApp()
    app.mainloop()
