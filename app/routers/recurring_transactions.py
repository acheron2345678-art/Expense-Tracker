from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session

from dateutil.relativedelta import relativedelta

from app.database import get_db

from app.models.user import User
from app.models.category import Category
from app.models.transaction import Transaction
from app.models.recurring_transaction import RecurringTransaction

from app.schemas.recurring_transactions import UpdateRecurringTransaction,CreateRecurringTransaction,ResponseRecurringTransaction
from app.services.recurring_service import calculate_next_run_date,process_due_recurring_transactions
from app.security import  get_current_user
from datetime import date
router=APIRouter(
    prefix="/recurring-transactions",
    tags=["Recurring Transactions"]
)

@router.post("/process")
def process_my_recurring_transactions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    result = process_due_recurring_transactions(
        db=db,
        user_id=current_user.id
    )

    return {
        "message": "Recurring transactions processed",
        **result
    }

@router.post("/",response_model=ResponseRecurringTransaction)
def create_recurring_transaction(
    recurring:CreateRecurringTransaction,
    db:Session=Depends(get_db),
    current_user:User=Depends(get_current_user)
):
    category=db.query(Category).filter(Category.id==recurring.category_id,Category.user_id==current_user.id).first()

    if not category:
        raise HTTPException(status_code=404,detail="Category not Found")

    new_recurring=RecurringTransaction(
        user_id=current_user.id,
        category_id=recurring.category_id,
        typr=recurring.type,
        amount=recurring.amount,
        description=recurring.description,
        frequency=recurring.frequency,
        start_date=recurring.start_date,
        next_run_date=recurring.start_date,
        end_date=recurring.end_date,
        active=True
    )

    db.add(new_recurring)
    db.commit()
    db.refresh(new_recurring)

    return new_recurring

@router.get("/",response_model=list[ResponseRecurringTransaction])
def get_recurring_transactions(
    db:Session=Depends(get_db),
    current_user:User=Depends(get_current_user)
):
    return(db.query(RecurringTransaction).filter(RecurringTransaction.user_id==current_user.id).all())

@router.get("/{recurring_id}",response_model=ResponseRecurringTransaction)
def get_recurring_transaction(
    recurring_id:int,
    db:Session=Depends(get_db),
    current_user:User=Depends(get_current_user)
):
    recurring=db.query(RecurringTransaction).filter(RecurringTransaction.id==recurring_id,RecurringTransaction.user_id==current_user.id).first()

    if not recurring:
        raise HTTPException(status_code=404,detail="Recurring transaction not found")

    return recurring


@router.get("/{recurring_id}",response_model=ResponseRecurringTransaction)
def update_recurring_transaction(
    recurring_id:int,
    updated_data:UpdateRecurringTransaction,
    db:Session=Depends(get_db),
    current_user:User=Depends(get_current_user)
):
    recurring=db.query(RecurringTransaction).filter(RecurringTransaction.id==recurring_id,RecurringTransaction.user_id==current_user.id).first()

    if not recurring:
        raise HTTPException(status_code=404,detail="Recurring Transaction not found")

    if updated_data.category_id is not None:
        category=db.query(Category).filter(Category.id==updated_data.category_id,Category.user_id==current_user.id).first()

        if not category:
            raise HTTPException(status_code=404,detail="Category not found")

    update_values=updated_data.model_dump(exclude_unset=True)
    for field,value in update_values.items():
        setattr(recurring,field,value)

    db.commit()
    db.refresh(recurring)
    return recurring


@router.delete("/{recurring_id}",response_model=ResponseRecurringTransaction)
def delete_recurring_transaction(
    recurring_id:int,
    db:Session=Depends(get_db),
    current_user:User=Depends(get_current_user)
):
    recurring=db.query(RecurringTransaction).filter(RecurringTransaction.id==recurring_id,RecurringTransaction.user_id==current_user.id).first()
    if not recurring:
        raise HTTPException(status_code=404,detail="Recurring Transaction not found")

    db.delete(recurring)
    db.commit()
    return {
        "message":"Recurring Transaction deleted Successfully"
    }

