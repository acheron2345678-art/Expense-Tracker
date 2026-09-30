from fastapi import APIRouter,Depends,HTTPException,Query
from sqlalchemy import func 
from sqlalchemy.orm import Session
from app.database import get_db
from decimal import Decimal
from datetime import date
from dateutil.relativedelta import relativedelta

from app.models.budget import Budget
from app.models.category import Category
from app.models.user import User
from app.models.transaction import Transaction
from app.models.monthly_budget import MonthlyBudget

from app.schemas.budget import CreateBudget,UpdateBudget,ResponseBudget,MonthlyBudgetResponse,MonthlyBudgetSet

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

@router.put("/monthly",response_model=MonthlyBudgetResponse)
def set_monthly_budget(
    budget_data:MonthlyBudgetSet,
    db:Session=Depends(get_db),
    current_user:User=Depends(get_current_user)
):
    monthly_budget=db.query(
        MonthlyBudget
        ).filter(
            MonthlyBudget.user_id==current_user.id,
            MonthlyBudget.month==budget_data.month,
            MonthlyBudget.year==budget_data.year
        ).first()

    if monthly_budget:
        monthly_budget.amount=budget_data.amount

    else:
        monthly_budget=MonthlyBudget(
            user_id=current_user.id,
            amount=budget_data.amount,
            month=budget_data.month,
            year=budget_data.year
        )

        db.add(monthly_budget)

    try:
        db.commit()
        db.refresh(monthly_budget)

    except Exception:
        db.rollback()
        raise

    return monthly_budget

@router.get("/monthly",response_model=MonthlyBudgetResponse)
def get_monthly_budget(
    month:int=Query(...,ge=1,le=12),
    year:int=Query(...,ge=2000,le=2100),
    db:Session=Depends(get_db),
    current_user:User=Depends(get_current_user)
):
    monthly_budget=db.query(
        MonthlyBudget
        ).filter(
            MonthlyBudget.user_id==current_user.id,
            MonthlyBudget.month==month,
            MonthlyBudget.year==year
        ).first()

    if not monthly_budget:
        raise HTTPException(status_code=404,detail="Monthly Budget not found")
    return monthly_budget

@router.delete("/monthly")
def delete_monthly_budget(
    month:int=Query(...,ge=1,le=12),
    year:int=Query(...,ge=2000,le=2100),
    db:Session=Depends(get_db),
    current_user:User=Depends(get_current_user)
):
    monthly_budget=db.query(
        MonthlyBudget
    ).filter(
        MonthlyBudget.user_id==current_user.id,
        MonthlyBudget.month==month,
        MonthlyBudget.year==year
    ).first()

    if not monthly_budget:
        raise HTTPException(status_code=404,detail="Monthly Budget not found")

    try:
        db.delete(monthly_budget)
        db.commit()

    except Exception:
        db.rollback()
        raise

    return {"message":"Monthly Budget deleted"}

@router.get("/overview")
def get_budget_overview(
    month:int=Query(...,ge=1,le=12),
    year:int=Query(...,ge=2000,le=2100),
    db:Session=Depends(get_db),
    current_user:User=Depends(get_current_user)
):
    zero=Decimal("0.00")
    start_date=date(year,month,1)
    end_date=start_date + relativedelta(months=1)
    monthly_budget=db.query(
        MonthlyBudget
    ).filter(
        MonthlyBudget.user_id==current_user.id,
        MonthlyBudget.month==month,
        MonthlyBudget.year==year
    ).first()

    category_budgets=db.query(
        Budget,Category.name
    ).join(
        Category,
        Category.id==Budget.category_id
    ).filter(
        Budget.user_id==current_user.id,
        Budget.month==month,
        Budget.year==year
    ).order_by(Category.name.asc()).all()

    spending_rows=db.query(
        Transaction.category_id,
        func.sum(Transaction.amount).label("spent")
    ).filter(
        Transaction.user_id==current_user.id,
        Transaction.type=="expense",
        Transaction.transaction_date>=start_date,
        Transaction.transaction_date<end_date
    ).goup_by(
        Transaction.category_id
    ).all()

    spending_map={
        row.category_id:row.spent or zero
        for row in spending_rows
    }

    total_spent=sum(spending_map.values(),zero)
    category_budget_total=zero
    categories=[]

    for budget,category_name in category_budgets:
        budget_amount=budget.amount

        spent=spending_map.get(budget.category_id,zero)
        remaining=budget_amount-spent

        if budget_amount>0:
            percentage_used=(spent/budget_amount)*Decimal("100")

        else:
            percentage_used=zero

        percentage_used=percentage_used.quantize(Decimal("0.01"))

        if percentage_used >=Decimal("100"):
            status="exceeded"

        elif percentage_used >=Decimal("80"):
            status="warning"

        else:
            status="safe"

        category_budget_total+=budget_amount

        categories.append(
            {
                "budget_id":budget.id,
                "category_id":budget.category_id,
                "category_name":category_name,
                "budget":budget_amount,
                "spent":spent,
                "remaining":remaining,
                "percentage_used":percentage_used,
                "status":status
            }
        )

    overall_budget_amount=None
    overall_remaining=None
    overall_percentage=None
    overall_status=None

    if monthly_budget:
        overall_budget_amount=monthly_budget.amount

        overall_remaining=overall_budget_amount-total_spent

        overall_percentage=(total_spent/overall_budget_amount*Decimal("100")).quantize(Decimal("0.01"))

        if overall_percentage>=Decimal("100"):
            overall_status="exceeded"

        elif overall_percentage>=Decimal("80"):
            overall_status="warning"

        else:
            overall_status="safe"


    return{
        "month":month,
        "year":year,
        "overall_budget":overall_budget_amount,
        "category_budget_total":category_budget_total,
        "total_spent":total_spent,
        "remaining":overall_remaining,
        "percentage_used":overall_percentage,
        "status":overall_status,
        "categories":categories
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
