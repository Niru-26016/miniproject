from openai import OpenAI

class NLPEngine:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)

    def generate_insight(self, brand, comments):
        prompt = f"""
        Analyze these genuine customer reviews for {brand}:
        {comments}
        
        Identify the top human problem and suggest 2 improvements. 
        Keep it humanized and conversational.
        """
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content