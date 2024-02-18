import requests
from globals import proxyLink
from urllib3 import disable_warnings

disable_warnings()


class RequestsManager:
    def __init__(self,maxAttempts=9,chances=2):
        self.maxAttempts = maxAttempts
        self.chances = chances
        self.proxy_list = []
        self.unique_proxy_list = []
        self.options = {}
        #self.timeout Set this after finishing testing, very important
        #prepared proxy lists, ready to use with requests
        self.ppl = []
        self.uppl = []
        self.pplPointer = 0
        self.upplPointer = 0
        
    def clearLists(self):
        self.proxy_list.clear()
        self.unique_proxy_list.clear()
        self.ppl.clear()
        self.uppl.clear()
        self.pplPointer = 0
        self.upplPointer = 0
        
    def getProxy(self,unique,consume):
    #we should reset pointers to 0 after using functions if we really care
        if consume:
            p = self.uppl.pop(0) if unique else self.ppl.pop(0)
        else:
            if unique:
                p = self.uppl[self.upplPointer]
                self.upplPointer += 1
            else:
                p = self.ppl[self.pplPointer]
                self.pplPointer += 1
        return p

    def refreshProxyList(self):
        #maybe use options for more params
        if len(self.ppl) > 0 or len(self.uppl) > 0:
        	self.clearLists()
        pr = requests.get(proxyLink)
        self.proxy_list = [x.replace("socks5","socks5h") for x in pr.text.split('\r\n') if len(x)>1]
        self.generateUniqueProxyList()
        self.prepareProxies()

    def generateUniqueProxyList(self):
        for p in self.proxy_list:
            if len(self.unique_proxy_list) == 0:
                self.unique_proxy_list.append(p)
                continue
            sock,ip,port = p.split(":")
            save = True
            for up in self.unique_proxy_list:
                if up.startswith(f'{sock}:{ip}'):
                    save = False
                    break
            if save:
                self.unique_proxy_list.append(p)

    def prepareProxies(self):
        self.ppl = [{'http':p, 'https':p} for p in self.proxy_list]
        self.uppl = [{'http':p, 'https':p} for p in self.unique_proxy_list]

    def requestWithProxy(self,method,url,session,unique=False,consume=False,**kwargs):
        kwargs['verify'] = False
        kwargs['proxies'] = self.getProxy(unique,consume)
        attempts = 0 #rename to retries, and chances to retries!
        fatalFlag = False
        for attempt in range(1,self.maxAttempts+1):
            if attempts >= self.chances or fatalFlag:
                print("Changing proxy!")
                kwargs['proxies'] = self.getProxy(unique,consume)
                attempts,fatalFlag = 0,False
            try:
                attempts += 1
                r = session.request(method,url,**kwargs)
                assert r.status_code == 200
                break
            except (requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout) as e:
                print(f"Attempt {attempt} failed! Reason: {e.__class__.__name__} -- NonCritical")
            except Exception as e:
                fatalFlag = True
                print(f"React attempt {attempt} failed! Reason: {e.__class__.__name__} -- CRITICAL")
        return r
