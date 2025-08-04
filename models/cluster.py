# models/cluster.py
from sqlalchemy import Column, Integer, String, Double, ForeignKey
from sqlalchemy.orm import relationship
from .user import Base  # Import Base dari user.py

class Cluster(Base):
    __tablename__ = "cluster"
    
    cluster_id = Column(Integer, primary_key=True, autoincrement=True)
    cluster_ke = Column(Integer)
    rata_penjualan = Column(Double)
    rata_harga = Column(Double)
    produk_dominan = Column(String(100))
    dataset_id = Column(Integer, ForeignKey("dataset.dataset_id", ondelete="CASCADE"))
    
    # Relationships
    dataset = relationship("Dataset", back_populates="clusters")
    hasil_clustering = relationship("HasilClustering", back_populates="cluster")
