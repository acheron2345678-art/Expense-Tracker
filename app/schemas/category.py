from datetime import datetime
from pydantic import BaseModel,Field,ConfigDict

class CreateCategory(BaseModel):
    name:str=Field(min_length=2,max_length=100)

class UpdateCategory(BaseModel):
    name:str=Field(min_length=2,max_length=100)

class ResponseCategory(BaseModel):
    id:int
    name:str
    user_id:int
    created_at:datetime

    model_config=ConfigDict(from_attributes=True)

    