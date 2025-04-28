"""
Ütemező konfigurációs beállításai.
"""
import os
from typing import Optional
from pydantic import BaseModel, validator

class SchedulerConfig(BaseModel):
    """Ütemező konfigurációs osztály."""
    
    # Általános beállítások
    scheduler_type: str = "apscheduler"  # "celery" vagy "apscheduler"
    max_instances: int = 1
    timezone: str = "Europe/Budapest"
    
    # Celery beállítások
    celery_broker_url: Optional[str] = None
    celery_backend_url: Optional[str] = None
    celery_task_serializer: str = "json"
    celery_result_serializer: str = "json"
    celery_accept_content: list = ["json"]
    celery_task_track_started: bool = True
    celery_task_time_limit: int = 3600  # 1 óra
    celery_worker_prefetch_multiplier: int = 1
    
    # APScheduler beállítások
    apscheduler_job_defaults: dict = {
        'coalesce': True,
        'max_instances': 1,
        'misfire_grace_time': 60
    }
    apscheduler_executors: dict = {
        'default': {'type': 'threadpool', 'max_workers': 20}
    }
    
    @validator('scheduler_type')
    def validate_scheduler_type(cls, v):
        """Ellenőrzi a scheduler_type értékét."""
        if v not in ['celery', 'apscheduler']:
            raise ValueError('A scheduler_type csak "celery" vagy "apscheduler" lehet')
        return v
    
    @validator('celery_broker_url', 'celery_backend_url')
    def validate_celery_urls(cls, v, values, field):
        """Ellenőrzi a Celery URL-eket."""
        if values.get('scheduler_type') == 'celery' and not v:
            raise ValueError(f'A {field.name} kötelező Celery használata esetén')
        return v
    
    @classmethod
    def from_env(cls) -> 'SchedulerConfig':
        """
        Létrehoz egy konfigurációt a környezeti változókból.
        
        Returns:
            SchedulerConfig: A konfigurációs objektum
        """
        config_dict = {
            'scheduler_type': os.getenv('SCHEDULER_TYPE', 'apscheduler'),
            'max_instances': int(os.getenv('SCHEDULER_MAX_INSTANCES', '1')),
            'timezone': os.getenv('SCHEDULER_TIMEZONE', 'Europe/Budapest'),
            
            # Celery
            'celery_broker_url': os.getenv('CELERY_BROKER_URL'),
            'celery_backend_url': os.getenv('CELERY_BACKEND_URL'),
            'celery_task_serializer': os.getenv('CELERY_TASK_SERIALIZER', 'json'),
            'celery_result_serializer': os.getenv('CELERY_RESULT_SERIALIZER', 'json'),
            'celery_accept_content': os.getenv('CELERY_ACCEPT_CONTENT', '["json"]'),
            'celery_task_track_started': os.getenv('CELERY_TASK_TRACK_STARTED', 'true').lower() == 'true',
            'celery_task_time_limit': int(os.getenv('CELERY_TASK_TIME_LIMIT', '3600')),
            'celery_worker_prefetch_multiplier': int(os.getenv('CELERY_WORKER_PREFETCH_MULTIPLIER', '1')),
            
            # APScheduler
            'apscheduler_job_defaults': {
                'coalesce': True,
                'max_instances': int(os.getenv('APSCHEDULER_MAX_INSTANCES', '1')),
                'misfire_grace_time': int(os.getenv('APSCHEDULER_MISFIRE_GRACE_TIME', '60'))
            },
            'apscheduler_executors': {
                'default': {
                    'type': 'threadpool',
                    'max_workers': int(os.getenv('APSCHEDULER_MAX_WORKERS', '20'))
                }
            }
        }
        
        return cls(**config_dict) 