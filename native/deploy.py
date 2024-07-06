from TonTools import *
import asyncio


async def deploy(mnemonics: list):
    client = TonCenterClient(orbs_access=True)
    wallet = Wallet(provider=client, mnemonics=mnemonics, version='v4r2')
    
    if await wallet.get_state() == 'uninitialized':
        await wallet.deploy()
        
    else:
        pass
    
    
    
#asyncio.run(deploy(mnemonics))
