from pytonapi import AsyncTonapi
import asyncio
from dotenv import load_dotenv
import os
from pytoniq_core import Address

load_dotenv()

api = os.getenv('TON_API')

async def main(x):
    tonapi= AsyncTonapi(api)

    s = await tonapi.rates.get_prices([x],['USD'])
    price = s.dict()['rates'][x]['prices']['USD']
    return price
    
if __name__ == "__main__":   
    print(asyncio.run(main('TON')))