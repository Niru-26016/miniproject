import requests
import os

class RedditScraper:
    def __init__(self):
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0'}

    def scrape(self, brand: str):
        """
        Search Reddit for posts matching the brand/query.
        Extracts comprehensive metadata from each post.
        """
        post_limit = os.getenv("REDDIT_POST_LIMIT", "15")
        url = f"https://www.reddit.com/search.json?q={brand}&limit={post_limit}&sort=relevance&t=week"
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code != 200: return []
            
            posts = response.json().get('data', {}).get('children', [])
            results = []

            for p in posts:
                d = p['data']
                post_title = d.get('title', '')
                post_body = d.get('selftext', '')
                permalink = d.get('permalink', '')

                results.append({
                    # Core fields
                    "id": d.get('id'),
                    "author": d.get('author'),
                    "content": f"{post_title} {post_body}".strip(),
                    "title": post_title,
                    "url": f"https://reddit.com{permalink}",
                    "brand": brand.lower(),
                    "type": "post",

                    # Engagement metrics
                    "score": d.get('score', 0),
                    "upvote_ratio": d.get('upvote_ratio'),
                    "comment_count": d.get('num_comments', 0),
                    "num_crossposts": d.get('num_crossposts', 0),
                    "total_awards": d.get('total_awards_received', 0),

                    # Post metadata
                    "subreddit": d.get('subreddit', ''),
                    "subreddit_subscribers": d.get('subreddit_subscribers', 0),
                    "domain": d.get('domain', ''),
                    "is_self": d.get('is_self', False),
                    "is_video": d.get('is_video', False),
                    "over_18": d.get('over_18', False),
                    "spoiler": d.get('spoiler', False),
                    "locked": d.get('locked', False),
                    "stickied": d.get('stickied', False),

                    # Author metadata
                    "author_premium": d.get('author_premium', False),
                    "author_flair_text": d.get('author_flair_text'),

                    # Timestamps
                    "created_utc": d.get('created_utc'),
                })

            return results
        except Exception as e:
            print(f"Scraper Error: {e}")
            return []