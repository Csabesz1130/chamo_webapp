"""
AI elemzés panel a felhasználói felületen.
"""

import tkinter as tk
from tkinter import ttk
from src.ai.signal_analyzer import SignalAnalyzer
from src.utils.logger import app_logger

class AIAnalysisPanel(ttk.Frame):
    """
    Panel az AI alapú jelanalízishez.
    """
    
    def __init__(self, parent, *args, **kwargs):
        """Inicializálja az AI elemzés panelt."""
        super().__init__(parent, *args, **kwargs)
        
        self.analyzer = SignalAnalyzer()
        self._setup_ui()
        
        app_logger.info("AI elemzés panel inicializálva")
    
    def _setup_ui(self):
        """Beállítja a felhasználói felület elemeit."""
        # Modell választó
        self.model_frame = ttk.LabelFrame(self, text="AI Modell")
        self.model_frame.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        self.model_var = tk.StringVar(value="default")
        self.model_combo = ttk.Combobox(
            self.model_frame,
            textvariable=self.model_var,
            values=["default", "advanced"],
            state="readonly"
        )
        self.model_combo.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        # Elemzés gomb
        self.analyze_button = ttk.Button(
            self,
            text="AI Elemzés indítása",
            command=self._on_analyze
        )
        self.analyze_button.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        
        # Eredmény megjelenítő
        self.result_frame = ttk.LabelFrame(self, text="Eredmények")
        self.result_frame.grid(row=2, column=0, padx=5, pady=5, sticky="nsew")
        
        self.result_text = tk.Text(
            self.result_frame,
            height=10,
            width=40,
            wrap=tk.WORD
        )
        self.result_text.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        # Grid konfiguráció
        self.grid_columnconfigure(0, weight=1)
        self.result_frame.grid_columnconfigure(0, weight=1)
        self.result_frame.grid_rowconfigure(0, weight=1)
    
    def _on_analyze(self):
        """Feldolgozza az AI elemzés gomb megnyomását."""
        model_type = self.model_var.get()
        app_logger.info(f"AI elemzés indítva {model_type} modellel")
        
        # TODO: Implementáljuk az elemzést
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, "Elemzés folyamatban...")
    
    def update_results(self, results: dict):
        """
        Frissíti az elemzés eredményeit.
        
        Args:
            results: Az elemzés eredményei
        """
        self.result_text.delete(1.0, tk.END)
        
        if results.get("success", False):
            self.result_text.insert(tk.END, "Elemzés sikeres!\n\n")
            for key, value in results.get("data", {}).items():
                self.result_text.insert(tk.END, f"{key}: {value}\n")
        else:
            self.result_text.insert(tk.END, f"Hiba: {results.get('message', 'Ismeretlen hiba')}") 