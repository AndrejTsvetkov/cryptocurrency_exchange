from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, Union

from pydantic import BaseModel

from exchange.models import CurrencyOperationType


class StatusType(Enum):
    OK = 'ok'
    ERROR = 'error'


class CurrencyInWalletModel(BaseModel):
    currency_id: int
    currency_amount: Decimal

    class Config:
        orm_mode = True


class CurrencyModel(BaseModel):
    id: int
    name: str
    exchange_rate: Decimal

    class Config:
        orm_mode = True


class ExtendedCurrencyModel(CurrencyModel):
    buying_rate: Decimal
    selling_rate: Decimal

    class Config:
        orm_mode = False


class RequestCurrencyModel(BaseModel):
    name: str


class WalletModel(BaseModel):
    balance: Decimal
    currencies: Optional[list[CurrencyInWalletModel]]

    class Config:
        orm_mode = True


class UserModel(BaseModel):
    id: int
    name: str
    registration_date: datetime
    wallet: WalletModel

    class Config:
        orm_mode = True


class RequestUserModel(BaseModel):
    name: str


# for operations stuff
class OperationModel(BaseModel):
    currency_name: str
    user_name: str
    operation: CurrencyOperationType
    currency_amount: Decimal
    exchange_rate: Decimal


class CurrencyOperationModel(BaseModel):
    currency_id: int
    wallet_id: int
    type: CurrencyOperationType
    amount: Decimal

    class Config:
        orm_mode = True


class ResponseModel(BaseModel):
    status: StatusType
    # Important! We should include the most specific type first in Union
    data: Optional[
        Union[
            ExtendedCurrencyModel,
            CurrencyModel,
            list[CurrencyModel],
            UserModel,
            list[CurrencyOperationModel],
        ]
    ]
    error: Optional[str]


class QueryModel(BaseModel):
    limit: int
    page: int
