from db import UserData
import json
#from native.encrypt import encrypt

db = UserData()

db.setup()


print(db.get_referrer(6046370889))
