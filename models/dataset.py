# models/dataset.py
from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .user import Base  # Import Base dari user.py

class Dataset(Base):
    __tablename__ = "dataset"
    
    dataset_id = Column(Integer, primary_key=True, autoincrement=True)
    nama_dataset = Column(String(100))
    tanggal_upload = Column(TIMESTAMP, server_default=func.current_timestamp())
    user_id = Column(Integer, ForeignKey("user.user_id", ondelete="CASCADE"))
    
    # Relationships
    user = relationship("User", back_populates="datasets")
    produks = relationship("Produk", back_populates="dataset")
    clusters = relationship("Cluster", back_populates="dataset")
