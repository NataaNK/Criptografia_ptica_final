from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
import cryptography.exceptions
from pathlib import Path
import base64
# GLOBAL VARIABLES
KEY_PEM_PATH = str(Path.cwd()) + "/data/key.pem"


# Generamos la clave privada y pública
class RSA:
    def __init__(self):
        self.generate_private_key()
        
    def generate_private_key(self):
        private_key = rsa.generate_private_key(
                                        public_exponent=65537,
                                        key_size=2048,
                                        )   
        self.private_key_serialization(private_key)
        
    def private_key_serialization(self, private_key):
        # Guardamos la clave privada encriptada en el disco con una contraseña

        private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.BestAvailableEncryption(b'zBm2754:3Fl2K:XV')
                )
        private_pem.splitlines()[0]
        b'-----BEGIN ENCRYPTED PRIVATE KEY-----'

        self.public_key_serialization(private_key)
        self.private_key_storage(private_pem)

    def public_key_serialization(self, private_key):
        # Atributo visible para todo el mundo: CLAVE PÚBLICA
        self.public_key = private_key.public_key()
        self.public_pem = self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
                )
        self.public_pem.splitlines()[0]
        b'-----BEGIN PUBLIC KEY-----'

    def private_key_storage(self, private_pem):
        with open(KEY_PEM_PATH, "wb") as key_file:
            key_file.write(private_pem)

    def encrypt_with_public_key(self, message: str):

        ciphertext = self.public_key.encrypt(
            bytes(message, 'ascii'),
            padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                        )
            )    

        print("\nMENSAJE DE DEPURACIÓN DEL CIFRADO: Encriptado con la clave pública (tamaño=2048) del servidor usando RSA\n", str(ciphertext)+"\n")
        return base64.b64encode(ciphertext)       
    
    def verify_signature_RSA_with_public_key(self, signature: bytes, message: str) -> bool:

        try:
            self.public_key.verify(
            base64.b64decode(signature + b'=='),
            bytes(message, 'ascii'),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
            )
        except cryptography.exceptions.InvalidSignature:
            return False
        return True
