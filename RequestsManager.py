import requests
import options
from config import proxyLinks
from datetime import datetime, timezone
from urllib3 import disable_warnings

disable_warnings()


class RequestsManager:
    def __init__(self,maxAttempts=10,maxRetries=2,refreshEvery=20,timeout=5):#because http proxies are shit we are going up with attempts and less timeouts
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
        delta = datetime.now(timezone.utc) - self.last_refresh
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
        #looks like we are need more proxy providers for resilience, ones from proxyscrape went down and never came back.
        if len(self.ppl) > 0 or len(self.uppl) > 0:
            self.clearLists()
        self.proxy_list = self.loadProxyList(proxyLinks)
        self.last_refresh = datetime.now(timezone.utc)
        self.generateUniqueProxyList()
        self.prepareProxies()
        if options.Logging.VERBOSE:
            print(self.ppl, flush=True)
            print(self.uppl, flush=True)

    def loadProxyList(self,PROVIDER_LIST):
        ready = []# we will make GEONODE mimic proxyscrape to reuse code
        for PROVIDER in PROVIDER_LIST:
            try:
                pr = requests.get(PROVIDER['Link'])
                if PROVIDER['Provider'] == 'PROXYSCRAPE':
                    pl = [x.replace("socks5","socks5h") for x in pr.text.split('\r\n') if len(x)>1]
                    ready.extend(pl)
                elif PROVIDER['Provider'] == 'GEONODE':
                    pl = []
                    for DATA in pr.json()['data']:
                        constructed = DATA['protocols'][0]+'://'+DATA['ip']+':'+DATA['port']
                        constructed.replace("socks5","socks5h")
                        pl.append(constructed)
                    ready.extend(pl)
            except:
                print("Error in loadProxyList",flush=True)
                continue
        return ready

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
        #We need https support for api calls, so https proxies are useless to us!
        self.ppl = [{'http':p, 'https':p} for p in self.proxy_list]
        self.uppl = [{'http':p, 'https':p} for p in self.unique_proxy_list]

    def requestWithProxy(self,method,url,session=requests.Session(),unique=False,consume=False,singleMode=False,alwaysProxy=False,**kwargs):
        kwargs['verify'] = False
        kwargs['timeout'] = kwargs.setdefault('timeout',self.timeout)
        if options.Proxy.FULL_PROXY == False and alwaysProxy == False:#This enables old mode, where we don't care about exposing ip, but it is more reliable!
            r = session.request(method,url,**kwargs)
            assert r.status_code == 200
            assert r 
            return r
        if singleMode:
            kwargs['proxies'], idx = self.getProxywidx(0,unique,consume)
        else:
            kwargs['proxies'] = self.getProxy(unique,consume)
        retries = 0 #rename to retries, and chances to retries!
        fatalFlag = False
        for attempt in range(1,self.maxAttempts+1):
            if retries >= self.maxRetries or fatalFlag:
                if options.Logging.VERBOSE:
                    print("Changing proxy!", flush=True)
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
                if options.Logging.VERBOSE:
                    print(f"Attempt {attempt} failed! Reason: {e.__class__.__name__} -- NonCritical", flush=True)
            except Exception as e:
                fatalFlag = True
                if options.Logging.VERBOSE:
                    print(f"Attempt {attempt} failed! Reason: {e.__class__.__name__} -- CRITICAL", flush=True)
        assert r
        return r
