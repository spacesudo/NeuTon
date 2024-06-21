from pytoniq import LiteBalancer, WalletV4R2
import asyncio

async def send_ton(dest: str, amount: float, mnemonics: list):
    provider = LiteBalancer.from_mainnet_config(2)
    await provider.start_up()

    try:
        wallet = await WalletV4R2.from_mnemonic(provider=provider, mnemonics=mnemonics)

        transfer = {
            "destination": dest,    # please remember about bounceable flags
            "amount":      int(10**9 * amount),             # amount sent, in nanoTON
        }

        await wallet.transfer(**transfer)
        await provider.close_all()
    except Exception as e:
        print(e)

if __name__ == "__main__":
    from mnemonics import mnemonics
    x = mnemonics
    dest = 'EQAb4-4c-QaCQSOxCfPZV34AVByxXQDdH0xCMNV7FniGJHXS'
    amount = 0.5
    
    asyncio.run(send_ton(dest, amount, x))