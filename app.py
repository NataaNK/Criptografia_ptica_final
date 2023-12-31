import tkinter as tk
from tkinter import *
from tkinter import messagebox
from tkinter import ttk
import json
from pathlib import Path
import os
import time
import base64
from criptografia import Criptografia
from cryptography.hazmat.primitives import serialization
from cryptography.x509 import load_pem_x509_certificate, ocsp
from rsa import rsa



# GLOBAL VARIABLES  
KEY_PEM_PATH = str(Path.cwd()) + "/data/clave servidor/key.pem"
KEY_USR_PATH = str(Path.cwd()) + "/data/clave usuarios/" 
USERS_JSON_FILE_PATH =  str(Path.cwd()) + "/data/users.json"
OFFERS_JSON_FILE_PATH = str(Path.cwd()) + "/data/offers.json"
BLOCKED_USERS_JSON_FILE_PATH = str(Path.cwd()) + "/data/blocked_users.json"
BLOCKED_TIME = 5*60 # 5 minutos

class App(tk.Frame):

    def __init__(self, cripto: Criptografia, criptosistema: rsa):

        # SISTEMA PARA CRIPTOGRAFÍA
        self.cripto = cripto
        self.rsa = criptosistema
        self.CRL_builder = self.rsa.AC.CRL_builder
        self.CRL = self.rsa.AC.CRL

        self.root = tk.Tk()
        super().__init__(self.root)

        # Fondo
        self.root.configure(bg="#424a57")

        # Tamaño de la ventana
        self.root.geometry("600x760")
        self.main()
        


    
    # ----------------------------- REGISTRO ----------------------------
    
    def __create_account_clicked(self):

        # Botón de confirmación de crear usuario
        confirmation = messagebox.askquestion("Confirm", "Are you sure?")
        if confirmation == "no":
            self.__sign_up_clicked()
            return

        # Comprobamos que no existe el usuario
        if(self.cripto.KDF_verify_user_name(self.username.get())):
            messagebox.showerror("Sign Up Error", "User already exists")
            self.__sign_up_clicked()
            return

        # --------------------------- CONTRASEÑA ROBUSTA ------------------------------

        if(not self.cripto.verify_strong_password(self.password.get())):
            messagebox.showerror("Sign Up Error", "Password not strong enough: Must have 8 characters,\n 1 \
                                 uppercase, 1 lowercase, 1 number and 1 special character ")
            self.__sign_up_clicked()
            return
        
        
        
        usr_public_pem = self.rsa.generate_private_key_usr(self.cripto.n_dict)
        usr_certificate_pem = self.rsa.user_pem_certificate
        AC2_certificate_pem = self.rsa.AC2.certificate_AC2.public_bytes(
            encoding=serialization.Encoding.PEM
        ).decode('ascii')
        AC_certificate_pem = self.rsa.AC.certificate_AC.public_bytes(
            encoding=serialization.Encoding.PEM
        ).decode('ascii')
        # Guardamos la clave derivada haciendo uso de KDF y los datos encriptados con RSA
        self.cripto.data_storage(
                            self.rsa.encrypt_with_public_key_server(self.username.get()),
                            self.password.get(),
                            self.rsa.encrypt_with_public_key_server("5000"),
                            self.rsa.encrypt_with_public_key_server("0"),
                            self.rsa.public_key_server, 
                            usr_public_pem,
                            usr_certificate_pem,
                            [AC2_certificate_pem, AC_certificate_pem]
                            )

        self.__clear_frame()
        
        # ------- AUTENTICACIÓN EN DOS PASOS - QR PARA OBTENER CLAVES TEMPORALES ---------

        # Mostramos el QR
        qr_path = str(Path.cwd()) + "/assets/images/qr_temp.png"
        qr = PhotoImage(file = qr_path)
        qr = qr.subsample(1, 1)
        qr_lbl = Label(self.root, image=qr, bg="#fff")
        qr_lbl.image = qr 
        qr_lbl.place(relx=0.1, rely=0.1)

        # Al darle a siguiente borramos el qr de la base de datos antes de ir a 
        # home window
        btn = Button(self.root, text = "Siguiente", fg = "green", command=self.__register_success)   
        btn.place(relx=0.8, rely=0.8)


    def __register_success(self):

            os.remove(str(Path.cwd()) + "/assets/images/qr_temp.png")

            # Confirmación de registro correcto
            # -------------------- FIRMA DIGITAL DEL SITEMA -------------------
            message = "Register Completed Successfully"
            # Firma del hash
            signature = self.cripto.signing_with_private_key_RSA(message, KEY_PEM_PATH)
            # Comprobamos el certificado y la clave pública del usuario,
            # seguimos la cadena ghasta encontrar la autoridad de la que se fía el sistema (AC)
            usr_public_key_pem = self.cripto.user_data_list[self.cripto.n_dict]["user_public_key"].encode('ascii')
            usr_certificate_pem = self.cripto.user_data_list[self.cripto.n_dict]["user_certificate"].encode('ascii')
            usr_certificate = load_pem_x509_certificate(usr_certificate_pem)
            # Cadena de validación 
            certificate_validiting = usr_certificate
            reliable = False
            for authority in self.cripto.user_data_list[self.cripto.n_dict]["certificate_chain"]:
                A_certificate_pem = authority.encode('ascii')
                A_certificate = load_pem_x509_certificate(A_certificate_pem)
                A_public_key = A_certificate.public_key()

                if(not self.cripto.certificate_validation(certificate_validiting, A_certificate, A_public_key, 
                                                          self.CRL, self.CRL_builder)):
                    messagebox.showerror("Register Error", "Incorrect public key or not valid, please sign in again")
                    self.__sign_up_clicked()
                    return
                
                # Como me fío de AC, compruebo que efectivamente le esta certificando AC
                if(str(A_certificate.subject) == "<Name(CN=AC)>"):
                    # AC se certifica a sí mismo puesto que es la autoridad máxima
                    if(not self.cripto.certificate_validation(A_certificate, A_certificate, A_public_key, 
                                                              self.CRL, self.CRL_builder)):
                        messagebox.showerror("Register Error", "Incorrect public key or not valid, please sign in again")
                        self.__sign_up_clicked()
                        return
                    reliable = True
                else:
                    certificate_validiting = A_certificate

            # Si no te fías de las autoridades salta error
            if not reliable:
                messagebox.showerror("Register Error", "Public key not reliable")
                self.__sign_up_clicked()
                return
            
            # Encriptamos mensaje, la clave publica es la que se corresponde con  el certificado
            encrypted_message = self.rsa.encrypt_with_public_key_usr(message, usr_public_key_pem)
            self.__open_home_window(encrypted_message, signature)
        


    # ------------------------------------- AUTENTICACIÓN -------------------------------------

    def __sign_in_authentication_1(self):
    
        # Confirmamos que el usuario existe
        if(not self.cripto.KDF_verify_user_name(self.username.get())):
            messagebox.showerror("Sign In Error", "User not found")
            self.__sign_in_clicked()
            return
        
        self.counter_pass_expiration = self.cripto.user_data_list[self.cripto.n_dict]["attempts_pass"][1]

        if ((time.time()-self.counter_pass_expiration) > 1800): #30 minutos
            self.cripto.user_data_list[self.cripto.n_dict]["attempts_pass"][0] = 0
            self.cripto.user_data_list[self.cripto.n_dict]["attempts_pass"][1] = time.time()
            # Actualizamos los atributos attempts
            try:
                with open(USERS_JSON_FILE_PATH, "r", encoding="UTF-8", newline="") as file:
                    user_data_list = json.load(file)
            except FileNotFoundError:
                user_data_list = []

            del user_data_list[self.cripto.n_dict]
            user_data_list.insert(self.cripto.n_dict, self.cripto.user_data_list[self.cripto.n_dict])
            with open(USERS_JSON_FILE_PATH, "w", encoding="UTF-8", newline="") as file:
                json.dump(user_data_list, file, indent=2)

        self.counter_pass = self.cripto.user_data_list[self.cripto.n_dict]["attempts_pass"][0]

        # Comprobamos si el usuario está bloqueado o lo bloqueamos
        # si supera los 6 intentos permitidos
        if (not self.maximum_attempts(self.counter_pass, "pass")):
            return
        
        # Comprobamos la contraseña
        if(not self.cripto.KDF_verify_password(self.password.get())):
            self.cripto.user_data_list[self.cripto.n_dict]["attempts_pass"][0] += 1
            # Actualizamos los atributos attempts
            try:
                with open(USERS_JSON_FILE_PATH, "r", encoding="UTF-8", newline="") as file:
                    user_data_list = json.load(file)
            except FileNotFoundError:
                user_data_list = []

            del user_data_list[self.cripto.n_dict]
            user_data_list.insert(self.cripto.n_dict, self.cripto.user_data_list[self.cripto.n_dict])
            with open(USERS_JSON_FILE_PATH, "w", encoding="UTF-8", newline="") as file:
                json.dump(user_data_list, file, indent=2)
            messagebox.showerror("Sign In Error", "Incorrect password")
            self.__sign_in_clicked()
            return
        
        # ------------- CON CADA INICIO DE SESIÓN CAMBIAMOS EL SALT Y LA CLAVE DE SESIÓN PÚBLICA
        try:
            with open(OFFERS_JSON_FILE_PATH, "r", encoding="UTF-8", newline="") as file:
                offers_data_list = json.load(file)
        except FileNotFoundError:
            offers_data_list = []

        for offer in offers_data_list:
            if(((self.cripto.decrypt_with_private_key(offer["user_seller"], KEY_PEM_PATH) == \
             self.cripto.decrypt_with_private_key(self.cripto.user_data_list[self.cripto.n_dict]["user_name"], KEY_PEM_PATH)))
               and (offer["accepted_offer"][0])):
                decrypted_offer_msg = self.cripto.decrypt_with_private_key(offer["accepted_offer"][0], KEY_USR_PATH + "key" + str(self.cripto.n_dict) + ".pem")
            
        derived_key_and_salt = self.cripto.KDF_derived_key_generate(self.password.get())
        usr_public_key = self.rsa.generate_private_key_usr(self.cripto.n_dict)
        num_offer = 0
        for offer in offers_data_list:
            if(((self.cripto.decrypt_with_private_key(offer["user_seller"], KEY_PEM_PATH) == \
                self.cripto.decrypt_with_private_key(self.cripto.user_data_list[self.cripto.n_dict]["user_name"], KEY_PEM_PATH)))
                and (offer["accepted_offer"][0])):
                offer["accepted_offer"][0] = self.rsa.encrypt_with_public_key_usr(decrypted_offer_msg, usr_public_key)
                del offers_data_list[num_offer]
                offers_data_list.insert(num_offer, offer)
            num_offer += 1

        with open(OFFERS_JSON_FILE_PATH, "w", encoding="UTF-8", newline="") as file:
            json.dump(offers_data_list, file, indent=2)

        usr_certificate = self.rsa.user_pem_certificate
        self.cripto.user_data_list[self.cripto.n_dict]["user_pass"] = base64.b64encode(derived_key_and_salt[0]).decode('ascii')
        self.cripto.user_data_list[self.cripto.n_dict]["user_salt"] = base64.b64encode(derived_key_and_salt[1]).decode('ascii')      
        self.cripto.user_data_list[self.cripto.n_dict]["user_public_key"] = usr_public_key.decode("ascii")
        self.cripto.user_data_list[self.cripto.n_dict]["user_certificate"] = usr_certificate.decode("ascii")


        # Actualizamos la base de datos
        try:
            with open(USERS_JSON_FILE_PATH, "r", encoding="UTF-8", newline="") as file:
                user_data_list = json.load(file)
        except FileNotFoundError:
            user_data_list = []

        del user_data_list[self.cripto.n_dict]
        user_data_list.insert(self.cripto.n_dict, self.cripto.user_data_list[self.cripto.n_dict])
        with open(USERS_JSON_FILE_PATH, "w", encoding="UTF-8", newline="") as file:
            json.dump(user_data_list, file, indent=2)
        
        self.__sign_in_input_authen_2()


    def __sign_in_authentication_2(self):

        self.counter_code_expiration = self.cripto.user_data_list[self.cripto.n_dict]["attempts_code"][1]
        if ((time.time()-self.counter_code_expiration) > 1800): #30 minutos
            self.cripto.user_data_list[self.cripto.n_dict]["attempts_code"][0] = 0
            self.cripto.user_data_list[self.cripto.n_dict]["attempts_code"][1] = time.time()
        self.counter_code = self.cripto.user_data_list[self.cripto.n_dict]["attempts_code"][0]
        # Comprobamos si el usuario está bloqueado o lo bloqueamos
        # si supera los 6 intentos permitidos
        if (not self.maximum_attempts(self.counter_code, "code")):
            return

        if(not self.cripto.TOKEN_verify_code(self.code.get())):
            self.cripto.user_data_list[self.cripto.n_dict]["attempts_code"][0] += 1
            messagebox.showerror("Sign In Error", "Incorrect code")
            self.__sign_in_input_authen_2()
            return

        self.__open_home_window()




    # --------------------- PREVISIÓN DE ATAQUES A FUERZA BRUTA ----------------------

    def maximum_attempts(self, counter: int, type: str):
        
        ret = True
        # Comprobamos si el usuario está bloquedo
        try:
            with open(BLOCKED_USERS_JSON_FILE_PATH, "r", encoding="UTF-8", newline="") as file:
                user_blocked_list = json.load(file)
        except FileNotFoundError:
            user_blocked_list = []

        n_block_dict = 0
        for dicti in user_blocked_list:
            if self.cripto.decrypt_with_private_key(dicti["user_name"], KEY_PEM_PATH) == \
            self.cripto.decrypt_with_private_key(self.cripto.user_data_list[self.cripto.n_dict]["user_name"], KEY_PEM_PATH):
                if (time.time()-float(dicti["blocked_time"]) > BLOCKED_TIME): 
                    del user_blocked_list[n_block_dict]
                    with open(BLOCKED_USERS_JSON_FILE_PATH, "w", encoding="UTF-8", newline="") as file:
                        json.dump(user_blocked_list, file, indent=2)
                else:
                    messagebox.showerror("Sign In Error", "Too many attempts, try again later")
                    ret = False
                    self.main()
                    
            n_block_dict += 1

        # Tras 6 intentos bloqueamos la cuenta para evitar un posible ataque por fuerza bruta
        if counter == 6:
            try:
                with open(BLOCKED_USERS_JSON_FILE_PATH, "r", encoding="UTF-8", newline="") as file:
                    user_blocked_list = json.load(file)
            except FileNotFoundError:
                user_blocked_list = []
            user_blocked_dict = {
                                "user_name": self.cripto.user_data_list[self.cripto.n_dict]["user_name"],
                                "blocked_time": time.time()
                                }
            user_blocked_list.append(user_blocked_dict)
            with open(BLOCKED_USERS_JSON_FILE_PATH, "w", encoding="UTF-8", newline="") as file:
                     json.dump(user_blocked_list, file, indent=2)

            if (type == "pass"): 
                self.cripto.user_data_list[self.cripto.n_dict]["attempts_pass"][0] = 0
            else:
                self.cripto.user_data_list[self.cripto.n_dict]["attempts_code"][0] = 0

            messagebox.showerror("Sign In Error", "Too many attempts, try again later")
            ret = False
            self.main()
            
        # Actualizamos los atributos attempts
        try:
            with open(USERS_JSON_FILE_PATH, "r", encoding="UTF-8", newline="") as file:
                user_data_list = json.load(file)
        except FileNotFoundError:
            user_data_list = []

        del user_data_list[self.cripto.n_dict]
        user_data_list.insert(self.cripto.n_dict, self.cripto.user_data_list[self.cripto.n_dict])
        with open(USERS_JSON_FILE_PATH, "w", encoding="UTF-8", newline="") as file:
            json.dump(user_data_list, file, indent=2)
  
        return ret



    
    # ---------------------- HACER OFERTAS y GUARDARLAS ----------------------------

    def __confirm_offer(self):
        # Obtenemos los valores del entry
        try:
            self.offer_tokens = int(self.entry_tokens.get())
            self.offer_price = int(self.entry_priced.get())
        except ValueError:
            messagebox.showerror("Offer Error", "Incorrect value, must be an integer")
            self.__make_offer_clicked()
            return
        user_tokens = int(self.cripto.decrypt_with_private_key(self.cripto.user_data_list[self.cripto.n_dict]["user_tokens"], 
                                                               KEY_PEM_PATH))
        user_total_tokens_offered = int(self.cripto.decrypt_with_private_key(self.cripto.user_data_list[self.cripto.n_dict]["user_total_tokens_offered"], 
                                                                             KEY_PEM_PATH))
        user_total_tokens_offered += self.offer_tokens
        

        # Comprobamos que los valores son válidos 
        if (user_tokens < 1) or (user_tokens < self.offer_tokens) or \
           (self.offer_price > 100000) or (self.offer_price < 1):
            messagebox.showerror("Offer Error", "Incorrect values, must be an integer belonging to the indicated range")
            self.__make_offer_clicked()
            return
        elif (user_total_tokens_offered > user_tokens):
            messagebox.showerror("Offer Error", "You don't have more tokens to offer")
            self.__make_offer_clicked()
            return
        else:

            self.cripto.user_data_list[self.cripto.n_dict]["user_total_tokens_offered"] = \
            self.rsa.encrypt_with_public_key_server(str(user_total_tokens_offered))

            try:
                with open(USERS_JSON_FILE_PATH, "r", encoding="UTF-8", newline="") as file:
                    data_list = json.load(file)
            except FileNotFoundError:
                    data_list = []

            del data_list[self.cripto.n_dict]
            data_list.append(self.cripto.user_data_list[self.cripto.n_dict])
            with open(USERS_JSON_FILE_PATH, "w", encoding="UTF-8", newline="") as file:
                json.dump(data_list, file, indent=2)


            # ----------------------- FIRMA DIGITAL DEL USUARIO: OFERTANTE--------------------

            # Generamos el hash hmac mediante el mesaje (oferta) que será:
            # user_name, tokens_offered, price_offered -> YA LO HACE LA FUNCIÓN DE FIRMA
            oferta = str(self.cripto.decrypt_with_private_key(self.cripto.user_data_list[self.cripto.n_dict]["user_name"], KEY_PEM_PATH)) + \
                     str(self.offer_tokens) + str(self.offer_price)
            signature = self.cripto.signing_with_private_key_RSA(oferta, KEY_USR_PATH + "key" + str(self.cripto.n_dict) + ".pem")
            
            # Verificamos el cetificado del servidor y obtenemos su clave publica
            server_certificate = self.rsa.server_certificate
            # Cadena de validación
            certificate_validiting = server_certificate
            reliable = False
            for authority in self.rsa.server_certificate_chaining:
                A_certificate_pem = authority.encode('ascii')
                A_certificate = load_pem_x509_certificate(A_certificate_pem)
                A_public_key = A_certificate.public_key()

                if(not self.cripto.certificate_validation(certificate_validiting, A_certificate, A_public_key, 
                                                          self.CRL, self.CRL_builder)):
                    messagebox.showerror("Publish Offer Error", "Incorrect public key or not valid, please sign in again")
                    self.__make_offer_clicked()
                    return
                
                # Cuando llegue a una autoridad de la que me fío, paro
                if(str(A_certificate.subject) in self.cripto.user_data_list[self.cripto.n_dict]["reliable_authorities"]):
                    certificate_validiting = A_certificate
                    if(not self.cripto.certificate_validation(certificate_validiting, A_certificate, A_public_key, 
                                                              self.CRL, self.CRL_builder)):
                        messagebox.showerror("Publish Offer Error", "Incorrect public key or not valid, please sign in again")
                        self.__make_offer_clicked()
                        return
                    reliable = True 
                else:
                    certificate_validiting = A_certificate

            # Si no te fías de las autoridades salta error
            if not reliable:
                messagebox.showerror("Publish Offer Error", "Public key not reliable")
                self.__make_offer_clicked()
                return
            
            # Encriptamos la oferta, la public_key que se usa en la función es la 
            # que se corresponde con el certificado
            oferta_encrypted = self.rsa.encrypt_with_public_key_server(oferta)

            self.__publish_offer(signature, oferta_encrypted)

    

    def __publish_offer(self, signature, oferta_encrypted):

        # --------------------------- COMPROBAR FIRMA DIGITAL Y HASH DEL OFERTANTE -----------------------------------
        # Antes de publicar la oferta comprobamos su autenticidad e integridad
        # mediante la verificación del hash, al igual que autenticar con la firma
        public_key_usr = self.cripto.user_data_list[self.cripto.n_dict]["user_public_key"]
        oferta = self.cripto.decrypt_with_private_key(oferta_encrypted, KEY_PEM_PATH)
        if not self.rsa.verify_signature_RSA_with_public_key(signature, oferta, public_key_usr.encode('ascii')):
            messagebox.showerror("Offer Error", "The data provided may have been corrupted, please try again")
            self.__make_offer_clicked()
            return


        # Guardamos la oferta en el json con su hmac
        try:
            with open(OFFERS_JSON_FILE_PATH, "r", encoding="UTF-8", newline="") as file:
                self.offer_list = json.load(file)
        except FileNotFoundError:
            self.offer_list = []

        offer_dict = {"user_seller": self.cripto.user_data_list[self.cripto.n_dict]["user_name"], # Ya está encriptado
                      "tokens_offered": self.offer_tokens,
                      "price_offered": self.offer_price, 
                      "accepted_offer": [False, None, None]}
        self.offer_list.append(offer_dict)
        with open(OFFERS_JSON_FILE_PATH, "w", encoding="UTF-8", newline="") as file:
            json.dump(self.offer_list, file, indent=2)

        # ----------------- FIRMA DIGITAL DEL SISTEMA -------------------------------
        message = "Offer Published Successfully"
        # Firma del hash
        signature = self.cripto.signing_with_private_key_RSA(message, KEY_PEM_PATH)
        # Comprobamos el certificado y la clave pública del usuario
        usr_public_key_pem = self.cripto.user_data_list[self.cripto.n_dict]["user_public_key"].encode('ascii')
        usr_certificate_pem = self.cripto.user_data_list[self.cripto.n_dict]["user_certificate"].encode('ascii')
        usr_certificate = load_pem_x509_certificate(usr_certificate_pem)
        # Cadena de validación
        certificate_validiting = usr_certificate
        reliable = False
        for authority in self.cripto.user_data_list[self.cripto.n_dict]["certificate_chain"]:
            A_certificate_pem = authority.encode('ascii')
            A_certificate = load_pem_x509_certificate(A_certificate_pem)
            A_public_key = A_certificate.public_key()

            if(not self.cripto.certificate_validation(certificate_validiting, A_certificate, A_public_key, 
                                                      self.CRL, self.CRL_builder)):
                messagebox.showerror("Publish Offer Error", "Incorrect public key or not valid, please sign in again")
                self.__make_offer_clicked()
                return
            
            # Como me fío de AC, compruebo que efectivamente le esta certificando AC
            if(str(A_certificate.subject) == "<Name(CN=AC)>"):
                # AC se certifica a sí mismo puesto que es la autoridad máxima
                if(not self.cripto.certificate_validation(A_certificate, A_certificate, A_public_key, 
                                                          self.CRL, self.CRL_builder)):
                    messagebox.showerror("Publish Offer Error", "Incorrect public key or not valid, please sign in again")
                    self.__make_offer_clicked()
                    return
                reliable = True 
            else:
                certificate_validiting = A_certificate
                
        # Si no te fías de las autoridades salta error
        if not reliable:
            messagebox.showerror("Publish Offer Error", "Public key not reliable")
            self.__make_offer_clicked()
            return
        
        # Encriptamos mensaje, la clave publica es la que se corresponde con  el certificado
        encrypted_message = self.rsa.encrypt_with_public_key_usr(message, usr_public_key_pem)
        self.__open_home_window(encrypted_message, signature)


     
    def __accept_offer(self, index: int, tokens_offered, price_offered, signature, compra_encrypted):

        # ------------------ COMPROBAR FIRMA DIGITAL Y HASH DEL COMPRADOR ---------------

        # Comprobamos que la información no se ha corrompido y autenticamos
        # su origen, comprobando el hash y firma
        public_key_usr = self.cripto.user_data_list[self.cripto.n_dict]["user_public_key"]
        compra = self.cripto.decrypt_with_private_key(compra_encrypted, KEY_PEM_PATH)
        if not self.rsa.verify_signature_RSA_with_public_key(signature, compra, public_key_usr.encode('ascii')):
            messagebox.showerror("Purchase Error", "The request to accept an offer may have been corrupted, please try again")
            self.__open_home_window()
            return
        
        # ----------------- FIRMA DIGITAL DEL SISTEMA -------------------------------
        message_buy = "Purchase Completed Successfully"
        # Firmamos el hash
        signature_buy = self.cripto.signing_with_private_key_RSA(message_buy, KEY_PEM_PATH)
        # Comprobamos el certificado y la clave pública del usuario
        usr_public_key_pem = self.cripto.user_data_list[self.cripto.n_dict]["user_public_key"].encode('ascii')
        usr_certificate_pem = self.cripto.user_data_list[self.cripto.n_dict]["user_certificate"].encode('ascii')
        usr_certificate = load_pem_x509_certificate(usr_certificate_pem)
        # Cadena de validación
        certificate_validiting = usr_certificate
        reliable = False
        for authority in self.cripto.user_data_list[self.cripto.n_dict]["certificate_chain"]:
            A_certificate_pem = authority.encode('ascii')
            A_certificate = load_pem_x509_certificate(A_certificate_pem)
            A_public_key = A_certificate.public_key()

            if(not self.cripto.certificate_validation(certificate_validiting, A_certificate, A_public_key, 
                                                      self.CRL, self.CRL_builder)):
                messagebox.showerror("Purchase Error", "Incorrect public key or not valid, please sign in again")
                self.__open_home_window()
                return
            
            # Como me fío de AC, compruebo que efectivamente le esta certificando AC
            if(str(A_certificate.subject) == "<Name(CN=AC)>"):
                # AC se certifica a sí mismo puesto que es la autoridad máxima
                if(not self.cripto.certificate_validation(A_certificate, A_certificate, A_public_key, 
                                                          self.CRL, self.CRL_builder)):
                    messagebox.showerror("Purchase Error", "Incorrect public key or not valid, please sign in again")
                    self.__open_home_window()
                    return
                reliable = True
            else:
                certificate_validiting = A_certificate

        if not reliable:
            messagebox.showerror("Purchase Error", "Public key not reliable")
            self.__open_home_window()
            return
        
        # Encriptamos mensaje, la clave publica es la que se corresponde con  el certificado
        encrypted_message_buy = self.rsa.encrypt_with_public_key_usr(message_buy, usr_public_key_pem)
        
        # Le sumamos los tokens al comprador
        self.cripto.user_data_list[self.cripto.n_dict]["user_tokens"] = \
        self.rsa.encrypt_with_public_key_server(str(int(self.cripto.decrypt_with_private_key(
                                                self.cripto.user_data_list[self.cripto.n_dict]["user_tokens"],
                                                KEY_PEM_PATH)) + int(tokens_offered)))


        # Lo actualizamos en la base de datos
        try:
            with open(USERS_JSON_FILE_PATH, "r", encoding="UTF-8", newline="") as file:
                user_data_list = json.load(file)
        except FileNotFoundError:
            user_data_list = []
 
        del user_data_list[self.cripto.n_dict]
        user_data_list.insert(self.cripto.n_dict, self.cripto.user_data_list[self.cripto.n_dict])
        with open(USERS_JSON_FILE_PATH, "w", encoding="UTF-8", newline="") as file:
            json.dump(user_data_list, file, indent=2)

        try:
            with open(OFFERS_JSON_FILE_PATH, "r", encoding="UTF-8", newline="") as file:
                offers_list = json.load(file)
        except FileNotFoundError:
            offers_list = []

        # ----------------- FIRMA DIGITAL DEL SISTEMA ------------------------------
       
        # Mediante index, podemos obtener el diccionario de la oferta
        # y marcarla como aceptada
        message_sell = str("Your offer of " + tokens_offered + "tokens for the price of " + price_offered + \
                    "euros has been accepted")
        # Firma del hash
        signature_sell = self.cripto.signing_with_private_key_RSA(message_sell, KEY_PEM_PATH)
        
        # Comprobamos el certificado y la clave pública del usuario vendedor
        for dicti in user_data_list:
            if (self.cripto.decrypt_with_private_key(self.offer_list[index]["user_seller"], KEY_PEM_PATH) == \
                self.cripto.decrypt_with_private_key(dicti["user_name"], KEY_PEM_PATH)):
                usr_public_key_pem = dicti["user_public_key"].encode('ascii')
                usr_certificate_pem = dicti["user_certificate"].encode('ascii')
                usr_certificate = load_pem_x509_certificate(usr_certificate_pem)

        # Cadena de validación
        certificate_validiting = usr_certificate
        reliable = False
        for authority in self.cripto.user_data_list[self.cripto.n_dict]["certificate_chain"]:
            A_certificate_pem = authority.encode('ascii')
            A_certificate = load_pem_x509_certificate(A_certificate_pem)
            A_public_key = A_certificate.public_key()

            if(not self.cripto.certificate_validation(certificate_validiting, A_certificate, A_public_key, 
                                                      self.CRL, self.CRL_builder)):
                messagebox.showerror("Purchase Error", "Incorrect public key or not valid, please sign in again")
                self.__make_offer_clicked()
                return
            
            # Como me fío de AC, compruebo que efectivamente le esta certificando AC
            if(str(A_certificate.subject) == "<Name(CN=AC)>"):
                # AC se certifica a sí mismo puesto que es la autoridad máxima
                if(not self.cripto.certificate_validation(A_certificate, A_certificate, A_public_key, 
                                                          self.CRL, self.CRL_builder)):
                    messagebox.showerror("Purchase Error", "Incorrect public key or not valid, please sign in again")
                    self.__make_offer_clicked()
                    return
                reliable = True
            else:
                certificate_validiting = A_certificate

        if not reliable:
            messagebox.showerror("Purchase Error", "Public key not reliable")
            self.__make_offer_clicked()
            return
        
        # Encriptamos mensaje, la clave publica es la que se corresponde con  el certificado
        encrypted_message_sell = self.rsa.encrypt_with_public_key_usr(message_sell, usr_public_key_pem)

        self.offer_list[index]["accepted_offer"] = [encrypted_message_sell, base64.b64encode(signature_sell).decode('ascii'), 
                                                    self.rsa.public_pem_server.decode('ascii')]


        del offers_list[index]
        offers_list.insert(index, self.offer_list[index])
        with open(OFFERS_JSON_FILE_PATH, "w", encoding="UTF-8", newline="") as file:
            json.dump(offers_list, file, indent=2)

        self.__open_home_window(encrypted_message_buy, signature_buy)   



    def __sell_offer(self, tokens_offered):
        # Restamos los tokens vendidos
        self.cripto.user_data_list[self.cripto.n_dict]["user_tokens"] = \
        self.rsa.encrypt_with_public_key_server(str(int(self.cripto.decrypt_with_private_key(
                                                    self.cripto.user_data_list[self.cripto.n_dict]["user_tokens"], 
                                                    KEY_PEM_PATH))-int(tokens_offered)))
        
        # Lo actualizamos en la base de datos
        try:
            with open(USERS_JSON_FILE_PATH, "r", encoding="UTF-8", newline="") as file:
                user_data_list = json.load(file)
        except FileNotFoundError:
            user_data_list = []

        del user_data_list[self.cripto.n_dict]
        user_data_list.insert(self.cripto.n_dict, self.cripto.user_data_list[self.cripto.n_dict])
        with open(USERS_JSON_FILE_PATH, "w", encoding="UTF-8", newline="") as file:
            json.dump(user_data_list, file, indent=2)

        self.__open_home_window()  



    # ------------------ HOME WINDOW: BOTONES DE COMPRAR Y OFERTAR TOKENS ------------------

    def __open_home_window(self, encrypted_message = None, signature = None): 

        # ----------------- VERIFICACIÓN FIRMA DIGITAL DEL SISTEMA ---------------------------
        if encrypted_message and signature:
            message = self.cripto.decrypt_with_private_key(encrypted_message, KEY_USR_PATH + "key" + str(self.cripto.n_dict) + ".pem")
            # El usuario comprueba la integridad, autenticación y no repudio
            # del mensaje del sistema comprobando su firma digital
            if not self.rsa.verify_signature_RSA_with_public_key(signature, message, self.rsa.public_pem_server):
                messagebox.showerror("Corrupt Information", "We are having some security problems")
                # Cerramos la aplicación para evitar un ataque
                self.root.destroy()
                return

            # Mostramos el mensaje una vez confirmado
            messagebox.showinfo("Information", message)

        # Abrimos pestaña de inicio
        self.__clear_frame()
        self.root.title("Tokens Market - Home")

        # Botón para ir hacia atrás
        btn1 = Button(self.root, text = "< BACK", fg = "red", 
                      command=self.__sign_in_clicked, width=8)
        btn1.place(relx=0.05, rely=0.06)

        # Nombre del usuario
        lbl = Label(self.root, text = self.cripto.decrypt_with_private_key(self.cripto.user_data_list[self.cripto.n_dict]["user_name"], KEY_PEM_PATH), 
                    bg="#424a57", fg="white", font=("Arial", 30))
        lbl.place(relx=0.5, rely=0.05)
        # Indicador de tokens
        coin_img_path = str(Path.cwd()) + "/assets/images/coin.png"
        coin = PhotoImage(file = coin_img_path)
        coin = coin.subsample(50, 50)
        coin_lbl = Label(self.root, image=coin, bg="#424a57")
        coin_lbl.image = coin 
        coin_lbl.place(relx=0.75, rely=0.06)

        lbl = Label(self.root, text = self.cripto.decrypt_with_private_key(self.cripto.user_data_list[self.cripto.n_dict]["user_tokens"], KEY_PEM_PATH), 
                    bg="#424a57", fg="white", font=("Arial", 30))
        lbl.place(relx=0.8, rely=0.05)

        # Listado de ofertas disponibles
        columns = ("TOKENS OFFERED", "PRICE")
        tree = ttk.Treeview(self.root, columns=columns, show="headings")
        tree.heading("TOKENS OFFERED", text="TOKENS OFFERED")
        tree.heading("PRICE", text="PRICE")
        tree.grid(row=0, column=0, sticky='nsew')
        tree.place(relx=0.15, rely=0.15, width=400, height=500)

        # Scrollbar para la lista
        scrollbar = Scrollbar(self.root, orient=VERTICAL, command=tree.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky='ns')
        scrollbar.place(relx=0.8, rely=0.15, width=20, height=500)

        # Botón de hacer oferta
        btn2 = Button(self.root, text = "MAKE AN OFFER", fg = "green", 
                      command=self.__make_offer_clicked, font=("Arial", 20), 
                      bg = "#a89732")
        btn2.place(relx=0.5, rely=0.86)

        # Insertamos las ofertas disponibles en la lista
        try:
            with open(OFFERS_JSON_FILE_PATH, "r", encoding="UTF-8", newline="") as file:
                self.offer_list = json.load(file)
        except FileNotFoundError:
            self.offer_list = []
        
        d = 0
        for dicti in self.offer_list:
            if (dicti["accepted_offer"][0]) and \
            (self.cripto.decrypt_with_private_key(dicti["user_seller"], KEY_PEM_PATH) == \
             self.cripto.decrypt_with_private_key(self.cripto.user_data_list[self.cripto.n_dict]["user_name"], KEY_PEM_PATH)):

                # ----------------- VERIFICACIÓN FIRMA DIGITAL DEL SISTEMA ---------------------------
                # El usuario comprueba la integridad, autenticación y no repudio
                # del mensaje del sistema comprobando su firma digital
                decrypted_message_sell = self.cripto.decrypt_with_private_key(dicti["accepted_offer"][0], KEY_USR_PATH + "key" + str(self.cripto.n_dict) + ".pem")

                if not self.rsa.verify_signature_RSA_with_public_key(base64.b64decode(dicti["accepted_offer"][1]), 
                                                decrypted_message_sell, dicti["accepted_offer"][2].encode('ascii')):
                    messagebox.showerror("Corrupt Information", "We are having some security problems")
                    # Cerramos la aplicación para evitar un ataques
                    self.root.destroy()
                    return

                # Mostramos mensaje de oferta aceptada
                messagebox.showinfo("Sale Information",  decrypted_message_sell)

                # Eliminamos la oferta de la base de datos
                del self.offer_list[d]
                with open(OFFERS_JSON_FILE_PATH, "w", encoding="UTF-8", newline="") as file:
                    json.dump(self.offer_list, file, indent=2)
                # Avisamos al vendedor de que ha sido aceptada su oferta y realizamos la transacción
                self.__sell_offer(dicti["tokens_offered"])
                return
            
            elif (not dicti["accepted_offer"][0]) and ((self.cripto.decrypt_with_private_key(dicti["user_seller"], KEY_PEM_PATH) == \
             self.cripto.decrypt_with_private_key(self.cripto.user_data_list[self.cripto.n_dict]["user_name"], KEY_PEM_PATH))):
                # Si la ofereta está disponible y es mía, la muestro indicando que es mía
                tree.insert("",END, values=("¡MINE! "+ str(dicti["tokens_offered"]), dicti["price_offered"]))
                
            elif (not dicti["accepted_offer"][0]):
                # Si la ofereta está disponible y no es mía, la muestro
                tree.insert("",END, values=(dicti["tokens_offered"], dicti["price_offered"]))
            d+=1

        # Define la función offer_clicked dentro de la clase
        def offer_clicked(event):  
            selected_item = tree.selection()
            if not selected_item:
                self.__open_home_window()
                return  # No se ha seleccionado ningún elemento
            
            # Obtén la columna donde se hizo clic
            column = tree.identify_column(event.x)
            
            # Si la columna es una columna de encabezado, no realices ninguna acción
            if column and "heading" in column:
                self.__open_home_window()
                return
            
            # Si la oferta es tuya no puedes aceptarla
            if tree.item(selected_item, "values")[0][0] == "¡":
                messagebox.showerror("Purchase Offer", "You can't accept your own offers")
                self.__open_home_window()
                return
            
            # Botón de confirmación de compra
            confirmation = messagebox.askquestion("Confirm Purchase", "Are you sure you want to buy these tokens?")
            if confirmation == "no":
                self.__open_home_window()
                return
            
            # ----------------------- FIRMA DIGITAL Y HASH DEL USUARIO: COMPRADOR--------------------
            if selected_item:
                index = int(tree.index(selected_item))
                tokens_offered = tree.item(selected_item, "values")[0]
                price_offered = tree.item(selected_item, "values")[1]
                # Generamos el hash y firma siendo el mensaje la oferta 
                # a aceptar y el usuario comprador: user_name, tokens, price
                compra = str(self.cripto.decrypt_with_private_key(self.cripto.user_data_list[self.cripto.n_dict]["user_name"], KEY_PEM_PATH)) +\
                         str(tokens_offered) + str(price_offered)
                signature = self.cripto.signing_with_private_key_RSA(compra, KEY_USR_PATH + "key" + str(self.cripto.n_dict) + ".pem")
               
                # Verificamos el cetificado del servidor y obtenemos su clave publica
                server_certificate = self.rsa.server_certificate   
                # Cadena de validación
                certificate_validiting = server_certificate
                reliable = False
                for authority in self.rsa.server_certificate_chaining:
                    A_certificate_pem = authority.encode('ascii')
                    A_certificate = load_pem_x509_certificate(A_certificate_pem)
                    A_public_key = A_certificate.public_key()

                    if(not self.cripto.certificate_validation(certificate_validiting, A_certificate, A_public_key, 
                                                              self.CRL, self.CRL_builder)):
                        messagebox.showerror("Offer Error", "Incorrect public key of the server or not valid, please sign in again")
                        self.__make_offer_clicked()
                        return
                    
                    # Cuando llegue a una autoridad de la que me fío, paro
                    if(str(A_certificate.subject) in self.cripto.user_data_list[self.cripto.n_dict]["reliable_authorities"]):
                        certificate_validiting = A_certificate
                        if(not self.cripto.certificate_validation(certificate_validiting, A_certificate, A_public_key, 
                                                                  self.CRL, self.CRL_builder)):
                            messagebox.showerror("Offer Error", "Incorrect public key of the server or not valid, please sign in again")
                            self.__make_offer_clicked()
                            return
                        reliable = True 
                    else:
                        certificate_validiting = A_certificate

                # Si no te fías de las autoridades salta error
                if not reliable:
                    messagebox.showerror("Offer Error", "Public key not reliable")
                    self.__make_offer_clicked()
                    return
                
                # Encriptamos el mensaje (compra), la public_key que se usa en la función es la 
                # que se corresponde con el certificado
                compra_encrypted = self.rsa.encrypt_with_public_key_server(compra)
                self.__accept_offer(index, tokens_offered, price_offered, signature, compra_encrypted)
                return

        # Asocia la función offer_clicked al evento de clic en el Treeview
        tree.bind("<ButtonRelease-1>", offer_clicked)
        


        


    # ------------------------- INTERFAZ --------------------------------------------

    def main(self):

        self.__clear_frame()
        # Título de la pestaña
        self.root.title("Tokens Market")

        # Mensaje de primera pestaña
        lbl = Label(self.root, text = "Do you want to sign up or sign in?")
        lbl.place(relx=0.35, rely=0.4)
        
        self.__sign_up()
        self.__sign_in()

    def __clear_frame(self):

        for widgets in self.root.winfo_children():
            widgets.destroy()

    def __sign_up(self):

        # Botón de sing up
        btn = Button(self.root, text = "Sign up", fg = "blue", command=self.__sign_up_clicked)   
        # Posición del botón en la pantalla
        btn.place(relx=0.4, rely=0.5)

    def __sign_up_clicked(self):

        # Ventana de registro
        self.__clear_frame()
        self.root.title("Tokens Market - Sign Up")
        # Nombre de usuario
        lbl = Label(self.root, text = "Username")
        lbl.place(relx=0.35, rely=0.4)
        self.username = Entry(self.root, width=10)
        self.username.place(relx=0.5, rely=0.4)
        # Contraseña
        lbl = Label(self.root, text = "Password")
        lbl.place(relx=0.35, rely=0.5)
        self.password = Entry(self.root, width=10)
        self.password.place(relx=0.5, rely=0.5)
        # Botón de enviar
        btn1 = Button(self.root, text = "CREATE ACCOUNT", fg = "green", command=self.__create_account_clicked)   
        btn1.place(relx=0.65, rely=0.5)
        btn2 = Button(self.root, text = "< BACK", fg = "red", command=self.main)
        btn2.place(relx=0.1, rely=0.1)


    def __sign_in(self):
        # Botón de sing up
        btn = Button(self.root, text = "Sign in", fg = "green", command=self.__sign_in_clicked)   
        btn.place(relx=0.55, rely=0.5)

    def __sign_in_clicked(self):

        # Ventana de registro
        self.__clear_frame()
        self.root.title("Tokens Market - Sign In")
        # Nombre de usuario
        lbl = Label(self.root, text = "Username")
        lbl.place(relx=0.35, rely=0.4)
        self.username = Entry(self.root, width=10)
        self.username.place(relx=0.5, rely=0.4)
        # Contraseña
        lbl = Label(self.root, text = "Password")
        lbl.place(relx=0.35, rely=0.5)
        self.password = Entry(self.root, width=10)
        self.password.place(relx=0.5, rely=0.5)
        # Botón de enviar
        btn1 = Button(self.root, text = "CONFIRM", fg = "green", command=self.__sign_in_authentication_1)   
        btn1.place(relx=0.65, rely=0.5)
        btn2 = Button(self.root, text = "< BACK", fg = "red", command=self.main)
        btn2.place(relx=0.1, rely=0.1)

    def __sign_in_input_authen_2(self):
        
        self.__clear_frame()
        self.root.title("Tokens Market - Two-factor authentication")
        btn = Button(self.root, text = "< BACK", fg = "red", command=self.__sign_in_clicked)
        btn.place(relx=0.1, rely=0.1)
        # Clave temporal
        lbl = Label(self.root, text = "Code")
        lbl.place(relx=0.35, rely=0.4)
        self.code = Entry(self.root, width=10)
        self.code.place(relx=0.5, rely=0.4)
        # Botón de enviar
        btn2 = Button(self.root, text = "CONFIRM", fg = "green", command=self.__sign_in_authentication_2)   
        btn2.place(relx=0.65, rely=0.5)
       
    def __make_offer_clicked(self):
        # Abrimos pestaña de hacer oferta
        self.__clear_frame()
        self.root.title("Tokens Market - Make an offer")
        
        # Botón para ir hacia atrás
        btn1 = Button(self.root, text = "< BACK", fg = "red", 
                      command=self.__open_home_window, width=8)
        btn1.place(relx=0.05, rely=0.06)

        # Campos para indicar tú oferta: tokens ofertados y su precio
        
        lbl1 = Label(self.root, text = "Tokens offered")
        lbl1.place(relx=0.3, rely=0.4)
        
        Var_text_tokens = StringVar(value="")
        Var_text_price = StringVar(value="")
        self.entry_tokens = Entry(self.root, textvariable=Var_text_tokens, 
                       width=20, fg="grey")
        self.entry_tokens.place(relx=0.5, rely=0.4)
        self.entry_tokens.insert(0, "1 - " + self.cripto.decrypt_with_private_key(self.cripto.user_data_list[self.cripto.n_dict]["user_tokens"], KEY_PEM_PATH))
        
        self.entry_tokens.bind("<FocusIn>", lambda event: self.entry_tokens.delete(0,"end")
                    if Var_text_tokens.get() == "1 - " + self.cripto.decrypt_with_private_key(self.cripto.user_data_list[self.cripto.n_dict]["user_tokens"], KEY_PEM_PATH) else None)
        self.entry_tokens.bind("<FocusOut>", lambda event: self.entry_tokens.insert(0, "1 - " + self.cripto.decrypt_with_private_key(self.cripto.user_data_list[self.cripto.n_dict]["user_tokens"],KEY_PEM_PATH)) 
                    if Var_text_tokens.get() == "" else None)
        
        self.entry_priced = Entry(self.root, textvariable=Var_text_price,width=20,fg="grey")
        self.entry_priced.place(relx=0.5, rely=0.5)
        self.entry_priced.insert(0, "1 - 100.000 €")
        self.entry_priced.bind("<FocusIn>", lambda event: self.entry_priced.delete(0,"end") 
                    if Var_text_price.get() == "1 - 100.000 €" else None)
        self.entry_priced.bind("<FocusOut>", lambda event: self.entry_priced.insert(0, "1 - 100.000 €") 
                    if Var_text_price.get() == "" else None)
        lbl2 = Label(self.root, text = "Price")
        lbl2.place(relx=0.35, rely=0.5)

        # Botón de confirmar
        btn = Button(self.root, text = "CONFIRM", fg = "green", command=self.__confirm_offer)   
        btn.place(relx=0.75, rely=0.5)


