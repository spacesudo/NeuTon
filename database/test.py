from db import UserData
import json
#from native.encrypt import encrypt

db = UserData()

db.setup()

db.add_user(2321, "wywww", 1111)

print(db.get_users())
