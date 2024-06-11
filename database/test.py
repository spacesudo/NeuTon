from trades import Trade

s = Trade()

s.setup()

#s.add(1212,'ttt', 'tyty', 12, 100)

print(s.get_buy_mc(1212, 'tyty'))