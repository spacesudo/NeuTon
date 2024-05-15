from pytoniq import LiteBalancer, WalletV4R2
import asyncio

async def import_wallet(mnemonics):
    provider = LiteBalancer.from_mainnet_config(1)
    
    wallet = await WalletV4R2.from_mnemonic(provider=provider, mnemonics=mnemonics)
    
    await provider.close_all()
    
    return wallet.address


if __name__ == "__main__":
    mnemonics = ['guard', 'remain', 'ramp', 'inquiry', 'legal', 'razor', 'entire', 'course', 'fish', 'pride', 'dynamic', 'eyebrow', 'print', 'grab', 'scare', 'same', 'dolphin', 'total', 'zone', 'chest', 'vivid', 'you', 'attract', 'normal']
    #wallet =  import_wallet(mnemonics)
    #print(wallet)
    x = asyncio.run(import_wallet(mnemonics))
    print(x)