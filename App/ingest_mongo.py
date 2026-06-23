import json
import logging
from pymongo import MongoClient
from pymongo.errors import BulkWriteError
from config import MONGO_URI

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

logger = logging.getLogger("mongo")


def run(dataset):
    logger.info(f"🚀 Mongo ingestion started for {dataset}")

    client = MongoClient(MONGO_URI)
    db = client["medical"]
    collection = db["consultations"]

    # Index unique sur consultation_id → garantit l'idempotence
    # (relancer le pipeline ne crée pas de doublons)
    collection.create_index("consultation_id", unique=True)

    file_path = f"{dataset}/consultations.json"

    with open(file_path) as f:
        data = json.load(f)

    if not isinstance(data, list):
        data = [data]

    try:
        result = collection.insert_many(data, ordered=False)
        logger.info(f"{len(result.inserted_ids)} documents inserted")
    except BulkWriteError as e:
        inserted = e.details.get("nInserted", 0)
        duplicates = len(e.details.get("writeErrors", []))
        logger.info(f"{inserted} documents inserted, {duplicates} duplicates skipped")

    client.close()
    logger.info(f"🏁 Mongo done for {dataset}")