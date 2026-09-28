from datetime import datetime

from sqlalchemy import String,DateTime,Column,Integer


from app.database import Base

class User(Base):
    __tablename__="users"
    id=Column(Integer,primary_key=True,index=True)
    name=Column(String(100),nullable=False)
    email=Column(String(255),nullable=False,unique=True,index=True)
    hashed_password=Column(String(255),nullable=False)
    created_at=Column(DateTime,default=datetime.now,nullable=False)
