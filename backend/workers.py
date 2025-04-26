from celery import Celery
from backend.main import run_analysis
celery = Celery(broker="redis://redis:6379/0", backend="redis://redis:6379/1")

@celery.task(name="analyze.run")
def analyze_task(path, task_id):
    run_analysis(path, task_id)
