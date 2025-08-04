# from sqlalchemy import Column, Integer, String, DateTime, Float, Text, ForeignKey
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import relationship
# from datetime import datetime

# Base = declarative_base()

# class Product(Base):
#     __tablename__ = "products"
    
#     product_id = Column(Integer, primary_key=True, index=True)
#     user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
#     nama_produk = Column(String(200), nullable=False)
#     harga = Column(Float, nullable=False)
#     stok = Column(Integer, nullable=False)
#     kategori = Column(String(100))
#     deskripsi = Column(Text)
#     uploaded_at = Column(DateTime, default=datetime.utcnow)
#     updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
#     # Relationship
#     user = relationship("User", back_populates="products")
#     clustering_results = relationship("ClusteringResult", back_populates="product")


# models/produk.py
from sqlalchemy import Column, Integer, String, Double, Date, ForeignKey
from sqlalchemy.orm import relationship
from .user import Base  # Import Base dari user.py

class Produk(Base):
    __tablename__ = "produk"
    
    produk_id = Column(Integer, primary_key=True, autoincrement=True)
    nama_produk = Column(String(100))
    kategori_produk = Column(String(100))
    jumlah_terjual = Column(Integer)
    harga = Column(Double)
    tanggal_transaksi = Column(Date)
    cluster_ke = Column(Integer)
    kategori_ABC = Column(String(1))
    dataset_id = Column(Integer, ForeignKey("dataset.dataset_id", ondelete="CASCADE"))
    
    # Relationships
    dataset = relationship("Dataset", back_populates="produks")
    hasil_clustering = relationship("HasilClustering", back_populates="produk")

# ===============================================