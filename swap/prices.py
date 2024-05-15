from dedust import Asset, Factory, PoolType
from pytoniq import LiteBalancer
import asyncio

async def main_price(amount, address, decimal):
    provider = LiteBalancer.from_mainnet_config(1)
    await provider.start_up()

    SCALE_ADDRESS = address

    TON = Asset.native()
    SCALE = Asset.jetton(SCALE_ADDRESS)

    pool = await Factory.get_pool(pool_type=PoolType.VOLATILE,
                                  assets=[TON, SCALE],
                                  provider=provider)
                                    
    price = (await pool.get_estimated_swap_out(asset_in=SCALE,
                                               amount_in=int(amount*decimal),
                                               provider=provider))["amount_out"]
    final = price / decimal
    
    return final

    await provider.close_all()

