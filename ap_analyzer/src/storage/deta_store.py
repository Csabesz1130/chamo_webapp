from typing import List, Dict, Any, Optional
import os
import json
from datetime import datetime
from deta import Deta
from src.utils.logger import app_logger
from src.data_ingestion.metadata_normaliser import PaperRecord

class DetaStore:
    """
    Deta Space alapú tárolási réteg.
    Ingyenes, korlátlan tárolást biztosít NoSQL adatbázissal és fájltárolással.
    """
    
    def __init__(self, project_key: str):
        """
        Inicializálja a Deta Space tárolót.
        
        Args:
            project_key: Deta projekt kulcs
        """
        self.deta = Deta(project_key)
        
        # Adatbázis és fájltároló inicializálása
        self.papers_db = self.deta.Base('papers')  # NoSQL adatbázis
        self.papers_drive = self.deta.Drive('papers')  # Fájltároló
        
        app_logger.info("Deta Space tároló inicializálva")
    
    def store_paper(self, paper: PaperRecord) -> bool:
        """
        Eltárol egy publikációt.
        
        Args:
            paper: A tárolandó publikáció
        
        Returns:
            bool: Sikeres volt-e a tárolás
        """
        try:
            # Konvertáljuk a rekordot dictionary-vé
            paper_dict = paper.dict()
            
            # Hozzáadjuk a tárolás időpontját
            paper_dict['ingestion_date'] = datetime.now().isoformat()
            
            # Mentjük az adatbázisba
            self.papers_db.put(paper_dict, key=paper.id)
            
            # Ha van absztrakt PDF, azt is mentjük
            if hasattr(paper, 'pdf_content') and paper.pdf_content:
                self.papers_drive.put(
                    f"{paper.id}.pdf",
                    paper.pdf_content
                )
            
            app_logger.info(f"Publikáció elmentve: {paper.id}")
            return True
            
        except Exception as e:
            app_logger.error(f"Hiba a publikáció mentésekor: {str(e)}")
            return False
    
    def store_papers(self, papers: List[PaperRecord]) -> int:
        """
        Eltárol több publikációt.
        
        Args:
            papers: A tárolandó publikációk listája
        
        Returns:
            int: A sikeresen tárolt publikációk száma
        """
        success_count = 0
        for paper in papers:
            if self.store_paper(paper):
                success_count += 1
        return success_count
    
    def get_paper(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """
        Lekér egy publikációt.
        
        Args:
            paper_id: A publikáció azonosítója
        
        Returns:
            Optional[Dict[str, Any]]: A publikáció adatai vagy None
        """
        try:
            paper = self.papers_db.get(paper_id)
            if paper:
                # PDF tartalom lekérése, ha létezik
                try:
                    pdf_content = self.papers_drive.get(f"{paper_id}.pdf")
                    if pdf_content:
                        paper['pdf_content'] = pdf_content.read()
                except:
                    pass
            return paper
            
        except Exception as e:
            app_logger.error(f"Hiba a publikáció lekérésekor: {str(e)}")
            return None
    
    def get_papers(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        source: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Lekér több publikációt szűrési feltételekkel.
        
        Args:
            start_date: Kezdő dátum
            end_date: Végdátum
            source: Forrás szűrő
        
        Returns:
            List[Dict[str, Any]]: A publikációk listája
        """
        try:
            # Alap lekérdezés
            query = {}
            
            # Dátum szűrők hozzáadása
            if start_date:
                query['date?gte'] = start_date.isoformat()
            if end_date:
                query['date?lte'] = end_date.isoformat()
            
            # Forrás szűrő hozzáadása
            if source:
                query['source'] = source
            
            # Lekérdezés végrehajtása
            papers = self.papers_db.fetch(query)
            
            return papers.items
            
        except Exception as e:
            app_logger.error(f"Hiba a publikációk lekérésekor: {str(e)}")
            return []
    
    def store_interaction(
        self,
        user_id: str,
        paper_id: str,
        interaction_type: str,
        score: float,
        clicked: bool
    ) -> bool:
        """
        Eltárol egy felhasználói interakciót.
        
        Args:
            user_id: Felhasználó azonosító
            paper_id: Publikáció azonosító
            interaction_type: Interakció típusa
            score: Párosítási pontszám
            clicked: Rákattintott-e a felhasználó
        
        Returns:
            bool: Sikeres volt-e a tárolás
        """
        try:
            interaction = {
                'user_id': user_id,
                'paper_id': paper_id,
                'type': interaction_type,
                'score': score,
                'clicked': clicked,
                'timestamp': datetime.now().isoformat()
            }
            
            # Mentés az interakciók adatbázisába
            interactions_db = self.deta.Base('interactions')
            interactions_db.put(interaction)
            
            app_logger.info(f"Interakció elmentve: {user_id} - {paper_id}")
            return True
            
        except Exception as e:
            app_logger.error(f"Hiba az interakció mentésekor: {str(e)}")
            return False 