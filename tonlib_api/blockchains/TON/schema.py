from pydantic import BaseModel


class Account(BaseModel):
    address: str
    balance: float
    unit: str = "TON"
    
    
class Wallet(BaseModel):
    address: str
    balance: float
    path: str|bytes
    seeds: str
    unit: str = "TON"