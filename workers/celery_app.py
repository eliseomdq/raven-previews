from celery import Celery
from config import REDIS_URL

app = Celery(
    "openclaw",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "workers.scraper",
        "workers.auditor",
        "workers.generator",
        "workers.deployer",
        "workers.outreach",
    ],
)

app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="America/Argentina/Buenos_Aires",
    enable_utc=True,
    task_track_started=True,
)
