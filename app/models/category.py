from datetime import datetime
from sqlalchemy import Column,Integer,String,DateTime,ForeignKey

from app.database import Base

class Category(Base):
    __tablename__="categories"

    id=Column(Integer,primary_key=True,index=True)
    name=Column(String(100),nullable=False)
    user_id=Column(Integer,ForeignKey("users.id"),nullable=False,index=True)
    created_at=Column(DateTime,default=datetime.now,nullable=False)

    