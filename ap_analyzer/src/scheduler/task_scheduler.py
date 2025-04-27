"""
Ütemezett feladatok kezelése Celery vagy APScheduler használatával.
"""
import os
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from src.utils.logger import app_logger

# Celery vagy APScheduler használata a környezeti változó alapján
USE_CELERY = os.getenv('USE_CELERY', 'false').lower() == 'true'

if USE_CELERY:
    from celery import Celery
    from celery.schedules import crontab
    
    # Celery app inicializálása Redis backend-del
    celery_app = Celery(
        'ap_analyzer',
        broker='redis://localhost:6379/0',
        backend='redis://localhost:6379/0'
    )
else:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger

class TaskScheduler:
    """Ütemezett feladatok kezelése."""
    
    def __init__(self):
        """Inicializálja az ütemezőt."""
        self.scheduler = None
        if not USE_CELERY:
            self.scheduler = BackgroundScheduler()
            self.scheduler.start()
        app_logger.info(f"Ütemező inicializálva: {'Celery' if USE_CELERY else 'APScheduler'}")
    
    def schedule_digest_job(self, user_id: str, preferred_time: str) -> None:
        """
        Beütemez egy digest küldési feladatot.
        
        Args:
            user_id: Felhasználó azonosító
            preferred_time: Preferált küldési idő (HH:MM formátumban)
        """
        try:
            hour, minute = map(int, preferred_time.split(':'))
            
            if USE_CELERY:
                # Celery ütemezés
                celery_app.add_periodic_task(
                    crontab(hour=hour, minute=minute),
                    compose_and_send_digest.s(user_id)
                )
            else:
                # APScheduler ütemezés
                self.scheduler.add_job(
                    compose_and_send_digest,
                    CronTrigger(hour=hour, minute=minute),
                    args=[user_id],
                    id=f'digest_{user_id}'
                )
            
            app_logger.info(f"Digest feladat ütemezve: {user_id} - {preferred_time}")
            
        except Exception as e:
            app_logger.error(f"Hiba a feladat ütemezésekor: {str(e)}")
    
    def remove_digest_job(self, user_id: str) -> None:
        """
        Eltávolít egy ütemezett digest feladatot.
        
        Args:
            user_id: Felhasználó azonosító
        """
        try:
            if not USE_CELERY:
                self.scheduler.remove_job(f'digest_{user_id}')
            # Celery esetén nincs egyszerű módja a feladat eltávolításának
            
            app_logger.info(f"Digest feladat eltávolítva: {user_id}")
            
        except Exception as e:
            app_logger.error(f"Hiba a feladat eltávolításakor: {str(e)}")
    
    def shutdown(self) -> None:
        """Leállítja az ütemezőt."""
        if not USE_CELERY and self.scheduler:
            self.scheduler.shutdown()
            app_logger.info("Ütemező leállítva")

# Celery task definíció
if USE_CELERY:
    @celery_app.task
    def compose_and_send_digest(user_id: str) -> None:
        """
        Összeállítja és elküldi a digest-et.
        
        Args:
            user_id: Felhasználó azonosító
        """
        from src.email.email_sender import EmailSender
        
        try:
            sender = EmailSender()
            sender.send_digest(user_id)
            app_logger.info(f"Digest elküldve: {user_id}")
            
        except Exception as e:
            app_logger.error(f"Hiba a digest küldésekor: {str(e)}")
            
# APScheduler task definíció
else:
    def compose_and_send_digest(user_id: str) -> None:
        """
        Összeállítja és elküldi a digest-et.
        
        Args:
            user_id: Felhasználó azonosító
        """
        from src.email.email_sender import EmailSender
        
        try:
            sender = EmailSender()
            sender.send_digest(user_id)
            app_logger.info(f"Digest elküldve: {user_id}")
            
        except Exception as e:
            app_logger.error(f"Hiba a digest küldésekor: {str(e)}") 