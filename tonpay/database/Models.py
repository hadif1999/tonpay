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
from tonpay.utils.ccxt import convert_ticker
from enum import Enum
from tonpay.wallets.blockchain.Base import Wallet as BaseWallet
from tonpay.wallets.blockchain import TON


PLATFORM_NAME = Defaults._platform_name

def get_table_by_blockchain(blockchain: Defaults.types.BLOCKCHAIN|None) -> "WalletDetailType":
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
    KEY = KEY_raw.format(user_id=kwargs.get("user_id", ""),
                         datetime=kwargs.get("datetime", ""),
                         salt=kwargs.get("salt", salt), address=kwargs.get("address", ""))
    return KEY


# note: use __tablename__: str = name_in_database to change table name 

async def insert_row(row: SQLModel, do_refresh:bool = True):
    async with AsyncSession(ASYNC_ENGINE) as session:
        session.add(row)
        await session.commit()
        if do_refresh: await session.refresh(row)
    return True
    

class User(SQLModel, table=True):
    __tablename__ = "_user"
    
    id: int|None = Field(primary_key=True, default=None)
    user_id: str = Field(index=True, unique=True, 
                         min_length=5, max_length=100, nullable=False)
    email: EmailStr|None = Field(min_length=5, max_length=200,
                                 unique=True, default=None)
    max_allowed_wallets: PositiveInt = Field(default=Defaults.users.wallets.count.demo,
                                             le=10, gt=0, nullable=False)
    password: str|None = Field(default=None, min_length=8, max_length=50)
    payment_gateway_active: bool = Field(default=False)
    wallets: list["Wallet"] = Relationship(back_populates="user")
    
    
    @property
    def _logger(self):
        return logger.bind(user_id=self.user_id)
    
    
    @staticmethod
    async def get(user_id: str|int, load_wallets: bool = True) -> "User":
        user_id = str(user_id)
        query = select(__class__).where(__class__.user_id == user_id)
        if load_wallets: query = query.options(selectinload(__class__.wallets))
        async with AsyncSession(ASYNC_ENGINE) as session:
            res = await session.exec( query )
            user = res.first()
        return user
    
    
    @logger.catch
    @validate_call
    async def dump_wallets(self, asjson: bool = False, *, 
                           include_fields: list[str]|None = None,
                           exclude_fields: list[str]|None = None, nameAsKey: bool = True)-> dict[str, Any]:
        _logger = self._logger
        with Session(ENGINE) as session: # load self.wallets into memory
            _self = session.merge(self)
            session.refresh(_self)
            wallets = _self.wallets
        if wallets == []:
            _logger.debug(f"no wallets defined yet")
            {}
        wallets_dump = {}
        wallets_dump_ls = []
        for wallet in wallets:
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
    async def add_wallet(self, *, name:str|None = None,
                         address:str = '', path:str = '', 
                         Type:Defaults.types.BLOCKCHAIN|None,
                         balance: float = 0, unit:str|None = None,
                         throw_exp: bool = False):
        _logger = self._logger
        async with AsyncSession(ASYNC_ENGINE) as session: # load self.wallets into memory
            _self = await session.merge(self)
            await session.refresh(_self)
            wallets = _self.wallets
        allowed = len(wallets) <= self.max_allowed_wallets
        _logger.debug(f"num max_allowed user's wallets:{self.max_allowed_wallets}")
        if throw_exp: assert allowed, "max wallets reached"
        wallet_names = list( (await self.dump_wallets()).keys() )
        _logger.debug(f"user's wallet names: {wallet_names}")
        if name and name in wallet_names:
            _logger.error("specified name already taken by user wallets")
            return
        name_fmt = Defaults.formats.wallet_name
        dt_now = dt.datetime.now()
        dt_now_str = dt_now.strftime(Defaults._datetime_fmt_encryption)
        Name = name or name_fmt.format(name = Type if Type else PLATFORM_NAME,
                                       ID = self.user_id, 
                                       datetime = dt_now_str) 
        _logger.debug(f"naming new wallet as {Name}")
        KEY = get_symmetric_KEY(user_id=self.user_id, 
                                datetime=dt_now_str,
                                address=address)
        _logger.debug(f"generated symm KEY: {KEY}")
        new_wallet = Wallet(name = Name, type=Type, user_id=self.id)
        await insert_row(new_wallet)
        if Type: # if is external wallet
            path_enc = Symmetric(KEY).encrypt(path)
            _logger.debug(f"encrypted seeds for external wallet: {path_enc}")
            wallet_table: WalletDetailType = get_table_by_blockchain(Type)
            new_wallet_detail = wallet_table(address=address, path=path_enc,
                                            type=Type, enc_time=dt_now, 
                                            balance=balance, unit=unit,
                                            wallet_id=new_wallet.id)
            return await insert_row(new_wallet_detail)
        else: # if is internal wallet
            from random import randint
            addr_raw = KEY + f":{randint(30001, 999999)}"
            address = SHA256(addr_raw)
            internal_wallet_detail = Internal_Wallet(balance=balance, address=address,
                                                enc_date=dt_now, wallet_id=new_wallet.id)
            return await insert_row(internal_wallet_detail)
    
    
    async def import_wallet(self, Type:Defaults.types.BLOCKCHAIN|None,
                            seeds: str, name: str|None = None, **kwargs):
        if not Type: return # can only import external wallets 
        _logger = self._logger
        import importlib
        Type = Type.upper()
        blockchain = importlib.import_module(f"tonpay.wallets.blockchain.{Type}")
        Wallet_cls: BaseWallet = blockchain.Wallet # get wallet from blockchain
        wallet: BaseWallet = await Wallet_cls.import_wallet_bySeeds(seeds, **kwargs)
        balance = 0
        addr = await wallet.get_address()
        path_raw = await wallet.get_path()
        dt_now = dt.datetime.now()
        dt_now_str = dt_now.strftime(Defaults._datetime_fmt_encryption)
        KEY = get_symmetric_KEY(user_id=self.user_id, datetime=dt_now_str, address=addr)
        path_enc = Symmetric(KEY).encrypt(path_raw)
        wallet_names = (await self.dump_wallets()).keys()
        if name and name in wallet_names:
            _logger.error("specified name already taken by user wallets")
            return
        name_fmt = Defaults.formats.wallet_name
        Name = name or name_fmt.format(name = Type if Type else PLATFORM_NAME,
                                       ID = self.user_id, 
                                       datetime = dt_now_str) 
        wallet_db = Wallet(name=Name, date_created=dt_now, type=Type, user_id=self.id)
        await insert_row(wallet_db)
        detail_table: WalletDetailType = get_table_by_blockchain(Type)
        wallet_detail = detail_table(address=addr, path=path_enc,
                                     type=Type, enc_date=dt_now,
                                     balance=balance, unit=Type,
                                     wallet_id=wallet_db.id)
        await insert_row(wallet_detail)
        return True
    
    
class Wallet(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True, default=None)
    name:str = Field(min_length=5, max_length=200)
    date_created: dt.datetime = Field(default=dt.datetime.now())
    type: Optional[Defaults.types.BLOCKCHAIN] = Field(default=None, 
                                                      nullable=True)
    user_id: int|None = Field(default=None, foreign_key="_user.id")
    user: User = Relationship(back_populates="wallets")
    
    
    @property # self.Wallet_Detail_ID keeps wallet detail data
    async def wallet_detail_id(self)->int: 
        wallet_detail_ID_attr = "_Wallet_Detail_ID"
        _wallet_detail_id = getattr(self, wallet_detail_ID_attr, None)
        if not _wallet_detail_id:
            detail_table = get_table_by_blockchain(self.type)
            query = select(detail_table).where(self.id == detail_table.wallet_id)
            async with AsyncSession(ASYNC_ENGINE) as session: 
                _wallet_detail_id = (await session.exec(query)).one().id
            setattr(self, wallet_detail_ID_attr, _wallet_detail_id)
        return _wallet_detail_id
    
    
    @property
    async def wallet_detail(self)-> "WalletDetailType":
        wallet_detail_id: int = await self.wallet_detail_id
        async with AsyncSession(ASYNC_ENGINE) as session:
            detail_table = get_table_by_blockchain(self.type)
            wallet_detail = await session.get(detail_table, wallet_detail_id)
        return wallet_detail
        
    
    @property
    async def balance(self) -> float:
        wallet_detail = await self.wallet_detail
        return max(0, await wallet_detail.get_balance())
    
    
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
    
    
    @property
    async def delete(self):
        async with AsyncSession(ASYNC_ENGINE) as session:
            detail = await self.wallet_detail
            # deleting wallet and it's detail
            await session.delete(self)
            await session.delete(detail)
            await session.commit()
        return self
    
    
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
    async def refresh(self):
        pass
    
    
    @property
    async def user_id(self) -> int:
        userID_atrr = "_userID"
        ID = getattr(self, userID_atrr, None)
        if not ID:
            async with AsyncSession(ASYNC_ENGINE) as session: 
                ID = (await session.get(Wallet, self.wallet_id)).user_id
            setattr(self, userID_atrr, ID)
        return ID
    
    
    @property
    async def user(self) -> User:
        async with AsyncSession(ASYNC_ENGINE) as session:
            user = await session.get(User, await self.user_id)
            return user


class Units_enum(str, Enum):
    USDT = "USDT"
    TON = "TON"
    BTC = "BTC"
        
# wallet on blockchain
class TON_Wallet(SQLModel, WalletDetail_ABC, table=True):
    id: Optional[int] = Field(primary_key=True, default=None)
    address: str = Field(unique=True, min_length=10, max_length=200, nullable=False)
    path: bytes = Field(unique=True, # SHA256(user_id:date_created("Y-M-D_H:MM:S"):salt)
                       min_length=10, max_length=1000, nullable=False)
    type:str = Field("TON", const= True)
    enc_date: dt.datetime = Field(default=dt.datetime.now()) # encryption time 
    balance: PositiveFloat = Field(default=0, nullable=False)
    unit: str = Field(default="TON", const=True) # balance unit in TON
    wallet_id: int|None = Field(default=None, foreign_key="wallet.id", nullable=False) 
            
    
    @property
    async def refresh(self):
        # refresh balance and unit if needed
        from tonpay.wallets.blockchain.TON import Wallet
        # passwd = self.user.password ??????????? # toDo: can we add password to wallet?
        wallet: Wallet = await Wallet.find_account(self.address)
        self.balance = await wallet.get_balance() # balance in TON
        return True
    
    
    async def get_balance(self):
        await self.refresh
        return max(0, self.balance)
    
    
    async def get_balance_USDT(self): 
        await self.refresh
        balance = self.balance
        if balance > 0: 
            balance_usdt = await convert_ticker(balance, self.type, "USDT")
        else: 
            balance_usdt = 0
        return balance_usdt
    
    
    async def get_address(self):
        return self.address
    
    
    async def get_unit(self):
        return self.unit
    
    
    @property
    async def decrypt_path(self) -> str:
        # decrypt path and return
        user = await self.user
        KEY = get_symmetric_KEY(datetime=self.enc_date, user_id= user.user_id,
                                address=self.address)
        path_org = Symmetric(KEY).decrypt(self.path)
        return path_org
    
    
    @property
    async def seeds(self):
        path = await self.decrypt_path
        logger.debug(f"{path = }")
        wallet = await TON.Wallet.find_wallet(path)
        return await wallet.get_seeds()



# wallet inside the platform
class Internal_Wallet(SQLModel, WalletDetail_ABC, table=True):
    id: Optional[int] = Field(primary_key=True, default=None)
    balance: PositiveFloat = Field(default=0, nullable=False) # holds theter or TON
    # this address can't be used in any transaction
    address: str = Field(unique=True,  # SHA256(user_id:date_created("Y-M-D_H:MM:S"):randint)
                         min_length=10, max_length=1000, nullable=False)
    enc_date: dt.datetime = Field(default=dt.datetime.now())# encryption time 
    type: Optional[str] = Field(None, const=True)
    unit: Optional[Units_enum] = Field(default=Units_enum.USDT,
                                       min_length=3, max_length=4, nullable=False)
    wallet_id: int|None = Field(default=None, foreign_key="wallet.id", nullable=False)
        
    
    @property
    async def refresh(self):
        pass
    
    
    async def get_balance_USDT(self):
        await self.refresh
        balance = self.balance
        if balance > 0:
            if self.unit.value != Units_enum.USDT.value: 
                balance_usdt = await convert_ticker(self.balance, self.unit.value,
                                                    "USDT")
            else: balance_usdt = self.balance
        else: balance_usdt = 0
        return balance_usdt
    
    
    async def get_balance(self):
        await self.refresh
        return max(0, self.balance)
    
    
    @validate_call
    async def change_unit(self, unit: Literal["USDT", "TON", "BTC"]):
        if self.unit == unit: return
        # change balance value in new unit
        balance = await self.get_balance()
        new_amt = await convert_ticker(balance, self.unit, unit) # balance in new unit
        self.balance = new_amt
        self.unit = unit
        return True
    
    
    async def get_unit(self):
        return self.unit
    
    
    async def get_address(self):
        return self.address
    
    
class WalletDetailType(Internal_Wallet):
    pass
    
    

# class Transaction_Side(SQLModel):
# #     address: str = Field(min_length=10, max_length=1000)
# #     user_id: str = Field(min_length=10, max_length=100)


# Transaction_QueryType = Literal["user_id", "address"]
# class Transaction(SQLModel, table=True):
#     id: int|None = Field(primary_key=True, default=None)
#     src: Transaction_Side = Field(sa_column=Field(JSON)) # "src":{"address": --- , "user_id": --- }
#     dest: Transaction_Side = Field(sa_column=Field(JSON))  # "dest":{"address":---, "user_id": --- }
#     amount: PositiveFloat = Field(gt=0)
#     status: Literal["pending", "failed", "success"] = Field(default="pending", max_length=10)
#     datetime: dt.datetime = Field(default=dt.datetime.now())
#     transaction_id: str = Field(unique=True, # SHA256(src.address:dest.address:datetime("Y-M-D_H:MM:S"))
#                                 min_length=10, max_length=1000) 
    


    
    
    
    