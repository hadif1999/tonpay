from typing import Any, Literal, Annotated
from loguru import logger
from abc import abstractmethod, ABC


class Wallet(ABC):
    
    @abstractmethod
    async def new_wallet(password:str|None = None,**kwargs) -> 'Wallet':
        pass        
        
    @abstractmethod
    async def find_wallet(path: bytes, password: str|None = None) -> 'Wallet':
        pass
    
    @abstractmethod
    async def find_account(address: str, **kwargs) -> 'Wallet':
        pass
    
    @abstractmethod
    async def get_address(self):
        pass
    
    @abstractmethod
    async def get_balance(self) -> Annotated[float, "unit in TON"]:
        pass
    
    @abstractmethod
    async def get_seeds(self):
        pass
    
    @abstractmethod
    async def get_path(self):
        pass
    
            
    @abstractmethod
    async def transfer(self, dest_addr:str, amount: float, comment: str| None = None, 
                       unit: Literal["TON", "nTON"] = "TON", **kwargs):
        pass
    

class InSufficientBalanceError(Exception):
    def __init__(self, msg: str, code: int|None = None) -> None:
        super().__init__(msg)
        self.error_code = code
        
    def __str__(self) -> str:
        code = self.error_code
        return "Error: {self.args[0]}" 
    

    
    