import tkinter as tk
from tkinter import *
from tkinter import messagebox
import json
from pathlib import Path

# GLOBAL VARIABLES  
JSON_FILE_PATH =  str(Path.cwd()) + "/users.json"

class App(tk.Frame):
    def __init__(self):

        self.root = tk.Tk()
        super().__init__(self.root)

        # Fondo
        self.root.configure(bg="#424a57")

        # Tamaño de la ventana
        self.root.geometry("600x822")

        # Título de la pestaña
        self.root.title("Tokens Market")

        # Mensaje de primera pestaña
        self.lbl = Label(self.root, text = "Do you want to sign up or sign in?")
        self.lbl.place(relx=0.35, rely=0.4)
        
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
        self.lbl = Label(self.root, text = "Username")
        self.lbl.place(relx=0.35, rely=0.4)
        self.username = Entry(self.root, width=10)
        self.username.place(relx=0.5, rely=0.4)
        # Contraseña
        self.lbl = Label(self.root, text = "Password")
        self.lbl.place(relx=0.35, rely=0.5)
        self.password = Entry(self.root, width=10)
        self.password.place(relx=0.5, rely=0.5)
        # Botón de enviar
        btn = Button(self.root, text = "SEND", fg = "green", command=self.SEND_clicked)   
        btn.place(relx=0.65, rely=0.5)
       
    def sign_in(self):
        # Botón de sing up
        btn = Button(self.root, text = "Sign in", fg = "green", command=self.sign_in_clicked)   
        btn.place(relx=0.55, rely=0.5)

    def sign_in_clicked(self):
        # Ventana de registro
        self.clear_frame()
        self.root.title("Tokens Market - Sign In")
        # Nombre de usuario
        self.lbl = Label(self.root, text = "Username")
        self.lbl.place(relx=0.35, rely=0.4)
        self.username = Entry(self.root, width=10)
        self.username.place(relx=0.5, rely=0.4)
        # Contraseña
        self.lbl = Label(self.root, text = "Password")
        self.lbl.place(relx=0.35, rely=0.5)
        self.password = Entry(self.root, width=10)
        self.password.place(relx=0.5, rely=0.5)
        # Botón de enviar
        btn = Button(self.root, text = "CONFIRM", fg = "green", command=self.CONFIRM_clicked)   
        btn.place(relx=0.65, rely=0.5)

    def SEND_clicked(self):
        # Botón de confirmación de crear usuario
        confirmation = messagebox.askquestion("Confirm", "Are you sure?")
        if confirmation == "no":
            self.sign_up_clicked()
            return

        # Guardamos la información en un json
        try:
            with open(JSON_FILE_PATH, "r", encoding="UTF-8", newline="") as file:
                data_list = json.load(file)
        except FileNotFoundError:
            data_list = []

        # No guardaremos información repetida
        for i in data_list:
            if self.username.get() in i:
                messagebox.showerror("Sign Up Error", "User already exists")
                self.sign_up_clicked()
                return

        else:
            messagebox.showerror("Sign Up Error", "User already exists")
            self.sign_up_clicked()
            return

        with open(JSON_FILE_PATH, "w", encoding="UTF-8", newline="") as file:
            json.dump(data_list, file, indent=2)
 
    def CONFIRM_clicked(self):
        # Confirmamos que el usuario existe
        try:
            with open(JSON_FILE_PATH, "r", encoding="UTF-8", newline="") as file:
                data_list = json.load(file)
        except FileNotFoundError:
            data_list = []
        # Comprobamos si su información existe
        if (self.username.get() in data_list) and (self.password.get() in data_list):
            # falta comprobacion de lista en json
            # Abrimos la aplicación
            self.open_home_window()
        else:
            #  Mensaje de error
            messagebox.showerror("Sign In Error", "User not found")
            self.sign_in_clicked()
            return

    def open_home_window(self):
        # Abrimos pestaña de inicio
        self.clear_frame()
        
   


myapp = App()
myapp.mainloop()