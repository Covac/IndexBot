from datetime import datetime
import globals

class User:#we will make user timeSTAMP itself when post is completed, so we only pass user because this is functional stuff!
    def __init__(self,session,api_me_json,e,p):#do i keep it for reconnect?!?
        self.id = api_me_json['userId']
        self.email = e
        self.password = p
        self.username = api_me_json['fullName']
        self.comments = api_me_json['numberOfComments']
        self.new_user = api_me_json['isNewUser']
        self.last_comment_time = None
        self.session = session
        self.burned_threads = []#well we lose it with restarts, but with email and database we could keep it. so more work? We really don't need it yet!
        self.last_refresh = datetime.utcnow()
        self.updates = 0
        self.banned = api_me_json['isCommentingBanned']

    def getProfileData(self,skip=0,take=5):
        qsp = {'createdById': self.id,'skip': skip,'take':take}
        r = globals.rm.requestWithProxy('GET','https://www.index.hr/api/comments/user',self.session,singleMode=True,params=qsp)#If we care about faking we can add referer to /profil
        return r.json()
    
    def refreshMe(self):
        self.last_refresh = datetime.utcnow()

    def sinceLastRefresh(self):
        delta = datetime.utcnow() - self.last_refresh
        return delta.total_seconds()

    def prepMe(self):#we will call this to get last_comment_time and later we could use it to load burned_threads but that might cause some suspicion, i also think that since we always want to comment on newset news automatically this won't be a problem for crawler,
                     #we will use last_comment_time as reference for what is new and what is old most likely
        try:
            pd = self.getProfileData()
            date = datetime.fromisoformat(pd['comments'][0]['createdDateUtc'])
            self.last_comment_time = date
        except:
            print("New account or BANNED?")

    def aboutMe(self):
        r = 'UNKNOWN'
        if self.last_comment_time != None:
            d = datetime.utcnow()-self.last_comment_time
            hours,remainder = divmod(d.total_seconds(),3600)
            minutes,seconds = divmod(remainder, 60)
            r = f'{int(hours)}H {int(minutes)}M {int(seconds)}S'
        print(f'User: {self.username}\nNumber of comments: {self.comments}\nLast commented {r} ago\nNew user?: {self.new_user}\nBANNED?: {self.banned}')

    def getSession(self,thread):
        #check if burned
        check_threads = thread in self.burned_threads
        if check_threads:
            print(f'{self.username} burned thread {thread}')
            return 'BURNED'
        if self.last_comment_time == None and not check_threads:
            return self.session
        elif (datetime.utcnow()-self.last_comment_time).seconds > 300 and not check_threads and self.comments >= 10:#THIS CAN FAIL if its None and there is a burned thread, which would be weird.
            return self.session
        elif (datetime.utcnow()-self.last_comment_time).seconds > 3600 and not check_threads and self.comments < 10:
            return self.session
        else:
            return 'STILL ON COOLDOWN'

    def burnThread(self,thread):
        self.burned_threads.append(thread)
        self.last_comment_time = datetime.utcnow()
        self.comments += 1