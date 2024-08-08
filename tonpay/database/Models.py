import datetime as dt
from pickle import NONE
from token import OP
from typing import Any, Literal, Optional, Union
from sqlmodel import Field, SQLModel, Relationship, Session, select
from sqlmodel.ext.asyncio.session import AsyncSession

from pydantic import EmailStr, PositiveFloat, validate_call, PositiveInt
from sqlalchemy import JSON

from tonpay.database.Engine import ASYNC_ENGINE, ENGINE
import datetime as dt
from tonpay import Defaults
from tonpay.Encryption import Symmetric, SHA256
from loguru import logger
from sqlalchemy.orm import selectinload
from abc import ABC, abstractmethod


PLATFORM_NAME = Defaults._platform_name

def get_table_by_blockchain(blockchain: Defaults.types.BLOCKCHAIN|None) -> "TON_Wallet"|"Internal_Wallet":
    tables_by_blockchain = {
        "TON": TON_Wallet,
        # "BNB": BNB_Wallet, 
        # "ETH": ETH_Wallet
    }
    table = tables_by_blockchain[blockchain] if blockchain else Internal_Wallet
    return table


def get_symmetric_KEY(**kwargs):
    KEY_cls = Defaults.formats.Symm_KEY
    KEY_raw, salt = KEY_cls.key_fmt, KEY_cls.salt
    # generating encryption Symmetric KEY
    KEY = KEY_raw.format(chat_id=kwargs.get("chat_id", ""),
                         datetime=kwargs.get("datetime", ""),
                         salt=kwargs.get("salt", salt), address=kwargs.get("address", ""))
    return KEY



async def ccxt_ticker_convert(amount:float, src_symbol: str,
                      target_symbol: str, exchange_name: str = "binance"):
    from ccxt import async_support as accxt
    exchange_name = exchange_name.lower()
    pair = f"{src_symbol}/{target_symbol}".upper()
    exchange = getattr(accxt, exchange_name)
    async with exchange() as exch:
        ticker = await exch.fetchTicker(pair)
        ticker_price = ticker["last"]
    value = ticker_price * amount
    return value



# note: use __tablename__: str = name_in_database to change table name 

async def insert_row(row: SQLModel, do_refresh:bool = True):
    async with AsyncSession(ASYNC_ENGINE) as session:
        session.add(row)
        await session.commit()
        if do_refresh: await session.refresh(row)
    return True
    

class User(SQLModel, table=True):
    id: int|None = Field(primary_key=True, default=None)
    chat_id: str = Field(index=True, unique=True, 
                         min_length=5, max_length=100)
    email: EmailStr|None = Field(min_length=5, max_length=200,
                                 unique=True, default=None)
    max_allowed_wallets: PositiveInt = Field(default=Defaults.users.wallets.count.demo,
                                             le=10, gt=0)
    password: str|None = Field(default=None, min_length=8, max_length=50)
    payment_gateway_active: bool = Field(default=False)
    wallets: list["Wallet"] = Relationship(back_populates="user")
    
    
    @property
    def _logger(self):
        return logger.bind(chat_id=self.chat_id)
    
    
    @staticmethod
    async def get(chat_id: str|int):
        chat_id = str(chat_id)
        async with AsyncSession(ASYNC_ENGINE) as session:
            res = await session.exec( select(__class__)
                                     .where(__class__.chat_id == chat_id)
                                     .options(selectinload(__class__.wallets)))
            user = res.first()
        return user
    
    
    @logger.catch
    @validate_call
    async def dump_wallets(self, asjson: bool = False, *, 
                           include_fields: list[str]|None = None,
                           exclude_fields: list[str]|None = None, nameAsKey: bool = True):
        _logger = self._logger
        if self.wallets == []:
            _logger.debug(f"no wallets defined yet")
            return
        wallets_dump = {}
        wallets_dump_ls = []
        for wallet in self.wallets:
            name = wallet.name
            blockchain = wallet.type
            wallet_table = get_table_by_blockchain(blockchain)
            query = select(wallet_table).where(wallet_table.wallet_id == wallet.id)
            async with AsyncSession(ASYNC_ENGINE) as session:
                wallet_detail: WalletDetailType = (await session.exec(query)).one()
            if asjson: 
                wallet_dump = {**wallet.model_dump(include=include_fields, 
                                                   exclude=exclude_fields), 
                               **wallet_detail.model_dump(include=include_fields, 
                                                          exclude=exclude_fields)}
            else: 
                wallet_dump = wallet # get as wallet,wallet_detail = wallet[name]
            wallets_dump[name] = wallet_dump
            wallets_dump_ls.append(wallet_dump)
        return wallets_dump if nameAsKey else wallets_dump_ls
                
        
    @logger.catch
    @validate_call
    async def add_wallet(self, *, name:str|None = None,
                         address:str, path:str, Type:Defaults.types.BLOCKCHAIN|None,
                         balance: float = 0, unit:str|None = None,
                         throw_exp: bool = False):
        _logger = self._logger
        allowed = len(self.wallets) <= self.max_allowed_wallets
        _logger.debug(f"num max_allowed user's wallets:{self.max_allowed_wallets}")
        if throw_exp: assert allowed, "max wallets reached"
        wallet_names = list( (await self.dump_wallets()).keys() )
        _logger.debug(f"user's wallet names: {wallet_names}")
        if name and name in wallet_names:
            _logger.error("specified name already taken by user wallets")
            return
        name_fmt = Defaults.formats.wallet_name
        dt_now = dt.datetime.now(dt.UTC)
        dt_now_str = dt_now.strftime(Defaults._datetime_fmt_encryption)
        Name = name or name_fmt.format(name = Type if Type else PLATFORM_NAME,
                                       ID = self.chat_id, 
                                       datetime = dt_now_str) 
        _logger.debug(f"naming new wallet as {Name}")
        KEY = get_symmetric_KEY(chat_id=self.chat_id, 
                                datetime=dt_now_str,
                                address=address)
        _logger.debug(f"generated symm KEY: {KEY}")
        path_enc = Symmetric(KEY).encrypt(path)
        _logger.debug(f"encrypted seeds for external wallet: {path_enc}")
        new_wallet = Wallet(name = Name, type=Type, user_id=self.id)
        await insert_row(new_wallet)
        wallet_table: WalletDetailType = get_table_by_blockchain(Type)
        new_wallet_detail = wallet_table(address=address, path=path_enc,
                                         type=Type, enc_time=dt_now, 
                                         balance=balance, unit=unit,
                                         wallet_id=new_wallet.id)
        await insert_row(new_wallet_detail)
        return True
            
            
class Wallet(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True, default=None)
    name:str = Field(min_length=5, max_length=200)
    date_created: dt.datetime = Field(default=dt.datetime.now(dt.UTC))
    type: Defaults.types.BLOCKCHAIN | None = Field(default="TON", min_length=3,
                                                     max_length=4)
    user_id: int|None = Field(default=None, foreign_key="user.id")
    user: User = Relationship(back_populates="wallets")
    
    
    @property # self.Wallet_Detail_ID keeps wallet detail data
    async def wallet_detail_id(self)->int: 
        wallet_detail_ID_attr = "_Wallet_Detail_ID"
        _wallet_detail_id = getattr(self, wallet_detail_ID_attr, None)
        if not _wallet_detail_id:
            detail_table = get_table_by_blockchain(self.type)
            query = select(detail_table).where(self.id == detail_table.wallet_id, 
                                               self.type == detail_table.type)
            async with AsyncSession(ASYNC_ENGINE) as session: 
                _wallet_detail_id = (await session.exec(query)).one().id
            setattr(self, wallet_detail_ID_attr, _wallet_detail_id)
        return _wallet_detail_id
    
    
    @property
    async def wallet_detail(self)-> "WalletDetailType":
        wallet_detail_id: int = await self.wallet_detail_id
        async with AsyncSession(ASYNC_ENGINE) as session:
            detail_table = get_table_by_blockchain(self.type)
            wallet_detail = session.get(detail_table, wallet_detail_id)
        return wallet_detail
        
        
    
    @property
    async def balance(self) -> float:
        wallet_detail = await self.wallet_detail
        return await wallet_detail.get_balance()
    
    
    @property
    async def balance_USDT(self) -> float:
        wallet_detail = await self.wallet_detail
        return await wallet_detail.get_balance_USDT()
    
    
    @property
    async def unit(self) -> str:
        wallet_detail = await self.wallet_detail
        return await wallet_detail.get_unit()
    
    
    async def change_name(self, new_name) -> bool:
        # check in name if not repeated in other wallets
        assert new_name not in await self.user.dump_wallets(), "the new name is not unique"
        self.name = new_name
        return True
    
    
    @property
    async def address(self):
        wallet_detail = await self.wallet_detail
        return await wallet_detail.get_address()
    
    
class WalletDetail_ABC(ABC): # abstract class for WalletDetail classes
    @abstractmethod
    async def get_balance(self):
        pass
    
    @abstractmethod
    async def get_balance_USDT(self):
        pass
    
    @abstractmethod
    async def get_unit(self):
        pass
    
    @abstractmethod
    async def get_address(self):
        pass
    
    @abstractmethod
    @property
    async def refresh(self):
        pass
    
    
    @property
    async def user_id(self) -> int:
        userID_atrr = "_userID"
        ID = getattr(self, userID_atrr, None)
        if not ID:
            async with AsyncSession(ASYNC_ENGINE) as session: 
                ID = session.get(Wallet, self.wallet_id).user_id
            setattr(self, userID_atrr, ID)
        return ID
    
    
    @property
    async def user(self) -> User:
        async with AsyncSession(ASYNC_ENGINE) as session:
            user = session.get(User, self.user_id)
            return user
        
        
# wallet on blockchain
class TON_Wallet(SQLModel, WalletDetail_ABC, table=True):
    id: Optional[int] = Field(primary_key=True, default=None)
    address: str = Field(unique=True, min_length=10, max_length=200)
    path: str = Field(unique=True, # SHA256(chat_id:date_created("Y-M-D_H:MM:S"):salt)
                       min_length=10, max_length=1000)
    type:str = Field("TON", const= True)
    enc_date: dt.datetime = Field(default=dt.datetime.now(dt.UTC))# encryption time 
    balance: PositiveFloat = Field(default=0)
    unit: str = Field(default="TON", const=True) # balance unit in TON
    wallet_id: int|None = Field(default=None, foreign_key="wallet.id") 
            
    
    @property
    async def refresh(self):
        # refresh balance and unit if needed
        path = await self.decrypt_path
        from tonpay.wallets.blockchain.TON import Wallet
        # passwd = self.user.password ??????????? # toDo: can we add password to wallet?
        wallet = await Wallet.find_wallet(path)
        self.balance = await wallet.get_balance() # balance in TON
        return True
    
    
    async def get_balance(self):
        await self.refresh
        return self.balance
    
    
    async def get_balance_USDT(self): 
        await self.refresh
        return ??? toUSDT(self.balance)
    
    
    @staticmethod
    async def import_wallet(seeds: str):
        pass
    
    
    async def get_address(self):
        return self.address
    
    
    async def get_unit(self):
        return self.unit
    
    
    @property
    async def decrypt_path(self) -> str:
        # decrypt path and return
        user = await self.user
        KEY = get_symmetric_KEY(datetime=self.enc_date, chat_id= user.chat_id,
                                address=self.address)
        path_org = Symmetric(KEY).decrypt(self.path)
        return path_org


# wallet inside the platform
class Internal_Wallet(SQLModel, WalletDetail_ABC, table=True):
    id: Optional[int] = Field(primary_key=True, default=None)
    balance: PositiveFloat = Field(default=0) # holds theter or TON
    # this address can't be used in any transaction
    address: str = Field(unique=True,  # SHA256(chat_id:date_created("Y-M-D_H:MM:S"))
                         min_length=10, max_length=1000)
    enc_date: dt.datetime = Field(default=dt.datetime.now(dt.UTC))# encryption time 
    type: None = Field(None, const=True)
    unit: Literal["USDT", "TON", "BTC"] = Field(default="USDT", min_length=3, max_length=4)
    wallet_id: int|None = Field(default=None, foreign_key="wallet.id")
    
    
    @property
    async def refresh(self):
        pass
    
    
    async def get_balance_USDT(self):
        await self.refresh
        # return toUSDT(self.balance)
        pass
    
    
    async def get_balance(self):
        await self.refresh
        return self.balance
    
    
    def change_unit(unit: Literal["USDT", "TON", "BTC"]):
        # change balance value in new unit 
        # ch unit in db
        pass
    
    
    async def get_unit(self):
        return self.unit
    
    
    async def get_address(self):
        return self.address
    
    
class WalletDetailType(Internal_Wallet):
    pass
    
    

# class Transaction_Side(SQLModel):
# #     address: str = Field(min_length=10, max_length=1000)
# #     chat_id: str = Field(min_length=10, max_length=100)


# Transaction_QueryType = Literal["chat_id", "address"]
# class Transaction(SQLModel, table=True):
#     id: int|None = Field(primary_key=True, default=None)
#     src: Transaction_Side = Field(sa_column=Field(JSON)) # "src":{"address": --- , "chat_id": --- }
#     dest: Transaction_Side = Field(sa_column=Field(JSON))  # "dest":{"address":---, "chat_id": --- }
#     amount: PositiveFloat = Field(gt=0)
#     status: Literal["pending", "failed", "success"] = Field(default="pending", max_length=10)
#     datetime: dt.datetime = Field(default=dt.datetime.now(dt.UTC))
#     transaction_id: str = Field(unique=True, # SHA256(src.address:dest.address:datetime("Y-M-D_H:MM:S"))
#                                 min_length=10, max_length=1000) 
    


    
    
    
    