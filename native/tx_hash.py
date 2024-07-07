from pytonapi import AsyncTonapi
from dotenv import load_dotenv
import os
import asyncio

load_dotenv()

api_key = os.getenv('TON_API')

async def main(account):
    tonapi = AsyncTonapi(api_key)
    
    hash = await tonapi.accounts.get_events(account, limit=1)
    
    print(hash.dict()['events'][0]['event_id'])
    
    
asyncio.run(main('UQDLzebYWhJaIt5YbZ5vz_glIbfqP7PxNg9V54HW3jSIhDPe'))