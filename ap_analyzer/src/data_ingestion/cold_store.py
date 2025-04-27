from typing import List, Dict, Any
import os
import json
from datetime import datetime
import pyarrow as pa
import pyarrow.parquet as pq
from src.utils.logger import app_logger
from src.data_ingestion.metadata_normaliser import PaperRecord

class ColdStore:
    """
    A publikációk tartós tárolásáért felelős osztály.
    Append-only parquet fájlokat használ S3-kompatibilis tárolóban.
    """
    
    def __init__(self, storage_path: str):
        """
        Inicializálja a Cold-store kezelőt.
        
        Args:
            storage_path: A tárolási útvonal
        """
        self.storage_path = storage_path
        self.current_batch = []
        self.batch_size = 1000  # Maximum rekord egy batch-ben
        
        # Séma definiálása
        self.schema = pa.schema([
            ('id', pa.string()),
            ('title', pa.string()),
            ('abstract', pa.string()),
            ('authors', pa.list_(pa.string())),
            ('mesh_terms', pa.list_(pa.string())),
            ('keywords', pa.list_(pa.string())),
            ('date', pa.timestamp('s')),
            ('source', pa.string()),
            ('doi', pa.string()),
            ('url', pa.string()),
            ('ingestion_date', pa.timestamp('s'))
        ])
        
        # Könyvtár létrehozása, ha nem létezik
        os.makedirs(storage_path, exist_ok=True)
        
        app_logger.info("Cold-store kezelő inicializálva")
    
    def store_records(self, records: List[PaperRecord]):
        """
        Eltárol több publikáció rekordot.
        
        Args:
            records: A tárolandó rekordok listája
        """
        try:
            # Rekordok hozzáadása a batch-hez
            for record in records:
                self.current_batch.append(self._prepare_record(record))
            
            # Ha elértük a batch méretet, mentünk
            if len(self.current_batch) >= self.batch_size:
                self._write_batch()
            
            app_logger.info(f"{len(records)} rekord hozzáadva a batch-hez")
            
        except Exception as e:
            app_logger.error(f"Hiba a rekordok tárolása közben: {str(e)}")
            raise
    
    def flush(self):
        """Kiírja a jelenlegi batch-et, függetlenül a méretétől."""
        if self.current_batch:
            self._write_batch()
    
    def _prepare_record(self, record: PaperRecord) -> Dict[str, Any]:
        """
        Előkészít egy rekordot a tároláshoz.
        
        Args:
            record: A tárolandó rekord
        
        Returns:
            Dict[str, Any]: Az előkészített rekord
        """
        # Konvertáljuk a Pydantic modellt dictionary-vé
        record_dict = record.dict()
        
        # Hozzáadjuk a tárolás időpontját
        record_dict['ingestion_date'] = datetime.now()
        
        return record_dict
    
    def _write_batch(self):
        """Kiírja az aktuális batch-et parquet formátumban."""
        try:
            if not self.current_batch:
                return
            
            # Létrehozzuk a parquet fájl nevét
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"papers_{timestamp}.parquet"
            filepath = os.path.join(self.storage_path, filename)
            
            # Konvertáljuk a rekordokat PyArrow táblává
            table = pa.Table.from_pylist(self.current_batch, schema=self.schema)
            
            # Kiírjuk a fájlt
            pq.write_table(
                table,
                filepath,
                compression='snappy',
                use_dictionary=True,
                write_statistics=True
            )
            
            # Töröljük a batch-et
            self.current_batch = []
            
            app_logger.info(f"Batch kiírva: {filepath}")
            
        except Exception as e:
            app_logger.error(f"Hiba a batch kiírásakor: {str(e)}")
            raise
    
    def read_records(self, start_date: datetime = None, end_date: datetime = None) -> List[Dict[str, Any]]:
        """
        Beolvassa a rekordokat egy adott időintervallumból.
        
        Args:
            start_date: Kezdő dátum
            end_date: Végdátum
        
        Returns:
            List[Dict[str, Any]]: A beolvasott rekordok listája
        """
        try:
            records = []
            
            # Összegyűjtjük az összes parquet fájlt
            parquet_files = [
                os.path.join(self.storage_path, f)
                for f in os.listdir(self.storage_path)
                if f.endswith('.parquet')
            ]
            
            for filepath in parquet_files:
                try:
                    # Beolvassuk a táblát
                    table = pq.read_table(filepath)
                    df = table.to_pandas()
                    
                    # Szűrés dátum szerint
                    if start_date:
                        df = df[df['date'] >= start_date]
                    if end_date:
                        df = df[df['date'] <= end_date]
                    
                    # Konvertálás dictionary-vé
                    records.extend(df.to_dict('records'))
                    
                except Exception as e:
                    app_logger.error(f"Hiba a {filepath} fájl olvasásakor: {str(e)}")
                    continue
            
            app_logger.info(f"{len(records)} rekord beolvasva")
            return records
            
        except Exception as e:
            app_logger.error(f"Hiba a rekordok olvasásakor: {str(e)}")
            raise 