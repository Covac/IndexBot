import re
import json
import requests
from time import sleep
from random import randint
from globals import *
from urllib.parse import urlparse, parse_qs
from urllib3 import disable_warnings
from concurrent.futures import ThreadPoolExecutor

disable_warnings()

def findRVT(text):#write decorators for these 3
    try:
        MATCH = re.search('"__RequestVerificationToken" type="hidden" value="',text)
        rvt = text[MATCH.span()[1]:MATCH.span()[1]+155]
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
    MATCH = re.search("name=\'id_token\' value=\'",text)#not static length
    MATCH2 = re.search("\' />\n<input type=\'hidden\' name=\'scope\' value=\'openid profile\'",text)
    id_token = text[MATCH.span()[1]:MATCH2.span()[0]]
    MATCH = re.search("name=\'scope\' value=\'",text)
    scope = text[MATCH.span()[1]:MATCH.span()[1]+14]
    MATCH = re.search("name=\'state\' value=\'",text)
    state = text[MATCH.span()[1]:MATCH.span()[1]+368]
    MATCH = re.search("name=\'session_state\' value=\'",text)
    session_state = text[MATCH.span()[1]:MATCH.span()[1]+76]
    form = {"id_token":id_token,"scope":scope,"state":state,"session_state":session_state}
    return form

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
def postComment(user,thread,comment,url,fake_pause=3):
    ses = user.session
    payload = {"commentThreadId":thread,"content":comment}
    j = json.dumps(payload,indent=None)
    commentHeaders = {'Accept':'application/json, text/plain, */*',
                      'Accept-Encoding':'gzip, deflate',
                      'Accept-Language':'en-US,en;q=0.9,hr;q=0.8',
                      'Content-Length': str(len(j)),
                      'Origin':'https://www.index.hr',
                      'Referer':url,
                      'Sec-Ch-Ua':'"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                      'Sec-Ch-Ua-Mobile': '?0',
                      'Sec-Ch-Ua-Platform': '"Windows"',
                      'Sec-Fetch-Dest': 'empty',
                      'Sec-Fetch-Mode': 'cors',
                      'Sec-Fetch-Site': 'same-origin',
                      'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                      }
    fakeget = rm.requestWithProxy('GET',url=url)
    #fakescroll1 = ses.get('https://www.index.hr/api/me')
    """params = {"sortBy": 2,
              "commentThreadId": thread,
              "skip": 0,
              "take": 10
              }"""#STILL DECIDING ON THIS FAKE SCROLLS...
    #fakescroll2 = ses.get('https://www.index.hr/api/comments',params=params)
    assert len(comment) <= 1500
    sleep(randint(0,fake_pause))#fake pisanje komentara)
    r3 = rm.requestWithProxy('POST',"https://www.index.hr/api/comments/",ses,singleMode=True,headers=commentHeaders,json=payload)
    rj = r3.json()
    if r3.status_code == 200 and rj['success']:
        user.burnThread(thread)
    comment_status = 'Posted' if rj['success'] else 'FAILED'
    print(f"{r3.status_code} {r3.reason} | {comment_status} | {thread} : {comment}")
    return r3

def login(email,password):# If I move this headers some will be generated from functions and other ones are static!
    session = requests.Session()
    head = {'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Encoding':'gzip, deflate, br',
            'Accept-Language':'en-US,en;q=0.9',
            'Cache-Control':'no-cache',
            'Pragma':'no-cache',
            'Sec-Ch-Ua':'"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
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
                     '__RequestVerificationToken': RVT,
                     'button': 'login'}
    loginparams = {'ReturnUrl': q_params}
    #Complete login
    #r2 = session.post('https://sso.index.hr/Account/Login',params=loginparams,data=loginformdata)
    r2 = rm.requestWithProxy('POST','https://sso.index.hr/Account/Login',session,singleMode=True,params=loginparams,data=loginformdata)
    signindata = findServerResponse(r2.text)
    sleep(1)
    #r3 = session.post('https://www.index.hr/signin-oidc',data=signindata)
    r3 = rm.requestWithProxy('POST','https://www.index.hr/signin-oidc',session,singleMode=True,data=signindata)
    #me = session.get('https://www.index.hr/api/me')
    me = rm.requestWithProxy('GET','https://www.index.hr/api/me',session,singleMode=True)
    print(r.status_code,r2.status_code,r3.status_code,me.status_code)
    return session, r, r2, r3 ,me, email, password

def reactToComment(user,comment_id,rType):
    #1 like, 0 dislike, null remove!
    payload = {'commentId':comment_id,'type': rType}
    r = rm.requestWithProxy('POST','https://www.index.hr/api/comments/react',user.session,unique=True,alwaysProxy=True,json=payload)
    print(r.json())

def massReact(comment_id,rType,timeout=0):
    #IP limited. So I will try to get as much likes as possible
    #I decided to try (tbd if it works) using tor as like system proxy for proxychains and then force proxy over it. Double trouble?
    #No more zipping, we only care about having more than 0 proxies
    with ThreadPoolExecutor(max_workers=12) as executor:
        for u in user_list.user_list+user_list.banned:
            try:
                sleep(timeout)
                executor.submit(reactToComment,u,comment_id,rType)#3 tries per proxy
                #I was expecting issues with print like ones in python shell, but with terminal it is fine so no need for threading lock :)
            except Exception as e:
                print(f"{u.username} failed to react! {e}")

def displayProfile(user,skip=0,take=5):
    j = user.getProfileData(skip,take)
    comments = j['comments']
    #print(comments)
    for c in comments:
        print(f"=========={c['commentId']}xx{c['posterFullName']}xx{c['createdDateUtc']}==========")
        print(f"https://www.index.hr/clanak.aspx?id={c['relationshipEntityId']} \nText:{c['content']}\n👍{c['numberOfLikes']} 👎{c['numberOfDislikes']} 💬{c['replyCount']}")

#there is a posibility of rewrite for some of these, and calling random sessions for these requests
def inspectUserProfile(url,take=5):#no checks for this really, might fail
    r = rm.requestWithProxy('GET',url=url)
    uid = findUserId(r.text)
    #uprofile = requests.get() WE DON'T ACTUALLY CARE ABOUT THIS
    qsp = {'createdById': uid,'skip': 0,'take':take}
    ucomments = rm.requestWithProxy('GET','https://www.index.hr/api/comments/user',params=qsp).json()
    for c in ucomments['comments']:
        print(f"=========={c['commentId']}xx{c['posterFullName']}xx{c['createdDateUtc']}==========")
        print(f"https://www.index.hr/clanak.aspx?id={c['relationshipEntityId']} \nText:{c['content']}\n👍{c['numberOfLikes']} 👎{c['numberOfDislikes']} 💬{c['replyCount']}")

def backupUsers():
    for u in user_list.user_list:
            with open(f'{u.username} - {datetime.utcnow().strftime("%Y-%m-%d %Hh%Mm%Ss")}.json','w',encoding="utf-8") as file:
                json.dump(u.getProfileData(0,int(u.comments)),file,ensure_ascii=False, indent=4)
                print(f"Saved comments for {u.username}")

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
    with ThreadPoolExecutor(max_workers=50) as ex:#finish up after getting results
        for acc in accs:
            try:
                #s,r1,r2,r3,me_info = login(acc[0],acc[1])
                future = ex.submit(login,acc[0],acc[1])
                finished.append(future)
            except Exception as e:
                print(e)
                continue
    for f in finished:
        try:
            s,r1,r2,r3,me_info,em,pa = f.result()
            auth_user = User(s,me_info.json(),em,pa)#Shall we remove passwords later if we stay logged in forever?
            auth_user.prepMe()
            auth_user.aboutMe()
            auth_user.refreshMe()
            if auth_user.banned:
                user_list.appendBanned(auth_user)
            else:
                user_list.append(auth_user)
            print("*********** DONE ***********")
        except Exception as e:
            print(e)


def display_all_profiles(amount=5):
    with ThreadPoolExecutor(max_workers=50) as ex:
        for u in user_list.user_list:
            ex.submit(displayProfile,u,0,amount)

def show_help():
    #Shows help information.
    print("Available commands: *CASE SENSITIVE*")
    print("login - login all accounts")
    print("comment <url>|<comment1>|<comment2>|...|<commentN>")
    print("dap <amout - optional>")
    print("inspect <profile url> <amount>")
    print("react <commentId>|<1=like, 0=dislike, empty=remove reactions>|<timeout in s - optional>")
    print("backup - make a json file with all comments of currently logged in users.")
    print("help - duh?!, quit")

def quit_program():
    #Exits the program.
    print("Exiting program. Goodbye!")
    exit()
