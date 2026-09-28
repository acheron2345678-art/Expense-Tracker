from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy import func 
from sqlalchemy.orm import Session
from app.database import get_db

from app.models.budget import Budget
from app.models.category import Category
from app.models.user import User
from app.models.transaction import Transaction

from app.schemas.budget import CreateBudget,UpdateBudget,ResponseBudget

from app.security import get_current_user

router=APIRouter(prefix="/budgets",tags=["Budgets"])

@router.post(
    "/",
    response_model=ResponseBudget
)
def create_budget(
    budget: CreateBudget,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    category = (
        db.query(Category)
        .filter(
            Category.id == budget.category_id,
            Category.user_id == current_user.id
        )
        .first()
    )

    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )

    existing_budget = (
        db.query(Budget)
        .filter(
            Budget.user_id == current_user.id,
            Budget.category_id == budget.category_id,
            Budget.month == budget.month,
            Budget.year == budget.year
        )
        .first()
    )

    if existing_budget:
        raise HTTPException(
            status_code=400,
            detail="Budget already exists for this category and month"
        )

    new_budget = Budget(
        user_id=current_user.id,
        category_id=budget.category_id,
        amount=budget.amount,
        month=budget.month,
        year=budget.year
    )

    db.add(new_budget)
    db.commit()
    db.refresh(new_budget)

    return new_budget

@router.get("/",response_model=list[ResponseBudget])
def get_budgets(
    db:Session=Depends(get_db),
    current_user:User=Depends(get_current_user)
):
    budgets=db.query(Budget).filter(Budget.user_id==current_user.id).all()

    return budgets

@router.get("/{budget_id}/progress")
def get_budget_progress(
    budget_id:int,
    db:Session=Depends(get_db),
    current_user:User=Depends(get_current_user)
):
    budget=db.query(Budget).filter(Budget.id==budget_id,Budget.user_id==current_user.id).first()

    if not budget:
        raise HTTPException(status_code=404,detail="Budget not found")

    spent=db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id==current_user.id,
        Transaction.category_id==budget.category_id,
        Transaction.type=="expense",
        func.month(Transaction.transaction_date)==budget.month,
        func.year(Transaction.transaction_date)==budget.year
    ).scalar() or 0

    remaining=budget.amount - spent

    percentage_used=(spent/budget.amount)*100
    percentage_used=round(percentage_used,2)

    if percentage_used>=100:
        status="exceeded"

    elif percentage_used>=80:
        status="warning"

    else:
        status="safe"

    return{
        "budget_id":budget.id,
        "category_id":budget.category_id,
        "month":budget.month,
        "year":budget.year,
        "budget_amount":budget.amount,
        "spent":spent,
        "remaining":remaining,
        "percentage_used":percentage_used,
        "status":status
    }

@router.get("/{budget_id}",response_model=ResponseBudget)
def get_budget(
    budget_id:int,
    db:Session=Depends(get_db),
    current_user:User=Depends(get_current_user)
):
    budget=db.query(Budget).filter(Budget.id==budget_id,Budget.user_id==current_user.id).first()

    if not budget:
        raise HTTPException(status_code=404,detail="Budget not Found")

    return budget

@router.patch("/{budget_id}",response_model=ResponseBudget)
def update_budget(
    budget_id:int,
    updated_data:UpdateBudget,
    db:Session=Depends(get_db),
    current_user:User=Depends(get_current_user)
):
    budget=db.query(Budget).filter(Budget.id==budget_id,Budget.user_id==current_user.id).first()

    if not budget:
        raise HTTPException(status_code=404,detail="Budget not found")

    update_values=updated_data.model_dump(exclude_unset=True)

    for field,value in update_values.items():
        setattr(
            budget,
            field,
            value
        )

    new_month=(
        updated_data.month
        if updated_data.month is not None
        else budget.month
    )

    new_year=(
        updated_data.year
        if updated_data.year is not None
        else budget.year
    )

    duplicate=db.query(Budget).filter(
        Budget.user_id==current_user.id,
        Budget.category_id==budget.category_id,
        Budget.month==new_month,
        Budget.year==new_year,
        Budget.id!=budget.id
    ).first()

    if duplicate:
        raise HTTPException(status_code=400,detail="Budget already exists for this category and month")

    db.commit()
    db.refresh(budget)
    return budget

@router.delete("/{budget_id}",response_model=ResponseBudget)
def delete_budget(
    budget_id:int,
    db:Session=Depends(get_db),
    current_user:User=Depends(get_current_user)
):
    budget=db.query(Budget).filter(Budget.id==budget_id,Budget.user_id==current_user.id).first()
    if not budget:
        raise HTTPException(status_code=404,detail="Budget not found")

    db.delete(budget)
    db.commit()
    return {
        "message":"Successfully deleted th Budget"
    }
