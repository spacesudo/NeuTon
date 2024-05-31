from dedust import Asset, Factory, PoolType, SwapParams, VaultNative
from pytoniq import WalletV4R2, LiteBalancer
import asyncio
import time

#mnemonics = ["your", "mnemonics", "here"]

async def jetton_swap(jetton_addr: str, mnemonics: list, amount: int, slip = 0.5):
    try:
        provider = LiteBalancer.from_mainnet_config(1)
        await provider.start_up()

        wallet = await WalletV4R2.from_mnemonic(provider=provider, mnemonics=mnemonics)

        #jetton_addr = "EQBlqsm144Dq6SjbPI4jjZvA1hqTIP3CvHovbIfW_t-SCA;E"

        TON = Asset.native()
        JET = Asset.jetton(jetton_addr)

        pool = await Factory.get_pool(pool_type=PoolType.VOLATILE,
                                    assets=[TON, JET],
                                    provider=provider)
                                    
        swap_params = SwapParams(deadline=int(time.time() + 60 * 5),
                                recipient_address=wallet.address)
        swap_amount = int(float(amount) * 1e9)

        swap = VaultNative.create_swap_payload(amount=swap_amount,
                                            pool_address=pool.address,
                                            swap_params=swap_params, limit=slip)

        swap_amount = int(swap_amount + (0.25*1e9)) # 0.25 = gas_value

        y = await wallet.transfer(destination="EQDa4VOnTYlLvDJ0gZjNYm5PXfSmmtL6Vs6A_CZEtXCNICq_", # native vault
                            amount=swap_amount,
                            body=swap)
        
        return y.__hash__()

        await provider.close_all()
        
    except Exception as e:
        print(e)


if __name__ == "__main__":
    addr = 'EQBlqsm144Dq6SjbPI4jjZvA1hqTIP3CvHovbIfW_t-SCALE'
    amount = 0.3
    my_mnemonics = ['guard', 'remain', 'ramp', 'inquiry', 'legal', 'razor', 'entire', 'course', 'fish', 'pride', 'dynamic', 'eyebrow', 'print', 'grab', 'scare', 'same', 'dolphin', 'total', 'zone', 'chest', 'vivid', 'you', 'attract', 'normal']
    my_mnemonics = ['media', 'amount', 'excite', 'corn', 'access', 'august', 'acid', 'banner', 'cinnamon', 'hollow', 'bracket', 'brisk', 'ship', 'fury', 'opera', 'street', 'connect', 'guide', 'burst', 'problem', 'pair', 'useless', 'pride', 'select']
    
    asyncio.run(jetton_swap(addr, my_mnemonics, amount))
