from ton.account import Account
from ton.sync import TonlibClient
import ton
from typing import Any, Literal, Annotated
from loguru import logger
from tonpay.wallets.blockchain.Base import InSufficientBalanceError
from tonpay.wallets.blockchain.Base import Wallet as BaseWallet


async def get_client(ls_index=2):
    client = TonlibClient(ls_index=ls_index)
    TonlibClient.enable_unaudited_binaries()
    await client.init_tonlib()
    return client


class Wallet(BaseWallet):
    __client = None
    
    
    def __init__(self, wallet):        
        # building client
        _client = TonlibClient() # it will be removed
        self.to_nano, self.from_nano = _client.to_nano, _client.from_nano
        self.__wallet: Account = wallet
        
    
    @classmethod
    async def _get_client(cls, refresh: bool = False, ls_index: int = 2):
        if refresh: cls.__client = None
        cls.__client = cls.__client or await get_client(ls_index)
        return cls.__client
        
        
    @logger.catch
    @staticmethod
    async def new_wallet(password:str|None = None,**kwargs) -> 'Wallet':
        client = await __class__._get_client()
        src = kwargs.get("source", "v4r2")
        if "source" in kwargs: del kwargs["source"]
        new_wallet = await client.create_wallet(local_password=password, source=src, **kwargs)
        return Wallet(new_wallet)
        
        
    @logger.catch
    @staticmethod
    async def find_wallet(path: bytes, password: str|None = None) -> 'Wallet':
        client = await __class__._get_client()
        new_wallet = await client.find_wallet(path, password) 
        return Wallet(new_wallet)
    
    
    @logger.catch
    async def find_account(address: str, **kwargs) -> 'Wallet':
        client = await __class__._get_client()
        account = await client.find_account(address, **kwargs)
        return Wallet(account)    
    
    
    @logger.catch
    async def get_address(self):
        return self.__wallet.address
    
    
    @logger.catch
    async def get_balance(self, to_nano: bool = False) -> Annotated[float, "unit in TON"]:
        _balance = await self.__wallet.get_balance()
        balance_ton = _balance if to_nano else self.from_nano(_balance) 
        return balance_ton
    
    
    @logger.catch
    async def get_seeds(self):
        return await self.__wallet.export()
    
    
    @logger.catch
    async def get_path(self):
        return self.__wallet.path
    
    
    @staticmethod
    async def import_wallet_bySeeds(seeds: str, **kwargs):
        client = await __class__._get_client()
        src = kwargs.get("source", "v4r2")
        if "source" in kwargs: del kwargs["source"]
        _wallet = await client.import_wallet(seeds, source=src, **kwargs)
        return Wallet(_wallet)
        
        
    @logger.catch
    async def transfer(self, dest_addr:str, amount: float, comment: str| None = None, 
                       unit: Literal["TON", "nTON"] = "TON", **kwargs):
        amount = self.from_nano(amount) if unit == "nTON" else amount # amount in ton 
        if (await self.get_balance()) < amount: 
            addr = await self.get_address()
            raise InSufficientBalanceError(f"insufficient balance in source wallet address: {addr}")
        await self.__wallet.transfer(dest_addr,
                                     self.to_nano(amount),
                                     comment = comment, **kwargs)
        return True
    

async def test():
    wallet = await Wallet.new_wallet("1234abcd")
    addr = await wallet.get_address()
    print(f"address = {addr}")
    seeds = await wallet.get_seeds()
    print(f"seeds = {seeds}")
    path = await wallet.get_path() # wallet path in base64
    print(f"path = {path}")
    balance = await wallet.get_balance()
    print(f"balance = {balance}")
    wallet2 = await Wallet.find_wallet(path, "1234abcd")
    print("found wallet: ", wallet2)
    
    
if __name__ == "__main__":
    import asyncio
    loop = asyncio.new_event_loop()
    loop.run_until_complete( test() )
    
    
    