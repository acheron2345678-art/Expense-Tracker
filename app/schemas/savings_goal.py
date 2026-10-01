from datetime import datetime,date

from decimal import Decimal

from typing import Literal

from pydantic import BaseModel,Field,ConfigDict

EntryType=Literal["contribution","withdrawal"]

class SavingsGoalCreate(BaseModel):
    name:str=Field(min_length=2,max_length=150)
    target_amount:Decimal=Field(gt=0)
    target_date:date|None=None
    description:str|None=Field(default=None,max_length=500)

class SavingsGoalUpdate(BaseModel):
    name:str|None=Field(default=None,min_length=2,max_length=150)
    target_amount:Decimal|None=Field(default=None,gt=0)
    target_date:date|None=None
    description:str|None=Field(default=None,max_length=500)

class SavingsGoalResponse(BaseModel):
    id:int
    user_id:int
    name:str
    target_amount:Decimal
    target_date:date|None
    description:str|None
    created_at:datetime
    updated_at:datetime
    model_config=ConfigDict(from_attributes=True)

class SavingsGoalEntryCreate(BaseModel):
    amount:Decimal=Field(gt=0)
    note:str|None=Field(default=None,max_length=255)

class SavingsGoalEntryResponse(BaseModel):
    id:int
    goal_id:int
    user_id:int
    entry_type:EntryType
    amount:Decimal
    note:str|None
    created_at:datetime
    model_config=ConfigDict(from_attributes=True)

    