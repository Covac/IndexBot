from User import User

class UserManager:
    def __init__(self):
        self.user_list = []
        self.banned = []

    def append(self,user):
        assert type(user) == User
        self.user_list.append(user)

    def appendBanned(self,user):
        assert type(user) == User
        self.banned.append(user)

    def clearUsers(self):
        self.user_list.clear()
        self.banned.clear()

    def getReadyUsers(self,thread):
        ready = []
        for u in self.user_list:
            if type(u.getSession(thread)) != str:
                ready.append(u)
        return ready