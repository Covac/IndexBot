from globals import rm,user_list#maybe we don't do it here? okay we do we want to reuse a LOT
from functions import *#test without all

class MessageHandler():
    def __init__(self,pipe) -> None:
        self.pipe = pipe

    def handleMessages(self,command):
        if command[0] == 'login':
            login_all(accs)
            
        if command[0] == 'comment':
            url,comments = command[1],command[2]
            comment(url,comments)

        if command[0] == 'react':
            args = command[1]
            if args[1].isnumeric():
                comment_id,rType = int(args[0]),int(args[1])
            else:
                comment_id,rType = int(args[0]), None
            if len(args) > 2:
                timeout = int(args[2])
                massReact(comment_id,rType,timeout)
            elif len(args) == 2:
                massReact(comment_id,rType)

        if command[0] == 'inspect':
            args = command[1].split()
            if len(args) == 1:
                inspectUserProfile(args[0])
            elif len(args) == 2:
                inspectUserProfile(args[0],args[1])

        if command[0] == 'dap':
            if len(command) == 1:
                display_all_profiles()
            elif len(command) == 2:
                display_all_profiles(command[1])

        if command[0] == 'backup':
            backupUsers()

        if command[0] == 'help':
            show_help()

        if command[0] == 'quit':
            quit_program()#we call it here and main because it exits the process anyway

    def serve(self,cycle_seconds=120):#site auto refreshes every 5 mins
        while True:
            if rm.sinceLastRefresh() >= rm.refreshEvery:
                rm.refreshProxyList()
            for user in user_list.user_list+user_list.banned:
                if user.sinceLastRefresh() > cycle_seconds:
                    rm.requestWithProxy('GET','https://www.index.hr/najnovije?kategorija=3',user.session,singleMode=True)
                    user.refreshMe()
            if self.pipe.poll(3):
                command = self.pipe.recv()
                self.handleMessages(command)#DO IT!
                self.pipe.send(True)#we send someething to sync cli and this process outputs
            #We can refresh and handle even in different threads since they will be sleeping anyway.