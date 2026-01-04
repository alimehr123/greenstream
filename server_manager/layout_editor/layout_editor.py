# server/server_manager/layout_editor/layout_editor.py
import os
import sys
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# -------------------------------------------------
# Bootstrap: allow standalone execution
# -------------------------------------------------
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# -------------------------------------------------
# Editor Application
# -------------------------------------------------
class LayoutEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.current_file = None
        self.is_dirty = False
        self._update_title()

        self.title("Layout Editor")
        self.geometry("1200x700")
        self.state("zoomed")

        self.current_file = None
        self.layout_data = self.empty_layout()

        self._build_menu()
        self._build_ui()
        self._bind_shortcuts()

        self.update_tree()
        self.set_status("Ready")
        
        self.protocol("WM_DELETE_WINDOW", self.on_exit)

    # -------------------------------------------------
    # Termination
    # -------------------------------------------------
    def on_exit(self):
        if not self.confirm_discard_changes():
            return
        self.destroy()

    # -------------------------------------------------
    # Update Screen Title:
    # -------------------------------------------------
    def _update_title(self):
        if self.current_file:
            name = os.path.basename(self.current_file)
        else:
            name = "(untitled)"
    
        dirty = " *" if self.is_dirty else ""
        self.title(f"Layout Editor: {name}{dirty}")
    
    def mark_dirty(self):
        if not self.is_dirty:
            self.is_dirty = True
            self._update_title()
        
    def mark_clean(self):
        self.is_dirty = False
        self._update_title()

    # -------------------------------------------------
    # Layout Model
    # -------------------------------------------------
    def empty_layout(self):
        return {
            "identity": {},
            "policy": {},
            "navigation": {},
            "state": {},
            "pages": [],
            "components": {},
            "actions": {},
            "interactions": []
        }

    # -------------------------------------------------
    # Menu
    # -------------------------------------------------
    def _build_menu(self):
        menubar = tk.Menu(self)

        # File
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New Layout", accelerator="Ctrl+N", command=self.new_layout)
        file_menu.add_command(label="Open Layout...", accelerator="Ctrl+O", command=self.open_layout)
        file_menu.add_command(label="Save Layout", accelerator="Ctrl+S", command=self.save_layout)
        file_menu.add_command(label="Save Layout As...", command=self.save_layout_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", accelerator="Ctrl+Q", command=self.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        # Validation
        validation_menu = tk.Menu(menubar, tearoff=0)
        validation_menu.add_command(label="Validate Layout", command=self.validate_layout)
        validation_menu.add_command(label="Compile Layout", command=self.compile_layout)
        validation_menu.add_command(label="Show Last Errors", command=self.show_errors)
        validation_menu.add_separator()
        validation_menu.add_command(label="Clear Errors", command=lambda: self.set_status("Errors cleared"))
        menubar.add_cascade(label="Validation", menu=validation_menu)

        # Help
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Layout Contract", command=self.show_contract)
        help_menu.add_command(label="Application Help", command=self.show_help)
        help_menu.add_command(label="Keyboard Shortcuts", command=self.show_shortcuts)
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.config(menu=menubar)

    def _bind_shortcuts(self):
        self.bind_all("<Control-n>", lambda e: self.new_layout())
        self.bind_all("<Control-o>", lambda e: self.open_layout())
        self.bind_all("<Control-s>", lambda e: self.save_layout())
        self.bind_all("<Control-q>", lambda e: self.quit())

    # -------------------------------------------------
    # UI Layout
    # -------------------------------------------------
    def _build_ui(self):
        main = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main.pack(fill=tk.BOTH, expand=True)
        
        style = ttk.Style()
        style.configure(
            "Custom.Treeview",
            background="#e8eef5",
            fieldbackground="#e8eef5",
            foreground="#000000"
        )

        # Tree (Left)
        tree_frame = tk.Frame(main, width=300, bg="#e8eef5")
        # self.tree = ttk.Treeview(tree_frame, show="tree")
        self.tree = ttk.Treeview(tree_frame, style="Custom.Treeview")
        # self.tree.configure(background="#e8eef5")
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        main.add(tree_frame, weight=1)
        
        # Center (Page Composer)
        center = tk.Frame(main, bg="#bbffaa")
        main.add(center, weight=2)

        # ttk.Label(center, text="Page Composer", font=("Arial", 11, "bold")).pack(anchor="w", padx=5, pady=5)
        tk.Label(
            center,
            text="Page Composer",
            font=("Arial", 11, "bold"),
            bg="#bbffaa",
            fg="#333333"
        ).pack(anchor="w", padx=5, pady=5)

        self.page_list = ttk.Combobox(center, state="readonly")
        self.page_list.pack(fill=tk.X, padx=5)
        self.page_list.bind("<<ComboboxSelected>>", self.on_page_selected)

        self.component_list = tk.Listbox(center, bg="#ffffff")
        self.component_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        buttons = ttk.Frame(center)
        buttons.pack(fill=tk.X)

        ttk.Button(buttons, text="Add", command=self.add_component_to_page).pack(side=tk.LEFT)
        ttk.Button(buttons, text="Remove", command=self.remove_component_from_page).pack(side=tk.LEFT)
        ttk.Button(buttons, text="Up", command=lambda: self.move_component(-1)).pack(side=tk.LEFT)
        ttk.Button(buttons, text="Down", command=lambda: self.move_component(1)).pack(side=tk.LEFT)
        ttk.Button(buttons, text="Jump to Component", command=self.jump_to_component).pack(side=tk.LEFT)

        # # Right (Details placeholder)
        # right = ttk.Frame(main, width=300)
        # ttk.Label(right, text="Details Panel", font=("Arial", 11, "bold")).pack(anchor="w", padx=5)
        # ttk.Label(right, text="(Version 1 – Placeholder)").pack(anchor="w", padx=5)
        # main.add(right, weight=1)
        
        # Right (Details Panel)
        self.details_panel = ttk.Frame(main, width=300)
        main.add(self.details_panel, weight=1)
        
        self.details_title = ttk.Label(
            self.details_panel,
            text="Details",
            font=("Arial", 11, "bold")
        )
        self.details_title.pack(anchor="w", padx=5, pady=5)
        
        self.details_body = ttk.Frame(self.details_panel)
        self.details_body.pack(fill=tk.BOTH, expand=True, padx=5)

        # Status Bar (5 lines)
        status_frame = ttk.Frame(self)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_text = tk.Text(
            status_frame,
            height=5,
            wrap="word",
            state="disabled",
            background="#f5f5b5"
        )
        self.status_text.pack(fill=tk.X, side=tk.LEFT, expand=True)
    
    # -------------------------------------------------
    # Tree Handling
    # -------------------------------------------------
    def update_tree(self):
        self.tree.delete(*self.tree.get_children())
        root = self.tree.insert("", "end", text="Layout", open=True)

        sections = [
            "identity", "policy", "navigation", "state",
            "pages", "components", "actions", "interactions"
        ]

        for sec in sections:
            sec_id = self.tree.insert(root, "end", text=sec.capitalize(), open=True)
            value = self.layout_data.get(sec)
            if isinstance(value, dict):
                for k in value.keys():
                    self.tree.insert(sec_id, "end", text=k)
            elif isinstance(value, list):
                for item in value:
                    label = item.get("id", str(item)) if isinstance(item, dict) else str(item)
                    self.tree.insert(sec_id, "end", text=label)

        self.update_pages_combo()

    # -------------------------------------------------
    # Page Composer
    # -------------------------------------------------
    def update_pages_combo(self):
        pages = [p["id"] for p in self.layout_data["pages"]]
        self.page_list["values"] = pages
        if pages:
            self.page_list.current(0)
            self.load_page_components(pages[0])

    def on_page_selected(self, _):
        self.load_page_components(self.page_list.get())

    def load_page_components(self, page_id):
        self.component_list.delete(0, tk.END)
        page = next(p for p in self.layout_data["pages"] if p["id"] == page_id)
        for c in page.get("components", []):
            self.component_list.insert(tk.END, c)

    def add_component_to_page(self):
        if not self.layout_data["components"]:
            return
        comp = list(self.layout_data["components"].keys())[0]
        page = self._current_page()
        page["components"].append(comp)
        self.load_page_components(page["id"])
        

    def remove_component_from_page(self):
        idx = self.component_list.curselection()
        if not idx:
            return
        page = self._current_page()
        page["components"].pop(idx[0])
        self.load_page_components(page["id"])

    def move_component(self, delta):
        idx = self.component_list.curselection()
        if not idx:
            return
        idx = idx[0]
        page = self._current_page()
        comp = page["components"].pop(idx)
        new_idx = max(0, min(len(page["components"]), idx + delta))
        page["components"].insert(new_idx, comp)
        self.load_page_components(page["id"])
        self.component_list.select_set(new_idx)

    def jump_to_component(self):
        idx = self.component_list.curselection()
        if not idx:
            return
        name = self.component_list.get(idx)
        for i in self.tree.get_children():
            if self.tree.item(i, "text") == "Components":
                for c in self.tree.get_children(i):
                    if self.tree.item(c, "text") == name:
                        self.tree.selection_set(c)
                        self.tree.see(c)
                        return

    def _current_page(self):
        pid = self.page_list.get()
        return next(p for p in self.layout_data["pages"] if p["id"] == pid)

    # -------------------------------------------------
    # File Actions
    # -------------------------------------------------
    def confirm_discard_changes(self):
        """
        Returns True if the caller may proceed.
        Returns False if the operation should be cancelled.
        """
        if not self.is_dirty:
            return True
    
        result = messagebox.askyesnocancel(
            title="Unsaved Changes",
            message="You have unsaved changes.\n\nDo you want to save them?"
        )

        # Cancel
        if result is None:
            return False
    
        # Yes → Save
        if result is True:
            saved = self.save_layout()
        # if user cancels save as
            return bool(saved)
    
        # No → Discard changes
        return True
    
    def new_layout(self):
        if not self.confirm_discard_changes():
           return
    
        # reset editor state
        self.current_file = None
        self.is_dirty = False
        self._update_title()
    
        self.set_status("New layout created.")

    def open_layout(self):
        if not self.confirm_discard_changes():
            return
    
        path = filedialog.askopenfilename(filetypes=[("Layout JSON", "*.json")])
        if not path:
            return
        with open(path, "r", encoding="utf-8") as f:
            self.layout_data = json.load(f)
    
        # load layout logic
        self.current_file = path
        self.is_dirty = False
        self._update_title()
        
        self.update_tree()
        self.set_status(f"Opened {path}")

    def save_layout(self):
        if not self.current_file:
            return self.save_layout_as()
    
        try:
            # serialize → compile → save
            self.editor_save_pipeline.save(self.current_file)
    
            self.mark_clean()
            self.set_status("Layout saved.")
            return True
        except Exception as e:
            messagebox.showerror("Save Failed", str(e))
            return False

    def save_layout_as(self):
        path = filedialog.asksaveasfilename(
            title="Save Layout As",
            defaultextension=".json",
            filetypes=[("Layout Files", "*.json")]
        )
        if not path:
            return False
    
        try:
            self.editor_save_pipeline.save(path)
    
            self.current_file = path
            self.mark_clean()
            self.set_status(f"Saved as:\n{path}")
            return True
        except Exception as e:
            messagebox.showerror("Save Failed", str(e))
            return False

    # -------------------------------------------------
    # Validation / Help Stubs
    # -------------------------------------------------
    def validate_layout(self):
        self.set_status("Validation passed (stub)")

    def compile_layout(self):
        self.set_status("Compilation successful (stub)")

    def show_errors(self):
        messagebox.showinfo("Errors", "No errors recorded")

    def show_contract(self):
        messagebox.showinfo("Layout Contract", "See Layout_Contract_.docx")

    def show_help(self):
        messagebox.showinfo("Help", "Layout Editor Version 1")

    def show_shortcuts(self):
        messagebox.showinfo(
            "Shortcuts",
            "Ctrl+N New\nCtrl+O Open\nCtrl+S Save\nCtrl+Q Exit"
        )

    def show_about(self):
        messagebox.showinfo("About", "Layout Editor\nVersion 1")

    # -------------------------------------------------
    def set_status(self, text, clear=True):
        self.status_text.config(state="normal")
        if clear:
            self.status_text.delete("1.0", tk.END)
        self.status_text.insert(tk.END, text + "\n")
        self.status_text.see(tk.END)
        self.status_text.config(state="disabled")
    
    #-----------------------------------------
    # details panel functions
    #-----------------------------------------
    def _policy_add_condition(self, lb):
        policy = self.layout_data["policy"]
        conditions = policy.setdefault("conditions", [])
    
        conditions.append({
            "source": "context",
            "key": "",
            "operator": "eq",
            "value": None
        })
    
        lb.insert(tk.END, "? eq")
        self.mark_dirty()
    
    
    def _policy_remove_condition(self, lb):
        sel = lb.curselection()
        if not sel:
            return
    
        index = sel[0]
        del self.layout_data["policy"]["conditions"][index]
        lb.delete(index)
        self.mark_dirty()

    def show_details(self, section, key):
        self.details_clear()
    
        if section == "Identity":
            self.show_identity_details()
        elif section == "Policy":
            self.show_policy_details()
        elif section == "Navigation":
            self.show_navigation_details()
        elif section == "State":
            self.show_state_details()
        elif section == "Pages":
            self.show_page_details(key)
        elif section == "Components":
            self.show_component_details(key)
        elif section == "Actions":
            self.show_action_details(key)
        elif section == "Interactions":
            self.show_interaction_details(key)
    
    def show_identity_details(self):
        self.details_title.config(text="Identity")
    
        identity = self.layout_data["identity"]
    
        for field in ("name", "version", "schema_version"):
            ttk.Label(self.details_body, text=field).pack(anchor="w")
            var = tk.StringVar(value=identity.get(field, ""))
            entry = ttk.Entry(self.details_body, textvariable=var)
            entry.pack(fill=tk.X, pady=2)
    
            def commit(v=var, f=field):
                identity[f] = v.get()
                self.mark_dirty()
    
            entry.bind("<FocusOut>", lambda e, c=commit: c())
            
    def show_policy_details(self):
        self.details_title.config(text="Policy")
    
        policy = self.layout_data.setdefault("policy", {})
        conditions = policy.setdefault("conditions", [])
    
        # ---- Listbox of conditions ----
        ttk.Label(self.details_body, text="Conditions").pack(anchor="w")
    
        list_frame = ttk.Frame(self.details_body)
        list_frame.pack(fill=tk.BOTH, expand=True)
    
        lb = tk.Listbox(list_frame, height=6)
        lb.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
        sb = ttk.Scrollbar(list_frame, orient="vertical", command=lb.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        lb.config(yscrollcommand=sb.set)
    
        for i, cond in enumerate(conditions):
            label = f"{cond.get('key','?')} {cond.get('operator','?')}"
            lb.insert(tk.END, label)
    
        # ---- Buttons ----
        btns = ttk.Frame(self.details_body)
        btns.pack(fill=tk.X, pady=5)
    
        ttk.Button(
            btns,
            text="Add",
            command=lambda: self._policy_add_condition(lb)
        ).pack(side=tk.LEFT)
    
        ttk.Button(
            btns,
            text="Remove",
            command=lambda: self._policy_remove_condition(lb)
        ).pack(side=tk.LEFT, padx=5)
    
        # ---- Editor Frame ----
        editor = ttk.Frame(self.details_body)
        editor.pack(fill=tk.BOTH, expand=True, pady=5)
    
        def render_editor(index):
            for w in editor.winfo_children():
                w.destroy()
    
            if index is None:
                return
    
            cond = conditions[index]
    
            # source (LOCKED = context)
            ttk.Label(editor, text="source").pack(anchor="w")
            ttk.Label(editor, text=cond.get("source", "context")).pack(anchor="w")
    
            # key
            ttk.Label(editor, text="key").pack(anchor="w")
            key_var = tk.StringVar(value=cond.get("key", ""))
            key_entry = ttk.Entry(editor, textvariable=key_var)
            key_entry.pack(fill=tk.X)
    
            # operator
            ttk.Label(editor, text="operator").pack(anchor="w")
            op_var = tk.StringVar(value=cond.get("operator", "eq"))
            op_combo = ttk.Combobox(
                editor,
                textvariable=op_var,
                values=["eq", "neq", "in", "not_in"],
                state="readonly"
            )
            op_combo.pack(fill=tk.X)
    
            # value (raw)
            ttk.Label(editor, text="value (raw)").pack(anchor="w")
            val_txt = tk.Text(editor, height=4)
            val_txt.pack(fill=tk.BOTH, expand=True)
            val_txt.insert("1.0", json.dumps(cond.get("value"), indent=2))
    
            def commit():
                cond["source"] = "context"
                cond["key"] = key_var.get()
                cond["operator"] = op_var.get()
                try:
                    cond["value"] = json.loads(val_txt.get("1.0", tk.END))
                except Exception:
                    cond["value"] = val_txt.get("1.0", tk.END).strip()
    
                self.mark_dirty()
                lb.delete(index)
                lb.insert(index, f"{cond.get('key','?')} {cond.get('operator','?')}")
    
            key_entry.bind("<FocusOut>", lambda e: commit())
            op_combo.bind("<<ComboboxSelected>>", lambda e: commit())
            val_txt.bind("<FocusOut>", lambda e: commit())
    
        def on_select(_):
            sel = lb.curselection()
            render_editor(sel[0] if sel else None)
    
        lb.bind("<<ListboxSelect>>", on_select)

    def show_navigation_details(self):
        self.details_title.config(text="Navigation")
    
        navigation = self.layout_data["navigation"]
    
        ttk.Label(self.details_body, text="initial_page").pack(anchor="w")
    
        # extract available page IDs
        pages = [p["id"] for p in self.layout_data.get("pages", [])]
    
        var = tk.StringVar(value=navigation.get("initial_page", ""))
    
        combo = ttk.Combobox(
            self.details_body,
            textvariable=var,
            values=pages,
            state="readonly"
        )
        combo.pack(fill=tk.X, pady=2)
    
        def commit():
            navigation["initial_page"] = var.get()
            self.mark_dirty()
    
        combo.bind("<<ComboboxSelected>>", lambda e: commit())

    def show_state_details(self):
        self.details_title.config(text="State")
    
        state_container = self.layout_data.setdefault("state", {})
    
        main = ttk.Frame(self.details_body)
        main.pack(fill=tk.BOTH, expand=True)
    
        # ─────────────────────────────
        # Left: State list
        # ─────────────────────────────
        left = ttk.Frame(main)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=4)
    
        ttk.Label(left, text="States").pack(anchor="w")
    
        state_list = tk.Listbox(left, height=10)
        state_list.pack(fill=tk.Y, expand=True)
    
        for key in state_container.keys():
            state_list.insert(tk.END, key)
    
        def add_state():
            base = "state"
            i = 1
            key = f"{base}.{i}"
            while key in state_container:
                i += 1
                key = f"{base}.{i}"
    
            state_container[key] = {
                "owner": "layout",
                "type": "string",
                "lifecycle": {
                    "create": "layout_init",
                    "destroy": "layout_exit",
                },
            }
    
            state_list.insert(tk.END, key)
            self.mark_dirty()
    
        def remove_state():
            sel = state_list.curselection()
            if not sel:
                return
            key = state_list.get(sel[0])
            del state_container[key]
            state_list.delete(sel[0])
            editor.destroy()
            self.mark_dirty()
    
        btns = ttk.Frame(left)
        btns.pack(fill=tk.X, pady=4)
    
        ttk.Button(btns, text="+", width=3, command=add_state).pack(side=tk.LEFT)
        ttk.Button(btns, text="–", width=3, command=remove_state).pack(side=tk.LEFT)
    
        # ─────────────────────────────
        # Right: Editor
        # ─────────────────────────────
        editor = ttk.Frame(main)
        editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8)
    
        def show_editor(state_key):
            for w in editor.winfo_children():
                w.destroy()
    
            data = state_container[state_key]
    
            def field(label, widget):
                ttk.Label(editor, text=label).pack(anchor="w")
                widget.pack(fill=tk.X, pady=2)
    
            # owner
            owner = tk.StringVar(value=data.get("owner", "layout"))
            owner_cb = ttk.Combobox(
                editor,
                textvariable=owner,
                values=["layout", "page", "component"],
                state="readonly",
            )
            field("owner", owner_cb)
    
            owner_cb.bind("<<ComboboxSelected>>", lambda e: commit())
    
            # page
            page_var = tk.StringVar(value=data.get("page", ""))
            field("page", ttk.Entry(editor, textvariable=page_var))
    
            # component
            component_var = tk.StringVar(value=data.get("component", ""))
            field("component", ttk.Entry(editor, textvariable=component_var))
    
            # type
            typ = tk.StringVar(value=data.get("type", "string"))
            type_cb = ttk.Combobox(
                editor,
                textvariable=typ,
                values=["string", "number", "boolean", "object", "array"],
                state="readonly",
            )
            field("type", type_cb)
    
            # flags
            readonly = tk.BooleanVar(value=data.get("readonly", False))
            nullable = tk.BooleanVar(value=data.get("nullable", False))
    
            ttk.Checkbutton(editor, text="readonly", variable=readonly).pack(anchor="w")
            ttk.Checkbutton(editor, text="nullable", variable=nullable).pack(anchor="w")
    
            # initial
            init = tk.StringVar(value=str(data.get("initial", "")))
            field("initial", ttk.Entry(editor, textvariable=init))
    
            # lifecycle
            ttk.Label(editor, text="lifecycle.create").pack(anchor="w")
            lc_create = tk.StringVar(
                value=data.get("lifecycle", {}).get("create", "layout_init")
            )
            ttk.Combobox(
                editor,
                textvariable=lc_create,
                values=["layout_init", "page_enter"],
                state="readonly",
            ).pack(fill=tk.X)
    
            ttk.Label(editor, text="lifecycle.destroy").pack(anchor="w")
            lc_destroy = tk.StringVar(
                value=data.get("lifecycle", {}).get("destroy", "layout_exit")
            )
            ttk.Combobox(
                editor,
                textvariable=lc_destroy,
                values=["layout_exit", "page_exit"],
                state="readonly",
            ).pack(fill=tk.X)
    
            # mutable_by
            mutable = tk.StringVar(
                value=", ".join(data.get("mutable_by", []))
            )
            field("mutable_by", ttk.Entry(editor, textvariable=mutable))
    
            def commit(*_):
                data["owner"] = owner.get()
                data["type"] = typ.get()
                data["readonly"] = readonly.get()
                data["nullable"] = nullable.get()
    
                if page_var.get():
                    data["page"] = page_var.get()
                else:
                    data.pop("page", None)
    
                if component_var.get():
                    data["component"] = component_var.get()
                else:
                    data.pop("component", None)
    
                data["initial"] = init.get()
    
                data["lifecycle"] = {
                    "create": lc_create.get(),
                    "destroy": lc_destroy.get(),
                }
    
                mb = [x.strip() for x in mutable.get().split(",") if x.strip()]
                if mb:
                    data["mutable_by"] = mb
                else:
                    data.pop("mutable_by", None)
    
                self.mark_dirty()
    
            for v in (
                owner, page_var, component_var, typ,
                readonly, nullable, init,
                lc_create, lc_destroy, mutable
            ):
                try:
                    v.trace_add("write", commit)
                except Exception:
                    pass
    
        state_list.bind(
            "<<ListboxSelect>>",
            lambda e: show_editor(state_list.get(state_list.curselection()[0]))
            if state_list.curselection()
            else None,
        )


    def show_page_details(self, page_id):
        self.details_title.config(text=f"Page: {page_id}")
        page = next(p for p in self.layout_data["pages"] if p["id"] == page_id)
    
        # ─────────────────────────────
        # ID (read-only)
        # ─────────────────────────────
        ttk.Label(self.details_body, text="id").pack(anchor="w")
        id_entry = ttk.Entry(self.details_body, state="readonly")
        id_entry.pack(fill=tk.X)
        id_entry.configure(state="normal")
        id_entry.insert(0, page_id)
        id_entry.configure(state="readonly")
    
        # ─────────────────────────────
        # title
        # ─────────────────────────────
        title_var = tk.StringVar(value=page.get("title", ""))
    
        ttk.Label(self.details_body, text="title").pack(anchor="w")
        ttk.Entry(self.details_body, textvariable=title_var).pack(fill=tk.X)
    
        def commit_title(*_):
            page["title"] = title_var.get()
            self.mark_dirty()
    
        title_var.trace_add("write", commit_title)
    
        # ─────────────────────────────
        # Components
        # ─────────────────────────────
        ttk.Label(self.details_body, text="components").pack(anchor="w")
    
        frame = ttk.Frame(self.details_body)
        frame.pack(fill=tk.BOTH, expand=True)
    
        listbox = tk.Listbox(frame, height=8)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
        for c in page.get("components", []):
            listbox.insert(tk.END, c)
    
        controls = ttk.Frame(frame)
        controls.pack(side=tk.LEFT, padx=4, fill=tk.Y)
    
        all_components = list(self.layout_data.get("components", {}).keys())
        sel_var = tk.StringVar()
    
        ttk.Combobox(
            controls,
            textvariable=sel_var,
            values=all_components,
            state="readonly"
        ).pack(fill=tk.X, pady=2)
    
        def add_component():
            cid = sel_var.get()
            if not cid:
                return
            page.setdefault("components", []).append(cid)
            listbox.insert(tk.END, cid)
            self.mark_dirty()
    
        def remove_component():
            sel = listbox.curselection()
            if not sel:
                return
            idx = sel[0]
            page["components"].pop(idx)
            listbox.delete(idx)
            self.mark_dirty()
    
        def move(delta):
            sel = listbox.curselection()
            if not sel:
                return
            i = sel[0]
            j = i + delta
            if j < 0 or j >= listbox.size():
                return
            page["components"][i], page["components"][j] = (
                page["components"][j],
                page["components"][i],
            )
            txt = listbox.get(i)
            listbox.delete(i)
            listbox.insert(j, txt)
            listbox.selection_set(j)
            self.mark_dirty()
    
        ttk.Button(controls, text="+", width=3, command=add_component).pack()
        ttk.Button(controls, text="–", width=3, command=remove_component).pack()
        ttk.Button(controls, text="↑", width=3, command=lambda: move(-1)).pack()
        ttk.Button(controls, text="↓", width=3, command=lambda: move(1)).pack()

    def show_component_details(self, component_id):
        self.details_title.config(text=f"Component: {component_id}")
        component = self.layout_data["components"][component_id]
    
        # ─────────────────────────────
        # type (LOCKED)
        # ─────────────────────────────
        ttk.Label(self.details_body, text="type").pack(anchor="w")
        type_entry = ttk.Entry(self.details_body, state="readonly")
        type_entry.pack(fill=tk.X)
        type_entry.configure(state="normal")
        type_entry.insert(0, component["type"])
        type_entry.configure(state="readonly")
    
        # ─────────────────────────────
        # bind (key → state_path)
        # ─────────────────────────────
        ttk.Label(self.details_body, text="bind").pack(anchor="w")
        bind = component.setdefault("bind", {})
    
        bind_frame = ttk.Frame(self.details_body)
        bind_frame.pack(fill=tk.X)
    
        bind_list = tk.Listbox(bind_frame, height=5)
        bind_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
        for k, v in bind.items():
            bind_list.insert(tk.END, f"{k} = {v}")
    
        def add_bind():
            key = key_var.get()
            val = val_var.get()
            if not key or not val:
                return
            bind[key] = val
            bind_list.insert(tk.END, f"{key} = {val}")
            self.mark_dirty()
    
        def remove_bind():
            sel = bind_list.curselection()
            if not sel:
                return
            txt = bind_list.get(sel[0])
            k = txt.split("=", 1)[0].strip()
            bind.pop(k, None)
            bind_list.delete(sel[0])
            self.mark_dirty()
    
        key_var = tk.StringVar()
        val_var = tk.StringVar()
    
        ttk.Entry(self.details_body, textvariable=key_var).pack(fill=tk.X)
        ttk.Entry(self.details_body, textvariable=val_var).pack(fill=tk.X)
    
        ttk.Button(self.details_body, text="Add bind", command=add_bind).pack()
        ttk.Button(self.details_body, text="Remove bind", command=remove_bind).pack()
    
        # ─────────────────────────────
        # events (event → action_id)
        # ─────────────────────────────
        ttk.Label(self.details_body, text="events").pack(anchor="w")
        events = component.setdefault("events", {})
    
        events_list = tk.Listbox(self.details_body, height=5)
        events_list.pack(fill=tk.X)
    
        for e, a in events.items():
            events_list.insert(tk.END, f"{e} → {a}")
    
        evt_var = tk.StringVar()
        act_var = tk.StringVar()
    
        ttk.Entry(self.details_body, textvariable=evt_var).pack(fill=tk.X)
        ttk.Entry(self.details_body, textvariable=act_var).pack(fill=tk.X)
    
        def add_event():
            e = evt_var.get()
            a = act_var.get()
            if not e or not a:
                return
            events[e] = a
            events_list.insert(tk.END, f"{e} → {a}")
            self.mark_dirty()
    
        def remove_event():
            sel = events_list.curselection()
            if not sel:
                return
            txt = events_list.get(sel[0])
            e = txt.split("→", 1)[0].strip()
            events.pop(e, None)
            events_list.delete(sel[0])
            self.mark_dirty()
    
        ttk.Button(self.details_body, text="Add event", command=add_event).pack()
        ttk.Button(self.details_body, text="Remove event", command=remove_event).pack()
    
    def show_action_details(self, action_id):
        self.details_title.config(text=f"Action: {action_id}")
        action = self.layout_data["actions"][action_id]
    
        # ─────────────────────────────
        # id (read-only)
        # ─────────────────────────────
        ttk.Label(self.details_body, text="id").pack(anchor="w")
        id_entry = ttk.Entry(self.details_body, state="readonly")
        id_entry.pack(fill=tk.X)
        id_entry.configure(state="normal")
        id_entry.insert(0, action_id)
        id_entry.configure(state="readonly")
    
        # ─────────────────────────────
        # intent
        # ─────────────────────────────
        ttk.Label(self.details_body, text="intent").pack(anchor="w")
        intent_var = tk.StringVar(value=action.get("intent", ""))
        ttk.Entry(self.details_body, textvariable=intent_var).pack(fill=tk.X)
    
        def commit_intent(*_):
            action["intent"] = intent_var.get()
            self.mark_dirty()
    
        intent_var.trace_add("write", commit_intent)
    
        # ─────────────────────────────
        # target (enum)
        # ─────────────────────────────
        ttk.Label(self.details_body, text="target").pack(anchor="w")
        target_var = tk.StringVar(value=action.get("target", ""))
    
        ttk.Combobox(
            self.details_body,
            textvariable=target_var,
            values=["state", "navigation", "external"],
            state="readonly"
        ).pack(fill=tk.X)
    
        def commit_target(*_):
            action["target"] = target_var.get()
            self.mark_dirty()
    
        target_var.trace_add("write", commit_target)
    
        # ─────────────────────────────
        # params (raw JSON, no logic)
        # ─────────────────────────────
        ttk.Label(self.details_body, text="params (raw JSON)").pack(anchor="w")
    
        params = action.setdefault("params", {})
    
        text = tk.Text(self.details_body, height=6)
        text.pack(fill=tk.BOTH, expand=True)
        text.insert("1.0", json.dumps(params, indent=2))
    
        def commit_params():
            try:
                value = json.loads(text.get("1.0", tk.END).strip())
                action["params"] = value
                self.mark_dirty()
                self.set_status("Params updated", level="info")
            except Exception as e:
                self.set_status(f"Invalid JSON in params: {e}", level="error")
    
        ttk.Button(self.details_body, text="Commit params", command=commit_params).pack(anchor="e")

    def show_interaction_details(self, index):
        self.details_title.config(text=f"Interaction #{index}")
        interaction = self.layout_data["interactions"][index]
    
        # ─────────────────────────────
        # trigger
        # ─────────────────────────────
        ttk.Label(self.details_body, text="trigger").pack(anchor="w")
        trigger_var = tk.StringVar(value=interaction.get("trigger", ""))
        ttk.Entry(self.details_body, textvariable=trigger_var).pack(fill=tk.X)
    
        def commit_trigger(*_):
            interaction["trigger"] = trigger_var.get()
            self.mark_dirty()
    
        trigger_var.trace_add("write", commit_trigger)
    
        # ─────────────────────────────
        # action (must reference existing action id)
        # ─────────────────────────────
        ttk.Label(self.details_body, text="action").pack(anchor="w")
    
        actions = list(self.layout_data.get("actions", {}).keys())
        action_var = tk.StringVar(value=interaction.get("action", ""))
    
        ttk.Combobox(
            self.details_body,
            textvariable=action_var,
            values=actions,
            state="readonly"
        ).pack(fill=tk.X)
    
        def commit_action(*_):
            interaction["action"] = action_var.get()
            self.mark_dirty()
    
        action_var.trace_add("write", commit_action)

    
    def details_clear(self):
        for w in self.details_body.winfo_children():
            w.destroy()

    def on_tree_select(self, _):
        sel = self.tree.selection()
        if not sel:
            return
    
        node = sel[0]
        text = self.tree.item(node, "text")
        parent = self.tree.parent(node)
        parent_text = self.tree.item(parent, "text") if parent else None
    
        self.show_details(parent_text, text)



if __name__ == "__main__":
    app = LayoutEditor()
    app.mainloop()
