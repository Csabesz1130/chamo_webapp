"""
Deta Space konfigurációs beállítások.
"""
import os
from typing import Optional

class DetaConfig:
    """Deta Space konfigurációs osztály."""
    
    def __init__(self):
        """Inicializálja a Deta Space konfigurációt."""
        self.project_key: Optional[str] = os.getenv('DETA_PROJECT_KEY')
        self.base_name: str = os.getenv('DETA_BASE_NAME', 'papers')
        self.drive_name: str = os.getenv('DETA_DRIVE_NAME', 'papers_pdfs')
        
    @property
    def is_configured(self) -> bool:
        """Ellenőrzi, hogy a Deta Space megfelelően konfigurálva van-e."""
        return bool(self.project_key)
        
    def validate(self) -> None:
        """Ellenőrzi a konfigurációt és kivételt dob, ha hiányos."""
        if not self.project_key:
            raise ValueError("A DETA_PROJECT_KEY környezeti változó nincs beállítva") 