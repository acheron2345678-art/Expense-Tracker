from sqlalchemy import Column,Integer,String,Numeric,Date,DateTime,ForeignKey
from datetime import datetime
from app.database import Base

class SavingsGoal(Base):
    __tablename__="savings_goals"

    id=Column(Integer,primary_key=True,index=True)
    user_id=Column(Integer,ForeignKey("users.id"),nullable=False,index=True)
    name=Column(String(150),nullable=False)
    target_amount=Column(Numeric(12,2),nullable=False)
    target_date=Column(Date,nullable=True)
    description=Column(String(500),nullable=True)
    created_at=Column(DateTime,default=datetime.now,nullable=False)
    updated_at=Column(DateTime,default=datetime.now,onupdate=datetime.now,nullable=False)

    