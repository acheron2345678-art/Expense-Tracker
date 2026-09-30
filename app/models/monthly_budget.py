from datetime import datetime

from sqlalchemy import Column,Numeric,Integer,DateTime,ForeignKey,UniqueConstraint

from app.database import Base

class MonthlyBudget(Base):
    __tablename__="monthly_budgets"
    __table_args__=(UniqueConstraint(
        "user_id",
        "month",
        "year",
        name="uq_monthly_budget_user_month_year"
    ),
    )
    id=Column(Integer,primary_key=True,index=True)
    user_id=Column(Integer,ForeignKey("users.id"),nullable=False,index=True)
    amount=Column(Numeric(12,2),nullable=False)
    month=Column(Integer,nullable=False)
    year=Column(Integer,nullable=False)
    created_at=Column(DateTime,default=datetime.now,nullable=False)
    updated_at=Column(DateTime,default=datetime.now,onupdate=datetime.now,nullable=False)
    