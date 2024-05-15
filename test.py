"""import json
# String representation of the list
word_string = '["build", "tide", "curious", "shallow", "give", "direct", "baby", "corn", "vapor", "sphere", "shield", "roast", "impact", "flock", "hawk", "nuclear", "stadium", "habit", "flame", "wrap", "album", "fiber", "cruise", "romance"]'

# Removing square brackets and splitting the string by commas
word_list = word_string.strip('[]').split(', ')

# Printing the resulting list
print(type(word_list))
word_list = [word.strip('"') for word in word_list]
print(word_list)

x = eval(word_string)
y = list(json.dumps(x))
print(x)"""

from native.encrypt import decrypt

from database.db import User

db = User()
db.setup()

print(db.get_wallet(7034272819))