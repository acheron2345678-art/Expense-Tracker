from fastapi import APIRouter ,Depends,HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.category import Category
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.category import CreateCategory,UpdateCategory,ResponseCategory
from app.security import get_current_user

router=APIRouter(
    prefix="/categories",
    tags=["Categories"]
)

@router.post("/",response_model=ResponseCategory)
def create_category(
    category:CreateCategory,
    db:Session=Depends(get_db),
    current_user:User=Depends(get_current_user)
):
    existing_category=db.query(Category).filter(Category.user_id==current_user.id,Category.name==category.name).first()
    if existing_category:
        raise HTTPException(status_code=400,detail="The category already exists")
    
    new_category=Category(
        name=category.name,
        user_id=current_user.id
    )

    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category

@router.get("/",response_model=list[ResponseCategory])
def get_categories(
    db:Session=Depends(get_db),
    current_user:User=Depends(get_current_user)
):
    categories=db.query(Category).filter(Category.user_id==current_user.id).all()

    return categories

@router.get("/{category_id}",response_model=ResponseCategory)
def get_category_by_id(
    category_id:int,
    db:Session=Depends(get_db),
    current_user:User=Depends(get_current_user)
):
    category=db.query(Category).filter(Category.id==category_id,Category.user_id==current_user.id).first()
    if not category:
        raise HTTPException(status_code=404,detail="category not found")

    return category

@router.put("/{category_id}",response_model=ResponseCategory)
def update_category(
    category_id:int,
    updated_data:UpdateCategory,
    db:Session=Depends(get_db),
    current_user:User=Depends(get_current_user)
):
    category=db.query(Category).filter(Category.id==category_id,Category.user_id==current_user.id).first()

    if not category:
        raise HTTPException(
            status_code=404,detail="Category not Found"
        )

    duplicate_category=db.query(Category).filter(Category.user_id==current_user.id,func.lower(Category.name)==updated_data.name.lower(),Category.id==category_id).first()
    if duplicate_category:
        raise HTTPException(status_code=400,detail="category already exists")

    category.name=updated_data.name
    db.commit()
    db.refresh(category)
    return category

@router.delete("/{category_id}",response_model=ResponseCategory)
def delete_category(
    category_id:int,
    db:Session=Depends(get_db),
    current_user:User=Depends(get_current_user)
):
    category=db.query(Category).filter(Category.id==category_id,Category.user_id==current_user.id).first()
    if not category:
        raise HTTPException(status_code=404,detail="Category not found")

    transaction_exists=db.query(Transaction).filter(Transaction.category_id==category.id,Transaction.user_id==current_user.id).first()
    if transaction_exists:
        raise HTTPException(status_code=400,detail="cannot delete category with existing transactions")

    db.delete(category)
    db.commit()
    return {
        "message":"Category Deleted"
    }

