# models/hasil_clustering.py
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

# Import Base dari user.py agar konsisten
from .user import Base

class HasilClustering(Base):
    __tablename__ = "hasilclustering"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    produk_id = Column(Integer, ForeignKey("produk.produk_id", ondelete="CASCADE"))
    cluster_id = Column(Integer, ForeignKey("cluster.cluster_id", ondelete="CASCADE"))
    
    # Relationships
    produk = relationship("Produk", back_populates="hasil_clustering")
    cluster = relationship("Cluster", back_populates="hasil_clustering")