from typing import Any, Literal, Optional
from abc import abstractmethod, ABC


class Wallet(ABC):
    
    @abstractmethod
    async def new_wallet(password: Optional[str] = None,**kwargs) -> 'Wallet':
        pass        
        
    @abstractmethod
    async def find_wallet(path: bytes, password: Optional[str] = None) -> 'Wallet':
        pass
    
    @abstractmethod
    async def find_account(address: str, **kwargs) -> 'Wallet':
        pass
    
    @abstractmethod
    async def get_address(self):
        pass
    
    @abstractmethod
    async def get_balance(self) -> float:
        pass
    
    @abstractmethod
    async def get_seeds(self):
        pass
    
    @abstractmethod
    async def get_path(self):
        pass
    
            
    @abstractmethod
    async def transfer(self, dest_addr:str, amount: float, comment: Optional[str] = None, 
                       unit: str = "TON", **kwargs):
        pass
    

class InSufficientBalanceError(Exception):
    def __init__(self, msg: str, code: Optional[str] = None) -> None:
        super().__init__(msg)
        self.error_code = code
        
    def __str__(self) -> str:
        code = self.error_code
        return "Error: {self.args[0]}" 
    

    
    