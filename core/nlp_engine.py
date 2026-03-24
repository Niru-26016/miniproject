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

        # Build numbered list for the prompt
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
            # Clean up markdown fencing if present
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
                if raw.endswith("```"):
                    raw = raw[:-3]
                raw = raw.strip()
            
            results = json.loads(raw)
            # Ensure results are in order and fill gaps
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