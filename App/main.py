import time
import logging
from database import create_tables
from ingest_postgres import run as pg_run
from ingest_mongo import run as mongo_run
from config import DATASETS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | MAIN | %(message)s"
)

logger = logging.getLogger("main")

logger.info("🔥 PIPELINE STARTED")

try:
    create_tables()

    for dataset in DATASETS:
        logger.info("==============================")
        logger.info(f"📦 Processing dataset: {dataset}")
        logger.info("==============================")

        start = time.time()
        pg_run(dataset)
        mongo_run(dataset)
        elapsed = time.time() - start

        logger.info(f"⏱️ {dataset} completed in {elapsed:.2f}s")

    logger.info("🎯 ALL DATASETS COMPLETED SUCCESSFULLY")

except Exception:
    logger.exception("❌ PIPELINE FAILED")

while True:
    logger.info("💓 alive")
    time.sleep(30)