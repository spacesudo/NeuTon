import asyncio
from genwallet import import_wallet
#from mnemonics import mnemonics
from TonTools import *
import os
from dotenv import load_dotenv
from pytonapi import Tonapi, AsyncTonapi

load_dotenv()

api_key = os.getenv('TON_API')


async def jetton_bal(jetton, wallet):
    try:
        tonapi = AsyncTonapi(api_key)
        
        account =  await tonapi.accounts.get_jetton_balance(wallet, jetton)
        
        ini = account.dict()['balance']
        
        dec = account.dict()['jetton']['decimals']
        
        return int(ini)/10**dec
    except Exception as e:
        return 0
    

def ton_bal(wallet):
    
    tonapi = Tonapi(api_key)
    
    account =  tonapi.accounts.get_info(wallet)
    
    bal = account.balance.to_amount()
    
    return bal

if __name__ == '__main__':
    from mnemonics import mnemonics
    print(asyncio.run(jetton_bal('EQBl3gg6AAdjgjO2ZoNU5Q5EzUIl8XMNZrix8Z5dJmkHUfxI', 'UQDLzebYWhJaIt5YbZ5vz_glIbfqP7PxNg9V54HW3jSIhDPe')))
    print(ton_bal('UQDLzebYWhJaIt5YbZ5vz_glIbfqP7PxNg9V54HW3jSIhDPe'))
    print(asyncio.run(jetton_bal('EQBlqsm144Dq6SjbPI4jjZvA1hqTIP3CvHovbIfW_t-SCALE', 'UQC-lmieMR0nMPvWbDllYCEnqcW_p233j46iTDrN6VUJjPzX')))