import asyncio
import requests
from pytoniq_core import Address

from pytoniq import LiteBalancer, WalletV4R2, LiteClient
from pytonapi import AsyncTonapi
import asyncio
from dotenv import load_dotenv
import os
from pytoniq_core import Address, Cell
import json


load_dotenv()

api = os.getenv('TON_API')



async def mint(address: str):
    
    tonapi = AsyncTonapi(api)
    
    x = await tonapi.jettons.get_info(address)
    
    return x.mintable

async def owner(address: str):
    try: 
        with open('config.json','r') as f:
            config = json.load(f.read())
        
        
        client = LiteBalancer.from_config(config, trust_level=2)

        await client.start_up()
        
        result = await client.run_get_method(address, method="get_jetton_data", stack=[])
        
        mt = Cell.begin_parse(result[3])
        print(mt)
        p = result[2].load_address()
        
        
        await client.close_all()
        
        return p.to_str()
    except Exception as e:
        return ""
    
if __name__ == "__main__":   
    x = asyncio.run(owner("EQDxnpzUaBsI9cvGPjuxRM3rHGTHDp92vGTKxPodiomXdtAa"))
    print(x)