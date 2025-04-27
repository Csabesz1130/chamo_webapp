import json
import os
from typing import List, Dict, Any
from datetime import datetime
from src.utils.logger import app_logger
from src.utils.persistent_settings_manager import PersistentSettingsManager

class ArticleManager:
    """
    A cikkek mentéséért és megosztásáért felelős osztály.
    """
    
    def __init__(self, settings_manager: PersistentSettingsManager):
        """
        Inicializálja az ArticleManager-t.
        
        Args:
            settings_manager: A PersistentSettingsManager példány
        """
        self.settings_manager = settings_manager
        self.articles_file = os.path.join(
            os.path.dirname(settings_manager.settings_path),
            'saved_articles.json'
        )
        self.articles = self._load_articles()
        
        app_logger.info("Cikk kezelő inicializálva")
    
    def _load_articles(self) -> Dict[str, Any]:
        """Betölti a mentett cikkeket a fájlból."""
        try:
            if os.path.exists(self.articles_file):
                with open(self.articles_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            app_logger.error(f"Hiba a mentett cikkek betöltésekor: {str(e)}")
        
        return {
            'reading_list': [],
            'shared_articles': {}
        }
    
    def _save_articles(self):
        """Elmenti a mentett cikkeket a fájlba."""
        try:
            with open(self.articles_file, 'w', encoding='utf-8') as f:
                json.dump(self.articles, f, indent=4, ensure_ascii=False)
        except Exception as e:
            app_logger.error(f"Hiba a mentett cikkek mentésekor: {str(e)}")
    
    def save_to_reading_list(self, article: Dict[str, Any]):
        """
        Elmenti egy cikket az olvasási listába.
        
        Args:
            article: A mentendő cikk adatai
        """
        try:
            # Ellenőrizzük, hogy már nincs-e mentve
            if not any(a['id'] == article['id'] for a in self.articles['reading_list']):
                # Hozzáadjuk a mentés dátumát
                article['saved_at'] = datetime.now().isoformat()
                
                # Hozzáadjuk az olvasási listához
                self.articles['reading_list'].append(article)
                
                # Elmentjük a változtatásokat
                self._save_articles()
                
                app_logger.info(f"Cikk mentve az olvasási listába: {article['id']}")
        except Exception as e:
            app_logger.error(f"Hiba a cikk mentésekor: {str(e)}")
    
    def share_article(self, article: Dict[str, Any], project_id: str):
        """
        Megoszt egy cikket egy projekttel.
        
        Args:
            article: A megosztandó cikk adatai
            project_id: A projekt azonosítója
        """
        try:
            # Ellenőrizzük, hogy a projekt létezik-e
            if project_id not in self.articles['shared_articles']:
                self.articles['shared_articles'][project_id] = []
            
            # Ellenőrizzük, hogy már nincs-e megosztva
            if not any(a['id'] == article['id'] for a in self.articles['shared_articles'][project_id]):
                # Hozzáadjuk a megosztás dátumát
                article['shared_at'] = datetime.now().isoformat()
                
                # Hozzáadjuk a projekt megosztott cikkeihez
                self.articles['shared_articles'][project_id].append(article)
                
                # Elmentjük a változtatásokat
                self._save_articles()
                
                app_logger.info(f"Cikk megosztva a {project_id} projekttel: {article['id']}")
        except Exception as e:
            app_logger.error(f"Hiba a cikk megosztásakor: {str(e)}")
    
    def get_reading_list(self) -> List[Dict[str, Any]]:
        """
        Lekéri az olvasási listát.
        
        Returns:
            List[Dict[str, Any]]: Az olvasási lista
        """
        return self.articles['reading_list']
    
    def get_shared_articles(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Lekéri egy projekt megosztott cikkeit.
        
        Args:
            project_id: A projekt azonosítója
        
        Returns:
            List[Dict[str, Any]]: A megosztott cikkek listája
        """
        return self.articles['shared_articles'].get(project_id, [])
    
    def remove_from_reading_list(self, article_id: str):
        """
        Eltávolít egy cikket az olvasási listából.
        
        Args:
            article_id: A cikk azonosítója
        """
        try:
            self.articles['reading_list'] = [
                a for a in self.articles['reading_list']
                if a['id'] != article_id
            ]
            self._save_articles()
            
            app_logger.info(f"Cikk eltávolítva az olvasási listából: {article_id}")
        except Exception as e:
            app_logger.error(f"Hiba a cikk eltávolításakor: {str(e)}")
    
    def remove_from_shared_articles(self, article_id: str, project_id: str):
        """
        Eltávolít egy cikket egy projekt megosztott cikkei közül.
        
        Args:
            article_id: A cikk azonosítója
            project_id: A projekt azonosítója
        """
        try:
            if project_id in self.articles['shared_articles']:
                self.articles['shared_articles'][project_id] = [
                    a for a in self.articles['shared_articles'][project_id]
                    if a['id'] != article_id
                ]
                self._save_articles()
                
                app_logger.info(f"Cikk eltávolítva a {project_id} projekt megosztott cikkei közül: {article_id}")
        except Exception as e:
            app_logger.error(f"Hiba a cikk eltávolításakor: {str(e)}") 