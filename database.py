# backend/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

MYSQL_USER = "root"
MYSQL_PASSWORD = "riyani_100205"
MYSQL_HOST = "localhost"
MYSQL_DB = "db_segmentasi_produk"

DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# =========================================================
# === BAGIAN YANG HILANG SEBELUMNYA ADA DI SINI ===
# =========================================================
def get_db():
    """
    Fungsi ini akan membuat dan menyediakan sesi database untuk setiap
    permintaan API, dan akan selalu memastikan sesi ditutup setelahnya.
    """
    db = SessionLocal()
    try:
        yield db  # 'yield' akan memberikan sesi ke endpoint
    finally:
        db.close() # 'finally' memastikan ini selalu dijalankan, bahkan jika ada error
# =========================================================