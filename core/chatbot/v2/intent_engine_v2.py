import json
import os
from functools import lru_cache
from django.conf import settings


class IntentEngineV2:
    @staticmethod
    @lru_cache(maxsize=1)
    def load_config():
        file_path = os.path.join(
            settings.BASE_DIR,
            "core",
            "chatbot",
            "v2",
            "chatbot.json"
        )

        with open(file_path, "r") as f:
            return json.load(f)

    @staticmethod
    def detect(message):
        if not message:
            return None

        message = message.lower().strip()

        config = IntentEngineV2.load_config()

        intents = config.get("intents", [])

        for intent in intents:
            for keyword in intent.get("keywords", []):
                keyword = keyword.lower().strip()

                if keyword in message:
                    return {
                        "intent": intent["id"],
                        "next_state": intent["next_state"]
                    }

        return {
            "intent": "product_search",
            "next_state": "recommendation_results"
        }