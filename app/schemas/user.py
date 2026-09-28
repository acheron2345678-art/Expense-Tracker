from pydantic import BaseModel,EmailStr,Field,ConfigDict
from datetime import datetime

class CreateUser(BaseModel):
    name:str=Field(min_length=2,max_length=100)
    email:EmailStr
    password:str=Field(min_length=6,max_length=200)

class UserResponse(BaseModel):
    id:int
    name:str
    email:EmailStr
    created_at:datetime

    model_config=ConfigDict(from_attributes=True)

class TokenResponse(BaseModel):
    access_token:str
    token_type:str