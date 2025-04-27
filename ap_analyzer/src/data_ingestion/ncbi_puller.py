from typing import List, Dict, Any
import time
from datetime import datetime, timedelta
from Bio import Entrez
from src.utils.logger import app_logger

class NCBIPuller:
    """
    Inkrementális PubMed rekord lekérő az NCBI E-utilities használatával.
    """
    
    def __init__(self, email: str, api_key: str = None):
        """
        Inicializálja az NCBI puller-t.
        
        Args:
            email: Az NCBI által megkövetelt e-mail cím
            api_key: Opcionális NCBI API kulcs (magasabb rate limit)
        """
        self.email = email
        self.api_key = api_key
        
        # NCBI E-utilities beállítása
        Entrez.email = email
        if api_key:
            Entrez.api_key = api_key
        
        # Utolsó futás időpontja
        self.last_run = datetime.now() - timedelta(minutes=30)
        
        app_logger.info("NCBI puller inicializálva")
    
    def fetch_recent_records(self) -> List[Dict[str, Any]]:
        """
        Lekéri a legutóbbi futás óta módosított PubMed rekordokat.
        
        Returns:
            List[Dict[str, Any]]: A módosított rekordok listája
        """
        try:
            # Keresési dátum beállítása
            date_from = self.last_run.strftime("%Y/%m/%d")
            current_time = datetime.now()
            
            # PubMed keresés
            search_handle = Entrez.esearch(
                db="pubmed",
                term=f"{date_from}[MDAT]",
                retmax=1000  # Maximum 1000 rekord egyszerre
            )
            search_results = Entrez.read(search_handle)
            search_handle.close()
            
            # Ha nincs találat, visszatérünk
            if not search_results["IdList"]:
                app_logger.info("Nincs új vagy módosított rekord")
                self.last_run = current_time
                return []
            
            # Rekordok letöltése
            records = []
            for pmid in search_results["IdList"]:
                try:
                    # Rate limiting (max 3 kérés/másodperc API kulcs nélkül)
                    if not self.api_key:
                        time.sleep(0.34)  # ~3 kérés/másodperc
                    
                    # Rekord letöltése
                    fetch_handle = Entrez.efetch(
                        db="pubmed",
                        id=pmid,
                        rettype="medline",
                        retmode="text"
                    )
                    record = fetch_handle.read()
                    fetch_handle.close()
                    
                    # Rekord feldolgozása és hozzáadása a listához
                    processed_record = self._process_record(record, pmid)
                    if processed_record:
                        records.append(processed_record)
                    
                except Exception as e:
                    app_logger.error(f"Hiba a {pmid} azonosítójú rekord letöltésekor: {str(e)}")
                    continue
            
            # Frissítjük az utolsó futás időpontját
            self.last_run = current_time
            
            app_logger.info(f"{len(records)} új/módosított rekord letöltve")
            return records
            
        except Exception as e:
            app_logger.error(f"Hiba a PubMed rekordok lekérésekor: {str(e)}")
            return []
    
    def _process_record(self, record: str, pmid: str) -> Dict[str, Any]:
        """
        Feldolgoz egy PubMed rekordot.
        
        Args:
            record: A nyers MEDLINE formátumú rekord
            pmid: A rekord PubMed azonosítója
        
        Returns:
            Dict[str, Any]: A feldolgozott rekord vagy None hiba esetén
        """
        try:
            # Itt implementálni kell a MEDLINE formátum feldolgozását
            # Ez egy egyszerűsített példa
            lines = record.split('\n')
            processed = {
                'id': f"pubmed_{pmid}",
                'source': 'PubMed',
                'title': '',
                'authors': [],
                'abstract': '',
                'mesh_terms': [],
                'keywords': [],
                'date': '',
                'doi': ''
            }
            
            current_field = None
            for line in lines:
                if not line.strip():
                    continue
                    
                if line.startswith('TI  - '):
                    processed['title'] = line[6:].strip()
                elif line.startswith('AU  - '):
                    processed['authors'].append(line[6:].strip())
                elif line.startswith('AB  - '):
                    processed['abstract'] = line[6:].strip()
                elif line.startswith('MH  - '):
                    processed['mesh_terms'].append(line[6:].strip())
                elif line.startswith('EDAT- '):
                    processed['date'] = line[6:].strip()
                elif line.startswith('LID - '):
                    if '[doi]' in line:
                        processed['doi'] = line[6:].strip().replace(' [doi]', '')
            
            return processed
            
        except Exception as e:
            app_logger.error(f"Hiba a {pmid} azonosítójú rekord feldolgozásakor: {str(e)}")
            return None 