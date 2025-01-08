class Logging:
    PRETTY_LOGIN = True
    VERBOSE = False
    DEBUG = False

class Proxy:
    FULL_PROXY = False #Change to true to fully conceal your ip and dns
    USE_MTM = True #You must have Tor installed, MTM config should be done in its own folder
    #Right now this causes app to launch twice, probably some circual imports and such, but i have a BIGGER problem at hand

class Server:
    HOST_SERVER = True
    ONE_LINE_LOGS = True #To make remote server logs cleaner, no *** DONE *** and multi-line user info

class Tasks:
    RUN_TASKS = True