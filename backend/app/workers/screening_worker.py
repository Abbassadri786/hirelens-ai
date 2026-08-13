import os
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.services.screening_queue import process_one

DATABASE_URL = os.environ["DATABASE_URL"]
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def run():
    interval = float(os.getenv("SCREENING_WORKER_INTERVAL", "2"))
    while True:
        with SessionLocal() as db:
            job = process_one(db)
        if job is None:
            time.sleep(interval)

if __name__ == "__main__":
    run()
