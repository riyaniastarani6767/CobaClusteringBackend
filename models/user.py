from sqlalchemy import Column, Integer, String
from database import Base

class User(Base):
    __tablename__ = "user"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    nama = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)



# models/user.py
# from sqlalchemy import Column, Integer, String, Text
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import relationship

# Base = declarative_base()

# class User(Base):
#     __tablename__ = "user"
    
#     user_id = Column(Integer, primary_key=True, autoincrement=True)
#     nama = Column(String(100))
#     email = Column(String(100), unique=True)
#     password_hash = Column(Text)
    
#     # Relationships
#     datasets = relationship("Dataset", back_populates="user")

# ===============================================

# models/user.py
# from sqlalchemy import Column, Integer, String, Text
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import relationship

# Base = declarative_base()

# class User(Base):
#     __tablename__ = "user"
    
#     user_id = Column(Integer, primary_key=True, autoincrement=True)
#     nama = Column(String(100))
#     email = Column(String(100), unique=True)
#     password_hash = Column(Text)
    
#     # Relationships
#     datasets = relationship("Dataset", back_populates="user")
