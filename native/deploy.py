from TonTools import *
import asyncio

#from mnemonics import mnemonics
#mnemonics = ["parent", "salmon", "subway", "truth", "slide", "mixture", "skill", "thunder", "dirt", "below", "regular", "peace", "illness", "heavy", "devote", "grunt", "light", "surge", "alone", "trick", "faculty", "north", "car", "hand"]
mnemonics = ["media", "amount", "excite", "corn", "access", "august", "acid", "banner", "cinnamon", "hollow", "bracket", "brisk", "ship", "fury", "opera", "street", "connect", "guide", "burst", "problem", "pair", "useless", "pride", "select"]

#api_key = "AEWQYU5YMJ4JHWYAAAAOUQ5HX3HGCMDUL227AL6ZPYKC6JXR6JREEGRZ5AJWNAX6GLGO5MI"

async def deploy(mnemonics: list):
    client = TonCenterClient(orbs_access=True)
    wallet = Wallet(provider=client, mnemonics=mnemonics, version='v4r2')
    
    if await wallet.get_state() == 'uninitialized':
        await wallet.deploy()
        
    else:
        pass
    
    
    
#asyncio.run(deploy(mnemonics))
