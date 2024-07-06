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

    asyncio.run(send_ton(FEES_ADDRESS, fees, user_mnemonics))
    time.sleep(15)
    return remains
    
def sell_fees(amount):
    charges = 0.01
    
    fees = amount * charges 
    
    return fees
  
def ref_fees(amount):
    return amount * 0.2 


if __name__ == "__main__":
    print(sell_fees(100))

    
    
    
