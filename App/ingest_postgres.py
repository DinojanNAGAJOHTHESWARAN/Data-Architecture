import pandas as pd
import logging
from psycopg2.extras import execute_values
from config import DATASETS
from database import get_connection

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

logger = logging.getLogger("postgres")

BATCH_SIZE = 5000


def run(dataset):
    logger.info(f"🚀 PostgreSQL ingestion started for {dataset}")

    conn = get_connection()
    cur = conn.cursor()

    # Ordre important : doctors et medications avant patients et prescriptions (FK)
    files = [
        ("doctors", f"{dataset}/doctors.csv"),
        ("patients", f"{dataset}/patients.csv"),
        ("medications", f"{dataset}/medications.csv"),
        ("prescriptions", f"{dataset}/prescriptions.csv"),
    ]

    for table, file in files:
        logger.info(f"Loading {file} → {table}")

        # keep_default_na + where() évite les soucis de NaN envoyés à psycopg2
        df = pd.read_csv(file)
        df = df.where(pd.notnull(df), None)

        logger.info(f"{len(df)} rows found")

        cols = list(df.columns)
        cols_str = ",".join(cols)

        query = f"""
            INSERT INTO {table} ({cols_str})
            VALUES %s
            ON CONFLICT (id) DO NOTHING
        """

        rows = [tuple(row) for row in df.itertuples(index=False, name=None)]

        # Insertion par batch : bien plus rapide que ligne par ligne
        # sur 600 000 / 6 000 000 lignes
        for i in range(0, len(rows), BATCH_SIZE):
            batch = rows[i:i + BATCH_SIZE]
            execute_values(cur, query, batch)
            conn.commit()

        logger.info(f"{table} inserted successfully")

    cur.close()
    conn.close()

    logger.info(f"🏁 PostgreSQL done for {dataset}")