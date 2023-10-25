import base64
from criptografia import Criptografia
from RSA import RSA

c = Criptografia()
r =  RSA()

e = r.encrypt_with_public_key('1')
print(e)

d = c.decrypt_with_private_key(e)
print(d)