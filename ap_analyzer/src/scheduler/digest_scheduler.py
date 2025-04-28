"""
Digest e-mailek ütemezésének kezelése.
"""
from typing import Optional, Dict, Any
from datetime import datetime
from src.utils.logger import app_logger
from src.config.scheduler_config import SchedulerConfig
from src.scheduler.task_scheduler import TaskScheduler
from src.email.email_sender import EmailSender

class DigestScheduler(TaskScheduler):
    """Digest e-mailek ütemezésének kezelése."""
    
    def __init__(self, config: Optional[SchedulerConfig] = None):
        """
        Inicializálja a digest ütemezőt.
        
        Args:
            config: Ütemező konfigurációs objektum
        """
        super().__init__(config)
        self.email_sender = EmailSender()
        app_logger.info("Digest ütemező inicializálva")
    
    def schedule_digest(self, user_id: str, preferred_time: str) -> bool:
        """
        Beütemez egy digest küldési feladatot.
        
        Args:
            user_id: Felhasználó azonosító
            preferred_time: Preferált küldési idő (HH:MM formátumban)
            
        Returns:
            bool: Sikeres volt-e az ütemezés
        """
        try:
            # Idő konvertálása cron kifejezéssé
            hour, minute = map(int, preferred_time.split(':'))
            cron_expression = f"{minute} {hour} * * *"
            
            # Feladat ütemezése
            return self.schedule_task(
                task_func=self._send_digest,
                cron_expression=cron_expression,
                task_id=f"digest_{user_id}",
                user_id=user_id
            )
            
        except Exception as e:
            app_logger.error(f"Hiba a digest ütemezésekor: {str(e)}")
            return False
    
    def remove_digest(self, user_id: str) -> bool:
        """
        Eltávolít egy ütemezett digest feladatot.
        
        Args:
            user_id: Felhasználó azonosító
            
        Returns:
            bool: Sikeres volt-e az eltávolítás
        """
        return self.remove_task(f"digest_{user_id}")
    
    def modify_digest_time(self, user_id: str, new_time: str) -> bool:
        """
        Módosítja egy digest küldési idejét.
        
        Args:
            user_id: Felhasználó azonosító
            new_time: Új küldési idő (HH:MM formátumban)
            
        Returns:
            bool: Sikeres volt-e a módosítás
        """
        try:
            # Új idő konvertálása cron kifejezéssé
            hour, minute = map(int, new_time.split(':'))
            cron_expression = f"{minute} {hour} * * *"
            
            # Feladat módosítása
            return self.modify_task(
                task_id=f"digest_{user_id}",
                cron_expression=cron_expression
            )
            
        except Exception as e:
            app_logger.error(f"Hiba a digest idő módosításakor: {str(e)}")
            return False
    
    def get_digest_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Lekéri egy digest feladat információit.
        
        Args:
            user_id: Felhasználó azonosító
            
        Returns:
            Dict[str, Any]: Feladat információk vagy None, ha nem található
        """
        return self.get_task_info(f"digest_{user_id}")
    
    def list_digest_tasks(self) -> Dict[str, Dict[str, Any]]:
        """
        Listázza az összes digest feladatot.
        
        Returns:
            Dict[str, Dict[str, Any]]: Digest feladatok és információik
        """
        all_tasks = self.list_tasks()
        digest_tasks = {}
        
        for task_id, task_info in all_tasks.items():
            if task_id.startswith("digest_"):
                digest_tasks[task_id] = task_info
        
        return digest_tasks
    
    def _send_digest(self, user_id: str) -> None:
        """
        Digest e-mail összeállítása és küldése.
        
        Args:
            user_id: Felhasználó azonosító
        """
        try:
            self.email_sender.send_digest(user_id)
            app_logger.info(f"Digest elküldve: {user_id}")
            
        except Exception as e:
            app_logger.error(f"Hiba a digest küldésekor: {str(e)}") 