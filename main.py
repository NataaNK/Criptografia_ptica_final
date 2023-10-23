
from criptografia import Criptografia
from RSA import RSA
from app import App
from pathlib import Path
import json
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
    dicti["user_name"] = cripto.decrypt_with_private_key(dicti["user_name"])
    dicti["user_tokens"] = cripto.decrypt_with_private_key(dicti["user_tokens"])
    dicti["usertotal_tokens_offered"] = cripto.decrypt_with_private_key(dicti["usertotal_tokens_offered"])
    dicti["totp"] = cripto.decrypt_with_private_key(dicti["totp"])
     
# offers.json
try:
    with open(OFFERS_JSON_FILE_PATH, "r", encoding="UTF-8", newline="") as file_offers:
        offers_data_list = json.load(file_offers)
except FileNotFoundError:
    offers_data_list = []

for dicti in offers_data_list:
    dicti["user_seller"] = cripto.decrypt_with_private_key(dicti["user_seller"])

# blocked_users.json
try:
    with open(BLOCKED_USERS_JSON_FILE_PATH, "r", encoding="UTF-8", newline="") as file_blocked:
        blocked_data_list = json.load(file_blocked)
except FileNotFoundError:
    blocked_data_list = []

for dicti in blocked_data_list:
    dicti["user_name"] = cripto.decrypt_with_private_key(dicti["user_name"])
     
# Generamos clave pública y privada del servidor
criptosistema = RSA()

# Ecriptamos los datos con la neuva clave

# users.json
for dicti in user_data_list:
    dicti["user_name"] = criptosistema.encrypt_with_public_key(dicti["user_name"])
    dicti["user_tokens"] = criptosistema.encrypt_with_public_key(dicti["user_tokens"])
    dicti["usertotal_tokens_offered"] = criptosistema.encrypt_with_public_key(dicti["usertotal_tokens_offered"])
    dicti["totp"] = criptosistema.encrypt_with_public_key(dicti["totp"])

# offers.json
for dicti in offers_data_list:
    dicti["user_seller"] = criptosistema.encrypt_with_public_key(dicti["user_seller"])

# blocked_users.json
for dicti in blocked_data_list:
    dicti["user_name"] = criptosistema.encrypt_with_public_key(dicti["user_name"])

# Guardamos los datos encriptados con la nueva clave:
with open(USERS_JSON_FILE_PATH, "w", encoding="UTF-8", newline="") as file_users:
    json.dump(user_data_list, file_users, indent=2)
with open(USERS_JSON_FILE_PATH, "w", encoding="UTF-8", newline="") as file_offers:
    json.dump(offers_data_list, file_offers, indent=2)
with open(BLOCKED_USERS_JSON_FILE_PATH, "w", encoding="UTF-8", newline="") as file_blocked:
    json.dump(blocked_data_list, file_blocked, indent=2)



myapp = App(cripto, criptosistema)

myapp.mainloop()