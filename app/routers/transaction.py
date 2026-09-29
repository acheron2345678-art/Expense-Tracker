from fastapi import APIRouter,Depends,HTTPException,Query
from sqlalchemy import or_
from sqlalchemy.orm import Session
from datetime import date
from typing import Literal
from app.database import get_db
from app.models.transaction import Transaction
from app.models.category import Category
from app.models.user import User

from app.schemas.transaction import CreateTransaction,UpdateTransaction,ResponseTransaction,PaymentMethodType

from app.security import get_current_user

router=APIRouter(
    prefix="/transactions",
    tags=["Transactions"]
)

@router.post("/",response_model=ResponseTransaction)
def create_transaction(
    transaction:CreateTransaction,
    db:Session=Depends(get_db),
    current_user:User=Depends(get_current_user)
):
    category=db.query(Category).filter(Category.id==transaction.category_id,Category.user_id==current_user.id).first()

    if not category:
        raise HTTPException(status_code=404,detail="Category not found")

    new_transaction=Transaction(
        user_id=current_user.id,
        category_id=transaction.category_id,
        type=transaction.type,
        amount=transaction.amount,
        description=transaction.description,
        transaction_date=transaction.transaction_date,
        payment_method=transaction.payment_method,
        merchant=transaction.merchant,
        notes=transaction.notes
    )

    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)
    return new_transaction

@router.get("/",response_model=list[ResponseTransaction])
def get_transactions(
    type:Literal["income","expense"]|None=None,
    category_id:int|None=None,
    payment_method:PaymentMethodType|None=None,
    merchant:str|None=None,
    recurring_only:bool|None=None,
    min_amount:float|None=None,
    max_amount:float|None=None,
    start_date:date|None=None,
    end_date:date|None=None,
    search:str|None=None,
    sort_by:Literal["amount","transaction_date","created_at",]="transaction_date",
    order:Literal["asc","desc"]="desc",
    skip:int=Query(default=0,ge=0),
    limit:int=Query(default=0,ge=1,le=100),
    db:Session=Depends(get_db),
    current_user:User=Depends(get_current_user)
):
    query=db.query(Transaction).filter(Transaction.user_id==current_user.id)
    if type is not None:
        query=query.filter(Transaction.type==type)

    if category_id is not None:
        query=query.filter(Transaction.category_id==category_id)

    if payment_method is not None:
        query=query.filter(Transaction.payment_method==payment_method)

    if merchant is not None:
        query=query.filter(Transaction.merchant.ilike(f"%{merchant}%"))

    if recurring_only is True:
        query=query.filter(Transaction.recurring_transaction_id.is_not(None))

    elif recurring_only is False:
        query=query.filter(Transaction.recurring_transaction_id.is_(None))

    if min_amount is not None:
        query=query.filter(Transaction.amount>=min_amount)

    if max_amount is not None:
        query=query.filter(Transaction.amount<=max_amount)

    if (
        min_amount is not None
        and max_amount is not None
        and min_amount<max_amount
    ):
        raise HTTPException(status_code=400,detail="min amount cannot be greater than the max amount ")

    if start_date is not None:
        query=query.filter(Transaction.transaction_date>=start_date)

    if end_date is not None:
        query=query.filter(Transaction.transaction_date<=end_date)

    if (
        end_date is not None
        and start_date is not None
        and start_date>end_date
    ):
        raise HTTPException(
            status_code=400,detail="start_date cannot be after end_date"
        )

    if search:
        search_pattern=f"%{search}%"
        query=query.filter(
            or_(
                Transaction.description.ilike(
                    search_pattern
                ),
                Transaction.merchant.ilike(
                    search_pattern
                )
            )
        )

    sort_columns={
        "amount":Transaction.amount,
        "transaction_date":Transaction.transaction_date,
        "created_at":Transaction.created_at
    }
    sort_column=sort_columns[sort_by]
    if order=="asc":
        query=query.order_by(sort_column.asc())

    else:
        query=query.order_by(sort_column.desc())

    transactions=query.offset(skip).limit(limit).all()
    return transactions 

    

@router.get("/{transction_id}",response_model=ResponseTransaction)
def get_transaction_by_id(
    transaction_id:int,
    db:Session=Depends(get_db),
    current_user:User=Depends(get_current_user)
):
    transaction=db.query(Transaction).filter(Transaction.id==transaction_id,Transaction.user_id==current_user.id).first()

    if not transaction:
        raise HTTPException(status_code=404,detail="Transaction not Found")

    return transaction


@router.patch("/{transaction_id}",response_model=ResponseTransaction)
def update_transaction(
    transaction_id:int,
    updated_data:UpdateTransaction,
    db:Session=Depends(get_db),
    current_user:User=Depends(get_current_user)
):
    transaction=db.query(Transaction).filter(Transaction.id==transaction_id,Transaction.user_id==current_user.id).first()

    if not transaction:
        raise HTTPException(status_code=404,detail="Transaction not found")

    if updated_data.category_id is not None:
        category=db.query(Category).filter(Category.id==updated_data.category_id,Category.user_id==current_user.id).first()

        if not category:
            raise HTTPException(status_code=404,detail="Category not Found")

    updated_values=updated_data.model_dump(exclude_unset=True)

    for field,value in updated_values.items():
        setattr(transaction,field,value)

    db.commit()
    db.refresh(transaction)
    return transaction


@router.delete("/{transaction_id}",response_model=ResponseTransaction)
def delete_transaction(
    transaction_id:int,
    db:Session=Depends(get_db),
    current_user:User=Depends(get_current_user)
):
    transaction=db.query(Transaction).filter(Transaction.id==transaction_id,Transaction.user_id==current_user.id).first()

    if not transaction:
        raise HTTPException(status_code=404,detail="Transaction not found")

    db.delete(transaction)
    db.commit()
    return {
        "message":"transaction removed successfully"
    }

