from globals import rm,user_list
from functions import *#test without all
from datetime import timedelta
from options import Server, Tasks
from requests.exceptions import RequestException
import traceback
import yaml
import copy

class MessageHandler():
    def __init__(self,pipe) -> None:
        self.pipe = pipe
        self.tasks = []#no reloads needed in case of failing I THINK?!?
        self.shared_history = []#Will make sure you never post to something ANY other account posted, only for tasks DUH!
        if Tasks.RUN_TASKS:
            self.loadTasks('tasks.yml')

    def loadTasks(self,tasks):
        ca = datetime.now(timezone.utc)
        with open(tasks,'r',encoding='utf-8') as t:
            tasks = yaml.safe_load(t)
        unpacked = []
        leftovers = []
        for t in tasks:
            t['createdAt'] = ca
            t['lastExeAt'] = ca
            t['history'] = []
            user = t.get('user', None)
            if isinstance(user, list):#Now multiple users can be added to 'user' field in tasks!
                for u in user:
                    unpackedTask = copy.deepcopy(t)
                    unpackedTask['user'] = u
                    unpacked.append(unpackedTask)
                leftovers.append(t)
        for left in leftovers:
            tasks.remove(left)
        tasks.extend(unpacked)
        self.tasks = tasks

    def doTasks(self):#looks like ip limit bs got confused and "FIXED?" after using proxies
        now = datetime.now(timezone.utc)
        time = now.time()
        try:
            for t in self.tasks:
                #schedule is optional
                startTime = t.get('start_time_utc', None)
                endTime = t.get('end_time_utc', None)
                #SHITPOST options, its nicer here
                aiComment = t.get('ai_generated', False) #Transforms comments into instructions for commenting on articles
                useRSS = t.get('use_rss_feed', False) # I will keep 'legacy' feed as main one because I doubt many use RSS which could be easily CUT or have traffic filtered and tracked
                sURL = t.get('feed', None)#specify feed to comment on, optional
                sharedHistoryEnabled = t.get('use_shared_history', False)# I suggest you use it because I recently had, 50% "attrition" on my new batch of accounts :(
                covert = t.get('low_profile', False)
                if (startTime != None) and (endTime != None):
                    startTime = datetime.strptime(startTime, '%H:%M:%S').time()
                    endTime = datetime.strptime(endTime, '%H:%M:%S').time()
                    if not(startTime <= time <= endTime):
                        continue
                tto = timedelta(seconds=t['timeout'])
                if (now - t['lastExeAt']) <tto:#first check against task timeout
                    continue

                if t['task'] == 'SHITPOST':
                    user = None
                    for u in user_list.user_list:
                        if u.email == t['user']:
                            user = u
                            break
                    if user == None:
                        print(t['user'] + ' NOT FOUND! Maybe he got banned :(',flush=True)
                        continue# need to add counters and timeouts for these so they don't spam logs, add more logic to fix
                    timeout = 3601 if user.new_user else 301#cleaner as 2 lines
                    timeout = timedelta(seconds=timeout)
                    if (now - user.last_comment_time) < timeout:
                        continue
                    if user.banned:#you should check periodically for bans yourself
                        continue #Well he shouldn't be banned since he would be is user_list.banned then
                    #NEXT WE DECIDE IF WE WANT TO USE SHARED HISTORY OR NOT!
                    if sharedHistoryEnabled:
                        #Extended history
                        history = t['history'].copy() + self.shared_history
                    else:
                        history = t['history']
                    if aiComment:# COMMENTS ARE NOW INSTRUCTIONS INSTEAD!
                        if isinstance(t['comments'], list):
                            t['comments'] = t['comments'][0]
                        elif isinstance(t['comments'], str):
                            pass
                        else:
                            print(f"Task {t['comment']} is BAD, removing associated task")
                            self.tasks.remove(t)
                    if sURL:
                        res, rj = doShitpost(user,t['comments'],history,covert,sURL,spoofBeacons=True,useAI=aiComment,useRSSFeed=useRSS)#well this ip restriction complicates things so I need whole response
                    else:#if used for longer change useAI into isAiGenerated and make it required
                        res, rj = doShitpost(user,t['comments'],history,covert,spoofBeacons=True,useAI=aiComment,useRSSFeed=useRSS)
                    if rj['success']:#if it failed, we are either banned OR posted to that thread already. Will succeed if we hit the end of list.
                        if Server.HOST_SERVER:
                            print(f"{t['task']} :: {user.username} | {user.email} | {user.public_url} TO -> {res[0]}", flush=True)#locally we know but on server we don't
                        t['lastExeAt'] = datetime.now(timezone.utc)
                        t['history'] += res
                        self.shared_history += res
                    else:#We have to analyze why task failed
                        reason = rj.get('error') or rj.get('reason')
                        if reason is None:
                            print(f'*CRITICAL?*Why did we fail? {rj}',flush=True)
                        else:
                            if reason['code'] == 14:#IP limiting
                                pass#we do nothing for now, we have about 15 seconds to try multiple ips
                            elif reason['code'] == 5:#We got banned, noticed that 2 of them got banned when dislikes per comment were over 2
                                self.tasks.remove(t)
                            elif reason['code'] == 400:
                                 print(f"{t['task']} :: {user.username} | {user.email} | {user.public_url} X--> FAILED, CODE = 400, *CUSTOM*\nINSIGHT:\n{reason['insight']}", flush=True)
                            elif reason['code'] == 429:#Groq error passed through, rate limit error, just wait for next iteration
                                print(f"{t['task']} :: {user.username} | {user.email} | {user.public_url} X--> FAILED, Rate Limited, CODE = 429", flush=True)
                                t['lastExeAt'] = datetime.now(timezone.utc)
                            else:#right now we don't care about other error
                                t['history'] += res#this is restart-proff, other errors we don't care about really...

                elif t['task'] == 'STALK':
                    res = doStalk(t['target'],t['type'],t['amount'],t['history'],t['lastExeAt'])
                    t['lastExeAt'] = datetime.now(timezone.utc)
                    t['history'] += res

                elif t['task'] == 'PRETEND':
                    user = None
                    for u in user_list.user_list:
                        if u.email == t['user']:
                            user = u
                            break
                    if user == None:
                        print(t['user'] + ' NOT FOUND! Maybe he got banned :(',flush=True)
                        continue
                    if user.banned:
                        continue 
                    t['lastExeAt'] = datetime.now(timezone.utc)
                    amount = t.get('amount', 1)
                    doFakeActivity(user,amount)#you can specify url if you wanna with specifyURL= needs logic first tho...

        except RequestException as e:#We want to capture error here
            print(f"Request exception {e} occured during {t['task']}, relogging the user!")
            if t['task'] == 'SHITPOST':
                newsession, *_ = login(user.email,user.password)
                user.session = newsession
            elif t['task'] == 'STALK':
                #if task falls we will just relog all but not before testing, not yet lol
                pass
        except Exception as e:
            trace = traceback.format_exc()
            print(trace, flush=True)
            if t['task'] == 'SHITPOST': #Removing shitpost tasks because of some ugly fails that wasted bandwidth
                print(f'{e} WAS CAUSED BY: {t} AND WAS REMOVED - USER: {user.username}', flush=True)
                self.tasks.remove(t) #I got random error because of ReqMan. assert r, looks like there is new filter from 28th
                #Right now I guess we are not removing anything because it will only fail because you are banned. And sadly get your logs flooded
            elif t['task'] == 'STALK':
                print(f'{e} WAS CAUSED BY: {t}')
        return None

    def handleMessages(self,command):
        if command[0] == 'login':
            login_all(accs)
            
        if command[0] == 'comment':
            url,comments = command[1],command[2]
            comment(url,comments)

        if command[0] == 'react':
            args = command[1]
            reactAmount = None
            if len(command) > 2:
                extendedArgs = command[2]
                reactAmount = int(extendedArgs[0])
                articleURL = str(extendedArgs[1])
            if args[1].isnumeric():
                comment_id,rType = int(args[0]),int(args[1])
            else:
                comment_id,rType = int(args[0]), None
            if len(args) > 2:
                timeout = int(args[2]) # this is unused, and might need to be 3
                massReact(comment_id,rType,timeout,rAmount=reactAmount,relatedArticleURL=articleURL)
            elif len(args) == 2:
                massReact(comment_id,rType,rAmount=reactAmount,relatedArticleURL=articleURL)

        if command[0] == 'inspect':
            args = command[1].split()
            if len(args) == 1:
                inspectUserProfile(args[0])
            elif len(args) == 2:
                inspectUserProfile(args[0],args[1])

        if command[0] == 'nuke':#needs fixing
            args = command[1]
            print(args)
            if len(args) == 2:
                nuke_profile(args[0],int(args[1]),userlist=user_list.user_list+user_list.banned)
            elif len(args) == 3:
                nuke_profile(args[0],int(args[1]),args[2],userlist=user_list.user_list+user_list.banned)

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

    def serve(self,cycle_seconds=118):#site auto refreshes every 5 mins, lowered a bit for tasks
        while True:
            try:
                if rm.sinceLastRefresh() >= rm.refreshEvery:
                    rm.refreshProxyList()
                for user in user_list.user_list+user_list.banned:
                    if user.sinceLastRefresh() > cycle_seconds:
                        rm.requestWithProxy('GET','https://www.index.hr/najnovije?kategorija=3',user.session,singleMode=True)
                        user.refreshMe()
                if (len(user_list.banned+user_list.user_list) > 0) and Tasks.RUN_TASKS:
                    self.doTasks()#comments now sadly need unique ips because some ips can get restricted or limited
                if self.pipe.poll(1):#ADJUST DEPENDING ON HOW MANY TASKS YOU HAVE, along with refreshEvery if you have a lot of them, refreshEvery from RequestsManager should be done less often or just BUY proxies.
                    command = self.pipe.recv()
                    self.handleMessages(command)#DO IT!
                    if not(Server.HOST_SERVER):
                        self.pipe.send(True)#we send someething to sync cli and this process outputs
                #We can refresh and handle even in different threads since they will be sleeping anyway.
            except Exception as e:#Need to better handle here!!!
                trace = traceback.format_exc()
                print(trace, flush=True)
                user_list.clearUsers()
                print('Background process experienced an error, attempting to restart...', flush=True)
                login_all(accs)

