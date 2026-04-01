"""
BotShield — Multi-signal heuristic bot/spam detection for Reddit posts.
Uses text pattern analysis, engagement metrics, author signals, and
post metadata to compute a bot probability score.
"""
import re
import math
from datetime import datetime, timezone


class BotShield:
    """
    Multi-signal bot detection engine.
    Analyzes post content and Reddit metadata to flag likely bots/spam.
    Each signal returns a score (0.0-1.0) and optional flag string.
    """

    # Spam / promotional phrases
    SPAM_PHRASES = [
        r'buy now', r'check out my', r'use code', r'discount',
        r'limited time', r'click here', r'subscribe to',
        r'follow me', r'dm me', r'free gift', r'giveaway',
        r'earn money', r'make money', r'sign up', r'join now',
        r'100% guaranteed', r'act now', r'don\'t miss',
        r'order now', r'best price', r'lowest price',
        r'affiliate', r'promo code', r'referral link',
    ]

    # Generic low-effort patterns
    GENERIC_PATTERNS = [
        r'^(great|awesome|nice|good|amazing|cool|love it|wow)\s*[.!]*$',
        r'^(this is (great|awesome|amazing|the best))[.!]*$',
        r'^(i agree|same|true|facts|real)\s*[.!]*$',
    ]

    def __init__(self):
        self.spam_re = [re.compile(p, re.IGNORECASE) for p in self.SPAM_PHRASES]
        self.generic_re = [re.compile(p, re.IGNORECASE) for p in self.GENERIC_PATTERNS]

    def analyze(self, post: dict) -> dict:
        """
        Analyze a single post and return bot detection results.

        Returns:
            dict with is_bot (bool), bot_score (float 0-1), flags (list)
        """
        content = post.get('content', '')
        flags = []
        signals = []

        # ──────────────────────────────────────────────
        # TEXT-BASED SIGNALS
        # ──────────────────────────────────────────────

        # Signal 1: Spam phrase detection
        spam_hits = sum(1 for p in self.spam_re if p.search(content))
        if spam_hits >= 3:
            signals.append(('spam_phrases', 0.9, 2.0))
            flags.append(f'spam_phrases:{spam_hits}')
        elif spam_hits >= 1:
            signals.append(('spam_phrases', 0.35, 2.0))
            flags.append(f'spam_phrases:{spam_hits}')
        else:
            signals.append(('spam_phrases', 0.0, 2.0))

        # Signal 2: Excessive links
        links = re.findall(r'https?://\S+', content)
        if len(links) >= 3:
            signals.append(('links', 0.85, 1.5))
            flags.append(f'excessive_links:{len(links)}')
        elif len(links) >= 1:
            signals.append(('links', 0.1, 1.5))
        else:
            signals.append(('links', 0.0, 1.5))

        # Signal 3: Very short / empty content
        word_count = len(content.split())
        if word_count < 3:
            signals.append(('length', 0.7, 1.0))
            flags.append('too_short')
        elif word_count < 8:
            signals.append(('length', 0.2, 1.0))
        else:
            signals.append(('length', 0.0, 1.0))

        # Signal 4: Generic / low-effort content
        is_generic = any(p.match(content.strip()) for p in self.generic_re)
        if is_generic:
            signals.append(('generic', 0.65, 1.5))
            flags.append('generic_content')
        else:
            signals.append(('generic', 0.0, 1.5))

        # Signal 5: Excessive CAPS or punctuation
        if len(content) > 10:
            upper_ratio = sum(1 for c in content if c.isupper()) / max(len(content), 1)
            exclaim_count = content.count('!') + content.count('?')
            if upper_ratio > 0.7:
                signals.append(('caps', 0.6, 1.0))
                flags.append('excessive_caps')
            elif exclaim_count > 5:
                signals.append(('caps', 0.35, 1.0))
                flags.append('excessive_punctuation')
            else:
                signals.append(('caps', 0.0, 1.0))
        else:
            signals.append(('caps', 0.0, 1.0))

        # Signal 6: Repetitive words
        words = content.lower().split()
        if len(words) >= 4:
            unique_ratio = len(set(words)) / len(words)
            if unique_ratio < 0.4:
                signals.append(('repetitive', 0.7, 1.5))
                flags.append('repetitive_words')
            else:
                signals.append(('repetitive', 0.0, 1.5))
        else:
            signals.append(('repetitive', 0.0, 1.5))

        # ──────────────────────────────────────────────
        # AUTHOR SIGNALS
        # ──────────────────────────────────────────────

        # Signal 7: Deleted / suspicious author
        author = post.get('author', '')
        if not author or author in ('[deleted]', '[removed]', 'AutoModerator'):
            signals.append(('author', 0.5, 1.0))
            flags.append('suspicious_author')
        else:
            signals.append(('author', 0.0, 1.0))

        # Signal 8: Author premium status (premium = more trustworthy)
        if post.get('author_premium') is True:
            signals.append(('premium', -0.15, 1.0))  # Negative = reduces bot score
        else:
            signals.append(('premium', 0.05, 1.0))

        # Signal 9: Author has flair (established community member)
        if post.get('author_flair_text'):
            signals.append(('flair', -0.1, 0.8))  # Slightly reduces bot score
        else:
            signals.append(('flair', 0.05, 0.8))

        # ──────────────────────────────────────────────
        # ENGAGEMENT SIGNALS
        # ──────────────────────────────────────────────

        # Signal 10: Upvote ratio
        upvote_ratio = post.get('upvote_ratio')
        if upvote_ratio is not None:
            if upvote_ratio < 0.3:
                signals.append(('upvote_ratio', 0.5, 1.0))
                flags.append(f'low_upvote_ratio:{upvote_ratio}')
            elif upvote_ratio > 0.8:
                signals.append(('upvote_ratio', -0.1, 1.0))  # Good sign
            else:
                signals.append(('upvote_ratio', 0.0, 1.0))
        else:
            signals.append(('upvote_ratio', 0.0, 1.0))

        # Signal 11: Post score (negative = heavily downvoted)
        post_score = post.get('score')
        if post_score is not None:
            if post_score < 0:
                signals.append(('post_score', 0.4, 0.8))
                flags.append('negative_score')
            elif post_score > 100:
                signals.append(('post_score', -0.15, 0.8))  # High score = trusted
            else:
                signals.append(('post_score', 0.0, 0.8))
        else:
            signals.append(('post_score', 0.0, 0.8))

        # Signal 12: Awards (awarded posts are more trustworthy)
        total_awards = post.get('total_awards', 0)
        if total_awards >= 1:
            signals.append(('awards', -0.2, 0.8))
        else:
            signals.append(('awards', 0.0, 0.8))

        # Signal 13: Comment engagement (high comments = real discussion)
        comment_count = post.get('comment_count', 0)
        if comment_count == 0:
            signals.append(('comments', 0.3, 0.8))
            flags.append('no_comments')
        elif comment_count > 50:
            signals.append(('comments', -0.15, 0.8))
        else:
            signals.append(('comments', 0.0, 0.8))

        # ──────────────────────────────────────────────
        # POST METADATA SIGNALS
        # ──────────────────────────────────────────────

        # Signal 14: External domain (non-self posts with suspicious domains)
        is_self = post.get('is_self', False)
        domain = post.get('domain', '')
        if not is_self and domain:
            # Known trustworthy domains
            trusted = ['reddit.com', 'imgur.com', 'youtube.com', 'youtu.be',
                        'twitter.com', 'x.com', 'bbc.co.uk', 'nytimes.com',
                        'theguardian.com', 'reuters.com', 'apnews.com']
            if not any(t in domain for t in trusted):
                signals.append(('domain', 0.2, 1.0))
                flags.append(f'external_domain:{domain}')
            else:
                signals.append(('domain', -0.05, 1.0))
        else:
            signals.append(('domain', 0.0, 1.0))

        # Signal 15: Crossposts (cross-posted content can be spam)
        num_crossposts = post.get('num_crossposts', 0)
        if num_crossposts > 5:
            signals.append(('crossposts', 0.3, 0.5))
            flags.append(f'heavy_crosspost:{num_crossposts}')
        else:
            signals.append(('crossposts', 0.0, 0.5))

        # Signal 16: Subreddit size (posts in tiny subreddits may be less vetted)
        sub_size = post.get('subreddit_subscribers', 0)
        if sub_size > 0 and sub_size < 1000:
            signals.append(('sub_size', 0.2, 0.5))
            flags.append('tiny_subreddit')
        elif sub_size > 100000:
            signals.append(('sub_size', -0.1, 0.5))
        else:
            signals.append(('sub_size', 0.0, 0.5))

        # Signal 17: Locked or stickied (mod-managed content)
        if post.get('stickied'):
            signals.append(('stickied', -0.3, 0.5))  # Mod-approved
        elif post.get('locked'):
            signals.append(('locked', 0.15, 0.5))
            flags.append('locked_post')
        else:
            signals.append(('locked', 0.0, 0.5))

        # ──────────────────────────────────────────────
        # COMBINE ALL SIGNALS
        # ──────────────────────────────────────────────

        weighted_sum = sum(score * weight for _, score, weight in signals)
        total_weight = sum(weight for _, _, weight in signals)
        raw_score = weighted_sum / total_weight if total_weight else 0

        # Clamp to 0-1
        bot_score = round(max(0.0, min(1.0, raw_score)), 3)

        # Threshold
        is_bot = bot_score >= 0.35

        return {
            'is_bot': is_bot,
            'bot_score': bot_score,
            'flags': flags
        }

    def analyze_batch(self, posts: list) -> list:
        """Analyze a list of posts and return results for each."""
        return [self.analyze(p) for p in posts]
