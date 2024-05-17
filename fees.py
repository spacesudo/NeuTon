from database.db import User
import asyncio
from native.transfer_ton import send_ton
from native.encrypt import decrypt
import time


FEES_ADDRESS = 'UQB9dNq-m1ZGrlLMgujPeQP6sIyKTKMUeWWO0ImWPtIEuQi9'
db = User()
def bot_fees(amount, owner):
    charges = 0.01
    user_mnemonics = eval(decrypt(db.get_mnemonics(owner)))
    
    fees = amount * charges 
    
    remains = amount - fees

    asyncio.run(send_ton(dest=FEES_ADDRESS, amount= fees, mnemonics=user_mnemonics))
    time.sleep(15)
    return remains
    
   
def ref_fees(amount):
    return amount * 0.1 


if __name__ == "__main__":
    print(ref_fees(100))

    
    
    
