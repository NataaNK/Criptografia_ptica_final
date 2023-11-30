import re
import os
import json
import base64
import time
import datetime
from pathlib import Path
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
import cryptography.exceptions
from cryptography.hazmat.primitives import serialization, hashes, hmac
from cryptography.hazmat.primitives.asymmetric import padding
import pyotp
import qrcode
from cryptography import x509
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import load_pem_public_key


# GLOBAL VARIABLES  
USERS_JSON_FILE_PATH =  str(Path.cwd()) + "/data/users.json"
KEY_PEM_PATH = str(Path.cwd()) + "/data/clave servidor/key.pem"


class Criptografia:
    def __init__(self):
       pass


    def verify_strong_password(self, contra: str) -> bool:
            patron = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[-@$_!%*?&])[A-Za-z\d@$_!-%*?&]{8,}$"
            return bool(re.match(patron, contra))
    

    def data_storage(self, name: bytes, contra: str, tokens: bytes, offers: bytes, public_key_server, 
                     public_pem_usr, user_certificate):
       
        # Generamos la contraseña derivada KDF a partir del salt
        derived_key_and_salt = self.KDF_derived_key_generate(contra)
        derived_key = derived_key_and_salt[0]
        salt = derived_key_and_salt[1]

        # Generamos el QR de la autenticación en dos pasos y guardamos la 
        # key encriptada para futuras comprobaciones
        totp_key = public_key_server.encrypt(
                bytes(self.TOKEN_code_authenticator_qr(name), 'ascii'),
                padding.OAEP(
                            mgf=padding.MGF1(algorithm=hashes.SHA256()),
                            algorithm=hashes.SHA256(),
                            label=None
                            )
                )   
        
        # Generamos la etiqueta de autenticación del usuario y la guardamos
        # encriptada
        hmac_key = public_key_server.encrypt(
                base64.b64encode(self.HMAC_hash_signature_generate()),
                padding.OAEP(
                            mgf=padding.MGF1(algorithm=hashes.SHA256()),
                            algorithm=hashes.SHA256(),
                            label=None
                            )
                )


        user_dict = {"user_name": name,
                     "user_pass": base64.b64encode(derived_key).decode('ascii'), # no encript
                     "user_public_key": public_pem_usr.decode('ascii'), # no encript
                     "user_certificate": user_certificate.decode('ascii'),
                     "user_tokens": tokens,
                     "user_total_tokens_offered": offers,
                     "user_salt": base64.b64encode(salt).decode('ascii'), # no encript
                     "user_totp_key": base64.b64encode(totp_key).decode('ascii'),
                     "user_hmac_key": base64.b64encode(hmac_key).decode('ascii'),
                     "attempts_pass": [0, time.time()],
                     "attempts_code": [0, time.time()]
                     }
        
        self.user_data_list.append(user_dict)
        with open(USERS_JSON_FILE_PATH, "w", encoding="UTF-8", newline="") as file:
            json.dump(self.user_data_list, file, indent=2)
            
        print("\nMENSAJE DE DEPURACIÓN DEL STORAGE: datos del usuario guardados correctamente \n", str(user_dict) + "\n")


    def KDF_derived_key_generate(self, contra):
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

        print("\nMENSAJE DE DEPURACIÓN: clave derivada obtenida con una KDF \n", str(derived_key) + "\n")
        return derived_key, salt
    

    def TOKEN_code_authenticator_qr(self, user_name: str):

        # Generar una clave secreta
        k = pyotp.random_base32()

        # Crear un OTP basado en tiempo (TOTP). Un OTP es un código de un solo uso que se genera cada 30 segundos.
        totp_auth = pyotp.totp.TOTP(k).provisioning_uri(name=self.decrypt_with_private_key(user_name, KEY_PEM_PATH), issuer_name=' Tokens Market')

        # Generar un código QR
        qrcode.make(totp_auth).save(str(Path.cwd()) + "/assets/images/qr_temp.png")

        print("\nMENSAJE DE DEPURACIÓN: QR generado correctamente a partir de un totp \n", str(totp_auth) + "\n")
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
            if(name == self.decrypt_with_private_key(dicti["user_name"], KEY_PEM_PATH)):
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
        totp_del_servidor = pyotp.totp.TOTP(self.decrypt_with_private_key(self.user_data_list[self.n_dict]["user_totp_key"], KEY_PEM_PATH))
        totp_auth = totp_del_servidor.now()
        totp_submited = input_key
        
        if totp_submited != totp_auth:
            return False
        return True
            

    def private_key_load(self, path):
        with open(path, "rb") as key_file:
            private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=b'zBm2754:3Fl2K:XV',
        )
        return private_key
    
    
    def decrypt_with_private_key(self, ciphertext: bytes, path):
        private_key = self.private_key_load(path)

        plaintext = private_key.decrypt(
            base64.b64decode(ciphertext),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
    
        return plaintext.decode('ascii')

    def HMAC_hash_signature_generate(self):
        key_hmac = os.urandom(32) # 32 bytes = 256 bits para SHA256

        return key_hmac
        
    def HMAC_label_authentication_generate(self, message, hmac_key):
        h = hmac.HMAC(hmac_key, hashes.SHA256())
        h.update(bytes(message, 'ascii'))
        hmac_sig = h.finalize()

        print("\nMENSAJE DE DEPURACIÓN: HMAC generado correctamente con hmac_sig (tamaño de la clave=256)\n", str(hmac_sig) + "\n")
        return hmac_sig

    def HMAC_label_authentication_verify(self, message, hmac_sig, hmac_key):

        h = hmac.HMAC(hmac_key, hashes.SHA256())
        h.update(bytes(message, 'ascii'))

        try:
            h.verify(hmac_sig)
        except cryptography.exceptions.InvalidSignature:
            return False
        print("\nMENSAJE DE DEPURACIÓN: HMAC verificado correctamente con hmac_verify\n", "True\n")
        return True


    def signing_with_private_key_RSA(self, message: str, path):
        private_key = self.private_key_load(path)

        signature = private_key.sign(
            bytes(message, 'ascii'),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

        print("\nMENSAJE DE DEPURACIÓN: firma creada con RSA\n", str(signature),"\n")
        return signature
    

    def certificate_validation(self, certificate: cryptography.x509.Certificate, 
                               issuer_certificate: cryptography.x509.Certificate, 
                               issuer_of_CRL_public_key: rsa.RSAPublicKey,
                               CRL: cryptography.x509.CertificateRevocationList):
        
        # Si el certificado está caducado lo añadimos a la CRL
        now = datetime.datetime.today()
        if((now < certificate.not_valid_before) or (now > certificate.not_valid_after)):

            revoked_cert = cryptography.x509.RevokedCertificateBuilder().serial_number(
                certificate.serial_number
                ).revocation_date(
                    datetime.datetime.today()
                ).build()

            CRL = CRL.add_revoked_certificate(revoked_cert)

        # Comprobamos validez del certificado
        CRL.is_signature_valid(issuer_of_CRL_public_key)
        
        # Comprobamos que el certificado ha sido emitido por el
        # que dice ser y es correcto
        try:
            certificate.verify_directly_issued_by(issuer_certificate)
        except cryptography.exceptions.InvalidSignature:
            return False
        return True


