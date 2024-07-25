from dedust import Asset, Factory, PoolType
from pytoniq import LiteBalancer
import asyncio
import requests
import json

async def main_price(amount, address, decimal):
    try:    
        with open('config.json','r') as f:
            config = json.load(f.read())
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
    
    except Exception as e:
        return e

if __name__ == "__main__":
    x = asyncio.run(main_price(2, 'EQBlqsm144Dq6SjbPI4jjZvA1hqTIP3CvHovbIfW_t-SCALE', 10**9)) 
    print(x)

