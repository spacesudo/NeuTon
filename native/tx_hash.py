from pytonapi import AsyncTonapi
from dotenv import load_dotenv
import os
import asyncio

load_dotenv()

api_key = os.getenv('TON_API')

async def main(account):
    try:
        tonapi = AsyncTonapi(api_key)
        
        last_hash = await tonapi.accounts.get_events(account, limit=1)
        
        hash = last_hash.dict()['events'][0]['event_id']
        
        return hash
    except Exception as e:
        return ""
    
if __name__ == "__main__":   
    print(asyncio.run(main('UQDLzebYWhJaIt5YbZ5vz_glIbfqP7PxNg9V54HW3jSIhDPe')))