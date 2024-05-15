from db import UserData
import json
#from native.encrypt import encrypt

db = UserData()

db.setup()

#db.add_user(121212, "fhfhfhf")

print(db.get_trading_vol(121212))
db.update_trading_vol(50,121212)
print(db.get_trading_vol(121212))