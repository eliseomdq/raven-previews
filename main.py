from db.database import init_db

if __name__ == "__main__":
    init_db()
    print("OpenClaw DB initialized. Run workers with: celery -A workers.celery_app worker --loglevel=info")
