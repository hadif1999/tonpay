async def convert_ticker(amount:float, src_symbol: str,
                         target_symbol: str, exchange_name: str = "binance"):
    from ccxt import async_support as accxt
    if amount == 0: return 0
    exchange_name = exchange_name.lower()
    pair = f"{src_symbol}/{target_symbol}".upper()
    exchange = getattr(accxt, exchange_name)
    async with exchange() as exch:
        ticker = await exch.fetchTicker(pair)
        ticker_price = ticker["last"]
    value = ticker_price * amount
    return value

