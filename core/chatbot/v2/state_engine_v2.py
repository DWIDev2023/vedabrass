import json
import os
from functools import lru_cache
from django.conf import settings
from .intent_engine_v2 import IntentEngineV2
from .action_engine_v2 import ActionEngineV2


class StateEngineV2:
    @staticmethod
    def _json_safe(value):
        """
        Convert accidental ORM/model/Decimal values into JSON-safe output.
        This keeps /chatbot/reply/ safe even when debug logs or future
        action payloads include Django objects.
        """
        if value is None or isinstance(value, (str, int, float, bool)):
            return value

        if isinstance(value, dict):
            return {
                str(key): StateEngineV2._json_safe(item)
                for key, item in value.items()
            }

        if isinstance(value, (list, tuple, set)):
            return [StateEngineV2._json_safe(item) for item in value]

        # Decimal, UUID, date/time, ImageFieldFile and similar objects.
        if hasattr(value, "isoformat"):
            return value.isoformat()

        # Last-resort model/object serialization for accidental log values.
        if hasattr(value, "pk") or hasattr(value, "id"):
            return {
                "id": getattr(value, "pk", getattr(value, "id", None)),
                "name": getattr(value, "name", None),
                "slug": getattr(value, "slug", None),
            }

        return str(value)


    RESET_CONTEXT_INTENTS = {
        "main_menu",
        "browse_products",
        "recommend_products",
    }

    GIFTING_SUBCATEGORY_STATE_MAP = {
        "festival gifts": "gifting_collection_festival",
        "festival-gifts": "gifting_collection_festival",
        "special occasion gifts": "gifting_collection_special",
        "special occassion gifts": "gifting_collection_special",
        "special-occassion-gifts": "gifting_collection_special",
        "special-occasion-gifts": "gifting_collection_special",
        "corporate gifting": "gifting_collection_corporate",
        "corporate-gifting": "gifting_collection_corporate",
    }

    @staticmethod
    def _normalize_choice(value):
        return (value or "").strip().lower().replace("_", "-")

    @staticmethod
    def _is_gifting_choice(value):
        text = StateEngineV2._normalize_choice(value)
        return text in {"gifting", "gift", "gifts", "gifting-items", "gifting items"}

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
    def _route_intent_if_command(chat_session, message, context, current_state):
        """
        Route explicit menu/quick-reply commands from any state.
        Free-text product searches should still be handled only from greeting,
        otherwise answers to questions like "Brass Idols" would be misrouted.
        """
        detected = IntentEngineV2.detect(message)

        if not detected:
            return None

        intent = detected.get("intent")

        # The intent engine defaults unknown text to product_search.
        # Do not treat that fallback as a global command.
        if intent == "product_search" and current_state != "greeting":
            return None

        next_state = detected.get("next_state")
        if not next_state:
            return None

        if intent in StateEngineV2.RESET_CONTEXT_INTENTS:
            context = {}

        chat_session.context = context
        chat_session.current_state = next_state
        chat_session.save(update_fields=["context", "current_state"])

        return StateEngineV2.process(
            next_state,
            message=message,
            context=context,
            chat_session=chat_session,
        )

    @staticmethod
    def handle(chat_session, message):
        config = StateEngineV2.load_config()
        context = chat_session.context or {}
        current_state = chat_session.current_state or "greeting"

        state = config["states"].get(current_state)

        if not state:
            chat_session.current_state = "greeting"
            chat_session.context = {}
            chat_session.save(update_fields=["current_state", "context"])
            return StateEngineV2.process(
                "greeting",
                chat_session=chat_session,
                context={},
            )

        # Explicit commands such as Main Menu, Browse Products, Track Order,
        # Download Invoice and Talk to Support should work from any state.
        command_result = StateEngineV2._route_intent_if_command(
            chat_session=chat_session,
            message=message,
            context=context,
            current_state=current_state,
        )
        if command_result is not None:
            return command_result

        state_type = state.get("type")

        # ===================================================
        # INPUT CAPTURE / QUESTION STATES
        # ===================================================
        if state_type in ["question", "input_capture"]:
            entity = state.get("store_entity")
            if entity:
                context[entity] = message

            next_state = state.get("next_state")

            # Gifting has a real hierarchy in the catalog:
            # gifting-items -> subcategory -> collection -> products.
            # Route the guided flow through that hierarchy instead of jumping
            # straight from "Gifting" to budget.
            if current_state in {"browse_category_select", "recommendation_usecase"} and StateEngineV2._is_gifting_choice(message):
                context["category"] = "Gifting"
                context["category_slug"] = "gifting-items"
                next_state = "gifting_subcategory_select"

            if current_state == "gifting_subcategory_select":
                selected_subcategory = StateEngineV2._normalize_choice(message)
                context["category"] = "Gifting"
                context["category_slug"] = "gifting-items"
                next_state = StateEngineV2.GIFTING_SUBCATEGORY_STATE_MAP.get(
                    selected_subcategory,
                    "gifting_subcategory_select",
                )

            if current_state.startswith("gifting_collection_"):
                context["category"] = "Gifting"
                context["category_slug"] = "gifting-items"

            if not next_state:
                chat_session.context = context
                chat_session.current_state = "greeting"
                chat_session.save(update_fields=["context", "current_state"])
                return StateEngineV2.process(
                    "greeting",
                    context=context,
                    chat_session=chat_session,
                )

            chat_session.context = context
            chat_session.current_state = next_state
            chat_session.save(update_fields=["context", "current_state"])

            next_config = config["states"].get(next_state)
            if next_config:
                next_type = next_config.get("type")

                if next_type in ["action", "escalation"]:
                    return StateEngineV2.process(
                        next_state,
                        message=message,
                        context=context,
                        chat_session=chat_session,
                    )

                return StateEngineV2.process(
                    next_state,
                    context=context,
                    chat_session=chat_session,
                )

        return StateEngineV2.process(
            state_name=current_state,
            message=message,
            context=context,
            chat_session=chat_session,
        )

    @staticmethod
    def process(state_name, message=None, context=None, chat_session=None):
        config = StateEngineV2.load_config()
        state = config["states"].get(state_name)

        if not state:
            return {"reply": "Invalid chatbot state."}

        state_type = state.get("type")

        # ===================================================
        # MESSAGE
        # ===================================================
        if state_type == "message":
            # Message states are informational. Keep the conversation open
            # by returning to greeting after rendering the message.
            if chat_session and state_name != "greeting":
                chat_session.current_state = "greeting"
                chat_session.save(update_fields=["current_state"])

            return {
                "reply": state.get("message"),
                "quick_replies": state.get("quick_replies", []),
                "links": state.get("links", []),
            }

        # ===================================================
        # QUESTION / INPUT
        # ===================================================
        if state_type in ["question", "input_capture"]:
            return {
                "reply": state.get("message"),
                "quick_replies": state.get("quick_replies", []),
            }

        # ===================================================
        # ACTION
        # ===================================================
        if state_type == "action":
            result = ActionEngineV2.execute(
                action=state["action"],
                message=message,
                context=context,
                chat_session=chat_session,
            )

            # Preserve quick replies defined in chatbot.json unless the action
            # explicitly returned its own.
            result.setdefault("quick_replies", state.get("quick_replies", []))

            if chat_session:
                chat_session.current_state = "greeting"
                chat_session.save(update_fields=["current_state"])

            return StateEngineV2._json_safe(result)

        # ===================================================
        # ESCALATION
        # ===================================================
        if state_type == "escalation":
            result = ActionEngineV2.execute(
                action="SHOW_SUPPORT",
                message=message,
                context=context,
                chat_session=chat_session,
            )
            result.setdefault("quick_replies", state.get("quick_replies", []))

            if chat_session:
                chat_session.current_state = "greeting"
                chat_session.save(update_fields=["current_state"])

            return StateEngineV2._json_safe(result)

        return {"reply": "Unsupported chatbot state."}
    
