import datetime as dt
from typing import Any, Literal
from sqlmodel import Field, SQLModel, Relationship, Session, select
from sqlmodel.ext.asyncio.session import AsyncSession

from pydantic import EmailStr, PositiveFloat, validate_call, PositiveInt
from sqlalchemy import JSON

from pytonlib.ton.client import wallet_methods

from .Engine import ASYNC_ENGINE
import datetime as dt
from .. import config, Defaults
from ..Account import get_client
from ..Encryption import Symmetric, SHA256
from loguru import logger


# note: use __tablename__: str = name_in_database to change table name 

class User(SQLModel, table=True):
    id: int|None = Field(primary_key=True,
                         min_length=5, max_length=100,
                         unique=True, default=None)
    chat_id: str = Field(index=True, unique=True, 
                         min_length=5, max_length=100)
    email: EmailStr|None = Field(min_length=5, max_length=200,
                                 unique=True, default=None)
    max_allowed_wallets: PositiveInt = Field(default=Defaults.users.wallets.count.demo,
                                             le=10, gt=0)
    payment_gateway_active: bool = False
    wallets: list["Wallet"] = Relationship(back_populates="user")
    
    
    def __init__(self, **data):
        super().__init__(**data)
        self.logger = logger.bind(chat_id=self.chat_id) # making logger for each user
    
    
    async def get(chat_id: str|int):
        async with AsyncSession(ASYNC_ENGINE) as session:
            res = await session.exec( select(__class__).where(__class__.chat_id == chat_id) )
            user = res.one()
            return user
        
        
    @logger.catch
    async def get_wallet_by_address(self, address:str):
            # fetching encrypted wallet
        async with AsyncSession(ASYNC_ENGINE) as session:
            res = await session.exec( select(Wallet).where(Wallet.address == address))
            wallet_enc = res.one()
            self.logger.debug("found wallet_addr:{addr}", addr=wallet_enc.address)
            user_wallets_addrs = [wallet.address for wallet in self.wallets]
            self.logger.debug("user's wallet adresses: {addrs}", addrs=user_wallets_addrs)
            assert wallet_enc.address in user_wallets_addrs, \
            f"wallet not owned by user! owner: {wallet_enc.chat_id}"
            # remaking wallet object
        if wallet_enc.is_external:
            KEY_cls = Defaults.formats.Symm_KEY
            KEY_raw, salt = KEY_cls.key_fmt, KEY_cls.salt
            dt_fmt = Defaults.formats.datetime
            KEY = KEY_raw.format(chat_id=wallet_enc.chat_id,
                                 datetime=wallet_enc.date_created.strftime(dt_fmt),
                                 salt=salt, address=wallet_enc.address)
            self.logger.debug("symm KEY is: {KEY}", KEY=KEY)
            self.logger.debug("enc seeds: {seeds}", seeds=wallet_enc.seeds)
            org_seeds = Symmetric(KEY).decrypt(wallet_enc.seeds)
            self.logger.debug("org seeds: {seeds}", seeds=org_seeds)
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
        allowed = len(self.wallets) <= self.max_allowed_wallets
        self.logger.debug(f"num max_allowed user's wallets:{self.max_allowed_wallets}")
        if throw_exp: assert allowed, "max wallets reached"
        wallets_name = [wallet._name for wallet in self.wallets]
        self.logger.debug(f"user's wallet names: {wallets_name}")
        if is_external:
            # getting a tonlib client
            client = await get_client()
            wallet  = await client.create_wallet()
            seeds = await wallet.export()
            addr = wallet.address
            self.logger.debug(f"wallet made with addr:{addr}")
            dt_now = dt.datetime.now(dt.UTC)
            KEY_cls = Defaults.formats.Symm_KEY
            KEY_raw, salt = KEY_cls.key_fmt, KEY_cls.salt
            dt_fmt = Defaults.formats.datetime
            dt_now_str = dt_now.strftime(dt_fmt)
            KEY = KEY_raw.format(chat_id=self.chat_id,
                                 datetime=dt_now_str,
                                 salt=salt, address=addr)
            self.logger.debug(f"generated symm KEY: {KEY}")
            seeds_enc = Symmetric(KEY).encrypt(seeds)
            self.logger.debug(f"encrypted seeds for external wallet: {seeds_enc}")
            name_default = Defaults.formats.wallet_name.external.format(datetime=dt_now_str,
                                                                        ID=self.chat_id[:4])
            name = name if name and name not in wallets_name else name_default
            self.logger.debug(f"chosen name for external wallet: {name}")
            wallet_db = External_Wallet(chat_id=self.chat_id, name=name, 
                                        address=addr, seeds=seeds_enc)
            async with AsyncSession(ASYNC_ENGINE) as session:
                session.add(wallet_db)
                await session.commit()
                await session.refresh()
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
            self.logger.debug(f"addr generated for internal wallet:{addr}")
            wallet_db = Internal_Wallet(chat_id=self.chat_id, name=name, 
                                        address=addr)
            async with AsyncSession(ASYNC_ENGINE) as session:
                session.add(wallet_db)
                await session.commit()
                await session.refresh()
            
            
class Wallet(SQLModel):
    id: int|None = Field(primary_key=True,
                         min_length=5, max_length=100,
                         unique=True, default=None)
    date_created: dt.datetime = Field(default=dt.datetime.now(dt.UTC))
    chat_id: str = Field(index=True, unique=True, 
                         min_length=5, max_length=100)
    name:str = Field(min_length=5, max_length=200)
    user: User = Relationship(back_populates="wallets")


# wallet on blockchain
class External_Wallet(Wallet, table=True):
    address: str = Field(unique=True,
                         min_length=10, max_length=200)
    seeds: str = Field(unique=True, # SHA256(chat_id:date_created("Y-M-D_H:MM:S"):salt)
                       min_length=10, max_length=1000) 
    is_external: bool = True


# wallet inside the platform
class Internal_Wallet(Wallet, table=True):
    balance: PositiveFloat = Field(min_value=0, default=0)
    address: str = Field(unique=True,  # SHA256(chat_id:date_created("Y-M-D_H:MM:S"))
                         min_length=10, max_length=1000)
    unit: Literal["TON", "mTON", "nTON"] = Field(default="nTON") # balance unit in mili-TON, nano-TON or TON
    is_external: bool = False
    

class Transaction_Side(SQLModel):
    address: str = Field(min_length=10, max_length=1000)
    chat_id: str = Field(min_length=10, max_length=100)


Transaction_QueryType = Literal["chat_id", "address"]
class Transaction(SQLModel, table=True):
    id: int|None = Field(primary_key=True,
                         min_length=5, max_length=100,
                         unique=True, default=None)
    src: Transaction_Side = Field(sa_column=Field(JSON)) # "src":{"address": --- , "chat_id": --- }
    dest: Transaction_Side = Field(sa_column=Field(JSON))  # "dest":{"address":---, "chat_id": --- }
    amount: PositiveFloat = Field(gt=0)
    datetime: dt.datetime = Field(default=dt.datetime.now(dt.UTC))
    transaction_id: str = Field(unique=True, # SHA256(src.address:dest.address:datetime("Y-M-D_H:MM:S"))
                                min_length=10, max_length=1000) 
    


    
    
    
    