import requests
import time
import os

class RedditScraper:
    def __init__(self):
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0'}

    def scrape(self, brand: str):
        """
        1. Search Reddit for posts matching the brand/query
        Returns a list of posts
        """
        post_limit = os.getenv("REDDIT_POST_LIMIT", "15")
        url = f"https://www.reddit.com/search.json?q={brand}&limit={post_limit}&sort=relevance&t=week"
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code != 200: return []
            
            posts = response.json().get('data', {}).get('children', [])
            results = []

            for p in posts:
                post_data = p['data']
                permalink = post_data.get('permalink', '')
                post_title = post_data.get('title', '')
                post_body = post_data.get('selftext', '')

                # Add the post itself
                results.append({
                    "id": post_data.get('id'),
                    "author": post_data.get('author'),
                    "content": f"{post_title} {post_body}",
                    "url": f"https://reddit.com{permalink}",
                    "brand": brand.lower(),
                    "type": "post"
                })

            return results
        except Exception as e:
            print(f"Scraper Error: {e}")
            return []