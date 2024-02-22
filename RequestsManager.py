import requests
from config import proxyLink
from datetime import datetime
from urllib3 import disable_warnings

disable_warnings()


class RequestsManager:
    def __init__(self,maxAttempts=9,maxRetries=2,refreshEvery=60,timeout=5):
        self.maxAttempts = maxAttempts
        self.maxRetries = maxRetries
        self.refreshEvery = refreshEvery
        self.last_refresh = None
        self.proxy_list = []
        self.unique_proxy_list = []
        self.options = {}
        self.timeout = timeout
        #prepared proxy lists, ready to use with requests
        self.ppl = []
        self.uppl = []
        self.pplPointer = 0
        self.upplPointer = 0
        self.refreshProxyList()
        
    def clearLists(self):
        self.proxy_list.clear()
        self.unique_proxy_list.clear()
        self.ppl.clear()
        self.uppl.clear()
        self.pplPointer = 0
        self.upplPointer = 0

    def sinceLastRefresh(self):#move this from here and User to functions, since it is shared
        delta = datetime.utcnow() - self.last_refresh
        return delta.total_seconds()
    
    def getProxywidx(self,idx,unique,consume):
        if consume:
            p = self.uppl.pop(idx) if unique else self.ppl.pop(idx)
        else:
            if unique:
                p = self.uppl[idx]
            else:
                p = self.ppl[idx]
        return p, idx
        
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
        self.last_refresh = datetime.utcnow()
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

    def requestWithProxy(self,method,url,session,unique=False,consume=False,singleMode=False,**kwargs):
        kwargs['verify'] = False
        if singleMode:
            kwargs['proxies'], idx = self.getProxywidx(0,unique,consume)
        else:
            kwargs['proxies'] = self.getProxy(unique,consume)
        kwargs['timeout'] = kwargs.setdefault('timeout',self.timeout)
        retries = 0 #rename to retries, and chances to retries!
        fatalFlag = False
        for attempt in range(1,self.maxAttempts+1):
            if retries >= self.maxRetries or fatalFlag:
                print("Changing proxy!")
                if singleMode:
                    kwargs['proxies'], idx = self.getProxywidx(idx+1,unique,consume)
                else:
                    kwargs['proxies'] = self.getProxy(unique,consume)
                retries,fatalFlag = 0,False
            try:
                retries += 1
                r = session.request(method,url,**kwargs)
                assert r.status_code == 200
                break
            except (requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout) as e:
                print(f"Attempt {attempt} failed! Reason: {e.__class__.__name__} -- NonCritical")
            except Exception as e:
                fatalFlag = True
                print(f"Attempt {attempt} failed! Reason: {e.__class__.__name__} -- CRITICAL")
        assert r
        return r
