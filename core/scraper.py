import requests

class RedditScraper:
    def __init__(self):
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0'}

    def scrape(self, brand: str):
        url = f"https://www.reddit.com/search.json?q={brand}&limit=25&sort=new"
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code != 200: return []
            
            posts = response.json().get('data', {}).get('children', [])
            return [{
                "id": p['data'].get('id'),
                "author": p['data'].get('author'),
                "content": f"{p['data'].get('title', '')} {p['data'].get('selftext', '')}",
                "url": f"https://reddit.com{p['data'].get('permalink')}",
                "brand": brand.lower()
            } for p in posts]
        except Exception as e:
            print(f"Scraper Error: {e}")
            return []