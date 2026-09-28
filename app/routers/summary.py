from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.transaction import Transaction
from app.models.category import Category
from app.models.user import User
from app.security import get_current_user

router=APIRouter(
    prefix="/summary",
    tags=["Summary"]
)

def get_summary(
        db:Session=Depends(get_db),
        current_user:User=Depends(get_current_user) 
):
    total_income=db.query(func.sum(Transaction.amount)).filter(Transaction.user_id==current_user.id,Transaction.type=="income").scalar() or 0
    total_expense=db.query(func.sum(Transaction.amount)).filter(Transaction.user_id==current_user.id,Transaction.type=="expense").scalar() or 0
    balance=total_income-total_expense

    return {
        "total_income":total_income,
        "total_expense":total_expense,
        "balance":balance
    }

@router.get("/categories")
def get_category_summary(
    db:Session=Depends(get_db),
    current_user:User=Depends(get_current_user)
):
    results=db.query(
        Category.name,
        func.sum(Transaction.amount).label("total")
    ).join(
        Transaction,Transaction.category_id==Category.id
    ).filter(
        Transaction.user_id==current_user.id
    ).group_by(
        Category.id,
        Category.name
    ).all()