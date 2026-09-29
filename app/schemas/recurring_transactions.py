from datetime import date,datetime
from fastapi import HTTPException
from typing import Literal
from decimal import Decimal

from pydantic import BaseModel,Field,ConfigDict,model_validator

Transaction_type=Literal["expense","income"]
Frequency_type=Literal["daily","weekly","monthly","yearly"]
PaymentMethodType = Literal[
    "cash",
    "upi",
    "credit_card",
    "debit_card",
    "bank_transfer",
    "wallet",
    "other"
]

class CreateRecurringTransaction(BaseModel):
    category_id:int=Field(gt=0)
    type:Transaction_type
    amount:Decimal=Field(gt=0)
    description:str=Field(min_length=3,max_length=255)
    payment_method:PaymentMethodType|None=None
    merchant:str|None=Field(default=None,max_length=150)
    notes:str|None=Field(default=None,max_length=500)
    frequency:Frequency_type
    start_date:date
    end_date:date|None=None

    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_date is not None and self.end_date<self.start_date:
            raise ValueError("End date cannot be before start date")

        return self


class UpdateRecurringTransaction(BaseModel):
    category_id:int|None=Field(default=None,gt=0)
    type:Transaction_type|None=None
    amount:Decimal|None=Field(default=None,gt=0)
    description:str|None=Field(defalut=None,min_length=3,max_length=255)
    payment_method:PaymentMethodType|None=None
    merchant:str|None=Field(default=None,max_length=150)
    notes:str|None=Field(default=None,max_length=500)
    frequency:Frequency_type|None=None
    end_date:date|None=None
    active:bool|None=None

class ResponseRecurringTransaction(BaseModel):
    id:int
    user_id:int
    category_id:int
    type:Transaction_type
    amount:Decimal
    description:str
    payment_method:PaymentMethodType|None
    merchant:str|None
    notes:str|None
    frequency:Frequency_type
    start_date:date
    next_run_date:date
    end_date:date|None
    active:bool
    created_at:datetime

    model_config=ConfigDict(from_attributes=True)

    
