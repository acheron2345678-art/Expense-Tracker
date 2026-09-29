from fastapi import APIRouter,HTTPException,Depends,Query
from sqlalchemy.orm import Session
from sqlalchemy import func,case

from app.database import get_db
from app.models.transaction import Transaction
from app.models.user import User
from app.models.category import Category
from app.security import get_current_user

router=APIRouter(
    prefix="/analytics",
    tags=["Analytics"]
)

@router.get("/monthly-trend")
def monthly_trend(
    year:int =Query(ge=2000,le=2100),
    db:Session=Depends(get_db),
    current_user:User=Depends(get_current_user)
):
    results = (
        db.query(
            func.month(
                Transaction.transaction_date
            ).label("month"),

            func.sum(
                case(
                    (
                        Transaction.type == "income",
                        Transaction.amount
                    ),
                    else_=0
                )
            ).label("income"),

            func.sum(
                case(
                    (
                        Transaction.type == "expense",
                        Transaction.amount
                    ),
                    else_=0
                )
            ).label("expense")
        )
        .filter(
            Transaction.user_id == current_user.id,
            func.year(
                Transaction.transaction_date
            ) == year
        )
        .group_by(
            func.month(
                Transaction.transaction_date
            )
        )
        .order_by(
            func.month(
                Transaction.transaction_date
            )
        )
        .all()
    )

    return[
        {
            "month":row.month,
            "income":row.income or 0,
            "expense":row.expense or 0
        }
        for row in results
    ]

@router.get("/top-categories")
def top_categories(
    year:int |None=Query(
        default=None,
        ge=2000,
        le=2100
    ),
    month:int |None=Query(
        default=None,
        ge=1,
        le=12
    ),
    limit:int=Query(
        default=5,
        ge=1,
        le=20
    ),
    db:Session=Depends(get_db),
    current_user:User=Depends(get_current_user)
):
    query=db.query(
        Category.id.label("category_id"),
        Category.name.label("category"),
        func.sum(
            Transaction.amount
        ).label("total")
    ).join(
        Transaction,
        Transaction.category_id==Category.id
    ).filter(
        Transaction.user_id==current_user.id,
        Transaction.type=="expense"
    )

    if year is not None:
        query=query.filter(
            func.year(
                Transaction.transaction_date
            )==year
        )

    if month is not None:
        query=query.filter(
            func.month(
                Transaction.transaction_date
            )==month
        )

    results=query.group_by(
        Category.id,
        Category.name
    ).order_by(
        func.sum(
            Transaction.amount
        ).desc()
    ).limit(limit).all()

    return[
        {
            "category_id":row.category_id,
            "category":row.category,
            "total":row.total
        }
        for row in results
    ]

@router.get("/dashboard")
def analytics_dashboard(
    year:int=Query(ge=2000,le=2100),
    month:int=Query(ge=1,le=12),
    db:Session=Depends(get_db),
    current_user:User=Depends(get_current_user)
):
    base_query=db.query(Transaction).filter(Transaction.user_id==current_user.id,func.year(Transaction.transaction_date)==year,func.month(Transaction.transaction_date)==month)

    total_income=db.query(
        func.sum(
            Transaction.amount
        )
    ).filter(
        Transaction.user_id==current_user.id,
        Transaction.type=="income",
        func.year(Transaction.transaction_date)==year,
        func.month(Transaction.transaction_date)==month,
    ).scalar() or 0

    total_expense=db.query(
        func.sum(
            Transaction.amount
        )
    ).filter(
        Transaction.user_id==current_user.id,
        Transaction.type=="expense",
        func.year(Transaction.transaction_date)==year,
        func.month(Transaction.transaction_date)==month,
    ).scalar() or 0

    balance=total_income-total_expense

    transaction_count=base_query.count()

    expense_count=(
        db.query(Transaction)
        .filter(
            Transaction.user_id==current_user.id,
            Transaction.type=="expense",
            func.year(
                Transaction.transaction_date
            )==year,
            func.month(
                Transaction.transaction_date
            )==month
        ).count()
    )

    income_count=(
        db.query(Transaction)
        .filter(
            Transaction.user_id==current_user.id,
            Transaction.type=="income",
            func.year(
                Transaction.transaction_date
            )==year,
            func.month(
                Transaction.transaction_date
            )==month
        ).count()
    )

    average_expense=(
        db.query(
            func.avg(
                Transaction.amount
            )
        ).filter(
            Transaction.user_id==current_user.id,
            Transaction.type=="expense",
            func.year(
                Transaction.transaction_date
            )==year,
            func.month(
                Transaction.transaction_date
            )==month
        ).scalar() or 0
    )

    average_expense=round(float(average_expense),2)

    largest_expense=db.query(
        func.max(Transaction.amount)
    ).filter(
        Transaction.user_id==current_user.id,
        Transaction.type=="expense",
        func.year(
            Transaction.transaction_date
        )==month
    ).scalar() or 0

    return {
        "year":year,
        "month":month,
        "total_income":total_income,
        "total_expense":total_expense,
        "balance":balance,
        "transaction_count":transaction_count,
        "expense_count":expense_count,
        "income_count":income_count,
        "average_expense":average_expense,
        "largest_expense":largest_expense
    }