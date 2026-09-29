from datetime import date

from dateutil.relativedelta import relativedelta

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.models.recurring_transaction import RecurringTransaction


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
    db: Session,
    user_id: int | None = None,
    as_of: date | None = None
):

    today = as_of or date.today()

    query = (
        db.query(RecurringTransaction)
        .filter(
            RecurringTransaction.active.is_(True),
            RecurringTransaction.next_run_date <= today
        )
    )

    # If called manually by a logged-in user,
    # process only that user's recurring transactions.
    #
    # If user_id is None, such as when called by
    # the scheduler, process all users.
    if user_id is not None:

        query = query.filter(
            RecurringTransaction.user_id == user_id
        )

    recurring_items = (
        query
        .order_by(
            RecurringTransaction.next_run_date.asc()
        )
        .all()
    )

    created_count = 0
    rules_processed = 0

    try:

        for recurring in recurring_items:

            rules_processed += 1

            # Keep generating transactions until
            # this recurring rule is caught up.
            while (
                recurring.active
                and recurring.next_run_date <= today
            ):

                # Stop if the recurring rule
                # has passed its end date.
                if (
                    recurring.end_date is not None
                    and recurring.next_run_date
                    > recurring.end_date
                ):

                    recurring.active = False
                    break

                # Store the current due date before
                # moving next_run_date forward.
                run_date = recurring.next_run_date

                new_transaction = Transaction(
                    user_id=recurring.user_id,
                    category_id=recurring.category_id,
                    type=recurring.type,
                    amount=recurring.amount,
                    description=recurring.description,

                    payment_method=recurring.payment_method,
                    merchant=recurring.merchant,
                    notes=recurring.notes,

                    transaction_date=run_date,

                    recurring_transaction_id=recurring.id
                )

                db.add(new_transaction)

                created_count += 1

                # Record when this recurring rule
                # most recently generated a transaction.
                recurring.last_run_date = run_date

                # Move forward exactly ONE occurrence.
                recurring.next_run_date = (
                    calculate_next_run_date(
                        run_date,
                        recurring.frequency
                    )
                )

                # If the next occurrence would be
                # after the configured end date,
                # automatically deactivate the rule.
                if (
                    recurring.end_date is not None
                    and recurring.next_run_date
                    > recurring.end_date
                ):

                    recurring.active = False

        db.commit()

    except SQLAlchemyError:

        db.rollback()
        raise

    except Exception:

        db.rollback()
        raise

    return {
        "transactions_created": created_count,
        "rules_processed": rules_processed
    }