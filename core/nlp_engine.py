from openai import OpenAI
import json


class NLPEngine:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)

    def generate_insight(self, brand, posts):
        prompt = f"""
        Analyze these genuine customer reviews for {brand}:
        {posts}
        
        Identify the top human problem and suggest 2 improvements. 
        Keep it humanized and conversational.
        """
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

    def detect_fake_posts(self, posts_list):
        """
        Takes a list of post strings and classifies each as real or fake.
        Returns a list of dicts: { "is_fake": bool, "confidence": float }
        """
        if not posts_list:
            return []

        numbered = "\n".join([f"{i+1}. {c[:500]}" for i, c in enumerate(posts_list)])

        prompt = f"""You are an expert at detecting fake, bot-generated, or spam posts on social media.

Analyze each of the following {len(posts_list)} posts and classify them as "real" or "fake".

A post is FAKE if it:
- Looks auto-generated, generic, or spammy
- Contains suspicious promotional language
- Is incoherent or nonsensical
- Appears to be from a bot (repetitive patterns, unnatural phrasing)
- Is an obvious advertisement or contains excessive links

A post is REAL if it:
- Contains genuine human opinion or experience
- Has natural language patterns
- Provides specific details about the product

Posts:
{numbered}

Respond ONLY with a valid JSON array of objects. Each object must have:
- "index": the 1-based post number
- "is_fake": boolean (true if fake, false if real)
- "confidence": float between 0.0 and 1.0

Example: [{{"index": 1, "is_fake": false, "confidence": 0.15}}, {{"index": 2, "is_fake": true, "confidence": 0.92}}]

JSON:"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            raw = response.choices[0].message.content.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
                if raw.endswith("```"):
                    raw = raw[:-3]
                raw = raw.strip()
            
            results = json.loads(raw)
            result_map = {r["index"]: r for r in results}
            ordered = []
            for i in range(1, len(posts_list) + 1):
                if i in result_map:
                    ordered.append({
                        "is_fake": result_map[i]["is_fake"],
                        "confidence": result_map[i]["confidence"]
                    })
                else:
                    ordered.append({"is_fake": False, "confidence": 0.0})
            return ordered
        except Exception as e:
            print(f"Fake detection error: {e}")
            return [{"is_fake": False, "confidence": 0.0} for _ in posts_list]

    def advanced_analysis(self, brand, posts_list):
        """
        Single OpenAI call that performs:
        1. Emotion Detection (joy, anger, fear, surprise, sadness, disgust)
        2. Aspect-Based Sentiment
        3. Keyword/Topic Extraction
        4. Actionable Recommendations

        Returns a dict with all results.
        """
        if not posts_list:
            return {
                "emotions": {"joy": 0, "anger": 0, "fear": 0, "surprise": 0, "sadness": 0, "disgust": 0},
                "post_emotions": [],
                "aspects": [],
                "keywords": [],
                "recommendations": []
            }

        numbered = "\n".join([f"{i+1}. {c[:400]}" for i, c in enumerate(posts_list)])

        prompt = f"""You are an expert sentiment and content analyst. Analyze these {len(posts_list)} posts about "{brand}".

Posts:
{numbered}

Perform ALL of the following analyses and return a single JSON object:

1. **EMOTION DETECTION**: For EACH post, detect the dominant emotion.
   Emotions: joy, anger, fear, surprise, sadness, disgust, neutral
   Also provide an overall emotion summary (count of each emotion across all posts).

2. **ASPECT-BASED SENTIMENT**: Identify the top product aspects/features discussed 
   (e.g., "camera", "battery", "price", "design", "performance", "customer service").
   For each aspect, provide the overall sentiment: positive, negative, or neutral.
   Only include aspects that are actually mentioned.

3. **KEYWORD/TOPIC EXTRACTION**: Extract the top 5 most discussed topics or features.
   For each keyword, provide a relevance score (0.0 to 1.0) and mention count.

4. **RECOMMENDATIONS**: Based on the sentiment patterns, generate 3-4 actionable 
   recommendations for the brand. Each should have a title, description, and priority 
   (high/medium/low).

Respond ONLY with valid JSON in this exact structure:
{{
    "emotions": {{
        "joy": <count>,
        "anger": <count>,
        "fear": <count>,
        "surprise": <count>,
        "sadness": <count>,
        "disgust": <count>,
        "neutral": <count>
    }},
    "post_emotions": [
        {{"index": 1, "emotion": "joy"}},
        {{"index": 2, "emotion": "anger"}}
    ],
    "aspects": [
        {{"aspect": "camera", "sentiment": "positive", "mentions": 5}},
        {{"aspect": "battery", "sentiment": "negative", "mentions": 3}}
    ],
    "keywords": [
        {{"keyword": "battery life", "relevance": 0.95, "mentions": 8}},
        {{"keyword": "camera quality", "relevance": 0.87, "mentions": 6}}
    ],
    "recommendations": [
        {{
            "title": "Improve Battery Life",
            "description": "Users frequently complain about battery drain...",
            "priority": "high"
        }}
    ]
}}

JSON:"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            raw = response.choices[0].message.content.strip()
            # Clean markdown fencing
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
                if raw.endswith("```"):
                    raw = raw[:-3]
                raw = raw.strip()

            result = json.loads(raw)

            # Validate and fill defaults
            defaults = {
                "emotions": {"joy": 0, "anger": 0, "fear": 0, "surprise": 0, "sadness": 0, "disgust": 0, "neutral": 0},
                "post_emotions": [],
                "aspects": [],
                "keywords": [],
                "recommendations": []
            }
            for key in defaults:
                if key not in result:
                    result[key] = defaults[key]

            return result

        except Exception as e:
            print(f"Advanced analysis error: {e}")
            return {
                "emotions": {"joy": 0, "anger": 0, "fear": 0, "surprise": 0, "sadness": 0, "disgust": 0, "neutral": 0},
                "post_emotions": [],
                "aspects": [],
                "keywords": [],
                "recommendations": []
            }