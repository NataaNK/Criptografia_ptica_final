"""
Clase de la autoridad superior a todas
"""

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
import json
import datetime
from pathlib import Path
from cryptography.hazmat.primitives import serialization

CRL_JSON_FILE_PATH = str(Path.cwd()) + "data/CRL.json"

class AC:
    
    def __init__(self):

        self.time_limit = datetime.timedelta(1, 0, 0)

        self.private_key_AC = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        self.public_key_AC = self.private_key_AC.public_key()
        self.certificate_AC = self.obtain_cert_from_the_issuer_AC("AC", self.public_key_AC)
        # Creamos lista de revocados
        self.create_revokated_certificate_list()

    def obtain_cert_from_the_issuer_AC(self, subject_name: str, subject_public_key: rsa.RSAPublicKey):    
        
        builder = x509.CertificateBuilder()
        builder = builder.subject_name(x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, subject_name),
        ]))
        builder = builder.issuer_name(x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, 'AC'),
        ]))

        builder = builder.not_valid_before(datetime.datetime.today())
        builder = builder.not_valid_after(datetime.datetime.today() + (self.time_limit * 30))
        builder = builder.serial_number(x509.random_serial_number())

        # Clave pública del usuario
        builder = builder.public_key(subject_public_key)

        # Firmamos certificado con privada de la autoridad
        certificate = builder.sign(
            private_key=self.private_key_AC, algorithm=hashes.SHA256(),
        )

        return certificate
    
    def create_revokated_certificate_list(self):

        update_time = datetime.timedelta(1, 0, 0)
        
        self.CRL_builder = x509.CertificateRevocationListBuilder()
        self.CRL_builder = self.CRL_builder.issuer_name(x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, 'AC'),
        ]))

        self.CRL_builder = self.CRL_builder.last_update(datetime.datetime.today())
        self.CRL_builder = self.CRL_builder.next_update(datetime.datetime.today() + update_time)

        try:
            with open(CRL_JSON_FILE_PATH, "r", encoding="UTF-8", newline="") as file:
                CRL_data = json.load(file)
        except FileNotFoundError:
            CRL_data = []

        # Cogemos lops certificados revocados de la base de datos
        for certificate_dict in CRL_data:
            certificate = x509.load_pem_x509_certificate(certificate_dict["certificate_pem"].encode('ascii')) 
            revoked_cert = x509.RevokedCertificateBuilder().serial_number(
                certificate.serial_number
            ).revocation_date(
                datetime.strptime(certificate_dict["revocation_date"],"%Y-%m-%d %H:%M:%S.%f")
            ).build()

            self.CRL_builder = self.CRL_builder.add_revoked_certificate(revoked_cert)
       
        self.CRL = self.CRL_builder.sign(
            private_key=self.private_key_AC, algorithm=hashes.SHA256(),
        )
