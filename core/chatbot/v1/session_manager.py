from core.models import ChatSession, ChatMessage


class SessionManager:
    @staticmethod
    def get_or_create_session(request):
        if not request.session.session_key:
            request.session.create()

        session_key = request.session.session_key

        chat_session, created = ChatSession.objects.get_or_create(
            session_key=session_key,
            is_active=True,
            defaults={
                "current_state": "greeting",
                "context": {}
            }
        )

        return chat_session

    @staticmethod
    def update_state(chat_session, state, context=None):
        chat_session.current_state = state

        if context is not None:
            chat_session.context = context

        chat_session.save(
            update_fields=[
                "current_state",
                "context"
            ]
        )

    @staticmethod
    def reset(chat_session):
        chat_session.current_state = "greeting"
        chat_session.context = {}
        chat_session.save(
            update_fields=[
                "current_state",
                "context"
            ]
        )

    @staticmethod
    def log_message(chat_session, sender, message, intent=None, state=None):
        ChatMessage.objects.create(
            session=chat_session,
            sender=sender,
            message=message,
            intent=intent,
            state=state
        )