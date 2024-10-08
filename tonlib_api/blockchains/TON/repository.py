from ton.account import Account
from ton.sync import TonlibClient
from typing import Any, Literal, Optional
from blockchains.Base import Wallet as BaseWallet, InSufficientBalanceError

async def get_client():
    client = TonlibClient()
    TonlibClient.enable_unaudited_binaries()
    await client.init_tonlib()
    return client


class Wallet(BaseWallet):
    def __init__(self, wallet):        
        # building client
        client = TonlibClient()
        self.to_nano, self.from_nano = client.to_nano, client.from_nano
        self.__wallet: Account = wallet
        
        
    @staticmethod
    async def new_wallet(password: Optional[str] = None, **kwargs) -> 'Wallet':
        client = await get_client()
        new_wallet = await client.create_wallet(local_password=password, **kwargs)
        return Wallet(new_wallet)
        
        
    @staticmethod
    async def find_wallet(path: bytes, password: Optional[str] = None) -> 'Wallet':
        client = await get_client()
        new_wallet = await client.find_wallet(path, password) 
        return Wallet(new_wallet)
    
    
    async def find_account(address: str, **kwargs) -> 'Wallet':
        client = await get_client()
        account = await client.find_account(address, **kwargs)
        return Wallet(account)    
    
    
    async def get_address(self):
        return self.__wallet.address
    
    
    async def get_balance(self) -> float:
        balance_ton = self.to_nano(await self.__wallet.get_balance())
        return balance_ton
    
    
    async def get_seeds(self):
        return await self.__wallet.export()
    
    
    async def get_path(self):
        return self.__wallet.path
    
    
    @staticmethod
    async def import_wallet_bySeeds(seeds: str, **kwargs):
        client = await get_client()
        _wallet = await client.import_wallet(seeds, **kwargs)
        return Wallet(_wallet)
        
        
    async def transfer(self, dest_addr:str, amount: float, comment: Optional[str] = None, 
                       unit: Literal["TON", "nTON"] = "TON", **kwargs):
        amount = self.from_nano(amount) if unit == "nTON" else amount # amount in ton 
        if (await self.balance) < amount: raise InSufficientBalanceError
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
    
    
    