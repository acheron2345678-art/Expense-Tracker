from datetime import datetime

from sqlalchemy import Column,Integer,String,Float,Date,DateTime,ForeignKey,Numeric

from app.database import Base

class Transaction(Base):
    __tablename__="transactions"
    id=Column(Integer,primary_key=True,index=True)
    user_id=Column(Integer,ForeignKey("users.id"),nullable=False,index=True)
    category_id=Column(Integer,ForeignKey("categories.id"),nullable=False,index=True)
    type=Column(String(20),nullable=False)
    amount=Column(Numeric(12,2),nullable=False)
    description=Column(String(255),nullable=False)
    transaction_date=Column(Date,nullable=False)
    payment_method=Column(String(30),nullable=True)
    merchant=Column(String(150),nullable=True)
    notes=Column(String(500),nullable=True)
    recurring_transaction_id=Column(Integer,ForeignKey("recurring_transactions.id",ondelete="SET NULL"),nullable=True,index=True)
    created_at=Column(DateTime,default=datetime.now,nullable=False)