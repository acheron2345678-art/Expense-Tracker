from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from app.database import Base, engine, get_db
from app.models.user import User
from app.models.category import Category
from app.models.transaction import Transaction
from app.models.budget import Budget
from app.models.recurring_transaction import RecurringTransaction
from app.schemas.user import CreateUser, UserResponse,TokenResponse
from app.security import hash_password,verify_password,create_access_token,get_current_user
from app.scheduler import start_scheduler,stop_scheduler,process_recurring_job

from app.routers import transaction,summary,budget,category,recurring_transactions,analytics,savings_goals

Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app:FastAPI):
    process_recurring_job()
    start_scheduler()
    yield

    stop_scheduler()

app=FastAPI(
    title="Expense Tracker API",
    lifespan=lifespan
)

app.include_router(category.router)
app.include_router(transaction.router)
app.include_router(summary.router)
app.include_router(budget.router)
app.include_router(recurring_transactions.router)
app.include_router(analytics.router)
app.include_router(savings_goals.router)

@app.get("/")
def home():
    return{
        "message":"Expense Tracker"
    }

@app.post("/register",response_model=UserResponse)
def register(user:CreateUser,db:Session=Depends(get_db)):
    existing_user=db.query(User).filter(User.email==user.email).first()

    if existing_user:
        raise HTTPException(status_code=400,detail="Email already Exists")

    hashed=hash_password(user.password)

    new_user=User(
        name=user.name,
        email=user.email,
        hashed_password=hashed
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/login",response_model=TokenResponse)
def login(
    form_data:OAuth2PasswordRequestForm=Depends(),
    db:Session=Depends(get_db)
):
    user=db.query(User).filter(User.email==form_data.username).first()

    if not user:
        raise HTTPException(status_code=401,detail="Invalid email or password")

    password_valid=verify_password(
        form_data.password,
        user.hashed_password
    )

    if not password_valid:
        raise HTTPException(status_code=401,detail="Invalid Email or password")

    access_token=create_access_token({
        "sub":str(user.id)
    }
    )
    return {
        "access_token":access_token,
        "token_type":"bearer"
    }

@app.get("/users/me",response_model=UserResponse)
def get_me(current_user:User=Depends(get_current_user)):
    return current_user

