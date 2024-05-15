import asyncio
from genwallet import import_wallet
#from mnemonics import mnemonics
from TonTools import *

api_key = "AEWQYU5YMJ4JHWYAAAAOUQ5HX3HGCMDUL227AL6ZPYKC6JXR6JREEGRZ5AJWNAX6GLGO5MI"
# jetton address
JETTON_MASTER = 'EQBl3gg6AAdjgjO2ZoNU5Q5EzUIl8XMNZrix8Z5dJmkHUfxI'

async def jetton_bal(jetton_addr, owner_addr):
    client = TonApiClient(key=api_key)
    try:
        jetton_wallet = await Jetton(jetton_addr, client).get_jetton_wallet(owner_address= owner_addr)
        await jetton_wallet.update()
        jetton_wallet_data = jetton_wallet
        
        x = jetton_wallet_data.to_dict()
        return x['balance'] / 10**9
    
    except Exception as e:
        return 0

    
    
async def ton_bal(mnemonics):
    client = TonCenterClient(orbs_access=True)
    wallet = Wallet(provider=client, mnemonics= mnemonics, version='v4r2')
    #print(wallet.address)
    bal = await wallet.get_balance()
    baln = bal/10**9
    return baln

if __name__ == '__main__':
    print(asyncio.run(jetton_bal('EQBlqsm144Dq6SjbPI4jjZvA1hqTIP3CvHovbIfW_t-SCALE', 'UQDLzebYWhJaIt5YbZ5vz_glIbfqP7PxNg9V54HW3jSIhDPe')))
    #asyncio.run(ton_bal())