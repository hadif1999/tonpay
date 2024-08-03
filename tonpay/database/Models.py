import datetime as dt
from pickle import NONE
from token import OP
from typing import Any, Literal, Optional
from xml.dom import NotFoundErr
from sqlmodel import Field, SQLModel, Relationship, Session, select
from sqlmodel.ext.asyncio.session import AsyncSession

from pydantic import EmailStr, PositiveFloat, validate_call, PositiveInt
from sqlalchemy import JSON

from tonpay.database.Engine import ASYNC_ENGINE, ENGINE
import datetime as dt
from tonpay import Defaults
from tonpay.Account import get_client
from tonpay.Encryption import Symmetric, SHA256
from loguru import logger
from sqlalchemy.orm import selectinload



# note: use __tablename__: str = name_in_database to change table name 

async def add_row(row: SQLModel, do_refresh:bool = True):
    async with AsyncSession(ASYNC_ENGINE) as session:
        session.add(row)
        await session.commit()
        if do_refresh: await session.refresh(row)
    

class User(SQLModel, table=True):
    id: int|None = Field(primary_key=True, default=None)
    chat_id: str = Field(index=True, unique=True, 
                         min_length=5, max_length=100)
    email: EmailStr|None = Field(min_length=5, max_length=200,
                                 unique=True, default=None)
    max_allowed_wallets: PositiveInt = Field(default=Defaults.users.wallets.count.demo,
                                             le=10, gt=0)
    payment_gateway_active: bool = Field(default=False)
    external_wallets: list["External_Wallet"] = Relationship(back_populates="user")
    internal_wallets: list["Internal_Wallet"] = Relationship(back_populates="user")
    
    
    @property
    def _logger(self):
        return logger.bind(chat_id=self.chat_id)
    
    
    async def get(chat_id: str|int):
        chat_id = str(chat_id)
        async with AsyncSession(ASYNC_ENGINE) as session:
            res = await session.exec( select(__class__)
                                     .where(__class__.chat_id == chat_id)
                                     .options(selectinload(__class__.internal_wallets),
                                              selectinload(__class__.external_wallets)))
            user = res.first()
        return user
        
        
    def get_wallets(self, field:str|None = None,
                          wallet_type: Literal["external", "internal"]|None = None):
        all_wallets = self.internal_wallets + self.external_wallets
        if not field:
            if wallet_type:
                return getattr(self, f"{wallet_type}_wallets", all_wallets)
            else: return all_wallets
        else: 
            if wallet_type:
                _wallets = getattr(self, f"{wallet_type}_wallets", all_wallets)
                return [getattr(w, field) for w in _wallets]
            else:
                return [getattr(w, field) for w in all_wallets]
            
        
    @logger.catch
    async def get_wallet_by_address(self, address:str):
        # fetching encrypted wallet
        _logger = self._logger
        address = str(address)
        wallets = [w for w in self.get_wallets() if w.address==address] 
        if wallets == []:
            _logger.error(f"wallet with address:{address} not found in user wallets")
            return
        wallet_enc = wallets[0]
        
            # remaking wallet object
        if wallet_enc.is_external:
            KEY_cls = Defaults.formats.Symm_KEY
            KEY_raw, salt = KEY_cls.key_fmt, KEY_cls.salt
            dt_fmt = Defaults.formats.datetime
            KEY = KEY_raw.format(chat_id=wallet_enc.chat_id,
                                 datetime=wallet_enc.date_created.strftime(dt_fmt),
                                 salt=salt, address=wallet_enc.address)
            _logger.debug("symm KEY is: {KEY}", KEY=KEY)
            _logger.debug("enc seeds: {seeds}", seeds=wallet_enc.seeds)
            org_seeds = Symmetric(KEY).decrypt(wallet_enc.seeds)
            _logger.debug("org seeds: {seeds}", seeds=org_seeds)
            # getting a tonlib client
            client = await get_client()
            wallet = await client.find_account(org_seeds) # fetching wallet
            wallet.is_external = True
            return wallet
        else:
            return wallet_enc
        
        
    @logger.catch
    @validate_call
    async def add_wallet(self, *, name:str|None = None,
                         is_external:bool = True, throw_exp: bool = False):
        _logger = self._logger
        allowed = len(self.get_wallets()) <= self.max_allowed_wallets
        _logger.debug(f"num max_allowed user's wallets:{self.max_allowed_wallets}")
        if throw_exp: assert allowed, "max wallets reached"
        wallets_name = self.get_wallets("name")
        _logger.debug(f"user's wallet names: {wallets_name}")
        if name in wallets_name:
            _logger.error("specified name already taken by user wallets")
            return
        if is_external:
            # getting a tonlib client
            client = await get_client()
            wallet  = await client.create_wallet()
            seeds = await wallet.export()
            addr = wallet.address
            _logger.debug(f"wallet made with addr:{addr}")
            dt_now = dt.datetime.now(dt.UTC)
            KEY_cls = Defaults.formats.Symm_KEY
            KEY_raw, salt = KEY_cls.key_fmt, KEY_cls.salt
            dt_fmt = Defaults.formats.datetime
            dt_now_str = dt_now.strftime(dt_fmt)
            KEY = KEY_raw.format(chat_id=self.chat_id,
                                 datetime=dt_now_str,
                                 salt=salt, address=addr)
            _logger.debug(f"generated symm KEY: {KEY}")
            seeds_enc = Symmetric(KEY).encrypt(seeds)
            _logger.debug(f"encrypted seeds for external wallet: {seeds_enc}")
            name_default = Defaults.formats.wallet_name.external.format(datetime=dt_now_str,
                                                                        ID=self.chat_id[:4])
            name = name if name and name not in wallets_name else name_default
            _logger.debug(f"chosen name for external wallet: {name}")
            wallet_db = External_Wallet(chat_id=self.chat_id, name=name, 
                                        address=addr, seeds=seeds_enc, user_id=self.id)
            await add_row(wallet_db)
        else:
            platform_name = Defaults.platform_name
            name_default = Defaults.formats.wallet_name.internal.format(datetime=dt_now_str,
                                                                        ID=self.chat_id[:4],
                                                                        name=platform_name)
            name = name if name and name not in wallets_name else name_default
            # making internal wallet address 
            KEY_cls = Defaults.formats.Symm_KEY
            KEY_raw, salt = KEY_cls.key_fmt, KEY_cls.salt
            dt_fmt = Defaults.formats.datetime
            dt_now = dt.datetime.now(dt.UTC)
            addr_raw = KEY_raw.format(chat_id=self.chat_id,
                                 datetime=dt_now.strftime(dt_fmt),
                                 salt=salt)
            
            # SHA256(chat_id:date_created("Y-M-D_H:MM:S"):salt)
            addr = SHA256(addr_raw).decode()
            _logger.debug(f"addr generated for internal wallet:{addr}")
            wallet_db = Internal_Wallet(chat_id=self.chat_id, name=name, 
                                        address=addr, user_id=self.id)
            await add_row(wallet_db)
            
            
class Wallet(SQLModel):
    date_created: dt.datetime = Field(default=dt.datetime.now(dt.UTC))
    chat_id: str = Field(index=True, unique=True, 
                         min_length=5, max_length=100)
    name:str = Field(min_length=5, max_length=200)
    user_id: int|None = Field(default=None, foreign_key="user.id")
    

# wallet on blockchain
class External_Wallet(Wallet, table=True):
    id: Optional[int] = Field(primary_key=True, default=None)
    address: str = Field(unique=True,
                         min_length=10, max_length=200)
    seeds: str = Field(unique=True, # SHA256(chat_id:date_created("Y-M-D_H:MM:S"):salt)
                       min_length=10, max_length=1000) 
    is_external: bool = Field(default=True)
    user: User = Relationship(back_populates="external_wallets")


# wallet inside the platform
class Internal_Wallet(Wallet, table=True):
    id: Optional[int] = Field(primary_key=True, default=None)
    balance: PositiveFloat = Field(default=0)
    address: str = Field(unique=True,  # SHA256(chat_id:date_created("Y-M-D_H:MM:S"))
                         min_length=10, max_length=1000)
    # unit: Literal["TON", "mTON", "nTON"] = Field(default="nTON") # balance unit in mili-TON, nano-TON or TON
    is_external: bool = Field(default=True)
    user: User = Relationship(back_populates="internal_wallets")
    
    

# class Transaction_Side(SQLModel):
#     address: str = Field(min_length=10, max_length=1000)
#     chat_id: str = Field(min_length=10, max_length=100)


# Transaction_QueryType = Literal["chat_id", "address"]
# class Transaction(SQLModel, table=True):
#     id: int|None = Field(primary_key=True, default=None)
#     src: Transaction_Side = Field(sa_column=Field(JSON)) # "src":{"address": --- , "chat_id": --- }
#     dest: Transaction_Side = Field(sa_column=Field(JSON))  # "dest":{"address":---, "chat_id": --- }
#     amount: PositiveFloat = Field(gt=0)
#     datetime: dt.datetime = Field(default=dt.datetime.now(dt.UTC))
#     transaction_id: str = Field(unique=True, # SHA256(src.address:dest.address:datetime("Y-M-D_H:MM:S"))
#                                 min_length=10, max_length=1000) 
    


    
    
    
    