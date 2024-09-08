from fastapi import FastAPI

from blockchains.TON import controller as TON


app = FastAPI()

app.include_router(TON.router, tags=["ton", "TON"])

@app.get('/')
async def root():
    return {"msg": "SUCCESS"}