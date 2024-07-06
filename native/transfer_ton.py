import asyncio

from tonsdk.boc import begin_cell

from pytonapi import AsyncTonapi
from tonsdk.utils import bytes_to_b64str, to_nano
from tonsdk.contract.wallet import Wallets, WalletVersionEnum
from dotenv import load_dotenv
import os
load_dotenv()

API_KEY = os.getenv('TON_API')

async def send_ton(DESTINATION_ADDRESS, amount,  MNEMONICS):
    try:
        tonapi = AsyncTonapi(api_key=API_KEY)

        # Create a wallet from the provided mnemonics
        mnemonics_list = MNEMONICS
        _mnemonics, _pub_k, _priv_k, wallet = Wallets.from_mnemonics(
            mnemonics_list,
            WalletVersionEnum.v4r2,  # Set the version of the wallet
            0,
        )

        # Get the sequence number of the wallet's current state
        method_result = await tonapi.blockchain.execute_get_method(
            wallet.address.to_string(False), "seqno"
        )
        seqno = int(method_result.decoded.get("state", 0))

        # Prepare a transfer message to the destination address with the specified amount and sequence number
        transfer_amount = to_nano(float(f"{amount}"), 'ton')

        # Create the comment payload
        payload = begin_cell().store_uint(0, 32).store_string("NeuTon Bot").end_cell()

        query = wallet.create_transfer_message(
            to_addr=DESTINATION_ADDRESS,
            amount=transfer_amount,
            payload=payload,
            seqno=seqno,
        )

        # Convert the message to Base64 and send it through the Tonapi blockchain
        message_boc = bytes_to_b64str(query["message"].to_boc(False))
        data = {'boc': message_boc}
        await tonapi.blockchain.send_message(data)
        
    except Exception as e:
        print(e)


if __name__ == "__main__":
    des = "UQCs_PQIq-FjctnPvWq8756ohqzIsDWYCvm4SjfpAy-SpDxG"
    mn = ['horse', 'kingdom', 'suffer', 'render', 'grape', 'stove', 'bleak', 'quote', 'exit', 'arrow', 'all', 'rubber', 'shrimp', 'scrap', 'aerobic', 'hill', 'hunt', 'tree', 'trial', 'swamp', 'round', 'super', 'large','share']
    asyncio.run(send_ton(des, 0.2, mn))
