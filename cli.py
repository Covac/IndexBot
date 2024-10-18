import cmd
#from globals import user_list,accs
from functions import *
from os import system

class InteractiveConsole(cmd.Cmd):
    prompt = "IndexBot>>> "

    def __init__(self, pipe):
        super().__init__()
        self.pipe = pipe

    def cmdloop(self, intro=None):#After finishing MessageHandler add to wait for server response
        while True:
            try:
                line = input(self.prompt)
                if line.strip() =='':
                    print("Empty commands forbidden, if you want repetition use arrow keys!")
                else:
                    stop = self.onecmd(line)
                    if stop:
                        break
            except KeyboardInterrupt:
                print("Keyboard interrupt detected! Exiting...")
                break

    def waitForHandler(self):
        self.pipe.recv()

    def do_comment(self, arg):
        args = arg.split("|")
        assert len(args) >= 2
        url = args[0]
        comments = list(args[1:])
        self.pipe.send(['comment',url,comments])
        self.waitForHandler()

    def do_login(self, arg):#former login_all
        self.pipe.send(['login'])
        self.waitForHandler()

    def do_help(self, arg):
        #Show help information.
        self.pipe.send(['help'])
        self.waitForHandler()

    def do_quit(self, arg):
        #Exit the program.
        self.pipe.send(['quit'])
        quit_program()
        return True
    
    def do_cls(self, arg):
        system('cls')#works on PS

    #I should add a place for option setting
    
    def do_dap(self, arg):
        #try:
        if arg:
            try:
                args = arg.split()
                a=int(args[0])#this fails so we are kinda safe when sending and receiving
                self.pipe.send(['dap',a])
                self.waitForHandler()
            except:
                print('That was not a number.')
        else:
            display_all_profiles()
            self.pipe.send(['dap'])#maybe add some arg anyway for simplicity?
            self.waitForHandler()

    def do_backup(self, arg):#move this logic to functions!
        #backup all logged in users
        self.pipe.send(['backup'])
        self.waitForHandler()
        
    def do_react(self, arg):
        args = arg.split("|")
        assert len(args) >= 2
        self.pipe.send(['react',args])
        self.waitForHandler()

    def do_nuke(self, arg):
        args = arg.split()
        assert len(args) >= 2
        self.pipe.send(['nuke',args])
        self.waitForHandler()

    def do_inspect(self,arg):
        self.pipe.send(['inspect',arg])
        self.waitForHandler()