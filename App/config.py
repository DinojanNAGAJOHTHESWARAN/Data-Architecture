import os

POSTGRES_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "postgres"),
    "database": os.getenv("POSTGRES_DB", "medical_db"),
    "user": os.getenv("POSTGRES_USER", "dino"),
    "password": os.getenv("POSTGRES_PASSWORD", "kami"),
    "port": os.getenv("POSTGRES_PORT", 5432),
}

MONGO_URI = os.getenv("MONGO_URI", "mongodb://dino:kami@mongo:27017/")

DATASETS = ["/data_small", "/data_medium", "/data_large"]