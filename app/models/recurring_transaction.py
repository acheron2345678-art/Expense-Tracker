from datetime import datetime

from sqlalchemy import Column,String,Integer,Float,Date,DateTime,Boolean,ForeignKey

from app.database import Base

class RecurringTransaction(Base):
    __tablename__="recurring_transactions"

    id=Column(Integer,primary_key=True,index=True)
    user_id=Column(Integer,ForeignKey("users.id"),nullable=False,index=True)
    category_id=Column(Integer,ForeignKey("categories.id"),nullable=False,index=True)
    type=Column(String(20),nullable=False)
    amount=Column(Float,nullable=False)
    description=Column(String(255),nullable=False)
    frequency=Column(String(20),nullable=False)
    start_date=Column(Date,nullable=False)
    next_run_date=Column(Date,nullable=False,index=True)
    end_date=Column(Date,nullable=False)
    created_at=Column(DateTime,default=datetime.now,nullable=False)
    active=Column(Boolean,default=True,nullable=False)