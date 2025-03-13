#!/usr/bin/env python3
import json
import os
import pickle
import re
import shutil
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

class AliasData:
    def __init__(self, alias="", command="", section="", description=""):
        self.alias = alias
        self.command = command
        self.section = section
        self.description = description

    def __eq__(self, other):
        if not isinstance(other, AliasData):
            return False
        return (self.alias == other.alias and
                self.command == other.command and
                self.section == other.section and
                self.description == other.description)

class AliasManager:
    def __init__(self, bashrc_path=None, descriptions_path=None):
        self.bashrc_path = bashrc_path or os.path.expanduser("~/.bashrc")
        self.script_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        self.descriptions_path = descriptions_path or self.script_dir / "alias_descriptions.json"
        self.backups_dir = self.script_dir / "backups"
        self.settings_path = self.script_dir / "alias_manager_settings.pkl"
        self.backups_dir.mkdir(exist_ok=True)
        self.aliases = []
        self.sections = []
        self.descriptions = {}
        self.load_descriptions()
        self.load_aliases()

    def load_descriptions(self):
        if os.path.exists(self.descriptions_path):
            try:
                with open(self.descriptions_path, 'r') as f:
                    self.descriptions = json.load(f)
            except json.JSONDecodeError:
                messagebox.showerror("Error", "Failed to process descriptions file. Creating a new one.")
                self.descriptions = {}
        else:
            self.descriptions = {}

    def save_descriptions(self):
        with open(self.descriptions_path, 'w') as f:
            json.dump(self.descriptions, f, indent=4)

    def load_aliases(self):
        self.aliases = []
        self.sections = []
        try:
            in_custom_aliases = False
            current_section = ""
            with open(self.bashrc_path, 'r') as f:
                lines = f.readlines()
            for line in lines:
                line = line.strip()
                if line == "# CUSTOM ALIASES":
                    in_custom_aliases = True
                    continue
                elif line.startswith("# ") and in_custom_aliases:
                    if not line.startswith("# ↓"):
                        current_section = line[2:]
                        if current_section not in self.sections:
                            self.sections.append(current_section)
                elif line.startswith("alias ") and in_custom_aliases:
                    parts = line.split('=', 1)
                    if len(parts) == 2:
                        alias_name = parts[0].replace("alias ", "").strip()
                        command = parts[1].strip()
                        if (command.startswith("'") and command.endswith("'")) or (command.startswith('"') and command.endswith('"')):
                            command = command[1:-1]
                        description = self.descriptions.get(alias_name, "")
                        alias_data = AliasData(alias_name, command, current_section, description)
                        self.aliases.append(alias_data)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load aliases from .bashrc: {str(e)}")

    def add_alias(self, alias_data):
        self.aliases.append(alias_data)
        if alias_data.section not in self.sections:
            self.sections.append(alias_data.section)
        self.descriptions[alias_data.alias] = alias_data.description
        self.save_to_bashrc()
        self.save_descriptions()
        return True

    def update_alias(self, old_alias, alias_data):
        for i, a in enumerate(self.aliases):
            if a.alias == old_alias:
                if old_alias != alias_data.alias and old_alias in self.descriptions:
                    del self.descriptions[old_alias]
                self.aliases[i] = alias_data
                self.descriptions[alias_data.alias] = alias_data.description
                if alias_data.section not in self.sections:
                    self.sections.append(alias_data.section)
                break
        self.save_to_bashrc()
        self.save_descriptions()
        return True

    def delete_alias(self, alias_name):
        self.aliases = [a for a in self.aliases if a.alias != alias_name]
        if alias_name in self.descriptions:
            del self.descriptions[alias_name]
        self.save_to_bashrc()
        self.save_descriptions()
        return True

    def save_to_bashrc(self):
        try:
            with open(self.bashrc_path, 'r') as f:
                lines = f.readlines()
            start_idx = -1
            for i, line in enumerate(lines):
                if line.strip() == "# CUSTOM ALIASES":
                    start_idx = i
                    break
            if start_idx == -1:
                messagebox.showerror("Error", "Section # CUSTOM ALIASES not found in .bashrc")
                return False
            new_content = lines[:start_idx+1]
            new_content.append("\n")
            aliases_by_section = {}
            for a in self.aliases:
                if a.section not in aliases_by_section:
                    aliases_by_section[a.section] = []
                aliases_by_section[a.section].append(a)
            sorted_sections = sorted(aliases_by_section.keys())
            for section in sorted_sections:
                new_content.append(f"# {section}\n")
                section_aliases = sorted(aliases_by_section[section], key=lambda x: x.alias)
                for a in section_aliases:
                    if "'" in a.command:
                        new_content.append(f'alias {a.alias}="{a.command}"\n')
                    else:
                        new_content.append(f"alias {a.alias}='{a.command}'\n")
                new_content.append("\n")
            found_end = False
            for i in range(len(lines) - 1, start_idx, -1):
                if lines[i].strip().startswith("alias "):
                    end_idx = i + 1
                    found_end = True
                    break
            if found_end:
                for i in range(end_idx, len(lines)):
                    if lines[i].strip() and not lines[i].strip().startswith("alias ") and not lines[i].strip().startswith("# "):
                        new_content.extend(lines[i:])
                        break
            with open(self.bashrc_path, 'w') as f:
                f.writelines(new_content)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save aliases to .bashrc: {str(e)}")
            return False

    def add_section(self, section_name):
        if section_name not in self.sections:
            self.sections.append(section_name)
            return True
        return False

    def rename_section(self, old_name, new_name):
        if new_name in self.sections:
            return False
        self.sections = [new_name if s == old_name else s for s in self.sections]
        for alias in self.aliases:
            if alias.section == old_name:
                alias.section = new_name
        self.save_to_bashrc()
        return True

    def delete_section(self, section_name):
        if section_name in self.sections:
            if any(a.section == section_name for a in self.aliases):
                return False
            self.sections.remove(section_name)
            return True
        return False

    def export_aliases(self, filepath):
        try:
            data = {
                "aliases": [
                    {
                        "alias": a.alias,
                        "command": a.command,
                        "section": a.section,
                        "description": a.description
                    }
                    for a in self.aliases
                ],
                "sections": self.sections
            }
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=4)
            return True
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export aliases: {str(e)}")
            return False

    def import_aliases(self, filepath, overwrite=False):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            if overwrite:
                self.aliases = []
                self.descriptions = {}
                self.sections = []
            for section in data.get("sections", []):
                if section not in self.sections:
                    self.sections.append(section)
            for alias_data in data.get("aliases", []):
                alias = alias_data["alias"]
                command = alias_data["command"]
                section = alias_data["section"]
                description = alias_data.get("description", "")
                existing = next((a for a in self.aliases if a.alias == alias), None)
                if existing:
                    if overwrite:
                        self.update_alias(alias, AliasData(alias, command, section, description))
                else:
                    self.add_alias(AliasData(alias, command, section, description))
            self.save_to_bashrc()
            self.save_descriptions()
            return True
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import aliases: {str(e)}")
            return False

    def backup_bashrc(self):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(self.backups_dir, f"bashrc.backup_{timestamp}")
            shutil.copy2(self.bashrc_path, backup_path)
            return backup_path
        except Exception as e:
            messagebox.showerror("Backup Error", f"Failed to create backup of .bashrc: {str(e)}")
            return None

    def backup_descriptions(self):
        try:
            if os.path.exists(self.descriptions_path):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = os.path.join(self.backups_dir, f"alias_descriptions.backup_{timestamp}")
                shutil.copy2(self.descriptions_path, backup_path)
                return backup_path
            return None
        except Exception as e:
            messagebox.showerror("Backup Error", f"Failed to create backup of descriptions: {str(e)}")
            return None

class UndoRedoManager:
    def __init__(self, max_history=30):
        self.history = []
        self.future = []
        self.max_history = max_history

    def add_state(self, state):
        self.history.append(state)
        self.future = []
        if len(self.history) > self.max_history:
            self.history.pop(0)

    def can_undo(self):
        return len(self.history) > 0

    def can_redo(self):
        return len(self.future) > 0

    def undo(self):
        if not self.can_undo():
            return None
        state = self.history.pop()
        self.future.append(state)
        if self.history:
            return self.history[-1]
        return None

    def redo(self):
        if not self.can_redo():
            return None
        state = self.future.pop()
        self.history.append(state)
        return state

class StatusBar(ttk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.message_var = tk.StringVar()
        self.message_label = ttk.Label(self, textvariable=self.message_var, anchor=tk.W, padding=(5, 2))
        self.message_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def set_message(self, message, message_type="info"):
        self.message_var.set(message)
        style = ttk.Style()
        if message_type == "success":
            style.configure("Status.TLabel", foreground="green")
        elif message_type == "error":
            style.configure("Status.TLabel", foreground="red")
        elif message_type == "warning":
            style.configure("Status.TLabel", foreground="orange")
        else:
            style.configure("Status.TLabel", foreground="black")
        self.message_label.configure(style="Status.TLabel")
        self.after(5000, self.clear_message)

    def clear_message(self):
        self.message_var.set("")

class AliasDetailDialog(tk.Toplevel):
    def __init__(self, parent, alias):
        super().__init__(parent)
        self.title(f"Alias Details: {alias.alias}")
        self.geometry("600x400")
        self.minsize(500, 350)
        self.transient(parent)
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        style = ttk.Style()
        style.configure("Heading.TLabel", font=("", 10, "bold"))
        ttk.Label(frame, text="Alias:", style="Heading.TLabel").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Label(frame, text=alias.alias).grid(row=0, column=1, sticky=tk.W, pady=5)
        ttk.Label(frame, text="Command:", style="Heading.TLabel").grid(row=1, column=0, sticky=tk.NW, pady=5)
        command_frame = ttk.Frame(frame)
        command_frame.grid(row=1, column=1, sticky=tk.NSEW, pady=5)
        command_text = tk.Text(command_frame, height=4, width=50, wrap=tk.WORD, font=("Consolas", 10))
        command_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        command_scroll = ttk.Scrollbar(command_frame, orient=tk.VERTICAL, command=command_text.yview)
        command_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        command_text.configure(yscrollcommand=command_scroll.set)
        command_text.insert("1.0", alias.command)
        command_text.configure(state="disabled")
        ttk.Label(frame, text="Section:", style="Heading.TLabel").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Label(frame, text=alias.section).grid(row=2, column=1, sticky=tk.W, pady=5)
        ttk.Label(frame, text="Description:", style="Heading.TLabel").grid(row=3, column=0, sticky=tk.NW, pady=5)
        desc_frame = ttk.Frame(frame)
        desc_frame.grid(row=3, column=1, sticky=tk.NSEW, pady=5)
        desc_text = tk.Text(desc_frame, height=10, width=50, wrap=tk.WORD)
        desc_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        desc_scroll = ttk.Scrollbar(desc_frame, orient=tk.VERTICAL, command=desc_text.yview)
        desc_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        desc_text.configure(yscrollcommand=desc_scroll.set)
        desc_text.insert("1.0", alias.description)
        desc_text.configure(state="disabled")
        ttk.Button(frame, text="Close", command=self.destroy).grid(row=4, column=0, columnspan=2, pady=20)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(3, weight=1)
        self.center_on_parent()
        self.update_idletasks()
        self.after(100, self.safely_set_grab)
        self.focus_set()

    def safely_set_grab(self):
        try:
            self.grab_set()
        except Exception as e:
            print(f"Warning: Failed to set window modality: {e}")

    def center_on_parent(self):
        self.update_idletasks()
        parent = self.master
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        width = self.winfo_width()
        height = self.winfo_height()
        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

class AliasManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Alias Manager")
        self.default_settings = {
            'window_geometry': '900x700+100+100',
            'paned_position': 450,
            'column_widths': {
                'alias': 100,
                'command': 300,
                'section': 150,
                'description': 200
            },
            'sort_by': 'alias',
            'sort_ascending': True,
            'theme': 'default'
        }
        self.alias_manager = AliasManager()
        self.undo_redo = UndoRedoManager()
        self.load_settings()
        self.root.geometry(self.settings['window_geometry'])
        self.create_styles()
        self.setup_ui()
        self.refresh_aliases()
        self.update_section_dropdown()
        self.bind_events()
        self.add_keyboard_shortcuts()

    def create_styles(self):
        style = ttk.Style()
        style.configure("Primary.TButton", font=("", 10, "bold"))
        style.configure("Accent.TButton", background="#4CAF50", foreground="white")
        style.map("Accent.TButton", background=[("active", "#45a049"), ("disabled", "#a0a0a0")])
        style.configure("Treeview", font=("", 10))
        style.configure("Treeview.Heading", font=("", 10, "bold"))
        style.configure("Header.TLabel", font=("", 12, "bold"))

    def setup_ui(self):
        self.create_menu()
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        self.paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)
        self.setup_left_panel()
        self.setup_right_panel()
        self.paned_window.sashpos(0, self.settings['paned_position'])
        separator = ttk.Separator(self.root, orient=tk.HORIZONTAL)
        separator.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_bar = StatusBar(self.root)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def create_menu(self):
        menu_bar = tk.Menu(self.root)
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="New alias", command=self.new_alias, accelerator="Ctrl+N")
        file_menu.add_command(label="Save alias", command=self.save_alias, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Import aliases", command=self.import_aliases)
        file_menu.add_command(label="Export aliases", command=self.export_aliases)
        file_menu.add_separator()
        file_menu.add_command(label="Backup .bashrc", command=self.backup_bashrc)
        file_menu.add_separator()
        file_menu.add_command(label="Refresh all", command=self.refresh_all, accelerator="F5")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing, accelerator="Alt+F4")
        menu_bar.add_cascade(label="File", menu=file_menu)
        edit_menu = tk.Menu(menu_bar, tearoff=0)
        edit_menu.add_command(label="Undo", command=self.undo_action, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Redo", command=self.redo_action, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Delete alias", command=self.delete_alias, accelerator="Delete")
        menu_bar.add_cascade(label="Edit", menu=edit_menu)
        section_menu = tk.Menu(menu_bar, tearoff=0)
        section_menu.add_command(label="Add section", command=self.add_section)
        section_menu.add_command(label="Rename section", command=self.rename_section)
        section_menu.add_command(label="Delete section", command=self.delete_section)
        menu_bar.add_cascade(label="Sections", menu=section_menu)
        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="Keyboard Shortcuts", command=self.show_shortcuts)
        menu_bar.add_cascade(label="Help", menu=help_menu)
        self.root.config(menu=menu_bar)

    def setup_left_panel(self):
        left_panel = ttk.Frame(self.paned_window)
        ttk.Label(left_panel, text="Alias List", style="Header.TLabel").pack(fill=tk.X, pady=(0, 10))
        search_frame = ttk.LabelFrame(left_panel, text="Search and Filter", padding=5)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        search_input_frame = ttk.Frame(search_frame)
        search_input_frame.pack(fill=tk.X, expand=True, pady=5)
        ttk.Label(search_input_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda name, index, mode: self.filter_aliases())
        search_entry = ttk.Entry(search_input_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(search_input_frame, text="×", width=3, command=lambda: self.search_var.set("")).pack(side=tk.LEFT)
        section_filter_frame = ttk.Frame(search_frame)
        section_filter_frame.pack(fill=tk.X, expand=True, pady=5)
        ttk.Label(section_filter_frame, text="Section:").pack(side=tk.LEFT, padx=(0, 5))
        self.section_filter_var = tk.StringVar(value="All")
        self.section_filter = ttk.Combobox(section_filter_frame, textvariable=self.section_filter_var)
        self.section_filter.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tree_frame = ttk.Frame(left_panel)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        columns = ("alias", "command", "section", "description")
        self.alias_tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
        self.sort_by = self.settings['sort_by']
        self.sort_ascending = self.settings['sort_ascending']
        self.alias_tree.heading("alias", text="Alias", command=lambda: self.sort_treeview("alias"))
        self.alias_tree.heading("command", text="Command", command=lambda: self.sort_treeview("command"))
        self.alias_tree.heading("section", text="Section", command=lambda: self.sort_treeview("section"))
        self.alias_tree.heading("description", text="Description", command=lambda: self.sort_treeview("description"))
        self.alias_tree.column("alias", width=self.settings['column_widths']['alias'], stretch=True)
        self.alias_tree.column("command", width=self.settings['column_widths']['command'], stretch=True)
        self.alias_tree.column("section", width=self.settings['column_widths']['section'], stretch=True)
        self.alias_tree.column("description", width=200, stretch=True)
        tree_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.alias_tree.yview)
        self.alias_tree.configure(yscrollcommand=tree_scrollbar.set)
        self.alias_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.paned_window.add(left_panel, weight=1)

    def setup_right_panel(self):
        right_panel = ttk.Frame(self.paned_window, padding=(10, 0, 0, 0))
        details_frame = ttk.LabelFrame(right_panel, text="Alias Details", padding=10)
        details_frame.pack(fill=tk.BOTH, expand=True)
        form_grid = ttk.Frame(details_frame)
        form_grid.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        ttk.Label(form_grid, text="Alias:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.alias_var = tk.StringVar()
        ttk.Entry(form_grid, textvariable=self.alias_var).grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        ttk.Label(form_grid, text="Command:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.command_var = tk.StringVar()
        ttk.Entry(form_grid, textvariable=self.command_var).grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        ttk.Label(form_grid, text="Section:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.section_var = tk.StringVar()
        self.section_dropdown = ttk.Combobox(form_grid, textvariable=self.section_var)
        self.section_dropdown.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)
        ttk.Label(form_grid, text="Description:").grid(row=3, column=0, sticky=tk.NW, pady=5)
        desc_frame = ttk.Frame(form_grid)
        desc_frame.grid(row=3, column=1, sticky=tk.NSEW, padx=5, pady=5)
        self.description_text = tk.Text(desc_frame, height=5, width=40, wrap=tk.WORD)
        desc_scrollbar = ttk.Scrollbar(desc_frame, orient=tk.VERTICAL, command=self.description_text.yview)
        self.description_text.configure(yscrollcommand=desc_scrollbar.set)
        self.description_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        desc_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        action_buttons = ttk.Frame(details_frame)
        action_buttons.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(action_buttons, text="New", command=self.new_alias).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_buttons, text="Save", command=self.save_alias, style="Primary.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(action_buttons, text="Delete", command=self.delete_alias).pack(side=tk.LEFT, padx=5)
        undo_redo_frame = ttk.Frame(details_frame)
        undo_redo_frame.pack(fill=tk.X)
        self.undo_button = ttk.Button(undo_redo_frame, text="Undo", command=self.undo_action, state=tk.DISABLED)
        self.undo_button.pack(side=tk.LEFT, padx=5)
        self.redo_button = ttk.Button(undo_redo_frame, text="Redo", command=self.redo_action, state=tk.DISABLED)
        self.redo_button.pack(side=tk.LEFT, padx=5)
        section_mgmt_frame = ttk.LabelFrame(right_panel, text="Section Management", padding=10)
        section_mgmt_frame.pack(fill=tk.X, pady=10)
        ttk.Button(section_mgmt_frame, text="Add section", command=self.add_section).pack(side=tk.LEFT, padx=5)
        ttk.Button(section_mgmt_frame, text="Rename section", command=self.rename_section).pack(side=tk.LEFT, padx=5)
        ttk.Button(section_mgmt_frame, text="Delete section", command=self.delete_section).pack(side=tk.LEFT, padx=5)
        backup_frame = ttk.LabelFrame(right_panel, text="Backup and Import/Export", padding=10)
        backup_frame.pack(fill=tk.X, pady=10)
        ttk.Button(backup_frame, text="Backup .bashrc", command=self.backup_bashrc).pack(side=tk.LEFT, padx=5)
        ttk.Button(backup_frame, text="Export", command=self.export_aliases).pack(side=tk.LEFT, padx=5)
        ttk.Button(backup_frame, text="Import", command=self.import_aliases).pack(side=tk.LEFT, padx=5)
        refresh_frame = ttk.Frame(right_panel, padding=10)
        refresh_frame.pack(fill=tk.X, pady=10)
        refresh_button = ttk.Button(refresh_frame, text="Refresh all", command=self.refresh_all, style="Accent.TButton")
        refresh_button.pack(fill=tk.X, padx=5)
        form_grid.columnconfigure(1, weight=1)
        form_grid.rowconfigure(3, weight=1)
        self.paned_window.add(right_panel, weight=1)

    def bind_events(self):
        self.root.bind("<Configure>", self.on_window_configure)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.alias_tree.bind("<<TreeviewSelect>>", self.on_alias_select)
        self.alias_tree.bind("<Double-1>", self.on_alias_double_click)
        self.alias_tree.bind("<ButtonRelease-1>", self.on_column_resize)
        self.section_filter.bind("<<ComboboxSelected>>", lambda e: self.filter_aliases())

    def add_keyboard_shortcuts(self):
        self.root.bind("<Control-n>", lambda e: self.new_alias())
        self.root.bind("<Control-s>", lambda e: self.save_alias())
        self.root.bind("<Control-z>", lambda e: self.undo_action())
        self.root.bind("<Control-y>", lambda e: self.redo_action())
        self.root.bind("<Delete>", lambda e: self.delete_alias())
        self.root.bind("<F5>", lambda e: self.refresh_all())

    def load_settings(self):
        try:
            if os.path.exists(self.alias_manager.settings_path):
                with open(self.alias_manager.settings_path, 'rb') as f:
                    self.settings = pickle.load(f)
            else:
                self.settings = self.default_settings.copy()
        except Exception as e:
            print(f"Error loading settings: {e}")
            self.settings = self.default_settings.copy()

    def save_settings(self):
        try:
            self.settings['window_geometry'] = self.root.geometry()
            self.settings['paned_position'] = self.paned_window.sashpos(0)
            self.settings['sort_by'] = self.sort_by
            self.settings['sort_ascending'] = self.sort_ascending
            with open(self.alias_manager.settings_path, 'wb') as f:
                pickle.dump(self.settings, f)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def refresh_aliases(self):
        self.alias_tree.delete(*self.alias_tree.get_children())
        filtered_aliases = [a for a in self.alias_manager.aliases if self.matches_filter(a)]
        self.sort_aliases(filtered_aliases)
        for alias in filtered_aliases:
            self.alias_tree.insert("", tk.END, values=(alias.alias, alias.command, alias.section, alias.description))
        for col in ["alias", "command", "section"]:
            if col == self.sort_by:
                direction = "▲" if self.sort_ascending else "▼"
                self.alias_tree.heading(col, text=f"{col.capitalize()} {direction}")
            else:
                self.alias_tree.heading(col, text=col.capitalize())
        self.update_undo_redo_buttons()

    def refresh_all(self):
        self.new_alias()
        self.alias_manager.load_descriptions()
        self.alias_manager.load_aliases()
        self.refresh_aliases()
        self.update_section_dropdown()
        self.search_var.set("")
        self.section_filter_var.set("All")
        self.status_bar.set_message("Application refreshed successfully.", "success")

    def update_section_dropdown(self):
        sections_filter = ["All"] + sorted(self.alias_manager.sections)
        self.section_filter["values"] = sections_filter
        self.section_dropdown["values"] = sorted(self.alias_manager.sections)
        if self.section_var.get() not in self.alias_manager.sections and self.alias_manager.sections:
            self.section_var.set(self.alias_manager.sections[0])

    def matches_filter(self, alias):
        section_filter = self.section_filter_var.get()
        if section_filter != "All" and alias.section != section_filter:
            return False
        search_text = self.search_var.get().lower()
        if search_text:
            if (search_text not in alias.alias.lower() and 
                search_text not in alias.command.lower() and 
                search_text not in alias.description.lower()):
                return False
        return True

    def filter_aliases(self):
        self.refresh_aliases()

    def sort_aliases(self, aliases_list):
        if self.sort_by == "alias":
            key_func = lambda a: a.alias.lower()
        elif self.sort_by == "command":
            key_func = lambda a: a.command.lower()
        elif self.sort_by == "description":
            key_func = lambda a: a.description.lower()
        else:
            key_func = lambda a: a.section.lower()
        aliases_list.sort(key=key_func, reverse=not self.sort_ascending)

    def sort_treeview(self, column):
        if self.sort_by == column:
            self.sort_ascending = not self.sort_ascending
        else:
            self.sort_by = column
            self.sort_ascending = True
        self.settings['sort_by'] = self.sort_by
        self.settings['sort_ascending'] = self.sort_ascending
        self.refresh_aliases()

    def on_alias_select(self, event):
        selected_items = self.alias_tree.selection()
        if not selected_items:
            return
        item = selected_items[0]
        values = self.alias_tree.item(item, "values")
        alias_name = values[0]
        alias = next((a for a in self.alias_manager.aliases if a.alias == alias_name), None)
        if not alias:
            return
        self.alias_var.set(alias.alias)
        self.command_var.set(alias.command)
        self.section_var.set(alias.section)
        self.description_text.delete("1.0", tk.END)
        self.description_text.insert("1.0", alias.description)

    def on_alias_double_click(self, event):
        selected_items = self.alias_tree.selection()
        if not selected_items:
            return
        item = selected_items[0]
        values = self.alias_tree.item(item, "values")
        alias_name = values[0]
        alias = next((a for a in self.alias_manager.aliases if a.alias == alias_name), None)
        if not alias:
            return
        AliasDetailDialog(self.root, alias)

    def on_column_resize(self, event):
        self.settings['column_widths']['alias'] = self.alias_tree.column('alias', 'width')
        self.settings['column_widths']['command'] = self.alias_tree.column('command', 'width')
        self.settings['column_widths']['section'] = self.alias_tree.column('section', 'width')
        self.settings['column_widths']['description'] = self.alias_tree.column('description', 'width')

    def on_window_configure(self, event):
        if event.widget == self.root:
            self.settings['window_geometry'] = self.root.geometry()

    def on_closing(self):
        try:
            self.save_settings()
        except Exception as e:
            print(f"Error during closing: {e}")
        finally:
            self.root.destroy()

    def new_alias(self):
        self.alias_var.set("")
        self.command_var.set("")
        if self.alias_manager.sections:
            self.section_var.set(self.alias_manager.sections[0])
        else:
            self.section_var.set("")
        self.description_text.delete("1.0", tk.END)
        for selected in self.alias_tree.selection():
            self.alias_tree.selection_remove(selected)

    def save_state(self):
        state = {
            "aliases": [
                {
                    "alias": a.alias,
                    "command": a.command,
                    "section": a.section,
                    "description": a.description
                }
                for a in self.alias_manager.aliases
            ],
            "sections": self.alias_manager.sections.copy()
        }
        self.undo_redo.add_state(state)
        self.update_undo_redo_buttons()

    def save_alias(self):
        alias = self.alias_var.get().strip()
        command = self.command_var.get().strip()
        section = self.section_var.get().strip()
        description = self.description_text.get("1.0", tk.END).strip()
        if not alias or not command or not section:
            messagebox.showerror("Error", "Alias, command and section are required")
            return
        self.save_state()
        selected_items = self.alias_tree.selection()
        if selected_items:
            item = selected_items[0]
            old_alias = self.alias_tree.item(item, "values")[0]
            if old_alias != alias and any(a.alias == alias for a in self.alias_manager.aliases):
                messagebox.showerror("Error", f"Alias '{alias}' already exists")
                return
            alias_data = AliasData(alias, command, section, description)
            success = self.alias_manager.update_alias(old_alias, alias_data)
        else:
            if any(a.alias == alias for a in self.alias_manager.aliases):
                messagebox.showerror("Error", f"Alias '{alias}' already exists")
                return
            alias_data = AliasData(alias, command, section, description)
            success = self.alias_manager.add_alias(alias_data)
        if not success:
            messagebox.showerror("Error", "Failed to save alias")
            return
        self.refresh_aliases()
        self.update_section_dropdown()
        for item in self.alias_tree.get_children():
            if self.alias_tree.item(item, "values")[0] == alias:
                self.alias_tree.selection_set(item)
                self.alias_tree.see(item)
                break
        self.status_bar.set_message(f"Alias '{alias}' saved successfully.", "success")

    def delete_alias(self):
        selected_items = self.alias_tree.selection()
        if not selected_items:
            messagebox.showerror("Error", "No alias selected")
            return
        item = selected_items[0]
        alias_name = self.alias_tree.item(item, "values")[0]
        confirm = messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete alias '{alias_name}'?")
        if not confirm:
            return
        self.save_state()
        success = self.alias_manager.delete_alias(alias_name)
        if not success:
            messagebox.showerror("Error", f"Failed to delete alias '{alias_name}'")
            return
        self.refresh_aliases()
        self.new_alias()
        self.status_bar.set_message(f"Alias '{alias_name}' deleted.", "success")

    def add_section(self):
        section_name = simpledialog.askstring("Add Section", "Enter the name of the new section:")
        if not section_name:
            return
        self.save_state()
        if self.alias_manager.add_section(section_name):
            self.update_section_dropdown()
            self.status_bar.set_message(f"Section '{section_name}' added.", "success")
        else:
            messagebox.showerror("Error", f"Section '{section_name}' already exists")

    def rename_section(self):
        sections = sorted(self.alias_manager.sections)
        if not sections:
            messagebox.showerror("Error", "No sections available to rename")
            return
        old_name = simpledialog.askstring("Rename Section", "Enter the section to rename:", initialvalue=sections[0])
        if not old_name or old_name not in sections:
            messagebox.showerror("Error", f"Section '{old_name}' does not exist")
            return
        new_name = simpledialog.askstring("Rename Section", f"Enter the new name for section '{old_name}':")
        if not new_name:
            return
        self.save_state()
        if self.alias_manager.rename_section(old_name, new_name):
            self.update_section_dropdown()
            self.refresh_aliases()
            self.status_bar.set_message(f"Section renamed from '{old_name}' to '{new_name}'.", "success")
        else:
            messagebox.showerror("Error", f"Section '{new_name}' already exists")

    def delete_section(self):
        sections = sorted(self.alias_manager.sections)
        if not sections:
            messagebox.showerror("Error", "No sections available to delete")
            return
        section_name = simpledialog.askstring("Delete Section", "Enter the section to delete:", initialvalue=sections[0])
        if not section_name or section_name not in sections:
            messagebox.showerror("Error", f"Section '{section_name}' does not exist")
            return
        confirm = messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete section '{section_name}'?")
        if not confirm:
            return
        self.save_state()
        if self.alias_manager.delete_section(section_name):
            self.update_section_dropdown()
            self.status_bar.set_message(f"Section '{section_name}' deleted.", "success")
        else:
            messagebox.showerror("Error", f"Cannot delete section '{section_name}' because it contains aliases")

    def backup_bashrc(self):
        backup_path = self.alias_manager.backup_bashrc()
        desc_backup_path = self.alias_manager.backup_descriptions()
        if not backup_path:
            messagebox.showerror("Error", "Failed to create backup of .bashrc")
            return
        msg = f".bashrc saved at:\n{backup_path}"
        if desc_backup_path:
            msg += f"\n\nAlias descriptions saved at:\n{desc_backup_path}"
        messagebox.showinfo("Backup", msg)
        self.status_bar.set_message("Backup created successfully.", "success")

    def export_aliases(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"aliases_export_{timestamp}.json"
        default_path = os.path.join(self.alias_manager.backups_dir, default_filename)
        filepath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")], title="Export Aliases", initialdir=self.alias_manager.backups_dir, initialfile=default_filename)
        if not filepath:
            return
        if self.alias_manager.export_aliases(filepath):
            messagebox.showinfo("Export", f"Aliases exported to {filepath}")
            self.status_bar.set_message("Aliases exported successfully.", "success")

    def import_aliases(self):
        filepath = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")], title="Import Aliases", initialdir=self.alias_manager.backups_dir)
        if not filepath:
            return
        overwrite = messagebox.askyesno("Import Options", "Do you want to overwrite existing aliases?\n\nYes - Replace all existing aliases\nNo - Add only new aliases and update existing ones")
        self.save_state()
        if self.alias_manager.import_aliases(filepath, overwrite):
            self.refresh_aliases()
            self.update_section_dropdown()
            messagebox.showinfo("Import", "Aliases imported successfully")
            self.status_bar.set_message("Aliases imported successfully.", "success")

    def update_undo_redo_buttons(self):
        if self.undo_redo.can_undo():
            self.undo_button.configure(state=tk.NORMAL)
        else:
            self.undo_button.configure(state=tk.DISABLED)
        if self.undo_redo.can_redo():
            self.redo_button.configure(state=tk.NORMAL)
        else:
            self.redo_button.configure(state=tk.DISABLED)

    def undo_action(self):
        state = self.undo_redo.undo()
        if state:
            self.apply_state(state)
        self.update_undo_redo_buttons()
        self.status_bar.set_message("Action undone.", "info")

    def redo_action(self):
        state = self.undo_redo.redo()
        if state:
            self.apply_state(state)
        self.update_undo_redo_buttons()
        self.status_bar.set_message("Action redone.", "info")

    def apply_state(self, state):
        self.alias_manager.aliases = []
        self.alias_manager.sections = state["sections"].copy()
        for alias_data in state["aliases"]:
            self.alias_manager.aliases.append(AliasData(
                alias_data["alias"],
                alias_data["command"],
                alias_data["section"],
                alias_data["description"]
            ))
            self.alias_manager.descriptions[alias_data["alias"]] = alias_data["description"]
        self.alias_manager.save_to_bashrc()
        self.alias_manager.save_descriptions()
        self.refresh_aliases()
        self.update_section_dropdown()

    def show_about(self):
        about_text = """
Alias Manager

Version: 2.0

A program for managing bash aliases.

Features:
- Create, edit, and delete aliases
- Organize aliases into sections
- Import/Export aliases
- Create backups

Author: Refactored and optimized system
        """
        messagebox.showinfo("About", about_text.strip())

    def show_shortcuts(self):
        shortcuts_text = """
Keyboard Shortcuts:

Ctrl+N - New alias
Ctrl+S - Save alias
Ctrl+Z - Undo
Ctrl+Y - Redo
Delete - Delete selected alias
F5 - Refresh all
        """
        messagebox.showinfo("Keyboard Shortcuts", shortcuts_text.strip())

if __name__ == "__main__":
    root = tk.Tk()
    app = AliasManagerApp(root)
    root.mainloop()
