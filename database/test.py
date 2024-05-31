from new import Trade

db = Trade()

db.insert_trade(1212,'00000', 'hhh')

print(db.get_last_contract_address(1212))