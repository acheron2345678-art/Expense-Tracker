from datetime import datetime
from pydantic import BaseModel,ConfigDict,Field
from decimal import Decimal

class CreateBudget(BaseModel):
    category_id:int=Field(gt=0)
    amount:Decimal=Field(gt=0)
    month:int=Field(ge=1,le=12)
    year:int =Field(ge=2000,le=2100)

class UpdateBudget(BaseModel):
    amount:Decimal|None=Field(default=None,gt=0)
    month:int|None=Field(default=None,ge=1,le=12)
    year:int|None =Field(default=None,ge=2000,le=2100)

class ResponseBudget(BaseModel):
    id:int
    user_id:int
    category_id:int
    amount:Decimal
    month:int
    year:int
    created_at:datetime

    model_config=ConfigDict(from_attributes=True)

