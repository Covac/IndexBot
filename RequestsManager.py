import requests
from globals import proxyLink
from urllib3 import disable_warnings

disable_warnings()

class RequestsManager:
    def __init__(self):
        self.proxy_list = []
        self.unique_proxy_list = []
        self.options = {}
        #prepared proxy lists, ready to use with requests
        self.ppl = []
        self.uppl = []
        
    def clearLists(self):
        self.proxy_list.clear()
        self.unique_proxy_list.clear()
        self.ppl.clear()
        self.uppl.clear()

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

    def requestWithProxy(self,method,url,session,unique=False,**kwargs):
        kwargs['verify'] = False
        kwargs['proxies'] = self.uppl.pop(0) if unique else self.ppl.pop(0)
        r = session.request(method,url,**kwargs)
        print(kwargs)
        return r
