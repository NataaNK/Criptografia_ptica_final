from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
import cryptography.exceptions
from pathlib import Path
import base64
from AC import AC
from AC1 import AC1
from AC2 import AC2

# GLOBAL VARIABLES
KEY_PEM_PATH = str(Path.cwd()) + "/data/clave servidor/key.pem"
KEY_USR_PATH = str(Path.cwd()) + "/data/clave usuarios/" 


# Generamos la clave privada y pública
class RSA:
    def __init__(self):
        # Generamos autoridad y su certificado
        self.AC = AC()
        # Autoridad AC1
        self.AC1 = AC1(self.AC)
        # Autoridad AC2
        self.AC2 = AC2(self.AC)
        self.generate_private_key_server()
        
    def generate_private_key_server(self):
        private_key_server = rsa.generate_private_key(
                                        public_exponent=65537,
                                        key_size=2048,
                                        )   
        self.private_key_serialization_server(private_key_server)

        
    def private_key_serialization_server(self, private_key_server):
        # Guardamos la clave privada encriptada en el disco con una contraseña
        private_pem_server = private_key_server.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.BestAvailableEncryption(b'zBm2754:3Fl2K:XV')
                    )
        private_pem_server.splitlines()[0]
        b'-----BEGIN ENCRYPTED PRIVATE KEY-----'

        self.public_key_serialization_server(private_key_server)
        self.private_key_storage_server(private_pem_server)


    def public_key_serialization_server(self, private_key_server):
        self.public_key_server = private_key_server.public_key()
        
        self.server_certificate = self.AC1.obtain_cert_from_the_issuer_AC1("servidor", self.public_key_server)
        AC1_certificate_pem = self.AC1.certificate_AC1.public_bytes(
            encoding=serialization.Encoding.PEM
        ).decode('ascii')
        AC_certificate_pem = self.AC.certificate_AC.public_bytes(
            encoding=serialization.Encoding.PEM
        ).decode('ascii')
        self.server_certificate_chaining = [AC1_certificate_pem, AC_certificate_pem]
        self.public_pem_server = self.public_key_server.public_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PublicFormat.SubjectPublicKeyInfo
                        )
        self.public_pem_server.splitlines()[0]
        b'-----BEGIN PUBLIC KEY-----'

    def private_key_storage_server(self, private_pem_server):
        with open(KEY_PEM_PATH, "wb") as key_file:
            key_file.write(private_pem_server)


    def generate_private_key_usr(self, num_usr):
        private_key_usr = rsa.generate_private_key(
                                        public_exponent=65537,
                                        key_size=2048,
                                        )   
        return self.private_key_serialization_usr(private_key_usr, num_usr)

    def private_key_serialization_usr(self, private_key_usr, num_usr):
        # Guardamos la clave privada encriptada en el disco con una contraseña

        private_pem_usr = private_key_usr.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.BestAvailableEncryption(b'zBm2754:3Fl2K:XV')
                )
        private_pem_usr.splitlines()[0]
        b'-----BEGIN ENCRYPTED PRIVATE KEY-----'
        
        self.private_key_storage_usr(private_pem_usr, num_usr)
        return self.public_key_serialization_usr(private_key_usr, num_usr)
        
    

    def public_key_serialization_usr(self, private_key, num_usr):
        self.public_key_usr = private_key.public_key()
    
        self.user_certificate = self.AC2.obtain_cert_from_the_issuer_AC2("user"+str(num_usr), self.public_key_usr)
        self.user_pem_certificate = self.user_certificate.public_bytes(
            encoding=serialization.Encoding.PEM
        )

        self.public_pem_usr = self.public_key_usr.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
                )
        self.public_pem_usr.splitlines()[0]
        b'-----BEGIN PUBLIC KEY-----'
    
        return self.public_pem_usr

    def private_key_storage_usr(self, private_pem, num_usr):
        
        pem_path_usr = KEY_USR_PATH + "key" + str(num_usr) + ".pem"

        with open(pem_path_usr, "wb") as key_file:
            key_file.write(private_pem)
    

    def encrypt_with_public_key_server(self, message: str):
 
        ciphertext = self.public_key_server.encrypt(
            bytes(message, 'ascii'),
            padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                        )
            )    

        print("\nMENSAJE DE DEPURACIÓN: Encriptado con la clave pública del servidor (tamaño=2048) usando RSA\n", str(ciphertext)+"\n")
        return base64.b64encode(ciphertext).decode('ascii')      

    
    def encrypt_with_public_key_usr(self, message: str, public_pem_usr):

        public_key_usr = serialization.load_pem_public_key(public_pem_usr)

        ciphertext = public_key_usr.encrypt(
            bytes(message, 'ascii'),
            padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                        )
            )    

        print("\nMENSAJE DE DEPURACIÓN: Encriptado con la clave pública del usuario (tamaño=2048) usando RSA\n", str(ciphertext)+"\n")
        return base64.b64encode(ciphertext).decode('ascii')   
    

    def verify_signature_RSA_with_public_key(self, signature: bytes, message: str, public_pem) -> bool:

        public_key = serialization.load_pem_public_key(public_pem)

        try:
            public_key.verify(
            signature,
            bytes(message, 'ascii'),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
            )
        except cryptography.exceptions.InvalidSignature:
            return False
        
        print("\nMENSAJE DE DEPURACIÓN: Verificación de la firma digital con RSA usando la clave pública\n", "True\n")
        return True
