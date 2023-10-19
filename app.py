import tkinter as tk
from tkinter import *
from tkinter import messagebox
from tkinter import ttk
import json
from pathlib import Path
from criptografia import Criptografia


# GLOBAL VARIABLES  
USERS_JSON_FILE_PATH =  str(Path.cwd()) + "/data/users.json"
OFFERS_JSON_FILE_PATH = str(Path.cwd()) + "/data/offers.json"

class App(tk.Frame):

    def __init__(self, cripto: Criptografia):

        # SISTEMA PARA CRIPTOGRAFÍA
        self.cripto = cripto

        self.root = tk.Tk()
        super().__init__(self.root)

        # Fondo
        self.root.configure(bg="#424a57")

        # Tamaño de la ventana
        self.root.geometry("600x822")
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
            messagebox.showerror("Sign Up Error", "Password not strong enough: Must have 8 characters,\n 1 uppercase, 1 lowercase, 1 number and 1 special character ")
            self.__sign_up_clicked()
            return
        
        # ---------------- ALMACENAMIENTO DE CONTRASEÑAS CON KDC Y SALT ----------------

        # Guardamos la clave derivada haciendo uso de KDF
        self.cripto.KDF_password_storage(self.username.get(),self.password.get(), 5000, 0)

        # Confirmación de registro correcto
        messagebox.showinfo("Registration Information", "Registration Completed Successfully")
        self.__open_home_window()



        
    # ------------------------------------- AUTENTICACIÓN -------------------------------------

    def __confirm_clicked(self):

        # Confirmamos que el usuario existe
        if(not self.cripto.KDF_verify_user_name(self.username.get())):
            messagebox.showerror("Sign In Error", "User not found")
            self.__sign_in_clicked()
            return
        
        # Comprobamos la contraseña
        if(not self.cripto.KDF_verify_password(self.password.get())):
            messagebox.showerror("Sign In Error", "Incorrect password")
            self.__sign_in_clicked()
            return

        self.__open_home_window()

        


    # ---------------------- CERTIFICADO - HACER OFERTAS y GUARDARLAS ----------------------------

    def __confirm_offer(self):
        # Obtenemos los valores del entry
        self.offer_tokens = float(self.entry_tokens.get())
        self.offer_price = float(self.entry_priced.get())
        self.data_list[self.cripto.n_dict]["user_total_tokens_offered"] += self.offer_tokens
        self.user_total_tokens_offered = self.data_list[self.cripto.n_dict]["user_total_tokens_offered"]

        # Comprobamos que los valores son válidos 
        if (self.user_tokens < 1) or (self.user_tokens < self.offer_tokens) or \
           (self.offer_price > 100000) or (self.offer_price < 1):
            
            messagebox.showerror("Offer Error", "Incorrect values")
            self.__make_offer_clicked()
            return
        elif (self.user_total_tokens_offered > self.user_tokens):
            messagebox.showerror("Offer Error", "You don't have more tokens to offer")
            self.__make_offer_clicked()
            return
        else:
            try:
                with open(USERS_JSON_FILE_PATH, "r", encoding="UTF-8", newline="") as file:
                    data_list = json.load(file)
            except FileNotFoundError:
                    data_list = []
                
            del data_list[self.cripto.n_dict]
            data_list.append(self.data_list[self.cripto.n_dict])
            with open(USERS_JSON_FILE_PATH, "w", encoding="UTF-8", newline="") as file:
                json.dump(data_list, file, indent=2)

            self.__publish_offer()


    def __publish_offer(self):

       # Guardamos la oferta en el json
        try:
            with open(OFFERS_JSON_FILE_PATH, "r", encoding="UTF-8", newline="") as file:
                self.offer_list = json.load(file)
        except FileNotFoundError:
            self.offer_list = []

        offer_dict = {"tokens_offered": self.offer_tokens,
                      "price_offered": self.offer_price}
        self.offer_list.append(offer_dict)
        with open(OFFERS_JSON_FILE_PATH, "w", encoding="UTF-8", newline="") as file:
            json.dump(self.offer_list, file, indent=2)
        
        self.__open_home_window()

        
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
        btn1 = Button(self.root, text = "CONFIRM", fg = "green", command=self.__confirm_clicked)   
        btn1.place(relx=0.65, rely=0.5)
        btn2 = Button(self.root, text = "< BACK", fg = "red", command=self.main)
        btn2.place(relx=0.1, rely=0.1)

    def __open_home_window(self):
        # GLOBAL VARIABLES
        self.user_name = self.cripto.user_data_list[self.cripto.n_dict]["user_name"]
        self.user_tokens = self.cripto.user_data_list[self.cripto.n_dict]["user_tokens"]

        # Abrimos pestaña de inicio
        self.__clear_frame()
        self.root.title("Tokens Market - Home")

        # Botón para ir hacia atrás
        btn1 = Button(self.root, text = "< BACK", fg = "red", 
                      command=self.__sign_in_clicked, width=8)
        btn1.place(relx=0.05, rely=0.06)

        # Nombre del usuario
        lbl = Label(self.root, text = self.user_name, 
                    bg="#424a57", fg="white", font=("Arial", 30))
        lbl.place(relx=0.6, rely=0.05)
        # Indicador de tokens
        coin_img_path = str(Path.cwd()) + "/assets/images/coin.png"
        coin = PhotoImage(file = coin_img_path)
        coin = coin.subsample(50, 50)
        coin_lbl = Label(self.root, image=coin, bg="#424a57")
        coin_lbl.image = coin 
        coin_lbl.place(relx=0.75, rely=0.06)

        lbl = Label(self.root, text = str(self.user_tokens), 
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
        btn2.place(relx=0.5, rely=0.8)

        # Insertamos las ofertas disponibles ne la lista
        try:
            with open(OFFERS_JSON_FILE_PATH, "r", encoding="UTF-8", newline="") as file:
                self.offer_list = json.load(file)
        except FileNotFoundError:
            self.offer_list = []
        
        for dicti in self.offer_list:
            
            # oferta = str(dicti["tokens_offered"])+ "✪" + str(dicti["price_offered"]) + "€"
            tree.insert("",END, values=(dicti["tokens_offered"], dicti["price_offered"]))
        
       
        
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
        self.entry_tokens.insert(0, "1 - " + str(self.user_tokens))
        
        # El texto escrito deberia ser negro pero es gris como lo q se superpone
        self.entry_tokens.bind("<FocusIn>", lambda event: self.entry_tokens.delete(0,"end")
                    if Var_text_tokens.get() == "1 - " + str(self.user_tokens) else None)
        self.entry_tokens.bind("<FocusOut>", lambda event: self.entry_tokens.insert(0, "1 - " + str(self.user_tokens)) 
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


