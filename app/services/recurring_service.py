from fastapi import Depends,HTTPException
from sqlalchemy.orm import Session

from dateutil.relativedelta import relativedelta

from app.database import get_db

from app.models.user import User
from app.models.category import Category
from app.models.transaction import Transaction
from app.models.recurring_transaction import RecurringTransaction
from app.security import  get_current_user
from datetime import date


def calculate_next_run_date(
    current_date: date,
    frequency: str
) -> date:

    if frequency == "daily":
        return current_date + relativedelta(days=1)

    if frequency == "weekly":
        return current_date + relativedelta(weeks=1)

    if frequency == "monthly":
        return current_date + relativedelta(months=1)

    if frequency == "yearly":
        return current_date + relativedelta(years=1)

    raise ValueError(
        f"Unsupported recurring frequency: {frequency}"
    )

def process_due_recurring_transactions(
        db:Session,
        user_id:int|None=None,
        as_of:date|None=None
):
    today=as_of or date.today()

    query=db.query(RecurringTransaction).filter(RecurringTransaction.active.is_(True),RecurringTransaction.next_run_date<=today)

    if user_id is not None:
        query=query.filter(RecurringTransaction.user_id==user_id)

    recurring_items=query.order_by(RecurringTransaction.next_run_date.asc()).all()

    created_count=0
    rules_processed=0

    try:
        for recurring in recurring_items:
            rules_processed+=1

            while(recurring.active and recurring.next_run_date<=today):
                if recurring.end_date is not None and recurring.next_run_date>recurring.end_date:
                    recurring.active=False
                    break

                new_transaction=Transaction(
                    user_id=recurring.user_id,
                    category_id=recurring.category_id,
                    type=recurring.type,
                    amount=recurring.amount,
                    description=recurring.description,
                    transaction_date=recurring.next_run_date
                )
                db.add(new_transaction)
                created_count+=1

                recurring.next_run_date=calculate_next_run_date(recurring.next_run_date,recurring.frequency)
                if recurring.end_date is not None and recurring.next_run_date>recurring.end_date:
                    recurring.active=False

        db.commit()

    except Exception:
        db.rollback()
        raise

    return{
        "transactions_created":created_count,
        "rules_processed":rules_processed
    }