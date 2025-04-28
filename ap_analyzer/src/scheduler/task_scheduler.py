"""
Ütemezett feladatok kezelése különböző ütemezőkkel.
"""
import os
from typing import Optional, Callable, Dict, Any
from datetime import datetime
from celery import Celery
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from src.utils.logger import app_logger
from src.config.scheduler_config import SchedulerConfig

class TaskScheduler:
    """Ütemezett feladatok kezelése."""
    
    def __init__(self, config: Optional[SchedulerConfig] = None):
        """
        Inicializálja az ütemezőt.
        
        Args:
            config: Ütemező konfigurációs objektum
        """
        self.config = config or SchedulerConfig.from_env()
        
        if self.config.scheduler_type == 'celery':
            self._init_celery()
        else:  # apscheduler
            self._init_apscheduler()
            
        app_logger.info(f"Ütemező inicializálva: {self.config.scheduler_type}")
    
    def _init_celery(self) -> None:
        """Celery ütemező inicializálása."""
        self.scheduler = Celery(
            'tasks',
            broker=self.config.celery_broker_url,
            backend=self.config.celery_backend_url
        )
        
        # Celery konfigurációk beállítása
        self.scheduler.conf.update(
            task_serializer=self.config.celery_task_serializer,
            result_serializer=self.config.celery_result_serializer,
            accept_content=self.config.celery_accept_content,
            task_track_started=self.config.celery_task_track_started,
            task_time_limit=self.config.celery_task_time_limit,
            worker_prefetch_multiplier=self.config.celery_worker_prefetch_multiplier,
            timezone=self.config.timezone
        )
    
    def _init_apscheduler(self) -> None:
        """APScheduler ütemező inicializálása."""
        self.scheduler = BackgroundScheduler(
            job_defaults=self.config.apscheduler_job_defaults,
            executors=self.config.apscheduler_executors,
            timezone=self.config.timezone
        )
        self.scheduler.start()
    
    def schedule_task(
        self,
        task_func: Callable,
        cron_expression: str,
        task_id: str,
        **kwargs: Dict[str, Any]
    ) -> bool:
        """
        Ütemezett feladat hozzáadása.
        
        Args:
            task_func: A végrehajtandó függvény
            cron_expression: Cron kifejezés az ütemezéshez
            task_id: Feladat azonosító
            **kwargs: További paraméterek a feladathoz
            
        Returns:
            bool: Sikeres volt-e a hozzáadás
        """
        try:
            if self.config.scheduler_type == 'celery':
                # Celery esetén dekorátor hozzáadása
                task = self.scheduler.task(
                    name=task_id,
                    bind=True,
                    **kwargs
                )(task_func)
                
                # Cron ütemezés beállítása
                self.scheduler.conf.beat_schedule[task_id] = {
                    'task': task_id,
                    'schedule': cron_expression,
                    'kwargs': kwargs
                }
                
            else:  # apscheduler
                # APScheduler esetén közvetlen hozzáadás
                self.scheduler.add_job(
                    task_func,
                    CronTrigger.from_crontab(cron_expression),
                    id=task_id,
                    replace_existing=True,
                    **kwargs
                )
            
            app_logger.info(f"Feladat ütemezve: {task_id}")
            return True
            
        except Exception as e:
            app_logger.error(f"Hiba a feladat ütemezésekor: {str(e)}")
            return False
    
    def remove_task(self, task_id: str) -> bool:
        """
        Ütemezett feladat eltávolítása.
        
        Args:
            task_id: Feladat azonosító
            
        Returns:
            bool: Sikeres volt-e az eltávolítás
        """
        try:
            if self.config.scheduler_type == 'celery':
                # Celery esetén törlés a beat_schedule-ból
                if task_id in self.scheduler.conf.beat_schedule:
                    del self.scheduler.conf.beat_schedule[task_id]
                
            else:  # apscheduler
                # APScheduler esetén közvetlen törlés
                self.scheduler.remove_job(task_id)
            
            app_logger.info(f"Feladat eltávolítva: {task_id}")
            return True
            
        except Exception as e:
            app_logger.error(f"Hiba a feladat eltávolításakor: {str(e)}")
            return False
    
    def modify_task(
        self,
        task_id: str,
        cron_expression: Optional[str] = None,
        **kwargs: Dict[str, Any]
    ) -> bool:
        """
        Ütemezett feladat módosítása.
        
        Args:
            task_id: Feladat azonosító
            cron_expression: Új cron kifejezés (opcionális)
            **kwargs: Új paraméterek a feladathoz
            
        Returns:
            bool: Sikeres volt-e a módosítás
        """
        try:
            if self.config.scheduler_type == 'celery':
                # Celery esetén módosítás a beat_schedule-ban
                if task_id in self.scheduler.conf.beat_schedule:
                    if cron_expression:
                        self.scheduler.conf.beat_schedule[task_id]['schedule'] = cron_expression
                    if kwargs:
                        self.scheduler.conf.beat_schedule[task_id]['kwargs'].update(kwargs)
                else:
                    raise ValueError(f"Nem található feladat: {task_id}")
                
            else:  # apscheduler
                # APScheduler esetén közvetlen módosítás
                job = self.scheduler.get_job(task_id)
                if job:
                    if cron_expression:
                        job.reschedule(CronTrigger.from_crontab(cron_expression))
                    if kwargs:
                        job.modify(**kwargs)
                else:
                    raise ValueError(f"Nem található feladat: {task_id}")
            
            app_logger.info(f"Feladat módosítva: {task_id}")
            return True
            
        except Exception as e:
            app_logger.error(f"Hiba a feladat módosításakor: {str(e)}")
            return False
    
    def get_task_info(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Ütemezett feladat információinak lekérése.
        
        Args:
            task_id: Feladat azonosító
            
        Returns:
            Dict[str, Any]: Feladat információk vagy None, ha nem található
        """
        try:
            if self.config.scheduler_type == 'celery':
                # Celery esetén információk a beat_schedule-ból
                if task_id in self.scheduler.conf.beat_schedule:
                    schedule = self.scheduler.conf.beat_schedule[task_id]
                    return {
                        'id': task_id,
                        'schedule': str(schedule['schedule']),
                        'kwargs': schedule['kwargs'],
                        'last_run': None  # Celery nem tárolja
                    }
                
            else:  # apscheduler
                # APScheduler esetén közvetlen lekérés
                job = self.scheduler.get_job(task_id)
                if job:
                    return {
                        'id': job.id,
                        'schedule': str(job.trigger),
                        'kwargs': job.kwargs,
                        'last_run': job.next_run_time.isoformat() if job.next_run_time else None
                    }
            
            return None
            
        except Exception as e:
            app_logger.error(f"Hiba a feladat információk lekérésekor: {str(e)}")
            return None
    
    def list_tasks(self) -> Dict[str, Dict[str, Any]]:
        """
        Összes ütemezett feladat listázása.
        
        Returns:
            Dict[str, Dict[str, Any]]: Feladatok és információik
        """
        try:
            tasks = {}
            
            if self.config.scheduler_type == 'celery':
                # Celery esetén feladatok a beat_schedule-ból
                for task_id, schedule in self.scheduler.conf.beat_schedule.items():
                    tasks[task_id] = {
                        'id': task_id,
                        'schedule': str(schedule['schedule']),
                        'kwargs': schedule['kwargs'],
                        'last_run': None  # Celery nem tárolja
                    }
                
            else:  # apscheduler
                # APScheduler esetén az összes job lekérése
                for job in self.scheduler.get_jobs():
                    tasks[job.id] = {
                        'id': job.id,
                        'schedule': str(job.trigger),
                        'kwargs': job.kwargs,
                        'last_run': job.next_run_time.isoformat() if job.next_run_time else None
                    }
            
            return tasks
            
        except Exception as e:
            app_logger.error(f"Hiba a feladatok listázásakor: {str(e)}")
            return {}
    
    def __del__(self):
        """Destruktor a megfelelő leállításhoz."""
        if self.config.scheduler_type == 'apscheduler':
            try:
                self.scheduler.shutdown()
            except:
                pass 