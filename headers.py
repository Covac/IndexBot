def dynamicCommentHeader(url,length):
    #Original: 'Content-Length': str(len(j))
    commentHeader = {'Accept':'application/json, text/plain, */*',
                      'Accept-Encoding':'gzip, deflate',
                      'Accept-Language':'en-US,en;q=0.9,hr;q=0.8',
                      'Content-Length': length,
                      'Origin':'https://www.index.hr',
                      'Referer':url,
                      'Sec-Ch-Ua':'"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
                      'Sec-Ch-Ua-Mobile': '?0',
                      'Sec-Ch-Ua-Platform': '"Windows"',
                      'Sec-Fetch-Dest': 'empty',
                      'Sec-Fetch-Mode': 'cors',
                      'Sec-Fetch-Site': 'same-origin',
                      'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
                      }
    return commentHeader

staticSessionHeader = {'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Encoding':'gzip, deflate',
            'Accept-Language':'en-US,en;q=0.9',
            'Cache-Control':'max-age=0',
            'Pragma':'no-cache',
            'Sec-Ch-Ua':'"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
            }