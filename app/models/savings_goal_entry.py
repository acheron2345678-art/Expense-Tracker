from datetime import datetime
from sqlalchemy import Column,Numeric,Integer,DateTime,ForeignKey,String

from app.database import Base

class SavingsGoalEntry(Base):
    __tablename__="savings_goal_entries"

    id=Column(Integer,primary_key=True,index=True)
    goal_id=Column(Integer,ForeignKey("savings_goals.id",ondelete="CASCADE"),nullable=False,index=True)
    user_id=Column(Integer,ForeignKey("users.id"),nullable=False,index=True)
    entry_type=Column(String(20),nullable=False)
    amount=Column(Numeric(12,2),nullable=False)
    note=Column(String(255),nullable=True)
    created_at=Column(DateTime,default=datetime.now,nullable=False)
    