import tkinter as tk
from sign_in_up import *

class App(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.pack()

        self.entrythingy = tk.Entry()
        self.entrythingy.pack()

        # Create the application variable.
        self.contents = tk.StringVar()
        # Set it to some value.
        self.contents.set("this is a variable")
        # Tell the entry widget to watch this variable.
        self.entrythingy["textvariable"] = self.contents

        # Define a callback for when the user hits return.
        # It prints the current value of the variable.
        self.entrythingy.bind('<Key-Return>',
                             self.print_contents)

    def print_contents(self, event):
        print("Hi. The current entry content is:",
              self.contents.get())

root = tk.Tk()

# Tamaño de la ventana
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
root.geometry(f"{screen_width}x{screen_height}")

#Fondo
root.configure(bg="#424a57")

# Sing in / Sing up
root.title("Sign In / Sign Up")

# Create a tab control
tab_control = ttk.Notebook(root)

# Create the sign-in and sign-up tabs
create_sign_in_tab(tab_control)
create_sign_up_tab(tab_control)

# Pack the tab control
tab_control.pack(expand=True)

# Start the Tkinter event loop
root.mainloop()



myapp = App(root)
myapp.mainloop()