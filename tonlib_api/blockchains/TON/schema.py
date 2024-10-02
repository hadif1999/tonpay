from pydantic import BaseModel
from typing import Union

class Account(BaseModel):
    address: str
    balance: float
    unit: str = "TON"


class Wallet(BaseModel):
    address: str
    balance: float
    path: Union[str, bytes]
    seeds: str
    unit: str = "TON"
