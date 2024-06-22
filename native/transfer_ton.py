from pytoniq import LiteBalancer, WalletV4R2
import asyncio
import requests
import json

async def send_ton(dest: str, amount: float, mnemonics: list):
    config = requests.get("https://dton.io/ls/7034272819/C35ACD5CBE58507986E4BBA1B4E0B0D4CE1F77BEB411C7C1F520FA7589205554/global.config.json").json()
    provider = LiteBalancer.from_config(config=config, trust_level=2)
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
    x = ['push', 'soldier', 'amount', 'ahead', 'plug', 'coyote', 'system', 'belt', 'offer', 'humor', 'ramp', 'sign', 'relief', 'thrive', 'sea', 'ride', 'album', 'vanish', 'sun', 'wear', 'spoil', 'hedgehog', 'rigid','swing']
    dest = 'UQCs_PQIq-FjctnPvWq8756ohqzIsDWYCvm4SjfpAy-SpDxG'
    amount = 0.5
    
    asyncio.run(send_ton(dest, amount, x))