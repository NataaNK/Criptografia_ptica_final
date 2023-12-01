
from criptografia import Criptografia
from rsa import RSA
from app import App
from pathlib import Path
import json
from datetime import datetime

# GLOBAL VARIABLES  
USERS_JSON_FILE_PATH =  str(Path.cwd()) + "/data/users.json"
OFFERS_JSON_FILE_PATH = str(Path.cwd()) + "/data/offers.json"
BLOCKED_USERS_JSON_FILE_PATH = str(Path.cwd()) + "/data/blocked_users.json"
KEY_PEM_PATH = str(Path.cwd()) + "/data/clave servidor/key.pem"
KEY_USR_PATH = str(Path.cwd()) + "/data/clave usuarios/" 

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
    dicti["user_name"] = cripto.decrypt_with_private_key(dicti["user_name"], KEY_PEM_PATH)
    dicti["user_tokens"] = cripto.decrypt_with_private_key(dicti["user_tokens"], KEY_PEM_PATH)
    dicti["user_total_tokens_offered"] = cripto.decrypt_with_private_key(dicti["user_total_tokens_offered"], KEY_PEM_PATH)
    dicti["user_totp_key"] = cripto.decrypt_with_private_key(dicti["user_totp_key"], KEY_PEM_PATH)
    dicti["user_hmac_key"] = cripto.decrypt_with_private_key(dicti["user_hmac_key"], KEY_PEM_PATH)
     
# offers.json
try:
    with open(OFFERS_JSON_FILE_PATH, "r", encoding="UTF-8", newline="") as file_offers:
        offers_data_list = json.load(file_offers)
except FileNotFoundError:
    offers_data_list = []


for dicti in offers_data_list:
    dicti["user_seller"] = cripto.decrypt_with_private_key(dicti["user_seller"], KEY_PEM_PATH)
 

# blocked_users.json
try:
    with open(BLOCKED_USERS_JSON_FILE_PATH, "r", encoding="UTF-8", newline="") as file_blocked:
        blocked_data_list = json.load(file_blocked)
except FileNotFoundError:
    blocked_data_list = []

for dicti in blocked_data_list:
    dicti["user_name"] = cripto.decrypt_with_private_key(dicti["user_name"], KEY_PEM_PATH)
     
# Generamos clave pública y privada del servidor
criptosistema = RSA()

# Ecriptamos los datos con la nueva clave

# users.json
for dicti in user_data_list:
    dicti["user_name"] = criptosistema.encrypt_with_public_key_server(dicti["user_name"])
    dicti["user_tokens"] = criptosistema.encrypt_with_public_key_server(dicti["user_tokens"])
    dicti["user_total_tokens_offered"] = criptosistema.encrypt_with_public_key_server(dicti["user_total_tokens_offered"])
    dicti["user_totp_key"] = criptosistema.encrypt_with_public_key_server(dicti["user_totp_key"])
    dicti["user_hmac_key"] = criptosistema.encrypt_with_public_key_server(dicti["user_hmac_key"])

# offers.json
for dicti in offers_data_list:
    dicti["user_seller"] = criptosistema.encrypt_with_public_key_server(dicti["user_seller"])

# blocked_users.json
for dicti in blocked_data_list:
    dicti["user_name"] = criptosistema.encrypt_with_public_key_server(dicti["user_name"])

# Guardamos los datos encriptados con la nueva clave:

with open(USERS_JSON_FILE_PATH, "w", encoding="UTF-8", newline="") as file_users:
    json.dump(user_data_list, file_users, indent=2)
with open(OFFERS_JSON_FILE_PATH, "w", encoding="UTF-8", newline="") as file_offers:
    json.dump(offers_data_list, file_offers, indent=2)
with open(BLOCKED_USERS_JSON_FILE_PATH, "w", encoding="UTF-8", newline="") as file_blocked:
    json.dump(blocked_data_list, file_blocked, indent=2) 


myapp = App(cripto, criptosistema)

myapp.mainloop()