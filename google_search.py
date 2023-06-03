import sys
import http.client
import json

from common import SERPER_DEV_API_KEY

def google_scraper( keyword ):
    print(f"Scraping keyword: {keyword}")
    conn = http.client.HTTPSConnection("google.serper.dev")
    payload = json.dumps({
        "q": keyword,
        "gl": "us",
        "hl": "en",
        "autocorrect": True
    })
    
    headers = {
        'X-API-KEY': SERPER_DEV_API_KEY,
        'Content-Type': 'application/json'
    }
    
    conn.request("POST", "/search", payload, headers)
    res = conn.getresponse()
    data = res.read().decode("utf-8")
    data = json.loads(data)
    
    for i in data["organic"]:
        print("Title: %s with URL: %s" % (i["title"], i["link"]))
    
    return data["organic"]


if __name__ == "__main__":
    while True:
        keyword = sys.stdin.readline()
        keyword = keyword.rstrip()
        if not keyword:
            break
        print(f"Getting SERPs for {keyword}")
        google_scraper(keyword)
        
            
