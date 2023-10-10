from celery import Celery
from app import create_app
import json
from config import Config
from datetime import datetime, timedelta
from app import db
from app.models.time_zone import TimeZone
from app.services.crud import CRUD

app = create_app()
app.app_context().push()
app = Celery('tasks', broker=Config.AMQP)

crud = CRUD()

BROKER_CONNECTION_RETRY = True  # will make it retry whenever it fails
BROKER_CONNECTION_MAX_RETRIES = 0  # will disable the retry limit.
BROKER_CONNECTION_TIMEOUT = 120
app.conf.beat_schedule = {
    'task1': {
        'task': 'app.tasks.start_processing',
        'schedule': timedelta(minutes=1)
    },
    # 'options': {
    #     'expires': 15.0  # beat scheduled tasks will be removed automatically
    # }
}
app.conf.timezone = 'UTC'


@app.task
def background_job_one(region: str, org_id: int, stored_resources: dict):
    return True


@app.task
def second_function():
    job_three.delay("<params>")
    return True


@app.task
def job_three(**kwargs):
    return True


@app.task
def start_processing():
    job_three.delay()
