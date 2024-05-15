import asyncio
from mnemonics import mnemonics
from TonTools import *
#MNEMONICS, JETTON_MASTER, amount, dest_addr
async def transfer_jet(dest: str, jetton_addr: str, mnemonics: list, amount: float):
    client = TonCenterClient(orbs_access=True)
    your_wallet = Wallet(provider=client, mnemonics=mnemonics, version='v3r2')
    """jet = 'EQC4FtSgVLwP6USbYXsVgTZ3hNlY_Rl5SHRWjmTUWa1K2oIe'
    j = Jetton(jet, provider=client).address
    print(j)"""
    await your_wallet.transfer_jetton_by_jetton_wallet(
        destination_address= dest,
        jetton_wallet=jetton_addr, 
        jettons_amount= amount,
    )

    print('done')

if __name__ == '__main__':
    from mnemonics import mnemonics
    x = mnemonics
    amount = 0.005
    jet = 'EQC4FtSgVLwP6USbYXsVgTZ3hNlY_Rl5SHRWjmTUWa1K2oIe'
    dest = 'EQAb4-4c-QaCQSOxCfPZV34AVByxXQDdH0xCMNV7FniGJHXS'
    asyncio.run(transfer_jet(dest, jet, x, amount))