from typing import Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, validator
from src.utils.logger import app_logger

class PaperRecord(BaseModel):
    """
    Egységesített publikáció rekord modell.
    """
    id: str = Field(..., description="Egyedi azonosító")
    title: str = Field(..., description="A publikáció címe")
    abstract: str = Field("", description="A publikáció absztraktja")
    authors: List[str] = Field(default_factory=list, description="Szerzők listája")
    mesh_terms: List[str] = Field(default_factory=list, description="MeSH kulcsszavak")
    keywords: List[str] = Field(default_factory=list, description="Egyéb kulcsszavak")
    date: datetime = Field(..., description="Publikálás dátuma")
    source: str = Field(..., description="Forrás (PubMed, bioRxiv, stb.)")
    doi: str = Field("", description="DOI azonosító")
    url: str = Field("", description="A publikáció URL-je")
    
    @validator('date', pre=True)
    def parse_date(cls, v):
        """Dátum formátum validátor."""
        if isinstance(v, datetime):
            return v
        try:
            # ISO formátum próbálása
            return datetime.fromisoformat(v)
        except (TypeError, ValueError):
            try:
                # PubMed formátum próbálása (YYYY/MM/DD)
                return datetime.strptime(v, "%Y/%m/%d")
            except (TypeError, ValueError):
                # Alapértelmezett: aktuális dátum
                app_logger.warning(f"Érvénytelen dátum formátum: {v}, alapértelmezett használata")
                return datetime.now()

class MetadataNormaliser:
    """
    A különböző forrásokból származó metaadatok normalizálásáért felelős osztály.
    """
    
    def __init__(self):
        """Inicializálja a normalizálót."""
        app_logger.info("Metaadat normalizáló inicializálva")
    
    def normalise_record(self, record: Dict[str, Any]) -> PaperRecord:
        """
        Normalizál egy publikáció rekordot.
        
        Args:
            record: A nyers publikáció rekord
        
        Returns:
            PaperRecord: A normalizált rekord
        """
        try:
            # Alap mezők átalakítása
            normalised = {
                'id': record['id'],
                'title': record['title'],
                'abstract': record.get('abstract', ''),
                'authors': record.get('authors', []),
                'mesh_terms': record.get('mesh_terms', []),
                'keywords': record.get('keywords', []),
                'date': record.get('date', datetime.now().isoformat()),
                'source': record['source'],
                'doi': record.get('doi', ''),
                'url': record.get('link', '')
            }
            
            # Validálás és konvertálás Pydantic modellé
            paper_record = PaperRecord(**normalised)
            
            app_logger.debug(f"Rekord normalizálva: {record['id']}")
            return paper_record
            
        except Exception as e:
            app_logger.error(f"Hiba a rekord normalizálásakor: {str(e)}")
            raise
    
    def normalise_records(self, records: List[Dict[str, Any]]) -> List[PaperRecord]:
        """
        Normalizál több publikáció rekordot.
        
        Args:
            records: A nyers publikáció rekordok listája
        
        Returns:
            List[PaperRecord]: A normalizált rekordok listája
        """
        normalised_records = []
        
        for record in records:
            try:
                normalised = self.normalise_record(record)
                normalised_records.append(normalised)
            except Exception as e:
                app_logger.error(f"Rekord kihagyva normalizálási hiba miatt: {str(e)}")
                continue
        
        return normalised_records 