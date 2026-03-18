import requests
import time
import os

class RedditScraper:
    def __init__(self):
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0'}

    def scrape(self, brand: str):
        """
        1. Search Reddit for posts matching the brand/query
        2. For each post, fetch top comments
        Returns a combined list of posts + their comments
        """
        post_limit = os.getenv("REDDIT_POST_LIMIT", "15")
        comments_per_post = int(os.getenv("REDDIT_COMMENTS_PER_POST", "10"))
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

                # Fetch comments for this post
                comments = self._fetch_comments(permalink, comments_per_post)
                results.extend(comments)

            return results
        except Exception as e:
            print(f"Scraper Error: {e}")
            return []

    def _fetch_comments(self, permalink, limit=3):
        """Fetch top comments from a single post"""
        try:
            url = f"https://www.reddit.com{permalink}.json?limit={limit}&sort=top"
            time.sleep(0.5)  # Rate limit - Reddit blocks rapid requests
            response = requests.get(url, headers=self.headers)
            if response.status_code != 200:
                return []

            data = response.json()
            if len(data) < 2:
                return []

            comments_data = data[1].get('data', {}).get('children', [])
            comments = []
            for c in comments_data:
                if c.get('kind') != 't1':  # skip non-comment entries
                    continue
                cdata = c['data']
                body = cdata.get('body', '').strip()
                if not body or body == '[deleted]' or body == '[removed]':
                    continue
                comments.append({
                    "id": cdata.get('id'),
                    "author": cdata.get('author'),
                    "content": body,
                    "url": f"https://reddit.com{cdata.get('permalink', '')}",
                    "brand": "",
                    "type": "comment"
                })
            return comments
        except Exception as e:
            print(f"Comment fetch error: {e}")
            return []