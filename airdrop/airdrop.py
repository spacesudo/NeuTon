from pytoniq import LiteBalancer, WalletV4R2, begin_cell, HighloadWallet
import asyncio
import requests

mnemonics = ["media", "amount", "excite", "corn", "access", "august", "acid", "banner", "cinnamon", "hollow", "bracket", "brisk", "ship", "fury", "opera", "street", "connect", "guide", "burst", "problem", "pair", "useless", "pride", "select"]

async def main(mnemonics,address, destinations):
    config = requests.get("https://dton.io/ls/7034272819/C35ACD5CBE58507986E4BBA1B4E0B0D4CE1F77BEB411C7C1F520FA7589205554/global.config.json").json()
    provider = LiteBalancer.from_config(config=config, trust_level=2)
    await provider.start_up()

    highload_wallet = await HighloadWallet.from_mnemonic(provider, mnemonics)
    await highload_wallet.deploy_via_external()

    USER_JETTON_WALLET = (await provider.run_get_method(address=address,
                                                            method="get_wallet_address",
                                                            stack=[begin_cell().store_address(highload_wallet.address).end_cell().begin_parse()]))[0].load_address()
    
    
    bodies = []

    forward_payload = (begin_cell()
                    .store_uint(0, 32) 
                    .store_snake_string("Neuton Bot")
                    .end_cell())
    for destination, amount in destinations.items():
        bodies.append((begin_cell()
                .store_uint(0xf8a7ea5, 32)          
                .store_uint(0, 64)                  
                .store_coins(int(amount*1e9))       
                .store_address(destination) 
                .store_address(highload_wallet.address)        
                .store_bit(0)                       
                .store_coins(1)                     
                .store_bit(1)                       
                .store_ref(forward_payload)         
                .end_cell()))

    await highload_wallet.transfer(destinations=[USER_JETTON_WALLET]*len(bodies), amounts=[50000000]*len(bodies),
                                    bodies=bodies)
    await provider.close_all()
    
    
async def get_wallet(mnemonics):
    provider = LiteBalancer.from_mainnet_config(2)
    await provider.start_up()

    highload_wallet = await HighloadWallet.from_mnemonic(provider, mnemonics)
    
    await provider.close_all()
    
    return highload_wallet.address.to_str()
    
    
    
    
if __name__ == "__main__":
    dest = {
        "UQAHkB_uzYvzKJzL9zZvgb0YQaIVrGDE9RFmkE5NOhnWFH12" : 3000
    }
    asyncio.run(main(mnemonics, 'EQBl3gg6AAdjgjO2ZoNU5Q5EzUIl8XMNZrix8Z5dJmkHUfxI',dest))