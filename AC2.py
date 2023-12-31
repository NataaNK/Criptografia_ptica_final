"""
Clase de la autoridad que provee el certificado a los usuarios
"""

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
import datetime
from AC import AC

class AC2:
    
    def __init__(self, AC: AC):

        self.time_limit = datetime.timedelta(1, 0, 0)

        self.private_key_AC2 = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        self.public_key_AC2 = self.private_key_AC2.public_key()
        self.certificate_AC2 = AC.obtain_cert_from_the_issuer_AC("AC2", self.public_key_AC2)

    def obtain_cert_from_the_issuer_AC2(self, subject_name: str, subject_public_key: rsa.RSAPublicKey):    
        
        builder = x509.CertificateBuilder()
        builder = builder.subject_name(x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, subject_name),
        ]))
        builder = builder.issuer_name(x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, 'AC2'),
        ]))

        builder = builder.not_valid_before(datetime.datetime.today())
        builder = builder.not_valid_after(datetime.datetime.today() + (self.time_limit * 30))
        builder = builder.serial_number(x509.random_serial_number())

        # Clave pública del usuario
        builder = builder.public_key(subject_public_key)

        # Firmamos certificado con privada de la autoridad
        certificate = builder.sign(
            private_key=self.private_key_AC2, algorithm=hashes.SHA256(),
        )

        print("\nMENSAJE DE DEPURACIÓN: certificado obtenido de AC2\n", str(certificate),"\n")
        return certificate