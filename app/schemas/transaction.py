from datetime import datetime,date
from typing import Literal
from pydantic  import BaseModel,Field,ConfigDict,field_validator
from decimal import Decimal

TransactionType=Literal["income","expense"]

PaymentMethodType=Literal[
    "cash",
    "upi",
    "credit_card",
    "debit_card",
    "bank_transfer",
    "wallet",
    "other"
]

class CreateTransaction(BaseModel):
    category_id:int =Field(gt=0)
    type:TransactionType
    amount:Decimal=Field(gt=0)
    description:str=Field(min_length=3,max_length=255)
    transaction_date:date
    payment_method:PaymentMethodType|None=None
    merchant:str|None=Field(default=None,max_length=150)
    notes:str|None=Field(default=None,max_length=500)
    @field_validator("transaction_date")
    @classmethod
    def validate_transaction_date(cls,value):
        if value>date.today():
            raise ValueError("transaction cannot be in the future")
        return value

class UpdateTransaction(BaseModel):
    category_id:int|None=Field(default=None,gt=0)
    type:TransactionType|None=None
    amount:Decimal|None=Field(default=None,gt=0)
    description:str|None=Field(default=None,min_length=3,max_length=255)
    transaction_date:date|None=None
    payment_method:PaymentMethodType|None=None
    metchant:str|None=Field(default=None,max_length=150)
    notes:str|None=Field(default=None,max_length=500)
    @field_validator("transaction_date")
    @classmethod
    def validate_transaction_date(cls,value):
        if value>date.today():
            raise ValueError("transaction cannot be in the future")
        return value

class ResponseTransaction(BaseModel):
    id:int
    user_id:int
    category_id:int
    type:TransactionType
    amount:Decimal
    description:str
    transaction_date:date
    payment_method:PaymentMethodType|None
    merchant:str|None
    notes:str|None
    recurring_transaction_id:int|None
    created_at:datetime

    model_config=ConfigDict(from_attributes=True)


