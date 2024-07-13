from pytonapi import AsyncTonapi
import asyncio
from dotenv import load_dotenv
import os
from pytoniq_core import Address

load_dotenv()

api = os.getenv('TON_API')


def str_addr(addr: str):
    try:
        x = Address(addr)
        
        return x.to_str()
    except Exception as e:
        print(e)


async def main(wallet):
    tonapi = AsyncTonapi(api_key=api)
    
    w = await tonapi.accounts.get_jettons_balances(wallet)
    p = w.dict()
    return p['balances']


if __name__ == "__main__":
    print(str_addr('0:65de083a0007638233b6668354e50e44cd4225f1730d66b8b1f19e5d26690751'))