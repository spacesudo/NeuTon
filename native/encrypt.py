import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import json

def keygen():
    password = b'sys.tonbot8010'
    salt = os.urandom(16)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(), length=32, salt=salt, iterations=480000
    )
    
    key = base64.urlsafe_b64encode(kdf.derive(password))
    try:
        with open('file.txt', 'wb') as f:
            f.write(key)
            
        return True
    except Exception as e:
        return True
    
    
def encrypt(data: list):
    try:
        key = open('file.txt', 'rb').read()
        f = Fernet(key)
        json_data = json.dumps(data)
        token = f.encrypt(json_data.encode('utf-8'))
        return token
        
    except FileNotFoundError:
        keygen()
        key = open('file.txt', 'rb').read()
        f = Fernet(key)
        json_data = json.dumps(data)
        token = f.encrypt(json_data.encode('utf-8'))
        return token
        
def decrypt(data):
    try:
        key = open('file.txt', 'rb').read()
        f = Fernet(key)
        
        token = f.decrypt(data)
        
        return token.decode('utf-8')
    
    except Exception as e:
        return e
        
        
        
if __name__ == "__main__":
    x = ['y','n','m']
    j = encrypt(x)
    print(j)
    print(f"\n{type(j)}")
    print("===============================================\n\n")
    y = decrypt(j)
    print(y)