# server/server_manager/layout_editor/layout_editorold_working.py
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import os
import tempfile
import webbrowser
import re

def is_json_action(text: str) -> bool:
    try:
        json.loads(text)
        return True
    except Exception:
        return False

BASE_DIR = Path(__file__).parent
GUIDE_FILE = BASE_DIR / "layout_guide.txt"
LAYOUTS_DIR = BASE_DIR / "layouts"
LAYOUTS_DIR.mkdir(exist_ok=True)


RENDERER_COMPONENT_TYPES = [
    "input", "video_list", "video_card", "video_player",
    "text", "image", "button", "tabs",
    "list", "container", "spacer"
]

PAGE_LAYOUT_TYPES = ["grid", "vertical", "horizontal"]


class LayoutEditorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Layout Editor")
        self.geometry("1400x780")
        try:
            self.state("zoomed")
        except:
            self.attributes("-zoomed", True)

        self.layout_data = {
            "layout_name": "",
            "version": 1,
            "meta": {"author": "", "description": ""},
            "pages": []
        }

        self.selected_page_index = None
        self.selected_component_index = None

        self._build_menu()
        self._build_ui()
        self._build_status_bar()

    # ---------- STATUS BAR (5 lines) ----------

    def _build_status_bar(self):
        self.status_text = tk.Text(
            self, height=5, wrap="word", state="disabled", bg="#f2e2e5"
        )
        self.status_text.pack(side="bottom", fill="x")

        self.set_status(" ")

    def set_status(self, text):
        self.status_text.config(state="normal")
        self.status_text.delete("1.0", tk.END)
        self.status_text.insert(tk.END, text)
        self.status_text.config(state="disabled")

    def bind_hint(self, widget, text):
        widget.bind("<Enter>", lambda e: self.set_status(text))
        widget.bind("<Leave>", lambda e: self.set_status(" "))

    # ---------- UTILS ----------

    def _layouts_dir(self):
       # p = Path(__file__).parent / "layouts"
        #p = BASE_DIR / "layouts"
        #p.mkdir(exist_ok=True)
        return LAYOUTS_DIR

    # ---------- MENU ----------

    def _build_menu(self):
        m = tk.Menu(self)
        self.config(menu=m)

        file_menu = tk.Menu(m, tearoff=0)
        file_menu.add_command(
            label="New Layout",
            accelerator="Ctrl+N",
            command=self.new_layout
            )
        file_menu.add_command(
            label="Load Layout",
            accelerator="Ctrl+O",
            command=self.load_layout
            )
        file_menu.add_command(
            label="Save Layout",
            accelerator="Ctrl+S",
            command=self.save_layout
            )

        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.destroy)
        
        self.bind_all("<Control-n>", lambda e: self.new_layout())
        self.bind_all("<Control-o>", lambda e: self.load_layout())
        self.bind_all("<Control-s>", lambda e: self.save_layout())

        help_menu = tk.Menu(m, tearoff=0)
        help_menu.add_command(label="Layout Guide", command=self.open_guide)
        help_menu.add_command(label="About layout editor", command=self.open_about)

        m.add_cascade(label="File", menu=file_menu)
        m.add_cascade(label="Help", menu=help_menu)
   
    # ================= COPY / PASTE =================

    def enable_copy_paste(self, widget):
        menu = tk.Menu(widget, tearoff=0)
        menu.add_command(label="Cut  Ctrl+X", command=lambda: widget.event_generate("<<Cut>>"))
        menu.add_command(label="Copy  Ctrl+C", command=lambda: widget.event_generate("<<Copy>>"))
        menu.add_command(label="Paste  Ctrl+V", command=lambda: widget.event_generate("<<Paste>>"))

        def popup(e):
            menu.tk_popup(e.x_root, e.y_root)

        widget.bind("<Button-3>", popup)
        widget.bind("<Control-c>", lambda e: widget.event_generate("<<Copy>>"))
        widget.bind("<Control-v>", lambda e: widget.event_generate("<<Paste>>"))
        widget.bind("<Control-x>", lambda e: widget.event_generate("<<Cut>>"))

    # ---------- UI ----------

    def _build_ui(self):
        root = ttk.Frame(self)
        root.pack(fill="both", expand=True, padx=0, pady=6)

        self._build_layout_info(root)

        body = ttk.Frame(root)
        body.pack(fill="both", expand=True)

        self._build_pages_panel(body)
        self._build_preview_panel(body)
        self._build_page_details(body)
        self._build_components_panel(body)
        self._build_component_details(body)

     
    # ---------- LAYOUT INFO ----------

    def _build_layout_info(self, parent):
        box = ttk.LabelFrame(parent, text="Layout Info")
        box.pack(fill="x")

        self.name_var = tk.StringVar()
        self.version_var = tk.IntVar(value=1)
        self.author_var = tk.StringVar()
        self.desc_var = tk.StringVar()

        ttk.Label(box, text="Name").grid(row=0, column=0)
        name_e = ttk.Entry(box, textvariable=self.name_var)
        name_e.grid(row=0, column=1, sticky="ew")
        self.bind_hint(
            name_e,
            "Layout logical name.\nSelected by Admin rules (user/time/ip)."
        )

        ttk.Label(box, text="Version").grid(row=0, column=2)
        name_ver = ttk.Entry(box, width=6, textvariable=self.version_var)
        name_ver.grid(row=0, column=3)
        self.bind_hint(name_ver, "Layout version.")

        ttk.Label(box, text="Author").grid(row=1, column=0)
        name_auth = ttk.Entry(box, textvariable=self.author_var)
        name_auth.grid(row=1, column=1, sticky="ew")
        self.bind_hint(name_auth, "Name of the auther.")
        
        ttk.Label(box, text="Description").grid(row=2, column=0)
        name_desc = ttk.Entry(box, textvariable=self.desc_var)
        name_desc.grid(row=2, column=1, columnspan=3, sticky="ew")
        self.bind_hint(name_desc, "layout description.")
        
        for i in range(4):
            box.columnconfigure(i, weight=1)

    # ---------- PAGES ----------

    def _build_pages_panel(self, parent):
        box = ttk.LabelFrame(parent, text="Pages")
        box.pack(side="left", fill="y")

        self.pages_list = tk.Listbox(box, width=22)
        self.pages_list.pack(fill="y")
        self.pages_list.bind("<<ListboxSelect>>", self.on_page_select)
        
        self.bind_hint(self.pages_list, "List of all defined pages")

        ttk.Button(box, text="+ Page", command=self.add_page).pack(fill="x")
        
        ttk.Button(box, text="- Page", command=self.remove_page).pack(fill="x")
        
    def add_page(self):
        self.layout_data["pages"].append({
            "page_id": f"page_{len(self.layout_data['pages']) + 1}",
            "title": "",
            "layout_type": "grid",
            "components": []
        })
        self.refresh_pages()

    def remove_page(self):
        if self.selected_page_index is None:
            return
        self.layout_data["pages"].pop(self.selected_page_index)
        self.selected_page_index = None
        self.refresh_pages()
        self.refresh_components()
        self.refresh_preview()

    def refresh_pages(self):
        self.pages_list.delete(0, tk.END)
        for p in self.layout_data["pages"]:
            self.pages_list.insert(tk.END, p["page_id"])

    def on_page_select(self, _):
        sel = self.pages_list.curselection()
        if not sel:
            return
        self.selected_page_index = sel[0]
        self.load_page_form()
        self.refresh_components()
        self.refresh_preview()

    # ---------- PREVIEW ----------

    def _build_preview_panel(self, parent):
        box = ttk.LabelFrame(parent, text="Page Preview")
        box.pack(side="left", fill="both", expand=True, padx=5)

        self.preview = tk.Text(box, height=14, state="disabled")
        self.preview.pack(fill="both", expand=True)
        
        self.enable_copy_paste(self.preview)
        self.bind_hint(self.preview, "A preview of the selected page")

        ttk.Button(box, text="Refresh Preview", command=self.refresh_preview).pack(fill="x")
        ttk.Button(box, text="View Page", command=self.view_page_in_browser).pack(fill="x")

    def refresh_preview(self):
        self.preview.config(state="normal")
        self.preview.delete("1.0", tk.END)

        if self.selected_page_index is not None:
            p = self.current_page()
            self.preview.insert(
                tk.END,
                f"Page: {p['page_id']} ({p['layout_type']})\n"
                f"Title: {p.get('title','')}\n\n"
            )
            for c in p["components"]:
                self.preview.insert(
                    tk.END,
                    f"  Component: {c['component_id']}\n"
                    f"    Type: {c['component_type']}\n"
                )
            
                # ✅ NEW: show text if present
                if c.get("text"):
                    self.preview.insert(
                        tk.END,
                        f"    Text: {c['text']}\n"
                    )
            
                self.preview.insert(
                    tk.END,
                    f"    Slot: {c.get('slot','')}\n"
                )
            
                if c.get("action"):
                    self.preview.insert(tk.END, "    Action:\n")
                    for a in c["action"]:
                        self.preview.insert(tk.END, f"      - {a}\n")

        self.preview.config(state="disabled")
    
    def view_page_in_browser(self):
        self.refresh_preview()
        self.open_preview_in_browser()

    # ---------- PAGE DETAILS ----------

    def _build_page_details(self, parent):
        box = ttk.LabelFrame(parent, text="Page Details")
        box.pack(side="left", fill="y")

        self.page_id_var = tk.StringVar()
        self.page_title_var = tk.StringVar()
        self.page_layout_var = tk.StringVar(value="grid")

        ttk.Label(box, text="Page ID").grid(row=0, column=0)
        pg_id = ttk.Entry(box, textvariable=self.page_id_var)
        pg_id.grid(row=0, column=1)
        self.bind_hint(pg_id, "Id (name) of the current active page")
        
        ttk.Label(box, text="Title").grid(row=1, column=0)
        ttl = ttk.Entry(box, textvariable=self.page_title_var)
        ttl.grid(row=1, column=1)
        self.enable_copy_paste(ttl)
        self.bind_hint(ttl, "Title of the selected page")
        
        ttk.Label(box, text="Layout").grid(row=2, column=0)
        meta_btn = ttk.Button(
            box,
            text="Meta Data",
            command=self.open_page_meta_editor
        )
        meta_btn.grid(row=4, column=1, columnspan=2, sticky="ew", pady=(8, 0))
        
        self.bind_hint(
            meta_btn,
            "Edit non-visual page metadata (SEO, auth, layout rules, flags)"
        )

        ttk.Combobox(
            box, values=PAGE_LAYOUT_TYPES,
            textvariable=self.page_layout_var,
            state="readonly"
        ).grid(row=2, column=1)
        
    def open_page_meta_editor(self):
        if self.selected_page_index is None:
            messagebox.showwarning("No Page", "Please select a page first.")
            return
    
        page = self.current_page()
        meta = page.setdefault("meta", {})
    
        win = tk.Toplevel(self)
        win.title(f"Meta Data — {page.get('page_id')}")
        win.geometry("520x520")
        win.grab_set()
    
        def section(label):
            f = ttk.LabelFrame(win, text=label)
            f.pack(fill="x", padx=10, pady=6)
            return f
    
        # ========== SEO ==========
        seo = meta.setdefault("seo", {})
        f_seo = section("SEO")
    
        seo_title = tk.StringVar(value=seo.get("title", ""))
        seo_desc = tk.StringVar(value=seo.get("description", ""))
        seo_keys = tk.StringVar(value=seo.get("keywords", ""))
    
        ttk.Label(f_seo, text="Title").grid(row=0, column=0, sticky="w")
        ttk.Entry(f_seo, textvariable=seo_title, width=40).grid(row=0, column=1)
    
        ttk.Label(f_seo, text="Description").grid(row=1, column=0, sticky="w")
        ttk.Entry(f_seo, textvariable=seo_desc, width=40).grid(row=1, column=1)
    
        ttk.Label(f_seo, text="Keywords").grid(row=2, column=0, sticky="w")
        ttk.Entry(f_seo, textvariable=seo_keys, width=40).grid(row=2, column=1)
    
        # ========== AUTH ==========
        auth = meta.setdefault("auth", {})
        f_auth = section("Authorization")
    
        auth_required = tk.BooleanVar(value=auth.get("required", False))
        auth_roles = tk.StringVar(value=auth.get("roles", ""))
    
        ttk.Checkbutton(f_auth, text="Auth Required", variable=auth_required).grid(row=0, column=0, columnspan=2, sticky="w")
        ttk.Label(f_auth, text="Allowed Roles").grid(row=1, column=0, sticky="w")
        ttk.Entry(f_auth, textvariable=auth_roles, width=30).grid(row=1, column=1)
    
        # ========== LAYOUT ==========
        layout_m = meta.setdefault("layout", {})
        f_layout = section("Layout Rules")
    
        layout_type = tk.StringVar(value=layout_m.get("type", ""))
        max_width = tk.StringVar(value=layout_m.get("max_width", ""))
        padding = tk.StringVar(value=layout_m.get("padding", ""))
    
        ttk.Label(f_layout, text="Type").grid(row=0, column=0, sticky="w")
        ttk.Entry(f_layout, textvariable=layout_type).grid(row=0, column=1)
    
        ttk.Label(f_layout, text="Max Width").grid(row=1, column=0, sticky="w")
        ttk.Entry(f_layout, textvariable=max_width).grid(row=1, column=1)
    
        ttk.Label(f_layout, text="Padding").grid(row=2, column=0, sticky="w")
        ttk.Entry(f_layout, textvariable=padding).grid(row=2, column=1)
    
        # ========== ANALYTICS ==========
        analytics = meta.setdefault("analytics", {})
        f_analytics = section("Analytics")
    
        page_name = tk.StringVar(value=analytics.get("page_name", ""))
        track = tk.BooleanVar(value=analytics.get("track", True))
    
        ttk.Label(f_analytics, text="Page Name").grid(row=0, column=0, sticky="w")
        ttk.Entry(f_analytics, textvariable=page_name).grid(row=0, column=1)
        ttk.Checkbutton(f_analytics, text="Enable Tracking", variable=track).grid(row=1, column=0, columnspan=2, sticky="w")
    
        # ========== FLAGS ==========
        flags = meta.setdefault("flags", {})
        f_flags = section("Feature Flags")
    
        experimental = tk.BooleanVar(value=flags.get("experimental", False))
        hidden = tk.BooleanVar(value=flags.get("hidden", False))
    
        ttk.Checkbutton(f_flags, text="Experimental", variable=experimental).pack(anchor="w")
        ttk.Checkbutton(f_flags, text="Hidden", variable=hidden).pack(anchor="w")
    
        # ========== ACTIONS ==========
        def save_and_close():
            page["meta"] = {
                "seo": {
                    "title": seo_title.get(),
                    "description": seo_desc.get(),
                    "keywords": seo_keys.get()
                },
                "auth": {
                    "required": auth_required.get(),
                    "roles": auth_roles.get()
                },
                "layout": {
                    "type": layout_type.get(),
                    "max_width": max_width.get(),
                    "padding": padding.get()
                },
                "analytics": {
                    "page_name": page_name.get(),
                    "track": track.get()
                },
                "flags": {
                    "experimental": experimental.get(),
                    "hidden": hidden.get()
                }
            }
            win.destroy()
    
        btns = ttk.Frame(win)
        btns.pack(pady=10)
        ttk.Button(btns, text="OK", command=save_and_close).pack(side="left", padx=5)
        ttk.Button(btns, text="Cancel", command=win.destroy).pack(side="left", padx=5)

    
    def load_page_form(self):
        p = self.current_page()
        self.page_id_var.set(p["page_id"])
        self.page_title_var.set(p["title"])
        self.page_layout_var.set(p["layout_type"])

    def _commit_page_form(self):
        if self.selected_page_index is None:
            return
        p = self.current_page()
        p["page_id"] = self.page_id_var.get()
        p["title"] = self.page_title_var.get()
        p["layout_type"] = self.page_layout_var.get()

    # ---------- COMPONENTS ----------

    def _build_components_panel(self, parent):
        box = ttk.LabelFrame(parent, text="Components")
        box.pack(side="left", fill="both", expand=True)

        self.comp_list = tk.Listbox(box)
        self.comp_list.pack(fill="both", expand=True)
        self.comp_list.bind("<<ListboxSelect>>", self.on_component_select)
        
        self.enable_copy_paste(self.comp_list)
        self.bind_hint(self.comp_list, "Components of the selected page")
        
        ttk.Button(box, text="+ Component", command=self.add_component).pack(fill="x")
        ttk.Button(box, text="- Component", command=self.remove_component).pack(fill="x")
        
    def add_component(self):
        if self.selected_page_index is None:
            return
        self.current_page()["components"].append({
            "component_id": f"component_{len(self.current_page()['components']) + 1}",
            "component_type": RENDERER_COMPONENT_TYPES[0],
            "slot": "",
            "action": []
        })
        self.refresh_components()
        self.refresh_preview()

    def remove_component(self):
        if self.selected_component_index is None:
            return
        self.current_page()["components"].pop(self.selected_component_index)
        self.selected_component_index = None
        self.refresh_components()
        self.refresh_preview()

    def refresh_components(self):
        self.comp_list.delete(0, tk.END)
        if self.selected_page_index is None:
            return
        for c in self.current_page()["components"]:
            self.comp_list.insert(tk.END, c["component_id"])

    def on_component_select(self, _):
        sel = self.comp_list.curselection()
        if not sel:
            return
        self.selected_component_index = sel[0]
        self.load_component_form()

    # ---------- COMPONENT DETAILS ----------

    def _build_component_details(self, parent):
        box = ttk.LabelFrame(parent, text="Component Details")
        box.pack(side="left", fill="y", padx=5)

        self.comp_id_var = tk.StringVar()
        self.comp_type_var = tk.StringVar()
        self.comp_text_var = tk.StringVar()
        self.comp_slot_var = tk.StringVar()

        ttk.Label(box, text="ID").grid(row=0, column=0)
        self.id_e = ttk.Entry(box, textvariable=self.comp_id_var)
        self.id_e.grid(row=0, column=1)
        
        ttk.Label(box, text="Type").grid(row=1, column=0)
        type_cb = ttk.Combobox(
            box, values=RENDERER_COMPONENT_TYPES,
            textvariable=self.comp_type_var, state="readonly"
        )
        type_cb.grid(row=1, column=1)
        
        # ✅ NEW: Text field
        ttk.Label(box, text="Text").grid(row=2, column=0)
        self.text_e = ttk.Entry(box, textvariable=self.comp_text_var, width=32)
        self.text_e.grid(row=2, column=1)
        self.enable_copy_paste(self.text_e)
        self.bind_hint(self.text_e, "Text content of the component (if applicable)")
        
        ttk.Label(box, text="Slot").grid(row=3, column=0)
        self.slot_e = ttk.Entry(box, textvariable=self.comp_slot_var)
        self.slot_e.grid(row=3, column=1)
        
        ttk.Label(box, text="Action Script").grid(row=4, column=0, sticky="nw")
        
        self.comp_action_text = tk.Text(box, height=8, width=32)
        self.comp_action_text.grid(row=4, column=1)

        
        self.enable_copy_paste(self.comp_action_text)
        self.bind_hint(
            self.comp_action_text,
            "Multi-step action script (one instruction per line).\n\n"
            "You can ask AI to generate this.\n"
            "Describe what the user does and expected behavior.\n\n"
            "Examples:\n"
            "emit:search_query\n"
            "fetch:/api/search\n"
            "navigate:results"
        )

    def load_component_form(self):
        c = self.current_component()
        self.comp_id_var.set(c["component_id"])
        self.comp_type_var.set(c["component_type"])
        self.comp_text_var.set(c.get("text", ""))
        self.comp_slot_var.set(c.get("slot", ""))

        self.comp_action_text.delete("1.0", tk.END)

        if "actions" in c and c["actions"]:
            # ✅ Show structured actions as JSON
            self.comp_action_text.insert(
                tk.END,
                json.dumps(c["actions"], indent=2, ensure_ascii=False)
                )
        else:
            # ✅ Legacy action script
            self.comp_action_text.insert(
                tk.END,
                "\n".join(c.get("action", []))
            )


    def _commit_component_form(self):
        if self.selected_component_index is None:
            return
    
        c = self.current_component()
        c["component_id"] = self.comp_id_var.get()
        c["component_type"] = self.comp_type_var.get()
        c["slot"] = self.comp_slot_var.get()
        
        text_value = self.comp_text_var.get().strip()

        if text_value:
            c["text"] = text_value
        else:
            c.pop("text", None)
    
        raw = self.comp_action_text.get("1.0", tk.END).strip()
    
        # cleanup
        c.pop("action", None)
        c.pop("actions", None)
    
        if not raw:
            return
    
        if is_json_action(raw):
            # ✅ Structured actions 그대로
            c["actions"] = json.loads(raw)
        else:
            # ✅ Legacy script 그대로
            c["action"] = [
                line.strip()
                for line in raw.splitlines()
                if line.strip()
            ]

    # ---------- HELPERS ----------

    def current_page(self):
        return self.layout_data["pages"][self.selected_page_index]

    def current_component(self):
        return self.current_page()["components"][self.selected_component_index]

    # ---------- FILE OPS ----------

    def new_layout(self):
        self.layout_data = {
            "layout_name": "",
            "version": 1,
            "meta": {"author": "", "description": ""},
            "pages": []
        }
        self.selected_page_index = None
        self.selected_component_index = None
        self.refresh_pages()
        self.refresh_components()
        self.refresh_preview()

    def save_layout(self):
        self._commit_page_form()
        self._commit_component_form()

        self.layout_data["layout_name"] = self.name_var.get()
        self.layout_data["version"] = self.version_var.get()
        self.layout_data["meta"]["author"] = self.author_var.get()
        self.layout_data["meta"]["description"] = self.desc_var.get()

        file = filedialog.asksaveasfilename(
            initialdir=str(self._layouts_dir()),
            defaultextension=".layout.json",
            filetypes=[("Layout JSON", "*.layout.json")]
        )
        if not file:
            return

        with open(file, "w", encoding="utf-8") as f:
            json.dump(self.layout_data, f, indent=2, ensure_ascii=False)

        messagebox.showinfo("Saved", "Layout saved successfully")

    def load_layout(self):
        file = filedialog.askopenfilename(
            initialdir=str(self._layouts_dir()),
            filetypes=[("Layout JSON", "*.layout.json")]
        )
        if not file:
            return

        with open(file, "r", encoding="utf-8") as f:
            self.layout_data = json.load(f)

        self.name_var.set(self.layout_data.get("layout_name", ""))
        self.version_var.set(self.layout_data.get("version", 1))
        self.author_var.set(self.layout_data["meta"].get("author", ""))
        self.desc_var.set(self.layout_data["meta"].get("description", ""))

        self.refresh_pages()
        self.refresh_components()
        self.refresh_preview()

    def open_guide(self):
        os.startfile(Path(__file__).parent / "layout_guide.txt")

    def open_about(self):
        os.startfile(Path(__file__).parent / "about.txt")
    
    def generate_html(self, pages):
        html_pages = []
    
        page_titles = " - ".join(p.get("title", "") for p in pages)
    
        for page in pages:
            slots = {}
    
            for comp in page["components"]:
                slot = comp.get("slot", "content")
                slots.setdefault(slot, "")
    
                cid = comp.get("id", "")
                ctype = comp.get("type", "")
                ctext = comp.get("text", "")
    
                # ---------- TEXT ----------
                if ctype == "text":
                    html = f"<h3 data-id='{cid}'>{ctext or cid}</h3>"
    
                # ---------- INPUT ----------
                elif ctype == "input":
                    html = f"""
                    <label>
                        {ctext or cid}
                        <input data-id="{cid}" placeholder="{ctext}" />
                    </label>
                    """
    
                # ---------- TEXTAREA ----------
                elif ctype == "textarea":
                    html = f"""
                    <label>
                        {ctext or cid}
                        <textarea data-id="{cid}" placeholder="{ctext}"></textarea>
                    </label>
                    """
    
                # ---------- BUTTON ----------
                elif ctype == "button":
                    html = f"<button data-id='{cid}'>{ctext or cid}</button>"
    
                # ---------- CHECKBOX ----------
                elif ctype == "checkbox":
                    html = f"""
                    <label>
                        <input type="checkbox" data-id="{cid}" />
                        {ctext or cid}
                    </label>
                    """
    
                # ---------- LIST ----------
                elif ctype == "list":
                    html = f"""
                    <ul data-id="{cid}" class="list">
                        <li class="list-empty">{ctext or f'[{cid}]'}</li>
                    </ul>
                    """
    
                # ---------- DROPDOWN ----------
                elif ctype == "dropdown":
                    html = f"""
                    <select data-id="{cid}">
                        <option selected>{ctext or f'[{cid}]'}</option>
                    </select>
                    """
    
                # ---------- IMAGE ----------
                elif ctype == "image":
                    html = f"""
                    <div class="image">
                        <img data-id="{cid}" alt="{ctext or cid}" />
                        <span class="image-label">{ctext or cid}</span>
                    </div>
                    """
    
                # ---------- VIDEO PLAYER ----------
                elif ctype == "video_player":
                    html = f"""
                    <div class="video">
                        <div class="video-placeholder">▶ {ctext or cid}</div>
                    </div>
                    """
    
                # ---------- CONTAINER ----------
                elif ctype == "container":
                    html = f"""
                    <div class="container" data-id="{cid}">
                        <div class="container-title">{ctext or cid}</div>
                    </div>
                    """
    
                # ---------- DIVIDER ----------
                elif ctype == "divider":
                    html = "<hr />"
    
                else:
                    raise ValueError(f"Unsupported component type: {ctype}")
    
                slots[slot] += html + "\n"
    
            slot_html = ""
            for name, content in slots.items():
                slot_html += f"""
                <div class="slot slot-{name}">
                    {content}
                </div>
                """
    
            html_pages.append(f"""
            <section class="page" data-page="{page["page_id"]}">
                {slot_html}
            </section>
            """)
    
        return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>{page_titles or "Layout Preview"}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                padding: 20px;
                background: #f4f4f4;
            }}
            section.page {{
                background: #fff;
                padding: 20px;
                margin-bottom: 30px;
            }}
            .slot {{
                margin-bottom: 20px;
            }}
            label {{
                display: block;
                margin-bottom: 10px;
            }}
            .container {{
                border: 1px solid #ccc;
                padding: 10px;
            }}
            .container-title {{
                font-weight: bold;
                margin-bottom: 5px;
            }}
            .list-empty {{
                color: #888;
                font-style: italic;
            }}
            .video-placeholder {{
                background: #000;
                color: #fff;
                padding: 20px;
                text-align: center;
            }}
        </style>
    </head>
    <body>
        {''.join(html_pages)}
    </body>
    </html>
        """


    def parse_preview_text(self,lines):
        pages = []
        current_page = None
        current_component = None
        in_action = False
    
        for idx, raw_line in enumerate(lines, start=1):
            line = raw_line.rstrip()
    
            if not line.strip():
                continue
    
            if line.startswith("-" * 10):
                if current_page:
                    pages.append(current_page)
                current_page = None
                current_component = None
                in_action = False
                continue
    
            if line.startswith("Page:"):
                m = re.match(r"Page:\s+(\w+)\s+\((\w+)\)", line)
                if not m:
                    raise PreviewParseError(f"Line {idx}: Invalid Page syntax → {line}")
    
                current_page = {
                    "page_id": m.group(1),
                    "layout": m.group(2),
                    "title": "",
                    "components": []
                }
                continue
    
            if line.startswith("Title:"):
                if not current_page:
                    raise PreviewParseError(f"Line {idx}: Title without Page")
                current_page["title"] = line.split("Title:", 1)[1].strip()
                continue
    
            if line.strip().startswith("Component:"):
                if not current_page:
                    raise PreviewParseError(f"Line {idx}: Component outside Page")
    
                current_component = {
                    "id": line.split("Component:", 1)[1].strip(),
                    "type": "",
                    "slot": "",
                    "actions": []
                }
                current_page["components"].append(current_component)
                in_action = False
                continue
    
            if line.strip().startswith("Type:"):
                if not current_component:
                    raise PreviewParseError(f"Line {idx}: Type outside Component")
                current_component["type"] = line.split("Type:", 1)[1].strip()
                continue
            if line.strip().startswith("Text:"):
                if not current_component:
                    raise PreviewParseError(f"Line {idx}: Text outside Component")
                current_component["text"] = line.split("Text:", 1)[1].strip()
                continue

    
            if line.strip().startswith("Slot:"):
                if not current_component:
                    raise PreviewParseError(f"Line {idx}: Slot outside Component")
                current_component["slot"] = line.split("Slot:", 1)[1].strip()
                continue
    
            if line.strip().startswith("Action:"):
                if not current_component:
                    raise PreviewParseError(f"Line {idx}: Action outside Component")
                in_action = True
                continue
    
            if in_action:
                m = re.match(r"\s*-\s*(.+)", line)
                if not m:
                    raise PreviewParseError(
                        f"Line {idx}: Invalid action item → {line}"
                    )
                current_component["actions"].append(m.group(1))
                continue
    
            raise PreviewParseError(f"Line {idx}: Unrecognized syntax → {line}")
    
        if current_page:
            pages.append(current_page)
    
        if not pages:
            raise PreviewParseError("No pages found in preview")
    
        return pages
    
    def open_preview_in_browser(self):
        try:
            raw_text = self.preview.get("1.0", tk.END)
            lines = raw_text.splitlines()
            pages = self.parse_preview_text(lines)
            html = self.generate_html(pages)
    
        except PreviewParseError as e:
            tk.messagebox.showerror(
                "Preview Syntax Error",
                str(e)
            )
            return
    
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=".html", encoding="utf-8", mode="w"
        ) as f:
            f.write(html)
            path = f.name
    
        webbrowser.open(f"file:///{path.replace(os.sep, '/')}")

class PreviewParseError(Exception):
    pass

if __name__ == "__main__":
    LayoutEditorApp().mainloop()