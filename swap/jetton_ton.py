from dedust import Asset, Factory, PoolType, JettonRoot, VaultJetton
import asyncio
from pytoniq import WalletV4R2, LiteBalancer
#clfrom ..native import mnemonics


async def ton_swap(jetton_addr: str, mnemonics: list, amount: int):
    provider = LiteBalancer.from_mainnet_config(1)
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
        forward_payload=VaultJetton.create_swap_payload(pool_address=pool.address)
    )

    await wallet.transfer(destination=scale_wallet.address,
                          amount=int(0.3*1e9),
                          body=swap)

    await provider.close_all()

if __name__ == "__main__":
    addr = 'EQBlqsm144Dq6SjbPI4jjZvA1hqTIP3CvHovbIfW_t-SCALE'
    amount = 0.37
    my_mnemonics = ['guard', 'remain', 'ramp', 'inquiry', 'legal', 'razor', 'entire', 'course', 'fish', 'pride', 'dynamic', 'eyebrow', 'print', 'grab', 'scare', 'same', 'dolphin', 'total', 'zone', 'chest', 'vivid', 'you', 'attract', 'normal']

    
    asyncio.run(ton_swap(addr, my_mnemonics, amount))