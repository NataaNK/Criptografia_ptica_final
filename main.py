
from criptografia import Criptografia
from app import App

import re
import os
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
import cryptography.exceptions
import json
from pathlib import Path

cripto = Criptografia()
myapp = App(cripto)


myapp.mainloop()