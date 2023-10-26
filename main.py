
from criptografia import Criptografia
from rsa import RSA
from app import App
from pathlib import Path
import json
import base64
# GLOBAL VARIABLES  
USERS_JSON_FILE_PATH =  str(Path.cwd()) + "/data/users.json"
OFFERS_JSON_FILE_PATH = str(Path.cwd()) + "/data/offers.json"
BLOCKED_USERS_JSON_FILE_PATH = str(Path.cwd()) + "/data/blocked_users.json"

cripto = Criptografia()

# Antes de obtener una nueva clave privada y pública
# Cogemos los datos encriptados anteriores y los desencriptamos con
# la privada anterior

# users.json
try:
    with open(USERS_JSON_FILE_PATH, "r", encoding="UTF-8", newline="") as file_users:
        user_data_list = json.load(file_users)
except FileNotFoundError:
        user_data_list = []

for dicti in user_data_list:
    dicti["user_name"] = cripto.decrypt_with_private_key(dicti["user_name"]).decode('ascii')
    dicti["user_tokens"] = cripto.decrypt_with_private_key(dicti["user_tokens"]).decode('ascii')
    dicti["user_total_tokens_offered"] = cripto.decrypt_with_private_key(dicti["user_total_tokens_offered"]).decode('ascii')
    dicti["user_totp_key"] = cripto.decrypt_with_private_key(dicti["user_totp_key"]).decode('ascii')
    dicti["user_hmac_key"] = cripto.decrypt_with_private_key(dicti["user_hmac_key"])
     
     
# offers.json
try:
    with open(OFFERS_JSON_FILE_PATH, "r", encoding="UTF-8", newline="") as file_offers:
        offers_data_list = json.load(file_offers)
except FileNotFoundError:
    offers_data_list = []

for dicti in offers_data_list:
    dicti["user_seller"] = cripto.decrypt_with_private_key(dicti["user_seller"]).decode('ascii')

# blocked_users.json
try:
    with open(BLOCKED_USERS_JSON_FILE_PATH, "r", encoding="UTF-8", newline="") as file_blocked:
        blocked_data_list = json.load(file_blocked)
except FileNotFoundError:
    blocked_data_list = []

for dicti in blocked_data_list:
    dicti["user_name"] = cripto.decrypt_with_private_key(dicti["user_name"]).decode('ascii')
     
# Generamos clave pública y privada del servidor
criptosistema = RSA()

# Ecriptamos los datos con la neuva clave

# users.json
for dicti in user_data_list:
    dicti["user_name"] = criptosistema.encrypt_with_public_key(dicti["user_name"]).decode('ascii')
    dicti["user_tokens"] = criptosistema.encrypt_with_public_key(dicti["user_tokens"]).decode('ascii')
    dicti["user_total_tokens_offered"] = criptosistema.encrypt_with_public_key(dicti["user_total_tokens_offered"]).decode('ascii')
    dicti["user_totp_key"] = criptosistema.encrypt_with_public_key(dicti["user_totp_key"]).decode('ascii')
    dicti["user_hmac_key"] = criptosistema.encrypt_with_public_key(base64.b64encode(dicti["user_hmac_key"])).decode('ascii')

# offers.json
for dicti in offers_data_list:
    dicti["user_seller"] = criptosistema.encrypt_with_public_key(dicti["user_seller"]).decode('ascii')

# blocked_users.json
for dicti in blocked_data_list:
    dicti["user_name"] = criptosistema.encrypt_with_public_key(dicti["user_name"]).decode('ascii')

# Guardamos los datos encriptados con la nueva clave:

with open(USERS_JSON_FILE_PATH, "w", encoding="UTF-8", newline="") as file_users:
    json.dump(user_data_list, file_users, indent=2)
with open(OFFERS_JSON_FILE_PATH, "w", encoding="UTF-8", newline="") as file_offers:
    json.dump(offers_data_list, file_offers, indent=2)
with open(BLOCKED_USERS_JSON_FILE_PATH, "w", encoding="UTF-8", newline="") as file_blocked:
    json.dump(blocked_data_list, file_blocked, indent=2)



myapp = App(cripto, criptosistema)

myapp.mainloop()