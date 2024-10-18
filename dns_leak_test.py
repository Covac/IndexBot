import string
import secrets
import RequestsManager
from time import sleep

def generateSession():
    charset = string.ascii_letters + string.digits
    skey = ''.join(secrets.choice(charset) for _ in range(40))
    return skey

def generateRandString():
    charset = string.ascii_letters
    rstring = ''.join(secrets.choice(charset) for _ in range(5))
    return rstring

rm = RequestsManager.RequestsManager()
session = generateSession()

for i in range(1,61):
    try:
        unique = generateRandString()
        constructed = f"https://{session}-{unique}.ipleak.net/dnsdetection/"
        r = rm.requestWithProxy('GET',constructed,unique=True,consume=True,alwaysProxy=True)
        d = r.json()
        print(f"ATTEMPT {i}:\n{d}")
    except Exception as e:
        print(f"Attempt {i} failed, {e}")
    finally:
        sleep(0.5)