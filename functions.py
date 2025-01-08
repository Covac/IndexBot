import re
import json
import groq #Just for error handling
import requests
import xml.etree.ElementTree as ET
from time import sleep
from random import randint,choice
from globals import *
from headers import *
from options import Server, Logging
from config import accountAmount
from urllib.parse import urlparse, parse_qs
from urllib3 import disable_warnings
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
if Logging.PRETTY_LOGIN:
    from prettytable import PrettyTable

disable_warnings()

def findRVT(text,length=155):#write decorators for these 3
    try:
        MATCH = re.search('"__RequestVerificationToken" type="hidden" value="',text)
        rvt = text[MATCH.span()[1]:MATCH.span()[1]+length]#logout and react use 198
        return rvt
    except Exception as e:
        print(e)
        raise RuntimeError("Cloudflare or you did something wrong!")

def findThread(text):
    MATCH = re.search('commentThreadId=',text)
    thread = text[MATCH.span()[1]:MATCH.span()[1]+7]
    return int(thread)

def findUserId(text):
    MATCH = re.search('userId: ',text)
    MATCH2 = re.search(', isOwner:',text)
    uid = text[MATCH.span()[1]:MATCH2.span()[0]]
    return int(uid)

def findServerResponse(text):
    MATCH = re.search("name=\'id_token\' value=\'",text)#not static length, 31st of May 2024, maybe it is fixed 1200 now
    MATCH2 = re.search("\' />\n<input type=\'hidden\' name=\'scope\' value=\'openid profile\'",text)
    id_token = text[MATCH.span()[1]:MATCH2.span()[0]]
    MATCH = re.search("name=\'scope\' value=\'",text)
    scope = text[MATCH.span()[1]:MATCH.span()[1]+14]
    MATCH = re.search("name=\'state\' value=\'",text)
    state = text[MATCH.span()[1]:MATCH.span()[1]+368]#582, 31st of May 2024, before some outage of some sort, but then went back to old 368
    MATCH = re.search("name=\'session_state\' value=\'",text)
    session_state = text[MATCH.span()[1]:MATCH.span()[1]+76]
    form = {"id_token":id_token,"scope":scope,"state":state,"session_state":session_state}
    return form

def extractTrackingBeaconData(text):
    title_match = re.search(r'var title\s*=\s*"([^"]+)"', text)
    title = title_match.group(1) if title_match else None

    # Extract the parameters from InitTracking
    init_tracking_match = re.search(r"articleService\.InitTracking\(([^)]+)\)", text)
    
    if init_tracking_match:
        params = init_tracking_match.group(1).split(',')
        article_id = params[1].strip().strip("'")
        root_category_id = params[2].strip().strip("'")
        # Title is already captured separately, so skip params[3]
        hours_old = params[4].strip().strip("'").replace(',', '.')
    else:
        article_id = root_category_id = hours_old = None

    seconds = 60
    extracted_data = {
        "article_id": article_id,
        "hours_old": hours_old,
        "seconds": seconds,
        "title": title,
        "root_category_id": root_category_id
    }
    return extracted_data

def queryStringParameters(url):#Well for now I only need ReturnUrl so we keep it simple
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    return query_params['ReturnUrl'][0]

"""
def getFreshProxies():#We could have had one pretty oneliner if we didn't want unique proxies
    pr = requests.get(proxyLink)
    proxies = [x.replace("socks5","socks5h") for x in pr.text.split('\r\n') if len(x)>1]
    unique_proxies = []
    for p in proxies:#Hopefully this fixes all the bloated same ips
        if len(unique_proxies) == 0:
            unique_proxies.append(p)
            continue
        sock,ip,port = p.split(":")
        save = True
        for up in unique_proxies:
            if up.startswith(f'{sock}:{ip}'):
                save = False
                break
        if save:
            unique_proxies.append(p)
    print(f"Removed bloat {len(proxies)-len(unique_proxies)}")
    print(f"{len(unique_proxies)} unique proxies!")
    return [{'http':p, 'https':p} for p in unique_proxies]"""

#lets do it FUNCTIONAL style =====================================================
#Might need some work on headers to be less sus and use less lines
#Interesting, looks like they now filter/limit/ban multiple accounts posting comments from same IP
#{'success': False, 'autoBanned': False, 'error': {'code': 14, 'message': 'Ne možete komentirati sa vaše IP adrese u ovom trenutku.'}, 'comment': None}
def postComment(user,thread,comment,url=None,fake_pause=3):
    payload = {"commentThreadId":thread,"content":comment}
    j = json.dumps(payload,indent=None)
    commentHeader = dynamicCommentHeader(url,str(len(j)))
    if url != None:
        fakeget = rm.requestWithProxy('GET',url=url,session=user.session)
    #fakescroll1 = ses.get('https://www.index.hr/api/me')
    """params = {"sortBy": 2,
              "commentThreadId": thread,
              "skip": 0,
              "take": 10
              }"""#STILL DECIDING ON THIS FAKE SCROLLS...
    #fakescroll2 = ses.get('https://www.index.hr/api/comments',params=params)
    assert len(comment) <= 1500
    sleep(randint(0,fake_pause))#fake pisanje komentara)
    r3 = rm.requestWithProxy('POST',"https://www.index.hr/api/comments/",user.session,headers=commentHeader,json=payload)
    rj = r3.json()
    if r3.status_code == 200 and rj['success']:
        user.burnThread(thread)
    comment_status = 'Posted' if rj['success'] else 'FAILED'
    print(f"{r3.status_code} | {r3.reason} | {comment_status} | {thread} | {user.username} : {comment}\nData : {rj}", flush=True)
    return r3

def fakeActivity(user,payload,proxy=False):
    if proxy:
        r = rm.requestWithProxy('POST',"https://www.index.hr/tracking-beacon",user.session,unique=True,alwaysProxy=True,json=payload)
    else:
        r = rm.requestWithProxy('POST',"https://www.index.hr/tracking-beacon",user.session,json=payload)
    print(f"{r} | {user.username}", flush=True)#DELETE
    return r

def login(email,password):# If I move this headers some will be generated from functions and other ones are static!
    session = requests.Session()
    head = staticSessionHeader
    session.headers.update(head)
    formdata = {'login_hint': email}
    params = {'redirectUrl': 'https://www.index.hr/'}
    #Login screen
    #r = session.post('https://www.index.hr/profil/prijava',params=params,data=formdata)
    r = rm.requestWithProxy('POST','https://www.index.hr/profil/prijava',session,singleMode=True,params=params,data=formdata)
    RVT = findRVT(r.text)
    q_params = queryStringParameters(r.url)
    loginformdata = {'ReturnUrl': q_params,
                     'Email': email,
                     'Password': password,
                     'RememberLogin': 'true',
                     'button': 'login',
                     '__RequestVerificationToken': RVT,
                     'RememberLogin': 'false'
                     }
    loginparams = {'ReturnUrl': q_params}
    #print(loginformdata)
    #print(loginparams)
    #Complete login
    #r2 = session.post('https://sso.index.hr/Account/Login',params=loginparams,data=loginformdata)
    r2 = rm.requestWithProxy('POST','https://sso.index.hr/Account/Login',session,singleMode=True,params=loginparams,data=loginformdata)
    signindata = findServerResponse(r2.text)
    #print(signindata)
    sleep(1)
    #r3 = session.post('https://www.index.hr/signin-oidc',data=signindata)
    r3 = rm.requestWithProxy('POST','https://www.index.hr/signin-oidc',session,singleMode=True,data=signindata)
    #me = session.get('https://www.index.hr/api/me')
    me = rm.requestWithProxy('GET','https://www.index.hr/api/me',session,singleMode=True)
    print(r.status_code,r2.status_code,r3.status_code,me.status_code, flush=True)
    return session, r, r2, r3 ,me, email, password

def reactToComment(user,comment_id,rType,article):
    #New sad and obnoxious attempt to block reacting below!
    #So... what caused main problem was content length that if wrong would cause 404
    #Also no RequestVerificationToken would cause 404, and just a bit different headers
    #Would cause 500 errors, after all time I spent doing this I couldn't care less
    #If there are some useless headers, their fault for chaning it and increasing their own
    #Traffic, it changed nothing... Think of this mess as Manual override!
    #IF there are going to be more OOM crashes, reuse r variable

    r00 = rm.requestWithProxy('GET',article,user.session)#Might not work with diff ips but we will try
    t = findThread(r00.text)
    r01 = rm.requestWithProxy('GET',f"https://www.index.hr/ajax-noindex/display-article-comments?commentThreadId={t}",user.session)
    rvt = findRVT(r01.text,length=198)
    # 1 like, 0 dislike, null remove!
    payload = {"commentId":comment_id,"type":rType}
    j = json.dumps(payload,separators=(',', ':'))
    l = str(len(j))
    cookies = user.session.cookies.get_dict()
    cookie_header = '; '.join([f'{key}={value}' for key, value in cookies.items()])
    rvtHeader = dynamicReactHeader(article,rvt,l,cookie_header)
    #No need to update session, it just works :D
    r = rm.requestWithProxy('POST','https://www.index.hr/api/comments/react',unique=True,alwaysProxy=True,headers=rvtHeader,data=j)#json passing is breaking stuff as of 18-Dec-25
    print(r.json(), flush=True)

def massReact(comment_id,rType,timeout=0,rAmount=0,relatedArticleURL=None,rebuildURL=False):
    #IP limited. So I will try to get as much likes as possible
    #I decided to try (tbd if it works) using tor as like system proxy for proxychains and then force proxy over it. Double trouble?
    #No more zipping, we only care about having more than 0 proxies
    if relatedArticleURL == None:
        #This is needed from now on because of the new changes
        print("CANNOT DO REACTS OF ANY KIND WITHOUT REQUESTVERIFICATIONTOKEN!!!",flush=True)
        return 404 #Very thematic!
    if relatedArticleURL != None and rebuildURL:
        relatedArticleURL = f"https://www.index.hr/clanak.aspx?id={relatedArticleURL}" # Rebuild link
    with ThreadPoolExecutor(max_workers=30) as executor:
        for u in (user_list.user_list+user_list.banned)[:rAmount]:
            try:
                sleep(timeout)
                executor.submit(reactToComment,u,comment_id,rType,relatedArticleURL)#3 tries per proxy
                #I was expecting issues with print like ones in python shell, but with terminal it is fine so no need for threading lock :)
            except Exception as e:
                print(f"{u.username} failed to react! {e}", flush=True)

def displayProfile(user,skip=0,take=5):
    j = user.getProfileData(skip,take)
    comments = j['comments']
    #print(comments)
    with stdout_lock:
        for c in comments:
            print(f"=========={c['commentId']}xx{c['posterFullName']}xx{c['createdDateUtc']}==========")
            print(f"https://www.index.hr/clanak.aspx?id={c['relationshipEntityId']} \nText:{c['content']}\n👍{c['numberOfLikes']} 👎{c['numberOfDislikes']} 💬{c['replyCount']}")

#there is a posibility of rewrite for some of these, and calling random sessions for these requests
def inspectUserProfile(url,take=5,returnData=False,skip=0):#no checks for this really, might fail
    r = rm.requestWithProxy('GET',url=url)
    uid = findUserId(r.text)
    #uprofile = requests.get() WE DON'T ACTUALLY CARE ABOUT THIS
    qsp = {'createdById': uid,'skip': skip,'take':take}
    ucomments = rm.requestWithProxy('GET','https://www.index.hr/api/comments/user',params=qsp).json()
    if returnData:
        return ucomments['comments']
    for c in ucomments['comments']:
        print(f"=========={c['commentId']}xx{c['posterFullName']}xx{c['createdDateUtc']}==========")
        print(f"https://www.index.hr/clanak.aspx?id={c['relationshipEntityId']} \nText:{c['content']}\n👍{c['numberOfLikes']} 👎{c['numberOfDislikes']} 💬{c['replyCount']}")

def getArticleComments(url,skip=0,take=10):#API function
    r = rm.requestWithProxy('GET',url=url)
    thread = findThread(r.text)
    qsp = {'sortBy': 2, 'commentThreadId': thread, 'skip': skip, 'take': take}
    r = rm.requestWithProxy('GET','https://www.index.hr/api/comments',params=qsp)
    acomments = r.json()
    return acomments

def getReplies(commentId,skip=0,take=5):
    url = 'https://www.index.hr/api/comments/replies'
    qsp = {'commentId': commentId, 'skip':skip, 'take':take}
    r = rm.requestWithProxy('GET',url=url,params=qsp)
    replies = r.json()
    return replies

def doShitpost(user,comments,history,covert=False,specifyURL='https://www.index.hr/najnovije',spoofBeacons=True,useAI=False,useRSSFeed=False):#lea or not?!?
    r = rm.requestWithProxy('GET',url=specifyURL,session=user.session)
    user.refreshMe()
    if useRSSFeed:
        root = ET.fromstring(r.content)
        articleLinks = [link.text for link in root.findall('.//link')]
        articleLinks.pop(0)#remove rss link from the list
    else:
        #Server has more processing headroom than ram, so if you want just make this global and keep it in mem
        soup = BeautifulSoup(r.text,'html.parser')
        articleTags = soup.find_all(href=re.compile("clanak"))
        articleLinks = [str('https://www.index.hr' + at.get('href')) for at in articleTags] #generate full links 
    if covert:
        articleLinks = articleLinks[::-1]
    #so we want to always shit on newest possible, and if there is nothing
    #just go shit on something old :)
    for al in articleLinks:
        if al in history:#Think i could actually use burned threads for this? but those are within articles
            #we already commented
            continue
        else:
            r = rm.requestWithProxy('GET',url=al,session=user.session)
            if useAI: #API LIMITS https://console.groq.com/settings/limits
            #I am keeping 2 different postComments because if spoofBeacon placement
                soup = BeautifulSoup(r.text,'html.parser')
                allP = soup.find_all('p')
                allPClean = "\n".join([p.get_text(strip=True) for p in allP])
                try:
                    completion = groq_clinet.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {
                                "role": "system",
                                "content": comments
                            },
                            {
                                "role": "user",
                                "content": allPClean
                            }
                        ],
                        temperature=0.49,
                        max_tokens=8000,
                        top_p=1,
                        stream=False,
                        stop=None,
                    )
                except groq.RateLimitError as e:#error is printed from return message object
                    return [], {'success':False,'reason':{'error':'Rate Limit Error','code':429}}
                except Exception as e:
                    return [], {'success':False,'reason':{'error':'Unhandled Groq Error','code':'UNKNOWN'}}
            if spoofBeacons:
                beaconPayload = extractTrackingBeaconData(r.text)#This along with proxied postComment is going to be sus!
                rb = fakeActivity(user,beaconPayload)
            thread = findThread(r.text)
            if useAI:
                r = postComment(user,thread,comment=completion.choices[0].message.content,url=r.url,fake_pause=0)
            else:
                r = postComment(user,thread,comment=choice(comments),url=r.url,fake_pause=0)#None is to not do fakeget,0 no pause
            if 'application/json' in r.headers.get('Content-Type'):
                rj = r.json()
            else:
                # We got cold shoulder from server, I am still unsure but could have been because i changed some accept encodings, we shall see!!!
                # So we will construct random "JSON to deal with the fallout"
                rj = {'success':False,'error':{'message':'Server returned wrong Content-Type, probably an empty response','code':400,'insight':r.text}}
            return [al], rj #for history
    return [], 'No articles left'#we have to return something iterable


def doStalk(target,rType,amount,history,lea):#we can always use more params for used funcs
    uc = inspectUserProfile(target,5,True,0)#to waste less time, even if we find bunch of comments
    stalkyResults = []
    for c in uc: #To be honest, here I could only pass threads and change dynamicHeader for react but if this is being actively fought, lets keep it spoofed
        cid = c['commentId']#I wonder...
        cra = c['relationshipEntityId']
        if cid in history:
            continue
        date = datetime.fromisoformat(c['createdDateUtc']).replace(tzinfo=timezone.utc)
        if date > lea:#newer is true
            stalkyResults.append(cid)
            massReact(cid,rType,0,amount,relatedArticleURL=cra,rebuildURL=True)
    return stalkyResults

def doFakeActivity(user,readAmount=1,specifyURL='https://www.index.hr/najnovije'):
    r = rm.requestWithProxy('GET',url=specifyURL,session=user.session)
    soup = BeautifulSoup(r.text,'html.parser')
    articleTags = soup.find_all(href=re.compile("clanak"))
    articleLinks = [at.get('href') for at in articleTags]
    for al in articleLinks[:readAmount]:
        fl = 'https://www.index.hr'+al
        r = rm.requestWithProxy('GET',url=fl,session=user.session)
        beaconPayload = extractTrackingBeaconData(r.text)
        r = fakeActivity(user,beaconPayload)

def backupUsers():
    for u in user_list.user_list:
            if not u.banned:
                with open(f'{u.username} - {datetime.now(timezone.utc).strftime("%Y-%m-%d %Hh%Mm%Ss")}.json','w',encoding="utf-8") as file:
                    for chunk in range(0,((int(u.comments)//20)+2)):
                        json.dump(u.getProfileData(chunk*20,(chunk+1)*20),file,ensure_ascii=False, indent=4)
                        print(f"Saved comments for {u.username}")

def getIP(request):
    # Check headers for original client IP
    if "X-Forwarded-For" in request.headers:
        # Use the first IP in the X-Forwarded-For chain
        return request.headers["X-Forwarded-For"].split(",")[0]#<--- We are using this one
    elif "X-Real-IP" in request.headers:
        return request.headers["X-Real-IP"]
    else:
        return request.remote_addr

#****************************************** CMD COMMANDS BELOW

def comment(url, comments):#Okay we need to finish this one up, simple for now
    #maybe add referer to spoof more? Also maybe proxies?
    #timeout options?
    r = rm.requestWithProxy('GET',url=url)
    thread = findThread(r.text)
    for u,c in zip(user_list.getReadyUsers(thread),comments):
        r1 = postComment(u,thread,c,r.url)
        sleep(randint(1,60))
        responses.append(r1)#debugging help

def login_all(accs):#maybe add fake and half options
    finished = []
    about_us = []
    with ThreadPoolExecutor(max_workers=50) as ex:#finish up after getting results
        for acc in accs:
            try:
                #s,r1,r2,r3,me_info = login(acc[0],acc[1])
                future = ex.submit(login,acc[0],acc[1])
                finished.append(future)
            except Exception as e:
                print(e, flush=True)
                continue
    for f in finished:
        try:
            s,r1,r2,r3,me_info,em,pa = f.result()
            auth_user = User(s,me_info.json(),em,pa)#Shall we remove passwords later if we stay logged in forever?
            auth_user.prepMe()
            if Logging.PRETTY_LOGIN:
                about_us.append(auth_user.aboutMe(retInfo=True))
            else:
                auth_user.aboutMe()
            auth_user.refreshMe()
            if auth_user.banned:
                user_list.appendBanned(auth_user)
            else:
                user_list.append(auth_user)
            if not Server.ONE_LINE_LOGS:
                print("*********** DONE ***********", flush=True)
            
        except Exception as e:
            print(e, flush=True)

    if Logging.PRETTY_LOGIN:
        table = PrettyTable()
        table.field_names = ["Username","Public URL","Number of comments","Last commented X ago","New user?","BANNED?"]
        table.add_rows(about_us)
        table.align = 'l'
        print(table,flush=True)


def display_all_profiles(amount=5):
    with ThreadPoolExecutor(max_workers=50) as ex:
        for u in user_list.user_list:
            ex.submit(displayProfile,u,0,amount)

def nuke_profile(target,typeId,amount=5,timeout=0,userlist=None):#we will keep it sequential to ensure enough proxies
    target_comments = inspectUserProfile(target,amount,True)
    for tc in target_comments:
        try:
            tc_id = int(tc['commentId'])
            tc_ra = tc['relationshipEntityId']
            massReact(tc_id,typeId,timeout=timeout,rAmount=accountAmount,relatedArticleURL=tc_ra,rebuildURL=True)
            #since this function is very long, we have to do the task of message handler, refreshing sessions
            print("Refresh subtask in progress", flush=True)
            for user in userlist:
                rm.requestWithProxy('GET','https://www.index.hr/najnovije?kategorija=3',user.session,singleMode=True)
                user.refreshMe()
            rm.refreshProxyList()
            print("Refresh subtask DONE!", flush=True)
            
        except Exception as e:
            print(e, flush=True)

def show_help():
    #Shows help information.
    print("Available commands: *CASE SENSITIVE*")
    print("login - login all accounts")
    print("comment <url>|<comment1>|<comment2>|...|<commentN>")
    print("dap <amout - optional>")
    print("inspect <profile url> <amount>")
    print("react <commentId>|<1=like, 0=dislike, empty=remove reactions>|<timeout in s - optional>")
    print("nuke <profile url> <react type, see above^> <amount - optional, default=5>")
    print("backup - make a json file with all comments of currently logged in users.")
    print("help - duh?!, quit")

def quit_program():
    #Exits the program.
    print("Exiting program. Goodbye!")
    exit()