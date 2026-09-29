from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from pwdlib import PasswordHash
import jwt
from datetime import datetime,timedelta,timezone
from fastapi.security import OAuth2PasswordBearer
from app.database import get_db
from app.models.user import User
from app.config import settings

password_hash=PasswordHash.recommended()
oauth2_scheme=OAuth2PasswordBearer(tokenUrl="login")

def hash_password(password:str):
    return password_hash.hash(password)

def verify_password(plain_password:str,hashed_password:str):
    return password_hash.verify(plain_password,hashed_password)

def create_access_token(data:dict):
    to_encode=data.copy()
    expire=datetime.now(timezone.utc)+timedelta(minutes=settings.access_token_expire_minutes)

    to_encode.update({
        "exp":expire
    })

    token=jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )

    return token

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):

    try:

        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )

        user_id = int(user_id)

    except (jwt.InvalidTokenError, ValueError):

        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:

        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    return user