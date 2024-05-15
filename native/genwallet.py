from tonsdk.contract.wallet import Wallets, WalletVersionEnum, WalletV4ContractR2
import asyncio
import requests
from pathlib import Path
from pytonlib import TonlibClient

from tonsdk.crypto import mnemonic_new

#mnemonics = ['guard', 'remain', 'ramp', 'inquiry', 'legal', 'razor', 'entire', 'course', 'fish', 'pride', 'dynamic', 'eyebrow', 'print', 'grab', 'scare', 'same', 'dolphin', 'total', 'zone', 'chest', 'vivid', 'you', 'attract', 'normal']
mnemonics = ["parent", "salmon", "subway", "truth", "slide", "mixture", "skill", "thunder", "dirt", "below", "regular", "peace", "illness", "heavy", "devote", "grunt", "light", "surge", "alone", "trick", "faculty", "north", "car", "hand"]

def gen_mnemonics():
    return mnemonic_new()

def import_wallet(mnemonics):
    mnemonics, pub_k, priv_k, wallet = Wallets.from_mnemonics(version= WalletVersionEnum.v4r2,mnemonics=mnemonics)
    return wallet


def get_addr(mnemonics):
    mnemonics, pub_k, priv_k, wallet = Wallets.from_mnemonics(version= WalletVersionEnum.v4r2,mnemonics=mnemonics)
    return wallet.address.to_string(True,True,False)

async def get_client():
    ton_config = requests.get('https://ton.org/global.config.json').json()
    keystore_dir = '/tmp/ton_keystore'
    Path(keystore_dir).mkdir(parents=True, exist_ok=True)

    # init TonlibClient
    client = TonlibClient(ls_index=2,  # choose LiteServer index to connect
                          config=ton_config,
                          keystore=keystore_dir)

    # init tonlibjson
    await client.init()

    return client

    
    

if __name__ == '__main__':
    wallet = import_wallet(mnemonics)
    print(wallet.address.to_string(True,True,False))
    


