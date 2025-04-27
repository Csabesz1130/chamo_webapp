"""
Deta Space kliens osztály a Deta szolgáltatások kezeléséhez.
"""
from typing import Any, Dict, List, Optional
from deta import Deta
from deta.base import Base
from deta.drive import Drive

from src.config.deta_config import DetaConfig

class DetaClient:
    """Deta Space kliens osztály."""
    
    def __init__(self, config: DetaConfig):
        """
        Inicializálja a Deta klienst.
        
        Args:
            config: DetaConfig objektum a beállításokkal
        """
        config.validate()
        self._deta = Deta(config.project_key)
        self._base: Base = self._deta.Base(config.base_name)
        self._drive: Drive = self._deta.Drive(config.drive_name)
        
    def store_article(self, article_data: Dict[str, Any]) -> str:
        """
        Eltárol egy cikket a Deta Base-ben.
        
        Args:
            article_data: A cikk adatai
            
        Returns:
            A létrehozott rekord azonosítója
        """
        return self._base.put(article_data)
        
    def get_article(self, article_id: str) -> Optional[Dict[str, Any]]:
        """
        Lekér egy cikket azonosító alapján.
        
        Args:
            article_id: A cikk azonosítója
            
        Returns:
            A cikk adatai vagy None ha nem található
        """
        return self._base.get(article_id)
        
    def list_articles(self, query: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Lekéri a cikkek listáját, opcionális szűréssel.
        
        Args:
            query: Szűrési feltételek
            
        Returns:
            A cikkek listája
        """
        fetch_res = self._base.fetch(query) if query else self._base.fetch()
        return fetch_res.items
        
    def store_pdf(self, name: str, content: bytes) -> None:
        """
        Eltárol egy PDF fájlt a Deta Drive-ban.
        
        Args:
            name: A fájl neve
            content: A fájl tartalma
        """
        self._drive.put(name, content)
        
    def get_pdf(self, name: str) -> Optional[bytes]:
        """
        Lekér egy PDF fájlt név alapján.
        
        Args:
            name: A fájl neve
            
        Returns:
            A fájl tartalma vagy None ha nem található
        """
        try:
            return self._drive.get(name).read()
        except:
            return None 