import json
import os
from difflib import SequenceMatcher
from django.conf import settings


class IntentEngine:
    @staticmethod
    def load_data():
        file_path = os.path.join(
            settings.BASE_DIR,
            "core",
            "chatbot",
            "v1",
            "chatbot.json"
        )

        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)

    @staticmethod
    def normalize(text):
        return str(text or "").lower().strip()

    @staticmethod
    def score_text(message, keyword):
        message = IntentEngine.normalize(message)
        keyword = IntentEngine.normalize(keyword)

        score = SequenceMatcher(None, message, keyword).ratio()

        if keyword in message:
            score += 0.5

        return score

    @staticmethod
    def match_intent(message):
        data = IntentEngine.load_data()
        best_intent = None
        best_score = 0

        for intent in data.get("intents", []):
            for keyword in intent.get("keywords", []):
                score = IntentEngine.score_text(message, keyword)

                if score > best_score:
                    best_score = score
                    best_intent = intent

        return best_intent, round(best_score, 2)