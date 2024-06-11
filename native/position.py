from pytonapi import AsyncTonapi
import asyncio
from dotenv import load_dotenv
import os

api = os.getenv('TON_API')




async def main(wallet):
    tonapi = AsyncTonapi(api_key=api)
    
    w = await tonapi.accounts.get_jettons_balances(wallet)
    p = w.dict()
    return p