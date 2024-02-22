from UserManager import *
from RequestsManager import *
#from threading import Lock
from config import *

accs = [] #20 accounts now!
with open('accounts.txt', 'r') as f:#only 1 empty lines is allowed at the end!
    for line in f:
        email, password = line.split()
        accs.append((email,password))

user_list = UserManager()
rm = RequestsManager()
responses = []
#stdout_lock = Lock()