from fastapi import APIRouter
from blockchains.TON.repository import Wallet
from blockchains.Base import Wallet as BaseWallet
from blockchains.TON.schema import Wallet as WalletSchema, Account as AccountSchema


router = APIRouter(prefix="/api/ton")


@router.get('/')
async def health_check():
    return {"msg": "SUCCESS"}


@router.get("/address/{addr:str}", response_model=AccountSchema)
async def get_account(addr: str):
    acc: BaseWallet = await Wallet.find_account(addr)
    balance = await acc.get_balance()
    addr = await acc.get_address()
    return AccountSchema(address=addr, balance=balance, unit="TON")


@router.get("/wallet/{path}", response_model=AccountSchema)
async def get_wallet(path: bytes):
    wallet: BaseWallet = await Wallet.find_wallet(path)
    balance = await wallet.get_balance()
    addr = await wallet.get_address()
    seeds = await wallet.get_seeds()
    path = await wallet.get_path()
    return AccountSchema(address=addr, balance=balance, path=path, seeds=seeds)


@router.post("/wallet", response_model=WalletSchema)
async def create_wallet():
    wallet: BaseWallet = await Wallet.new_wallet()
    balance = await wallet.get_balance()
    addr = await wallet.get_address()
    seeds = await wallet.get_seeds()
    path = await wallet.get_path()
    return WalletSchema(address=addr, balance=balance, path=path, seeds=seeds)