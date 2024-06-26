import asyncio

from tonsdk.boc import begin_cell

from pytonapi import AsyncTonapi
from tonsdk.utils import bytes_to_b64str, to_nano
from tonsdk.contract.wallet import Wallets, WalletVersionEnum
from dotenv import load_dotenv
import os
load_dotenv()

API_KEY = os.getenv('TON_API')


async def update(addr: str):
    tonapi = AsyncTonapi(API_KEY)
    
    x = await tonapi.jettons.get_info(addr)
    
    #print(x.dict()['metadata']['decimals'])
    return x.dict()['metadata']
    

if __name__ == "__main__":
    p = asyncio.run(update("EQCOe7CdgxUsaWBta4AgRxWtd6D7rzSvI8mwgQPh0VIcLlsn"))
    print(p['decimals'])