from pytoniq import LiteBalancer, WalletV4R2
import asyncio
import requests
import json

async def import_wallet(mnemonics):
    config = requests.get("https://dton.io/ls/7034272819/C35ACD5CBE58507986E4BBA1B4E0B0D4CE1F77BEB411C7C1F520FA7589205554/global.config.json").json()
    provider = LiteBalancer.from_config(config=config, trust_level=2)
    
    provider.start_up()
    
    wallet = await WalletV4R2.from_mnemonic(provider=provider, mnemonics=mnemonics)
    
    await provider.close_all()
    
    return wallet.address


if __name__ == "__main__":
    mnemonics = ""
    x = asyncio.run(import_wallet(mnemonics))
    print(x)