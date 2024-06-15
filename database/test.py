from db import Bridge

db = Bridge()
db.setup()
db.add_user(121212)
db.update_amount(555, 121212)
print(db.get_amount(121212))