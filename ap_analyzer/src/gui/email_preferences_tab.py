import tkinter as tk
from tkinter import ttk, messagebox
from typing import List
from src.utils.logger import app_logger
from src.utils.email_preferences_manager import EmailPreferencesManager


class EmailPreferencesTab:
    """
    Az e-mail beállítások kezeléséért felelős felhasználói felület.
    """

    def __init__(self, parent, email_manager: EmailPreferencesManager):
        """
        Inicializálja az EmailPreferencesTab-ot.

        Args:
            parent: A szülő widget
            email_manager: Az EmailPreferencesManager példány
        """
        self.parent = parent
        self.email_manager = email_manager

        # Létrehozás
        self.frame = ttk.LabelFrame(parent, text="E-mail Beállítások")
        self.frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Változók inicializálása
        self.init_variables()

        # UI komponensek létrehozása
        self.setup_keyword_section()
        self.setup_source_section()
        self.setup_delivery_section()
        self.setup_enable_section()

        # Beállítások betöltése
        self.load_preferences()

        app_logger.debug("E-mail beállítások tab inicializálva")

    def init_variables(self):
        """Inicializálja a változókat."""
        self.keyword_var = tk.StringVar()
        self.keyword_logic_var = tk.StringVar(value="AND")
        self.source_vars = {
            "PubMed": tk.BooleanVar(value=True),
            "bioRxiv": tk.BooleanVar(value=True),
            "arXiv-q-bio": tk.BooleanVar(value=True),
        }
        self.delivery_day_var = tk.StringVar(value="0")
        self.delivery_time_var = tk.StringVar(value="08:00")
        self.enabled_var = tk.BooleanVar(value=True)

    def setup_keyword_section(self):
        """Beállítja a kulcsszó szekciót."""
        keyword_frame = ttk.LabelFrame(self.frame, text="Kulcsszavak")
        keyword_frame.pack(fill="x", padx=5, pady=5)

        # Kulcsszó hozzáadása
        keyword_entry_frame = ttk.Frame(keyword_frame)
        keyword_entry_frame.pack(fill="x", padx=5, pady=2)

        ttk.Label(keyword_entry_frame, text="Új kulcsszó:").pack(side="left")
        keyword_entry = ttk.Entry(keyword_entry_frame, textvariable=self.keyword_var)
        keyword_entry.pack(side="left", fill="x", expand=True, padx=5)

        ttk.Button(keyword_entry_frame, text="Hozzáad", command=self.add_keyword).pack(
            side="left"
        )

        # Kulcsszó lista
        self.keyword_listbox = tk.Listbox(keyword_frame, height=5)
        self.keyword_listbox.pack(fill="x", padx=5, pady=2)

        ttk.Button(
            keyword_frame, text="Törlés", command=self.remove_selected_keyword
        ).pack(pady=2)

        # Logikai operátor
        logic_frame = ttk.Frame(keyword_frame)
        logic_frame.pack(fill="x", padx=5, pady=2)

        ttk.Label(logic_frame, text="Logikai operátor:").pack(side="left")
        ttk.Radiobutton(
            logic_frame,
            text="ÉS",
            variable=self.keyword_logic_var,
            value="AND",
            command=self.update_keyword_logic,
        ).pack(side="left", padx=5)
        ttk.Radiobutton(
            logic_frame,
            text="VAGY",
            variable=self.keyword_logic_var,
            value="OR",
            command=self.update_keyword_logic,
        ).pack(side="left", padx=5)

    def setup_source_section(self):
        """Beállítja a forrás szekciót."""
        source_frame = ttk.LabelFrame(self.frame, text="Források")
        source_frame.pack(fill="x", padx=5, pady=5)

        for source, var in self.source_vars.items():
            ttk.Checkbutton(
                source_frame, text=source, variable=var, command=self.update_sources
            ).pack(anchor="w", padx=5, pady=2)

    def setup_delivery_section(self):
        """Beállítja a kézbesítés szekciót."""
        delivery_frame = ttk.LabelFrame(self.frame, text="Kézbesítés")
        delivery_frame.pack(fill="x", padx=5, pady=5)

        # Nap kiválasztása
        day_frame = ttk.Frame(delivery_frame)
        day_frame.pack(fill="x", padx=5, pady=2)

        ttk.Label(day_frame, text="Nap:").pack(side="left")
        days = ["Hétfő", "Kedd", "Szerda", "Csütörtök", "Péntek", "Szombat", "Vasárnap"]
        day_combo = ttk.Combobox(
            day_frame,
            textvariable=self.delivery_day_var,
            values=[str(i) for i in range(7)],
            state="readonly",
        )
        day_combo.pack(side="left", padx=5)
        ttk.Label(day_frame, text=days[int(self.delivery_day_var.get())]).pack(
            side="left"
        )

        # Idő beállítása
        time_frame = ttk.Frame(delivery_frame)
        time_frame.pack(fill="x", padx=5, pady=2)

        ttk.Label(time_frame, text="Idő:").pack(side="left")
        time_entry = ttk.Entry(time_frame, textvariable=self.delivery_time_var, width=5)
        time_entry.pack(side="left", padx=5)

        # Frissítés gomb
        ttk.Button(
            delivery_frame, text="Frissítés", command=self.update_delivery_schedule
        ).pack(pady=2)

    def setup_enable_section(self):
        """Beállítja az engedélyezés szekciót."""
        enable_frame = ttk.Frame(self.frame)
        enable_frame.pack(fill="x", padx=5, pady=5)

        ttk.Checkbutton(
            enable_frame,
            text="E-mail értesítések engedélyezése",
            variable=self.enabled_var,
            command=self.update_enabled,
        ).pack(anchor="w")

    def load_preferences(self):
        """Betölti a beállításokat az EmailPreferencesManager-ből."""
        # Kulcsszavak
        for keyword in self.email_manager.get_keywords():
            self.keyword_listbox.insert(tk.END, keyword)

        # Logikai operátor
        self.keyword_logic_var.set(
            self.email_manager.preferences.get("keyword_logic", "AND")
        )

        # Források
        sources = self.email_manager.get_sources()
        for source, var in self.source_vars.items():
            var.set(source in sources)

        # Kézbesítés
        schedule = self.email_manager.get_delivery_schedule()
        self.delivery_day_var.set(str(schedule["day"]))
        self.delivery_time_var.set(schedule["time"])

        # Engedélyezés
        self.enabled_var.set(self.email_manager.is_enabled())

    def add_keyword(self):
        """Hozzáad egy új kulcsszót."""
        keyword = self.keyword_var.get().strip()
        if not keyword:
            return

        try:
            self.email_manager.add_keyword(keyword)
            self.keyword_listbox.insert(tk.END, keyword)
            self.keyword_var.set("")
        except ValueError as e:
            messagebox.showerror("Hiba", str(e))

    def remove_selected_keyword(self):
        """Eltávolítja a kiválasztott kulcsszót."""
        selection = self.keyword_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        keyword = self.keyword_listbox.get(index)

        self.email_manager.remove_keyword(keyword)
        self.keyword_listbox.delete(index)

    def update_keyword_logic(self):
        """Frissíti a kulcsszavak logikai operátorát."""
        self.email_manager.set_keyword_logic(self.keyword_logic_var.get())

    def update_sources(self):
        """Frissíti a kiválasztott forrásokat."""
        sources = [source for source, var in self.source_vars.items() if var.get()]
        self.email_manager.set_sources(sources)

    def update_delivery_schedule(self):
        """Frissíti a kézbesítési beállításokat."""
        try:
            day = int(self.delivery_day_var.get())
            time_str = self.delivery_time_var.get()
            self.email_manager.set_delivery_schedule(day, time_str)
        except ValueError as e:
            messagebox.showerror("Hiba", str(e))

    def update_enabled(self):
        """Frissíti az e-mail értesítések engedélyezését."""
        self.email_manager.set_enabled(self.enabled_var.get())
