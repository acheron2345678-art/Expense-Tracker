from datetime import datetime

from sqlalchemy import Column,Integer,String,Float,Date,DateTime,ForeignKey

from app.database import Base

class Transaction(Base):
    __tablename__="transactions"
    id=Column(Integer,primary_key=True,index=True)
    user_id=Column(Integer,ForeignKey("users.id"),nullable=False,index=True)
    category_id=Column(Integer,ForeignKey("categories.id"),nullable=False,index=True)
    type=Column(String(20),nullable=False)
    amount=Column(Float,nullable=False)
    description=Column(String(255),nullable=False)
    transaction_date=Column(Date,nullable=False)
    created_at=Column(DateTime,default=datetime.now,nullable=False)
    