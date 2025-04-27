import requests
from typing import List, Dict, Any
from datetime import datetime, timedelta
from src.utils.logger import app_logger
from src.utils.email_preferences_manager import EmailPreferencesManager

class ArticleFetcher:
    """
    A cikkek lekéréséért felelős osztály a különböző forrásokból.
    """
    
    def __init__(self, email_manager: EmailPreferencesManager):
        """
        Inicializálja az ArticleFetcher-t.
        
        Args:
            email_manager: Az EmailPreferencesManager példány
        """
        self.email_manager = email_manager
        
        # API kulcsok és végpontok
        self.pubmed_api_key = None  # A felhasználónak kell beállítania
        self.biorxiv_api_key = None  # A felhasználónak kell beállítania
        self.arxiv_api_key = None  # A felhasználónak kell beállítania
        
        app_logger.info("Cikk lekérő inicializálva")
    
    def get_recommended_articles(self) -> List[Dict[str, Any]]:
        """
        Lekéri a javasolt cikkeket a beállított forrásokból.
        
        Returns:
            List[Dict[str, Any]]: A javasolt cikkek listája
        """
        articles = []
        
        # Lekérjük a beállításokat
        keywords = self.email_manager.get_keywords()
        sources = self.email_manager.get_sources()
        keyword_logic = self.email_manager.preferences.get('keyword_logic', 'AND')
        
        if not keywords or not sources:
            return articles
        
        # Lekérjük a cikkeket minden forrásból
        for source in sources:
            try:
                if source == 'PubMed':
                    articles.extend(self._fetch_from_pubmed(keywords, keyword_logic))
                elif source == 'bioRxiv':
                    articles.extend(self._fetch_from_biorxiv(keywords, keyword_logic))
                elif source == 'arXiv-q-bio':
                    articles.extend(self._fetch_from_arxiv(keywords, keyword_logic))
            except Exception as e:
                app_logger.error(f"Hiba a cikkek lekérésekor a {source} forrásból: {str(e)}")
        
        # Rendezzük a cikkeket a relevancia alapján
        articles.sort(key=lambda x: x['score'], reverse=True)
        
        # Visszaadjuk az első 5 legrelevánsabb cikket
        return articles[:5]
    
    def _fetch_from_pubmed(self, keywords: List[str], logic: str) -> List[Dict[str, Any]]:
        """Lekéri a cikkeket a PubMed-ből."""
        # Ez egy példa implementáció
        # Valós implementációban itt kell használni a PubMed API-t
        return [
            {
                'id': 'pubmed-1',
                'title': 'Példa PubMed cikk',
                'authors': 'Kovács János, Nagy Péter',
                'source': 'PubMed',
                'date': '2024-03-20',
                'link': 'https://pubmed.ncbi.nlm.nih.gov/example',
                'score': 90
            }
        ]
    
    def _fetch_from_biorxiv(self, keywords: List[str], logic: str) -> List[Dict[str, Any]]:
        """Lekéri a cikkeket a bioRxiv-ből."""
        # Ez egy példa implementáció
        # Valós implementációban itt kell használni a bioRxiv API-t
        return [
            {
                'id': 'biorxiv-1',
                'title': 'Példa bioRxiv cikk',
                'authors': 'Kiss Anna, Tóth Béla',
                'source': 'bioRxiv',
                'date': '2024-03-19',
                'link': 'https://www.biorxiv.org/content/example',
                'score': 85
            }
        ]
    
    def _fetch_from_arxiv(self, keywords: List[str], logic: str) -> List[Dict[str, Any]]:
        """Lekéri a cikkeket az arXiv-ből."""
        # Ez egy példa implementáció
        # Valós implementációban itt kell használni az arXiv API-t
        return [
            {
                'id': 'arxiv-1',
                'title': 'Példa arXiv cikk',
                'authors': 'Szabó István, Horváth Mária',
                'source': 'arXiv-q-bio',
                'date': '2024-03-18',
                'link': 'https://arxiv.org/abs/example',
                'score': 80
            }
        ]
    
    def _calculate_relevance_score(self, article: Dict[str, Any], keywords: List[str], logic: str) -> float:
        """
        Kiszámítja egy cikk relevancia pontszámát a kulcsszavak alapján.
        
        Args:
            article: A cikk adatai
            keywords: A kulcsszavak listája
            logic: A logikai operátor ('AND' vagy 'OR')
        
        Returns:
            float: A relevancia pontszám 0-100 között
        """
        # Ez egy egyszerű példa implementáció
        # Valós implementációban itt kell használni egy fejlettebb relevancia algoritmust
        title = article['title'].lower()
        score = 0
        
        for keyword in keywords:
            if keyword.lower() in title:
                score += 20  # Minden egyezés 20 pontot ér
        
        return min(score, 100)  # Maximum 100 pont lehet 