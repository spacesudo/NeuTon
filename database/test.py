from db import Trade
import json
#from native.encrypt import encrypt

db = Trade()

db.setup()


print(db.retrieve_buyamt(6046370889))
