from decimal import Decimal

from fastapi import APIRouter,Depends,HTTPException

from sqlalchemy import func
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.savings_goal_entry import SavingsGoalEntry
from app.models.savings_goal import SavingsGoal

from app.schemas.savings_goal import SavingsGoalCreate,SavingsGoalEntryCreate,SavingsGoalEntryResponse,SavingsGoalResponse,SavingsGoalUpdate
from app.security import get_current_user

router=APIRouter(prefix="/savings-goals",tags=["Savings Goal"])


def calculate_goal_balance(
        db:Session,
        goal_id:int,
        user_id:int,
)->Decimal:
    contributions=db.query(
        func.sum(SavingsGoalEntry.amount)
    ).filter(
        SavingsGoalEntry.goal_id==goal_id,
        SavingsGoalEntry.user_id==user_id,
        SavingsGoalEntry.entry_type=="contribution"
    ).scalar() or Decimal("0.00")

    withdrawals=db.query(
        func.sum(SavingsGoalEntry.amount)
    ).filter(
        SavingsGoalEntry.goal_id==goal_id,
        SavingsGoalEntry.user_id==user_id,
        SavingsGoalEntry.entry_type=="withdrawal"
    ).scalar() or Decimal("0.00")

    return contributions - withdrawals

@router.post("/",response_model=SavingsGoalEntryResponse)
def create_savings_goal(
    goal_data:SavingsGoalCreate,
    db:Session=Depends(get_db),
    current_user:User=Depends(get_current_user)
):
    goal=SavingsGoal(
        user_id=current_user.id,
        name=goal_data.name,
        target_amount=goal_data.target_amount,
        target_date=goal_data.target_date,
        description=goal_data.description
    )

    try:
        db.add(goal)
        db.commit()
        db.refresh(goal)

    except Exception:
        db.rollback()
        raise

    return goal

@router.get("/")
def get_savings_goals(
    db:Session=Depends(get_db),
    current_user:User=Depends(get_current_user)
):
    goals=db.query(
        SavingsGoal
    ).filter(
        SavingsGoal.user_id==current_user.id
    ).order_by(
        SavingsGoal.created_at.desc()
    ).all()

    result=[]

    for goal in goals:
        saved = calculate_goal_balance(
            db,
            goal.id,
            current_user.id
        )

        remaining=goal.target_amount-saved
        if remaining <Decimal("0.00"):
            remaining-Decimal("0.00")

        percentage=saved/goal.target_amount*Decimal("100")

        percentage=percentage.quantize(Decimal("0.01"))

        if saved>=goal.target_amount:
            status="completed"

        else:
            status="active"

        result.append(
            {
                "id":goal.id,
                "name":goal.name,
                "target_amount":saved,
                "remaining_amount":remaining,
                "percentage":percentage,
                "status":status,
                "target_date":goal.target_date,
                "description":goal.description,
                "created_at":goal.created_at
            }
        )

    return result

@router.get("/,{goal_id}")
def get_savings_goal(
    goal_id:int,
    db:Session=Depends(get_db),
    current_user:User=Depends(get_current_user)
):
    goal=db.query(
        SavingsGoal
    ).filter(
        SavingsGoal.id==goal_id,
        SavingsGoal.user_id==current_user.id
    ).first()

    if not goal:
        raise HTTPException(status_code=404,detail="Savings goal not found")

    saved=calculate_goal_balance(
        db,
        goal.id,
        current_user.id
    )

    remaining=goal.target_amount-saved

    if remaining < Decimal("0.00"):
        remaining=Decimal("0.00")

    percentage=(saved/goal.target_amount*Decimal("0.01"))

    return {
        "id":goal.id,
        "name":goal.name,
        "target_amount":goal.target_amount,
        "saved_amount":saved,
        "remaining_amount":remaining,
        "percentage":percentage,
        "status":(
            "completed"
            if saved >= goal.target_amount
            else "active"
        ),
        "target_date":goal.target_date,
        "description":goal.description,
        "created_at":goal.created_at,
        "updated_at":goal.updated_at
    }

@router.post("/{goal_id}/contribute",response_model=SavingsGoalEntryResponse)
def contribute_to_goal(
    goal_id:int,
    entry_data:SavingsGoalEntryCreate,
    db:Session=Depends(get_db),
    current_user:User=Depends(get_current_user)
):
    goal=db.query(
        SavingsGoal
    ).filter(
        SavingsGoal.id==goal_id,
        SavingsGoal.user_id==current_user.id
    ).first()

    if not goal:
        raise HTTPException(status_code=404,detail="Savings goal not found")

    entry=SavingsGoalEntry(
        goal_id=goal.id,
        user_id=current_user.id,
        entry_type="contribution",
        amount=entry_data.amount,
        note=entry_data.note
    )

    try:
        db.add(entry)
        db.commit()
        db.refresh(entry)

    except Exception:
        db.rollback()
        raise

    return entry

@router.post("/{goal_id}/withdraw",response_model=SavingsGoalEntryResponse)
def withdraw_from_goal(
    goal_id:int,
    entry_data:SavingsGoalEntryCreate,
    db:Session=Depends(get_db),
    current_user:User=Depends(get_current_user)
):
    goal=db.query(
        SavingsGoal
    ).filter(
        SavingsGoal.id==goal_id,
        SavingsGoal.user_id==current_user.id
    ).first()

    if not goal:
        raise HTTPException(status_code=404,detail="Savings Goal not found")

    current_balance=calculate_goal_balance(
        db,
        goal.id,
        current_user.id
    )

    if entry_data>current_balance:
        raise HTTPException(status_code=400,detail="Withdrawal excceds current savings")

    entry=SavingsGoalEntry(
        goal_id=goal.id,
        user_id=current_user.id,
        entry_tpe="withdrawal",
        amount=entry.amount,
        note=entry_data.note
    )

    try:
        db.add(entry)
        db.commit()
        db.refresh(entry)

    except Exception:
        db.rollback()
        raise
    return entry

@router.get("/{goal_id}/history",response_model=list[SavingsGoalEntryResponse])
def get_goal_history(
    goal_id:int,
    db:Session=Depends(get_db),
    current_user:User=Depends(get_current_user)
):
    goal=db.query(
        SavingsGoal
        ).filter(
            SavingsGoal.id==goal_id,
            SavingsGoal.user_id==current_user.id
        ).first()

    if not goal:
        raise HTTPException(status_code=404,detail="Savings goal not found")

    return(
        db.query(
            SavingsGoal
            ).filter(
                SavingsGoal.id==goal_id,
                SavingsGoal.user_id==current_user.id,
            ).order_by(
                SavingsGoalEntry.created_at.desc()
            ).all()
    )

@router.patch("/{goal_id}",response_model=SavingsGoalEntryResponse)
def update_savings_goal(
    goal_id:int,
    updated_data:SavingsGoalUpdate,
    db:Session=Depends(get_db),
    current_user:User=Depends(get_current_user)
):
    goal=db.query(
        SavingsGoal
    ).filter(
        SavingsGoal.id==goal_id,
        SavingsGoal.user_id==current_user.id
    ).first()

    if not goal:
        raise HTTPException(status_code=404,detail="Savings Goal not found")

    values=updated_data.model_dump(exclude_unset=True)

    for field,value in values.items():
        setattr(goal,field,value)

    try:
        db.commit()
        db.refresh(goal)

    except Exception:
        db.rollback()
        raise
    return goal


@router.delete("/{goal_id}")
def delete_savings_goal(
    goal_id:int,
    db:Session=Depends(get_db),
    current_user:User=Depends(get_current_user)
):
    goal=db.query(
        SavingsGoal
        ).filter(
            SavingsGoal.id==goal_id,
            SavingsGoal.user_id==current_user.id
        ).first()

    if not goal:
        raise HTTPException(status_code=404,detail="Savings Goal not found")

    try:
        db.delete(goal)
        db.commit()

    except Exception:
        db.rollback()
        raise

    return {
        "message":"Savings Goal Deleted"
    }