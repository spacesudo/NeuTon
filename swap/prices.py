from dedust import Asset, Factory, PoolType
from pytoniq import LiteBalancer
import asyncio
import requests

async def main_price(amount, address, decimal):
    
    config = requests.get("https://dton.io/ls/7034272819/C35ACD5CBE58507986E4BBA1B4E0B0D4CE1F77BEB411C7C1F520FA7589205554/global.config.json").json()
    provider = LiteBalancer.from_config(config=config, trust_level=2)
    
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
    
    await provider.close_all()
    
    return final

if __name__ == "__main__":
    x = asyncio.run(main_price(0.2, 'EQBlqsm144Dq6SjbPI4jjZvA1hqTIP3CvHovbIfW_t-SCALE', 10e9)) 
    print(x)

