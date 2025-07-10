import os

# Backend selection logic
backend = os.environ.get("CIRCLE_SKETCH_DB_BACKEND", "sqlite").lower()

if backend == "mysql":
    from .storage_mysql import MySQLStorage as Storage
else:
    from .storage_sqlite import Storage
