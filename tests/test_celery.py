from workers.celery_app import app


def test_celery_app_created():
    assert app.main == "openclaw"


def test_celery_broker_configured():
    assert "redis" in app.conf.broker_url
