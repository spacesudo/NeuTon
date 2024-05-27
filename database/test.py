"""from db import Trade
import json
#from native.encrypt import encrypt

db = Trade()

db.setup()


print(db.retrieve_buyamt(6046370889))"""


from db import Bridge

db = Bridge()
db.setup()

#db.add_user(1212)
print(db.get_amount(1212))