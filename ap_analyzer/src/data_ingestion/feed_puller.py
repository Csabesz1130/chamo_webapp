from typing import List, Dict, Any
import feedparser
import time
from datetime import datetime, timedelta
import hashlib
from src.utils.logger import app_logger

class FeedPuller:
    """
    RSS/Atom feed kezelő a bioRxiv/medRxiv/arXiv források figyeléséhez.
    """
    
    def __init__(self):
        """Inicializálja a feed kezelőt."""
        # Feed URL-ek
        self.feeds = {
            'bioRxiv': 'http://connect.biorxiv.org/biorxiv_xml.php?subject=all',
            'medRxiv': 'http://connect.medrxiv.org/medrxiv_xml.php?subject=all',
            'arXiv-q-bio': 'http://export.arxiv.org/rss/q-bio'
        }
        
        # Utolsó ellenőrzés időpontja és már látott DOI-k/arXiv ID-k
        self.last_check = {source: datetime.now() - timedelta(minutes=30) 
                          for source in self.feeds.keys()}
        self.seen_ids = set()
        
        app_logger.info("Feed kezelő inicializálva")
    
    def fetch_recent_papers(self) -> List[Dict[str, Any]]:
        """
        Lekéri az új preprint-eket az összes forrásból.
        
        Returns:
            List[Dict[str, Any]]: Az új preprint-ek listája
        """
        papers = []
        current_time = datetime.now()
        
        for source, url in self.feeds.items():
            try:
                # Rate limiting
                time.sleep(1)  # 1 másodperc várakozás források között
                
                # Feed lekérése
                feed = feedparser.parse(url)
                
                # Hibakezelés
                if feed.bozo and feed.bozo_exception:
                    app_logger.error(f"Hiba a {source} feed lekérésekor: {feed.bozo_exception}")
                    continue
                
                # Bejegyzések feldolgozása
                for entry in feed.entries:
                    try:
                        # Azonosító generálása
                        if source == 'arXiv-q-bio':
                            paper_id = entry.id.split('/abs/')[-1]
                        else:
                            paper_id = entry.get('doi', self._generate_id(entry))
                        
                        # Duplikáció ellenőrzés
                        if paper_id in self.seen_ids:
                            continue
                        
                        # Rekord feldolgozása
                        paper = self._process_entry(entry, source, paper_id)
                        if paper:
                            papers.append(paper)
                            self.seen_ids.add(paper_id)
                    
                    except Exception as e:
                        app_logger.error(f"Hiba a {source} bejegyzés feldolgozásakor: {str(e)}")
                        continue
                
                # Frissítjük az utolsó ellenőrzés időpontját
                self.last_check[source] = current_time
                
            except Exception as e:
                app_logger.error(f"Hiba a {source} feed feldolgozásakor: {str(e)}")
                continue
        
        app_logger.info(f"{len(papers)} új preprint találva")
        return papers
    
    def _process_entry(self, entry: Dict[str, Any], source: str, paper_id: str) -> Dict[str, Any]:
        """
        Feldolgoz egy feed bejegyzést.
        
        Args:
            entry: A feed bejegyzés
            source: A forrás neve
            paper_id: A generált/kinyert azonosító
        
        Returns:
            Dict[str, Any]: A feldolgozott rekord vagy None hiba esetén
        """
        try:
            # Közös mezők kinyerése
            processed = {
                'id': f"{source.lower()}_{paper_id}",
                'source': source,
                'title': entry.get('title', '').strip(),
                'authors': [author.get('name', '') for author in entry.get('authors', [])],
                'abstract': entry.get('summary', '').strip(),
                'date': entry.get('published', datetime.now().isoformat()),
                'doi': entry.get('doi', ''),
                'link': entry.get('link', ''),
                'keywords': []
            }
            
            # Forrás-specifikus feldolgozás
            if source == 'arXiv-q-bio':
                # arXiv kategóriák kinyerése
                if 'tags' in entry:
                    processed['keywords'] = [tag.get('term', '') for tag in entry.tags]
            
            return processed
            
        except Exception as e:
            app_logger.error(f"Hiba a bejegyzés feldolgozásakor: {str(e)}")
            return None
    
    def _generate_id(self, entry: Dict[str, Any]) -> str:
        """
        Generál egy egyedi azonosítót egy bejegyzéshez.
        
        Args:
            entry: A feed bejegyzés
        
        Returns:
            str: Az egyedi azonosító
        """
        # Használjuk a címet és a dátumot az azonosító generálásához
        content = f"{entry.get('title', '')}{entry.get('published', '')}"
        return hashlib.md5(content.encode()).hexdigest() 