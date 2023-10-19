import Fingerprint
import re
import os
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
import cryptography.exceptions
import json
from pathlib import Path
import base64


# GLOBAL VARIABLES  
USERS_JSON_FILE_PATH =  str(Path.cwd()) + "/data/users.json"

class Criptografia:
    def __init__(self):
       pass

    def verify_strong_password(self, contra: str):
            patron = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[-@$_!%*?&])[A-Za-z\d@$_!-%*?&]{8,}$"
            return bool(re.match(patron, contra))
    
    def KDF_password_storage(self, name: str, contra: str, tokens: float, offers: float):
        # Salt: random string, recommended bytes -> 128b=16B
        salt = os.urandom(16)
        KDF = Scrypt(
                        salt=salt,
                        length=32,
                        n=2**14,
                        r=8,
                        p=1,
                        )
        
        # Obtenemos la clave derivada
        derived_key = KDF.derive(contra.encode('ascii')) 

        user_dict = {"user_name": name,
                     "user_pass": base64.b64encode(derived_key).decode('ascii'),
                     "user_tokens": tokens,
                     "user_total_tokens_offered": offers,
                     "user_salt": base64.b64encode(salt).decode('ascii')}
        self.user_data_list.append(user_dict)
        with open(USERS_JSON_FILE_PATH, "w", encoding="UTF-8", newline="") as file:
            json.dump(self.user_data_list, file, indent=2)


    def KDF_verify_user_name(self, name: str):
        
        # Abrimos el almacén de datos de los usuarios
        try:
            with open(USERS_JSON_FILE_PATH, "r", encoding="UTF-8", newline="") as file:
                self.user_data_list = json.load(file)
        except FileNotFoundError:
            self.user_data_list = []

        # Comprobamos que existe el usuario
        self.n_dict = 0
        for dicti in self.user_data_list:
            if(name == dicti["user_name"]):
                return True
            self.n_dict += 1
        return False
            
    def KDF_verify_password(self, contra: str):
 
        # Abrimos el almacén de datos
        try:
            with open(USERS_JSON_FILE_PATH, "r", encoding="UTF-8", newline="") as file:
                self.user_data_list = json.load(file)
        except FileNotFoundError:
            self.user_data_list = []

        KDF = Scrypt(
                salt=base64.b64decode(self.user_data_list[self.n_dict]["user_salt"]),
                length=32,
                n=2**14,
                r=8,
                p=1,
                )
        
        # Comprobamos que la contraseña coincide
        try:
            KDF.verify(contra.encode('ascii'), base64.b64decode(self.user_data_list[self.n_dict]["user_pass"]))
        except cryptography.exceptions.InvalidKey:
            return False
        return True
    

    def TOKEN_verify_finger_print(self):
        pass
   