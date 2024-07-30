from TonTools import *
import asyncio


async def deploy(mnemonics: list):
    client = TonCenterClient(orbs_access=True)
    wallet = Wallet(provider=client, mnemonics=mnemonics, version='v4r2')
    
    if await wallet.get_state() == 'uninitialized':
        await wallet.deploy()
        
    else:
        pass
    
"""
mnemonics = [
    "glory", "pause", "sting", "apart", "hamster", "innocent", "famous",
    "assault", "primary", "improve", "weapon", "prize", "genuine", "liquid",
    "used", "lonely", "couple", "topic", "skirt", "hurt", "bless", "nature",
    "place", "exotic"
]
asyncio.run(deploy(mnemonics))
"""