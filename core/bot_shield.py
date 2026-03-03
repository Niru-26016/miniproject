import re

class BotShield:
    def predict(self, comment_data):
        content = comment_data.get('content', '').lower()
        
        # (Placeholder for your XGBoost logic)
        is_spam_text = len(re.findall(r'http\S+', content)) > 2 
        is_too_short = len(content.split()) < 4
        
        bot_score = 0.9 if (is_spam_text or is_too_short) else 0.1
        is_bot = bot_score > 0.5
        
        return is_bot, bot_score