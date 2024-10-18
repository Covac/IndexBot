import os
proxyLinks = [{'Provider':'PROXYSCRAPE','Link':'https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies&protocol=socks4,socks5&proxy_format=protocolipport&format=text&anonymity=Elite&timeout=4500'}]#if you abuse this it might get ruined for everybody, don't be that guy
              #{'Provider':'GEONODE','Link':'https://proxylist.geonode.com/api/proxy-list?protocols=socks4%2Csocks5&filterLastChecked=1&speed=fast&limit=20&page=1&sort_by=lastChecked&sort_type=desc'}]
#GEONODE free tier is shit. If you have your own links you add them here, pretty sure it supports multiple proxy lists. Adjust stuff based on your needs.
dbPath = os.getenv('DB_PATH','data.db')
cardanoscanHeader = {'apiKey':'APIKEYHERE'}#only production
blockfrostHeader = {'Accept': 'application/json' ,'project_id': 'YOURPROJECTID'}#now in production, can do testing if we change app
blockfrostAPI = 'APIKEYHERE'
cardanoAddress = 'addr1 USE YOUR OWN'
coinmarketcapHeader = {'Accepts': 'application/json', 'X-CMC_PRO_API_KEY': 'APIKEYHERE'}#used in production and testing

faucetFundedAddr = {'psk':'{"type": "PaymentSigningKeyShelley_ed25519", "description": "PaymentSigningKeyShelley_ed25519", "cborHex": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"}',
                    'pvk':'{"type": "PaymentVerificationKeyShelley_ed25519", "description": "PaymentVerificationKeyShelley_ed25519", "cborHex": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"}'
                    }
groqCloud = 'APIKEYHERE'
accountAmount = 0 #Well you don't need this because i havent realeased frontend and probably never will
