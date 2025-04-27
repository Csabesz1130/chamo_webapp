import json
from typing import List, Dict, Any
from datetime import datetime, time
from src.utils.logger import app_logger
from src.utils.persistent_settings_manager import PersistentSettingsManager


class EmailPreferencesManager:
    """
    Az e-mail beállítások kezeléséért felelős osztály.
    """

    def __init__(self, settings_manager: PersistentSettingsManager):
        """
        Inicializálja az EmailPreferencesManager-t.

        Args:
            settings_manager: A PersistentSettingsManager példány
        """
        self.settings_manager = settings_manager
        self.load_preferences()

    def load_preferences(self):
        """Betölti az e-mail beállításokat a PersistentSettingsManager-ből."""
        self.preferences = self.settings_manager.get_setting(
            "email_preferences",
            {
                "keywords": [],
                "keyword_logic": "AND",  # 'AND' vagy 'OR'
                "sources": ["PubMed", "bioRxiv", "arXiv-q-bio"],
                "delivery_day": 0,  # 0 = hétfő, 1 = kedd, stb.
                "delivery_time": "08:00",
                "enabled": True,
            },
        )

    def save_preferences(self):
        """Elmenti az e-mail beállításokat a PersistentSettingsManager-be."""
        self.settings_manager.set_setting("email_preferences", self.preferences)
        self.settings_manager.save_settings()

    def get_keywords(self) -> List[str]:
        """Visszaadja a mentett kulcsszavakat."""
        return self.preferences.get("keywords", [])

    def add_keyword(self, keyword: str):
        """Hozzáad egy új kulcsszót, maximum 10 lehet."""
        keywords = self.get_keywords()
        if len(keywords) < 10:
            keywords.append(keyword)
            self.preferences["keywords"] = keywords
            self.save_preferences()
        else:
            raise ValueError("Maximum 10 kulcsszó lehet mentve")

    def remove_keyword(self, keyword: str):
        """Eltávolít egy kulcsszót."""
        keywords = self.get_keywords()
        if keyword in keywords:
            keywords.remove(keyword)
            self.preferences["keywords"] = keywords
            self.save_preferences()

    def set_keyword_logic(self, logic: str):
        """Beállítja a kulcsszavak logikai operátorát ('AND' vagy 'OR')."""
        if logic not in ["AND", "OR"]:
            raise ValueError("A logikai operátor csak 'AND' vagy 'OR' lehet")
        self.preferences["keyword_logic"] = logic
        self.save_preferences()

    def get_sources(self) -> List[str]:
        """Visszaadja a kiválasztott forrásokat."""
        return self.preferences.get("sources", [])

    def set_sources(self, sources: List[str]):
        """Beállítja a kiválasztott forrásokat."""
        valid_sources = ["PubMed", "bioRxiv", "arXiv-q-bio"]
        if not all(source in valid_sources for source in sources):
            raise ValueError("Érvénytelen forrás megadva")
        self.preferences["sources"] = sources
        self.save_preferences()

    def get_delivery_schedule(self) -> Dict[str, Any]:
        """Visszaadja a kézbesítési beállításokat."""
        return {
            "day": self.preferences.get("delivery_day", 0),
            "time": self.preferences.get("delivery_time", "08:00"),
        }

    def set_delivery_schedule(self, day: int, time_str: str):
        """Beállítja a kézbesítési napot és időt."""
        if not 0 <= day <= 6:
            raise ValueError("A nap 0 és 6 között kell legyen (0 = hétfő)")
        try:
            datetime.strptime(time_str, "%H:%M")
        except ValueError:
            raise ValueError("Az idő formátuma 'HH:MM' kell legyen")

        self.preferences["delivery_day"] = day
        self.preferences["delivery_time"] = time_str
        self.save_preferences()

    def is_enabled(self) -> bool:
        """Visszaadja, hogy engedélyezve van-e az e-mail értesítés."""
        return self.preferences.get("enabled", True)

    def set_enabled(self, enabled: bool):
        """Beállítja, hogy engedélyezve van-e az e-mail értesítés."""
        self.preferences["enabled"] = enabled
        self.save_preferences()
