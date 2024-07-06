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
    wal = "UQBrwW51lflDqL_QexevoYOBf_uozIQYfTLZZsgpCSnlYu-V"
    x = asyncio.run(main(wal))
    for i in x:
        print(str_addr(i['jetton']['address']))