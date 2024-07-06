from db import UserData
db = UserData()

db.update_referrals_vol(0.000, 7034272819)

print(db.get_users())