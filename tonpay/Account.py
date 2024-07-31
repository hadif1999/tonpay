from xml.dom import NotFoundErr
import ton.account
from ton.sync import TonlibClient
import ton
from typing import Any


async def get_client():
    client = TonlibClient()
    TonlibClient.enable_unaudited_binaries()
    await client.init_tonlib()
    return client

class Account:
    async def __init__(self):
        self.__wallets: dict[str, ton.account.Account] = {} # each account can have multiple wallets
        self.__current_wallet:ton.account.Account = None
        
        # building client
        self.__client = TonlibClient()
        TonlibClient.enable_unaudited_binaries()
        await self.__client.init_tonlib()
        
        
    async def add_new_wallet(self, name:str):
        wallet = await self.__client.create_wallet()
        self.__current_wallet = name
        self.__wallets[name] = wallet
        return True
    
    
    async def add_existing_wallet(self, name:str, seeds: tuple[str]):
        assert len(seeds) < 6, "seed len not acceptable"
        seeds_str = " ".join(seeds)
        wallet = await self.__client.find_account(seeds_str)
        self.__current_wallet = name 
        self.__wallets[name] = wallet
        return True
    
    
    def select_wallet(self, name:str):
        if name in self.__wallets:
            self.__current_wallet = name
        else: 
            raise NotFoundErr(f"Wallet {name} not found")
        
    
    async def transfer(self, src_wallet_name:str, dest_wallet_addr:str, amount: float):
        src_wallet = self.select_wallet(src_wallet_name)
        await src_wallet.transfer(dest_wallet_addr,
                              self.__client.to_nano(amount),
                              comment = f'tonpay: {src_wallet.address}->{dest_wallet_addr}')
        return True
    
    
    async def generate_payment_link(self, dest_wallet_name:str,
                                    src_wallet_addr:str, amount:float,
                                    dest_id:str, dest_name:str):
        dest_wallet = self.select_wallet(dest_wallet_name)
        amt = self.__client.to_nano(amount)
        
        
        
        
    async def fetch_wallets_from_db(self):
        pass 
    
    
    async def save_wallets_in_db(self):
        pass