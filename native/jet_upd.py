import asyncio

from TonTools import *

# jetton address
JETTON_MASTER = 'EQDb56PQSfdBgF3DR6fY_lTr5lmHr4LnWX7GolyJ0BDLRhBa'

async def update(jetton_addr: str):
    client = TonCenterClient(orbs_access=True)

    jetton_master_data = await client.get_jetton_data(jetton_addr)
    
    

    return jetton_master_data.to_dict()

if __name__ == '__main__':
    x = asyncio.run(update(JETTON_MASTER))
    print(x['decimals'])