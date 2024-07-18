import asyncio
import requests
from pytoniq_core import Address

from pytoniq import LiteBalancer, WalletV4R2, LiteClient
from pytonapi import AsyncTonapi
import asyncio
from dotenv import load_dotenv
import os
from pytoniq_core import Address

load_dotenv()

api = os.getenv('TON_API')



async def mint(address: str):
    
    tonapi = AsyncTonapi(api)
    
    x = await tonapi.jettons.get_info(address)
    
    return x.mintable

async def owner(address: str):
    try: 
        config = requests.get("https://dton.io/ls/7034272819/C35ACD5CBE58507986E4BBA1B4E0B0D4CE1F77BEB411C7C1F520FA7589205554/global.config.json").json()
        client = LiteBalancer.from_config(config=config, trust_level=2)

        await client.start_up()
        
        result = await client.run_get_method(address, method="get_jetton_data", stack=[])
        
        p = result[2].load_address()
        
        
        await client.close_all()
        
        return p.to_str()
    except Exception as e:
        return ""
    
if __name__ == "__main__":   
    x = asyncio.run(mint("EQDxnpzUaBsI9cvGPjuxRM3rHGTHDp92vGTKxPodiomXdtAa"))
    print(x)