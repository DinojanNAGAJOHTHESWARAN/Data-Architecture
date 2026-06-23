import psycopg2
import logging
from config import POSTGRES_CONFIG

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

logger = logging.getLogger("database")


def get_connection():
    logger.info("Connecting to PostgreSQL...")
    return psycopg2.connect(**POSTGRES_CONFIG)


def create_tables():
    logger.info("Creating tables...")

    conn = get_connection()
    cur = conn.cursor()

    # Ordre important : les tables référencées (doctors, medications)
    # doivent exister avant les tables qui les référencent (patients, prescriptions)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS doctors (
            id TEXT PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            specialty TEXT,
            hospital TEXT,
            phone TEXT
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id TEXT PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            dob DATE,
            gender TEXT,
            blood_type TEXT,
            doctor_id TEXT REFERENCES doctors(id)
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS medications (
            id TEXT PRIMARY KEY,
            name TEXT,
            dosage TEXT,
            unit TEXT,
            category TEXT
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS prescriptions (
            id TEXT PRIMARY KEY,
            consultation_id TEXT,
            medication_id TEXT REFERENCES medications(id),
            date DATE,
            duration_days INT
        );
    """)

    # Index sur les FK pour accélérer les jointures à grande volumétrie
    cur.execute("CREATE INDEX IF NOT EXISTS idx_patients_doctor_id ON patients(doctor_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_prescriptions_medication_id ON prescriptions(medication_id);")

    conn.commit()
    cur.close()
    conn.close()

    logger.info("Tables created successfully")