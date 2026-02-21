from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import List, Optional


class TransactionBase(BaseModel):
    date: datetime
    amount: float


class TransactionEnriched(BaseModel):
    date: str
    amount: float
    ceiling: float
    remanent: float


class ValidatorRequest(BaseModel):
    wage: float
    transactions: List[TransactionEnriched]


class PeriodQ(BaseModel):
    fixed: float
    start: datetime
    end: datetime


class PeriodP(BaseModel):
    extra: float
    start: datetime
    end: datetime


class PeriodK(BaseModel):
    start: datetime
    end: datetime


class FilterRequest(BaseModel):
    q: List[PeriodQ]
    p: List[PeriodP]
    k: List[PeriodK]
    transactions: List[TransactionBase]


class ReturnsRequest(BaseModel):
    age: int
    wage: float
    inflation: float
    q: List[PeriodQ]
    p: List[PeriodP]
    k: List[PeriodK]
    transactions: List[TransactionBase]
