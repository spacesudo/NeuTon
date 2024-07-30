from pytoniq import LiteBalancer, WalletV4R2
import asyncio
import requests
import json

async def import_wallet(mnemonics):
    with open('config.json','r') as f:
        config = json.load(f)
    provider = LiteBalancer.from_config(config=config, trust_level=2)
    
    provider.start_up()
    
    wallet = await WalletV4R2.from_mnemonic(provider=provider, mnemonics=mnemonics)
    
    await provider.close_all()
    
    return wallet.address


if __name__ == "__main__":
    mnemonics = ""
    x = asyncio.run(import_wallet(mnemonics))
    print(x)