import json
import os
from typing import Dict, Any
from datetime import datetime
from src.utils.logger import app_logger
from src.utils.persistent_settings_manager import PersistentSettingsManager

class ClickTracker:
    """
    A kattintások követéséért felelős osztály.
    """
    
    def __init__(self, settings_manager: PersistentSettingsManager):
        """
        Inicializálja a ClickTracker-t.
        
        Args:
            settings_manager: A PersistentSettingsManager példány
        """
        self.settings_manager = settings_manager
        self.clicks_file = os.path.join(
            os.path.dirname(settings_manager.settings_path),
            'click_tracking.json'
        )
        self.clicks = self._load_clicks()
        
        app_logger.info("Kattintás követő inicializálva")
    
    def _load_clicks(self) -> Dict[str, Any]:
        """Betölti a kattintások adatait a fájlból."""
        try:
            if os.path.exists(self.clicks_file):
                with open(self.clicks_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            app_logger.error(f"Hiba a kattintások betöltésekor: {str(e)}")
        
        return {
            'articles': {},
            'keywords': {},
            'sources': {},
            'total_clicks': 0
        }
    
    def _save_clicks(self):
        """Elmenti a kattintások adatait a fájlba."""
        try:
            with open(self.clicks_file, 'w', encoding='utf-8') as f:
                json.dump(self.clicks, f, indent=4, ensure_ascii=False)
        except Exception as e:
            app_logger.error(f"Hiba a kattintások mentésekor: {str(e)}")
    
    def track_article_click(self, article_id: str, action: str):
        """
        Nyomon követi egy cikkre történt kattintást.
        
        Args:
            article_id: A cikk azonosítója
            action: A végrehajtott művelet ('read', 'save', 'share')
        """
        try:
            # Frissítjük a cikk statisztikáit
            if article_id not in self.clicks['articles']:
                self.clicks['articles'][article_id] = {
                    'reads': 0,
                    'saves': 0,
                    'shares': 0,
                    'last_click': None
                }
            
            self.clicks['articles'][article_id][f"{action}s"] += 1
            self.clicks['articles'][article_id]['last_click'] = datetime.now().isoformat()
            
            # Frissítjük az összes kattintások számát
            self.clicks['total_clicks'] += 1
            
            # Elmentjük a változtatásokat
            self._save_clicks()
            
            app_logger.debug(f"Kattintás rögzítve: {article_id} - {action}")
        except Exception as e:
            app_logger.error(f"Hiba a kattintás rögzítésekor: {str(e)}")
    
    def track_keyword_click(self, keyword: str):
        """
        Nyomon követi egy kulcsszóra történt kattintást.
        
        Args:
            keyword: A kulcsszó
        """
        try:
            if keyword not in self.clicks['keywords']:
                self.clicks['keywords'][keyword] = 0
            
            self.clicks['keywords'][keyword] += 1
            self._save_clicks()
            
            app_logger.debug(f"Kulcsszó kattintás rögzítve: {keyword}")
        except Exception as e:
            app_logger.error(f"Hiba a kulcsszó kattintás rögzítésekor: {str(e)}")
    
    def track_source_click(self, source: str):
        """
        Nyomon követi egy forrásra történt kattintást.
        
        Args:
            source: A forrás neve
        """
        try:
            if source not in self.clicks['sources']:
                self.clicks['sources'][source] = 0
            
            self.clicks['sources'][source] += 1
            self._save_clicks()
            
            app_logger.debug(f"Forrás kattintás rögzítve: {source}")
        except Exception as e:
            app_logger.error(f"Hiba a forrás kattintás rögzítésekor: {str(e)}")
    
    def get_article_stats(self, article_id: str) -> Dict[str, Any]:
        """
        Lekéri egy cikk statisztikáit.
        
        Args:
            article_id: A cikk azonosítója
        
        Returns:
            Dict[str, Any]: A cikk statisztikái
        """
        return self.clicks['articles'].get(article_id, {
            'reads': 0,
            'saves': 0,
            'shares': 0,
            'last_click': None
        })
    
    def get_keyword_stats(self) -> Dict[str, int]:
        """
        Lekéri a kulcsszavak statisztikáit.
        
        Returns:
            Dict[str, int]: A kulcsszavak és kattintásaik száma
        """
        return self.clicks['keywords']
    
    def get_source_stats(self) -> Dict[str, int]:
        """
        Lekéri a források statisztikáit.
        
        Returns:
            Dict[str, int]: A források és kattintásaik száma
        """
        return self.clicks['sources']
    
    def get_total_clicks(self) -> int:
        """
        Lekéri az összes kattintások számát.
        
        Returns:
            int: Az összes kattintások száma
        """
        return self.clicks['total_clicks'] 