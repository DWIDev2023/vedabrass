from core.chatbot.v1.intent_engine import IntentEngine
from core.chatbot.v1.action_engine import ActionEngine
from core.chatbot.v1.faq_engine import FAQEngine
from core.chatbot.v1.session_manager import SessionManager
from core.chatbot.v1.entity_extractor import EntityExtractor


class StateEngine:
    MAIN_MENU_REPLIES = [
        {"label": "Browse Products", "message": "Browse Products"},
        {"label": "Help Me Choose", "message": "Recommend Products"},
        {"label": "Track Order", "message": "Track Order"},
        {"label": "Download Invoice", "message": "Download Invoice"},
        {"label": "Shipping Help", "message": "Shipping Help"},
        {"label": "Talk to Support", "message": "Talk to Support"},
    ]

    NAVIGATION_REPLIES = [
        {"label": "Main Menu", "message": "Main Menu"},
        {"label": "Talk to Support", "message": "Talk to Support"},
    ]

    @staticmethod
    def main_menu(chat_session):
        SessionManager.reset(chat_session)

        return {
            "reply": "How can I help you today?",
            "quick_replies": StateEngine.MAIN_MENU_REPLIES,
            "intent": "main_menu",
        }

    @staticmethod
    def recommendation_type(chat_session, context=None, intent_id=None):
        SessionManager.update_state(
            chat_session,
            "waiting_for_recommendation_type",
            context or {}
        )

        return {
            "reply": "What are you shopping for?",
            "intent": intent_id or "recommendation_type",
            "quick_replies": [
                {"label": "Brass Idols", "message": "Brass Idols"},
                {"label": "Home Decor", "message": "Home Decor"},
                {"label": "Pooja Essentials", "message": "Pooja Essentials"},
                {"label": "Gifting", "message": "Gifting"},
                {"label": "Main Menu", "message": "Main Menu"},
            ]
        }

    @staticmethod
    def ask_order_id(chat_session, context=None, intent_id=None):
        SessionManager.update_state(
            chat_session,
            "waiting_for_order_id",
            context or {}
        )

        return {
            "reply": "Please enter your Order ID.",
            "intent": intent_id or "track_order",
            "quick_replies": StateEngine.NAVIGATION_REPLIES
        }

    @staticmethod
    def ask_invoice_order_id(chat_session, context=None, intent_id=None):
        SessionManager.update_state(
            chat_session,
            "waiting_for_invoice_order_id",
            context or {}
        )

        return {
            "reply": "Please enter your Order ID to download your invoice.",
            "intent": intent_id or "invoice",
            "quick_replies": StateEngine.NAVIGATION_REPLIES
        }

    @staticmethod
    def handle_next_state(next_state, chat_session, message, context, intent_id):
        if not next_state:
            return None

        if next_state == "greeting":
            return StateEngine.main_menu(chat_session)

        if next_state == "track_order_init":
            return StateEngine.ask_order_id(
                chat_session,
                context,
                intent_id
            )

        if next_state == "invoice_init":
            return StateEngine.ask_invoice_order_id(
                chat_session,
                context,
                intent_id
            )

        if next_state in [
            "browse_category_select",
            "recommendation_usecase"
        ]:
            return StateEngine.recommendation_type(
                chat_session,
                context,
                intent_id
            )

        if next_state == "shipping_help":
            result = ActionEngine.execute(
                action="SHIPPING_HELP",
                message=message,
                context=context,
                chat_session=chat_session
            )

            result["intent"] = intent_id
            result.setdefault(
                "quick_replies",
                [
                    {"label": "Track Order", "message": "Track Order"},
                    {"label": "Main Menu", "message": "Main Menu"},
                    {"label": "Talk to Support", "message": "Talk to Support"},
                ]
            )

            return result

        if next_state == "human_handoff":
            result = ActionEngine.execute(
                action="SHOW_SUPPORT",
                message=message,
                context=context,
                chat_session=chat_session
            )

            result["intent"] = intent_id
            result.setdefault(
                "quick_replies",
                [
                    {"label": "Main Menu", "message": "Main Menu"},
                ]
            )

            return result

        return None

    @staticmethod
    def handle_action(action, chat_session, message, context, intent_id):
        if not action:
            return None

        if action == "ASK_ORDER_ID":
            return StateEngine.ask_order_id(
                chat_session,
                context,
                intent_id
            )

        if action == "ASK_INVOICE_ORDER_ID":
            return StateEngine.ask_invoice_order_id(
                chat_session,
                context,
                intent_id
            )

        if action == "ASK_RECOMMENDATION_TYPE":
            return StateEngine.recommendation_type(
                chat_session,
                context,
                intent_id
            )

        result = ActionEngine.execute(
            action=action,
            message=message,
            context=context,
            chat_session=chat_session
        )

        result["intent"] = intent_id
        result.setdefault(
            "quick_replies",
            StateEngine.NAVIGATION_REPLIES
        )

        return result

    @staticmethod
    def handle(chat_session, message):
        message = str(message or "").strip()
        message_lower = message.lower()
        context = chat_session.context or {}
        current_state = chat_session.current_state or "greeting"

        extracted_budget = EntityExtractor.extract_budget(message)
        extracted_category = EntityExtractor.extract_category(message)
        extracted_use_case = EntityExtractor.extract_use_case(message)
        extracted_order_id = EntityExtractor.extract_order_id(message)

        if extracted_budget:
            context["budget"] = extracted_budget

        if extracted_category:
            context["category"] = extracted_category

        if extracted_use_case:
            context["use_case"] = extracted_use_case

        if message_lower in [
            "main menu",
            "menu",
            "start over",
            "start again",
            "go back",
            "back"
        ]:
            return StateEngine.main_menu(chat_session)

        if current_state == "waiting_for_order_id":
            result = ActionEngine.execute(
                action="TRACK_ORDER",
                message=message,
                context=context,
                chat_session=chat_session
            )

            SessionManager.update_state(
                chat_session,
                "greeting",
                context
            )

            result.setdefault(
                "quick_replies",
                [
                    {"label": "Track Another Order", "message": "Track Order"},
                    {"label": "Main Menu", "message": "Main Menu"},
                    {"label": "Talk to Support", "message": "Talk to Support"},
                ]
            )

            return result

        if current_state == "waiting_for_invoice_order_id":
            result = ActionEngine.execute(
                action="GET_INVOICE",
                message=message,
                context=context,
                chat_session=chat_session
            )

            SessionManager.update_state(
                chat_session,
                "greeting",
                context
            )

            result.setdefault(
                "quick_replies",
                [
                    {"label": "Try Another Invoice", "message": "Download Invoice"},
                    {"label": "Main Menu", "message": "Main Menu"},
                    {"label": "Talk to Support", "message": "Talk to Support"},
                ]
            )

            return result

        if current_state == "waiting_for_recommendation_type":
            context["category"] = message

            SessionManager.update_state(
                chat_session,
                "waiting_for_budget",
                context
            )

            return {
                "reply": "What is your preferred budget?",
                "intent": "recommendation_budget",
                "quick_replies": [
                    {"label": "Under ₹1000", "message": "Under 1000"},
                    {"label": "₹1000 - ₹3000", "message": "1000 to 3000"},
                    {"label": "₹3000 - ₹7000", "message": "3000 to 7000"},
                    {"label": "Above ₹7000", "message": "Above 7000"},
                    {"label": "Main Menu", "message": "Main Menu"},
                ]
            }

        if current_state == "waiting_for_budget":
            context["budget"] = message

            result = ActionEngine.execute(
                action="RECOMMEND_PRODUCTS",
                message=message,
                context=context,
                chat_session=chat_session
            )

            SessionManager.update_state(
                chat_session,
                "greeting",
                {}
            )

            result.setdefault(
                "quick_replies",
                [
                    {"label": "Recommend Again", "message": "Recommend Products"},
                    {"label": "Main Menu", "message": "Main Menu"},
                    {"label": "Talk to Support", "message": "Talk to Support"},
                ]
            )

            return result
        
        if (
            current_state == "greeting"
            and (
                extracted_category
                or extracted_use_case
                or extracted_budget
            )
        ):
            result = ActionEngine.execute(
                action="RECOMMEND_PRODUCTS",
                message=message,
                context=context,
                chat_session=chat_session
            )

            if result.get("products"):
                SessionManager.update_state(
                    chat_session,
                    "greeting",
                    {}
                )

                result.setdefault(
                    "quick_replies",
                    [
                        {"label": "Recommend Again", "message": "Recommend Products"},
                        {"label": "Main Menu", "message": "Main Menu"},
                        {"label": "Talk to Support", "message": "Talk to Support"},
                    ]
                )

                return result

        faq_result = FAQEngine.find_answer(message)

        if faq_result["found"]:
            return {
                "reply": faq_result["answer"],
                "intent": "faq",
                "quick_replies": StateEngine.NAVIGATION_REPLIES
            }

        intent, score = IntentEngine.match_intent(message)

        if intent and score >= 0.55:
            intent_id = intent.get("id")
            action = intent.get("action")
            next_state = intent.get("next_state")

            next_state_result = StateEngine.handle_next_state(
                next_state=next_state,
                chat_session=chat_session,
                message=message,
                context=context,
                intent_id=intent_id
            )

            if next_state_result:
                return next_state_result

            action_result = StateEngine.handle_action(
                action=action,
                chat_session=chat_session,
                message=message,
                context=context,
                intent_id=intent_id
            )

            if action_result:
                return action_result

        recommendation_keywords = [
            "idol", "idols", "ganesha", "ganapati", "lakshmi", "krishna",
            "radha", "hanuman", "shiva", "durga", "narsimha", "narasimha",
            "balaji", "murugan", "vishnu", "saraswati", "laddu gopal",
            "khatu shyam", "sai baba", "urli", "diya", "diyas", "bell",
            "kalash", "asan", "chowki", "sadaari", "deepam", "dhoop",
            "cookware", "serveware", "drinkware", "cup", "saucer",
            "glass", "teapot", "mug", "handi", "decor", "wall decor",
            "table decor", "gift", "gifting", "pooja", "worship",
            "mandir", "festival", "diwali", "corporate", "housewarming",
            "anniversary", "wedding", "home decor", "renuka", "maata",
            "gomatha", "divine symbols", "sacred heritage",
            "vintage", "cooking serve pot", "sacred heritage decor",
            "cooking pot", "serving pot", "mug", "urli", "elephant urli",
            "horse decor", "turtle decor", "lion decor", "swastik decor"
        ]

        if any(keyword in message_lower for keyword in recommendation_keywords):
            result = ActionEngine.execute(
                action="RECOMMEND_PRODUCTS",
                message=message,
                context=context,
                chat_session=chat_session
            )

            result.setdefault(
                "quick_replies",
                [
                    {"label": "Recommend Again", "message": "Recommend Products"},
                    {"label": "Main Menu", "message": "Main Menu"},
                    {"label": "Talk to Support", "message": "Talk to Support"},
                ]
            )

            return result

        return {
            "reply": "I can help with product recommendations, order tracking, invoices, shipping and support.",
            "intent": "fallback",
            "quick_replies": StateEngine.MAIN_MENU_REPLIES
        }