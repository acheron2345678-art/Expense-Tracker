from datetime import datetime
from sqlalchemy import Column,Integer,Float,DateTime,ForeignKey
from app.database import Base

class Budget(Base):
    __tablename__="budgets"
    id=Column(Integer,primary_key=True,index=True)
    user_id=Column(Integer,ForeignKey("users.id"),nullable=False,index=True)
    category_id=Column(Integer,ForeignKey("categories.id"),nullable=False,index=True)
    amount=Column(Float,nullable=False)
    month=Column(Integer,nullable=False)
    year=Column(Integer,nullable=False)
    created_at=Column(DateTime,default=datetime.now,nullable=False)
        
