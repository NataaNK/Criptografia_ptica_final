import re
import os
import json
import base64
import time
from pathlib import Path
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
import cryptography.exceptions
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
import pyotp
import qrcode

# GLOBAL VARIABLES  
USERS_JSON_FILE_PATH =  str(Path.cwd()) + "/data/users.json"
KEY_PEM_PATH = str(Path.cwd()) + "/data/key.pem"

class Criptografia:
    def __init__(self):
       pass


    def verify_strong_password(self, contra: str) -> bool:
            patron = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[-@$_!%*?&])[A-Za-z\d@$_!-%*?&]{8,}$"
            return bool(re.match(patron, contra))
    

    def KDF_password_storage(self, name: bytes, contra: str, tokens: bytes, offers: bytes, public_key):
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

        # Generamos el QR de la autenticación en dos pasos y guardamos la 
        # key encriptada para futuras comprobaciones
        totp_key = public_key.encrypt(
                bytes(self.TOKEN_code_authenticator_qr(name), 'ascii'),
                padding.OAEP(
                            mgf=padding.MGF1(algorithm=hashes.SHA256()),
                            algorithm=hashes.SHA256(),
                            label=None
                            )
                )   

        user_dict = {"user_name": name.decode('ascii'),
                     "user_pass": base64.b64encode(derived_key).decode('ascii'),
                     "user_tokens": tokens.decode('ascii'),
                     "user_total_tokens_offered": offers.decode('ascii'),
                     "user_salt": base64.b64encode(salt).decode('ascii'),
                     "user_totp_key": base64.b64encode(totp_key).decode('ascii'),
                     "attempts_pass": [0, time.time()],
                     "attempts_code": [0, time.time()]
                     }
        self.user_data_list.append(user_dict)
        with open(USERS_JSON_FILE_PATH, "w", encoding="UTF-8", newline="") as file:
            json.dump(self.user_data_list, file, indent=2)



    def TOKEN_code_authenticator_qr(self, user_name: str):

        # Generar una clave secreta
        k = pyotp.random_base32()

        # Crear un OTP basado en tiempo (TOTP). Un OTP es un código de un solo uso que se genera cada 30 segundos.
        totp_auth = pyotp.totp.TOTP(k).provisioning_uri(name=self.decrypt_with_private_key(user_name), issuer_name=' Tokens Market')

        # Generar un código QR
        qrcode.make(totp_auth).save(str(Path.cwd()) + "/assets/images/qr_temp.png")

        return k
    

    def KDF_verify_user_name(self, name: str) -> bool:
        
        # Abrimos el almacén de datos de los usuarios
        try:
            with open(USERS_JSON_FILE_PATH, "r", encoding="UTF-8", newline="") as file:
                self.user_data_list = json.load(file)
        except FileNotFoundError:
            self.user_data_list = []

        # Comprobamos que existe el usuario
        self.n_dict = 0
        for dicti in self.user_data_list:
            if(name == self.decrypt_with_private_key(dicti["user_name"]).decode('ascii')):
                return True
            self.n_dict += 1
        return False
            

    def KDF_verify_password(self, contra: str) -> bool:
 
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
    

    def TOKEN_verify_code(self, input_key: str) -> bool:
            
        # Comprobamos que el código introducido coincide con el generado automáticamente
        totp_del_servidor = pyotp.totp.TOTP(self.decrypt_with_private_key(self.user_data_list[self.n_dict]["user_totp_key"]).decode('ascii'))
        totp_auth = totp_del_servidor.now()
        totp_submited = input_key
        
        if totp_submited != totp_auth:
            return False
        return True
            

    def private_key_load(self):
        with open(KEY_PEM_PATH, "rb") as key_file:
            private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=b'zBm2754:3Fl2K:XV',
        )
        return private_key
    
    def decrypt_with_private_key(self, ciphertext: bytes):
        private_key = self.private_key_load()

        plaintext = private_key.decrypt(
            base64.b64decode(ciphertext),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        return plaintext