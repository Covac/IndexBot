from cli import *
from MessageHandler import *
from multiprocessing import Process, Pipe

if __name__ == "__main__":
    try:
        cliPipe, botPipe = Pipe()
        messageHandler = MessageHandler(botPipe)
        mhProcess = Process(target=messageHandler.serve)
        mhProcess.start()
        console = InteractiveConsole(cliPipe)
        console.cmdloop("Dobrodošao u troll prompt hue hue hue!")
    except Exception as e:
        print(e)
        input()
