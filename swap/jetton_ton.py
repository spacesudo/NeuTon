from dedust import Asset, Factory, PoolType, JettonRoot, VaultJetton
import asyncio
from pytoniq import WalletV4R2, LiteBalancer
#clfrom ..native import mnemonics
import requests


async def ton_swap(jetton_addr: str, mnemonics: list, amount: int,limit: int):
    try:
        config = open("config.json", 'rb')
        provider = LiteBalancer.from_config(config=config, trust_level=2)
        
        await provider.start_up()

        wallet = await WalletV4R2.from_mnemonic(provider=provider, mnemonics=mnemonics)

        #jetton_addr = "EQBlqsm144Dq6SjbPI4jjZvA1hqTIP3CvHovbIfW_t-SCALE"

        TON = Asset.native()
        SCALE = Asset.jetton(jetton_addr)

        pool = await Factory.get_pool(PoolType.VOLATILE, [TON, SCALE], provider)
    
        scale_vault = await Factory.get_jetton_vault(jetton_addr, provider)
        scale_root = JettonRoot.create_from_address(jetton_addr)
        scale_wallet = await scale_root.get_wallet(wallet.address, provider)

        swap_amount = int(float(amount) * 1e9)
        swap = scale_wallet.create_transfer_payload(
            destination=scale_vault.address,
            amount=swap_amount,
            response_address=wallet.address,
            forward_amount=int(0.25*1e9),
            forward_payload=VaultJetton.create_swap_payload(pool_address=pool.address, limit=limit)
        )

        y = await wallet.transfer(destination=scale_wallet.address,
                            amount=int(0.3*1e9),
                            body=swap)
        

        await provider.close_all()
        
        return y.__hash__()
    
    except Exception as e:
        return e
        

if __name__ == "__main__":
    addr = 'EQBlqsm144Dq6SjbPI4jjZvA1hqTIP3CvHovbIfW_t-SCALE'
    amount = 0.37
    my_mnemonics = [
    "citizen", "powder", "common", "rather", "piano", "trend",
    "oxygen", "finish", "where", "twice", "shop", "shift",
    "alert", "debate", "seed", "riot", "expire", "sign",
    "ivory", "nominee", "absorb", "voyage", "tattoo", "bottom"
]
    asyncio.run(ton_swap(addr, my_mnemonics, amount, 0))