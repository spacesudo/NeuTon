from db import UserData

db = UserData()

db.setup()

print(db.get_users())