def dynamicCommentHeader(url,length):
    #Original: 'Content-Length': str(len(j))
    commentHeader = {
        'Accept':'application/json, text/plain, */*',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'en-US,en;q=0.5',
        'Content-Length': length,
        'Content-Type': 'application/json',
        'Origin':'https://www.index.hr',
        'Referer':url,
        'Origin': 'https://www.index.hr',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'Priority': 'u=0',
        'TE': 'trailers',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0'
        }
    return commentHeader

def dynamicReactHeader(article,requestVerificationToken,length,cookieHeader):
    reactHeader = {
        'Host': 'www.index.hr',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Referer': article,
        'Content-Type': 'application/json',
        'RequestVerificationToken': requestVerificationToken,
        'Content-Length': length,
        'Origin': 'https://www.index.hr',
        'Connection': 'keep-alive',
        'Cookie': cookieHeader,
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'Priority': 'u=0',
        'TE': 'trailers'
        }
    return reactHeader

staticSessionHeader = {
    'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Encoding':'gzip, deflate',
    'Accept-Language':'en-US,en;q=0.9',
    'Cache-Control':'max-age=0',
    'Pragma':'no-cache',
    'Sec-Ch-Ua':'"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"Windows"',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    }