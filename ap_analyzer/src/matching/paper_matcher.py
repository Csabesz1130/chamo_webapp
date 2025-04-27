from typing import List, Dict, Any, Tuple
import numpy as np
from datetime import datetime, timedelta
from sentence_transformers import SentenceTransformer
from src.utils.logger import app_logger
from src.data_ingestion.metadata_normaliser import PaperRecord

class PaperMatcher:
    """
    A felhasználói kulcsszavak és publikációk párosításáért felelős osztály.
    Sentence-transformers modellt használ a szemantikus kereséshez.
    """
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Inicializálja a párosító algoritmust.
        
        Args:
            model_name: A használandó sentence-transformers modell neve
        """
        self.model = SentenceTransformer(model_name)
        app_logger.info(f"Párosító algoritmus inicializálva: {model_name}")
    
    def find_matching_papers(
        self,
        user_keywords: List[str],
        papers: List[PaperRecord],
        top_k: int = 5,
        min_score: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Megkeresi a kulcsszavakhoz legjobban illeszkedő publikációkat.
        
        Args:
            user_keywords: Felhasználói kulcsszavak/kifejezések
            papers: Elérhető publikációk listája
            top_k: Hány találatot adjunk vissza
            min_score: Minimum hasonlósági pontszám
        
        Returns:
            List[Dict[str, Any]]: A legjobban illeszkedő publikációk
        """
        try:
            # Kulcsszavak vektorizálása
            keyword_embeddings = self.model.encode(user_keywords, convert_to_tensor=True)
            
            # Átlagos kulcsszó vektor számítása
            user_vector = keyword_embeddings.mean(dim=0)
            
            # Publikációk vektorizálása és párosítása
            matches = []
            for paper in papers:
                # Publikáció szövegének előkészítése (cím + absztrakt)
                paper_text = f"{paper.title} {paper.abstract}"
                
                # FAISS keresés helyett egyszerű cosine similarity
                paper_vector = self.model.encode(paper_text, convert_to_tensor=True)
                similarity = self._cosine_similarity(user_vector, paper_vector)
                
                if similarity >= min_score:
                    matches.append({
                        'paper': paper,
                        'score': float(similarity)
                    })
            
            # Rendezés pontszám szerint
            matches.sort(key=lambda x: x['score'], reverse=True)
            
            # Exploration vs exploitation
            final_matches = self._apply_exploration_strategy(matches[:top_k])
            
            app_logger.info(f"{len(final_matches)} találat a {len(papers)} publikáció közül")
            return final_matches
            
        except Exception as e:
            app_logger.error(f"Hiba a publikációk párosításakor: {str(e)}")
            return []
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Kiszámítja két vektor közötti cosine similarity-t.
        
        Args:
            vec1: Első vektor
            vec2: Második vektor
        
        Returns:
            float: Hasonlósági pontszám (0-1 között)
        """
        # Vektorok normalizálása
        vec1_normalized = vec1 / np.linalg.norm(vec1)
        vec2_normalized = vec2 / np.linalg.norm(vec2)
        
        # Cosine similarity számítása
        return float(np.dot(vec1_normalized, vec2_normalized))
    
    def _apply_exploration_strategy(
        self,
        matches: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Alkalmazza az exploration vs exploitation stratégiát.
        
        Args:
            matches: A legjobb találatok listája
        
        Returns:
            List[Dict[str, Any]]: A végső találati lista
        """
        if not matches:
            return []
        
        # Ellenőrizzük a találatok korát
        all_old = all(
            (datetime.now() - match['paper'].date).days > 60
            for match in matches
        )
        
        if all_old and len(matches) == 5:
            # Véletlenszerűen kiválasztunk egy újabb cikket a következő decilisből
            next_matches = matches[5:15]  # Következő 10 találat
            if next_matches:
                # Lecseréljük az utolsó találatot egy véletlenszerűen választottra
                random_new = np.random.choice(next_matches)
                matches[4] = random_new
        
        return matches 