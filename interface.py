import tkinter as tk
from tkinter import *
from tkinter import messagebox
import json
from pathlib import Path


# GLOBAL VARIABLES  
USERS_JSON_FILE_PATH =  str(Path.cwd()) + "/data/users.json"
OFFERS_JSON_FILE_PATH = str(Path.cwd()) + "/data/offers.json"

class App(tk.Frame):

    def __init__(self):

        self.root = tk.Tk()
        super().__init__(self.root)

        # Fondo
        self.root.configure(bg="#424a57")

        # Tamaño de la ventana
        self.root.geometry("600x822")
        self.main()


    def main(self):

        self.clear_frame()
        # Título de la pestaña
        self.root.title("Tokens Market")

        # Mensaje de primera pestaña
        lbl = Label(self.root, text = "Do you want to sign up or sign in?")
        lbl.place(relx=0.35, rely=0.4)
        
        self.sign_up()
        self.sign_in()


    def clear_frame(self):

        for widgets in self.root.winfo_children():
            widgets.destroy()


    def sign_up(self):

        # Botón de sing up
        btn = Button(self.root, text = "Sign up", fg = "blue", command=self.sign_up_clicked)   
        # Posición del botón en la pantalla
        btn.place(relx=0.4, rely=0.5)


    def sign_up_clicked(self):

        # Ventana de registro
        self.clear_frame()
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
        btn1 = Button(self.root, text = "CREATE ACCOUNT", fg = "green", command=self.create_account_clicked)   
        btn1.place(relx=0.65, rely=0.5)
        btn2 = Button(self.root, text = "< BACK", fg = "red", command=self.main)
        btn2.place(relx=0.1, rely=0.1)
       

    def sign_in(self):

        # Botón de sing up
        btn = Button(self.root, text = "Sign in", fg = "green", command=self.sign_in_clicked)   
        btn.place(relx=0.55, rely=0.5)


    def sign_in_clicked(self):

        # Ventana de registro
        self.clear_frame()
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
        btn1 = Button(self.root, text = "CONFIRM", fg = "green", command=self.confirm_clicked)   
        btn1.place(relx=0.65, rely=0.5)
        btn2 = Button(self.root, text = "< BACK", fg = "red", command=self.main)
        btn2.place(relx=0.1, rely=0.1)


    def create_account_clicked(self):

        # Botón de confirmación de crear usuario
        confirmation = messagebox.askquestion("Confirm", "Are you sure?")
        if confirmation == "no":
            self.sign_up_clicked()
            return

        # Guardamos la información en un json
        try:
            with open(USERS_JSON_FILE_PATH, "r", encoding="UTF-8", newline="") as file:
                self.data_list = json.load(file)
        except FileNotFoundError:
            self.data_list = []

        # No guardaremos información repetida
        self.n_dict = 0
        for dicti in self.data_list:
            if self.username.get() == dicti["user_name"]:
                messagebox.showerror("Sign Up Error", "User already exists")
                self.sign_up_clicked()
                return
            self.n_dict += 1

        # Guardamos la información si no está repetida
        user_dict = {"user_name": self.username.get(),
                     "user_pass": self.password.get(),
                     "user_tokens": 5000}
        self.data_list.append(user_dict)
        with open(USERS_JSON_FILE_PATH, "w", encoding="UTF-8", newline="") as file:
            json.dump(self.data_list, file, indent=2)

        # Confirmación de registro correcto
        messagebox.showinfo("Registration Information", "Registration Completed Successfully")
        self.open_home_window()
 

    def confirm_clicked(self):

        # Confirmamos que el usuario existe
        try:
            with open(USERS_JSON_FILE_PATH, "r", encoding="UTF-8", newline="") as file:
                self.data_list = json.load(file)
        except FileNotFoundError:
            self.data_list = []
            
        # Comprobamos si su información existe
        self.n_dict = 0
        for dicti in self.data_list:
            if (self.username.get() == dicti["user_name"]) \
                and (self.password.get() == dicti["user_pass"]):
                # Abrimos la aplicación
                self.open_home_window()
                return
            self.n_dict += 1

        #  Mensaje de error
        messagebox.showerror("Sign In Error", "User not found or incorrect password")
        self.sign_in_clicked()
        return


    def open_home_window(self):
        # GLOBAL VARIABLES
        self.user_name = str(self.data_list[self.n_dict]["user_name"])
        self.user_tokens = self.data_list[self.n_dict]["user_tokens"]

        # Abrimos pestaña de inicio
        self.clear_frame()
        self.root.title("Tokens Market - Home")

        # Botón para ir hacia atrás
        btn1 = Button(self.root, text = "< BACK", fg = "red", 
                      command=self.sign_in_clicked, width=8)
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
        
        # Botón de hacer oferta
        btn2 = Button(self.root, text = "MAKE AN OFFER", fg = "green", 
                      command=self.make_offer_clicked, font=("Arial", 20), 
                      bg = "#a89732")
        btn2.place(relx=0.5, rely=0.8)
        
    def make_offer_clicked(self):
        # Abrimos pestaña de hacer oferta
        self.clear_frame()
        self.root.title("Tokens Market - Make an offer")
        
        # Botón para ir hacia atrás
        btn1 = Button(self.root, text = "< BACK", fg = "red", 
                      command=self.open_home_window, width=8)
        btn1.place(relx=0.05, rely=0.06)

        # Campos para indicar tú oferta: tokens ofertados y su precio
        
        lbl1 = Label(self.root, text = "Tokens offered")
        lbl1.place(relx=0.3, rely=0.4)
        
        Var_text_tokens = StringVar(value="")
        Var_text_price = StringVar(value="")
        entry1 = Entry(self.root, textvariable=Var_text_tokens, 
                       width=20, fg="grey")
        entry1.place(relx=0.5, rely=0.4)
        entry1.insert(0, "1 - " + str(self.user_tokens))
        entry1.bind("<FocusIn>", lambda event: entry1.delete(0,"end") 
                    if Var_text_tokens.get() == "1 - " + str(self.user_tokens) else None)
        entry1.bind("<FocusOut>", lambda event: entry1.insert(0, "1 - " + str(self.user_tokens)) 
                    if Var_text_tokens.get() == "" else None)
        
        entry2 = Entry(self.root, textvariable=Var_text_price,width=20,fg="grey")
        entry2.place(relx=0.5, rely=0.5)
        entry2.insert(0, "1 - 100.000 €")
        entry2.bind("<FocusIn>", lambda event: entry2.delete(0,"end") 
                    if Var_text_price.get() == "1 - 100.000 €" else None)
        entry2.bind("<FocusOut>", lambda event: entry2.insert(0, "1 - 100.000 €") 
                    if Var_text_price.get() == "" else None)
        lbl2 = Label(self.root, text = "Price")
        lbl2.place(relx=0.35, rely=0.5)
        
        
        
   

myapp = App()
myapp.mainloop()