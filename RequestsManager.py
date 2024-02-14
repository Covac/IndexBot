import requests

class RequestsManager:
    def __init__(self):
        self.proxy_list = []
        self.unique_proxy_list = []
        self.options = {}
        #prepared proxy lists, ready to use with requests
        self.ppl = []
        self.uppl = []

    def refreshProxyList(self):
        #maybe use options for more params
        pr = requests.get()
        self.proxy_list = [x.replace("socks5","socks5h") for x in pr.text.split('\r\n') if len(x)>1]

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
                self.unique_proxy_list(p)

    def prepareProxies(self):
        self.ppl = [{'http':p, 'https':p} for p in self.proxy_list]
        self.uppl = [{'http':p, 'https':p} for p in self.unique_proxy_list]

    #Think about maybe just requests.request vs making 2 methods?!?
    def getWithProxy(self,session,unique=False,params=None,json=None,**kwargs):
        #done for now!
