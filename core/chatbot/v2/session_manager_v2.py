from core.models import ChatSession, ChatMessage
from core.models import ChatbotSearchLog


class SessionManagerV2:
    @staticmethod
    def get_or_create_session(request):
        if not request.session.session_key:
            request.session.create()

        chat_session, _ = ChatSession.objects.get_or_create(
            session_key=request.session.session_key,
            is_active=True,
            defaults={
                "current_state": "greeting",
                "context": {},
            },
        )

        return chat_session

    @staticmethod
    def update_state(
        chat_session,
        state,
        context=None,
    ):
        chat_session.current_state = state

        if context is not None:
            chat_session.context = context

        chat_session.save(
            update_fields=[
                "current_state",
                "context",
            ]
        )

    @staticmethod
    def update_context(
        chat_session,
        **kwargs,
    ):
        context = chat_session.context or {}
        context.update(kwargs)
        chat_session.context = context
        chat_session.save(
            update_fields=["context"]
        )

        return context

    @staticmethod
    def attach_customer(
        chat_session,
        customer,
    ):
        chat_session.customer = customer

        chat_session.save(
            update_fields=["customer"]
        )

    @staticmethod
    def reset(
        chat_session,
    ):
        chat_session.current_state = "greeting"
        chat_session.context = {}

        chat_session.save(
            update_fields=[
                "current_state",
                "context",
            ]
        )

    @staticmethod
    def log_message(
        chat_session,
        sender,
        message,
        intent=None,
        state=None,
    ):
        return ChatMessage.objects.create(
            session=chat_session,
            sender=sender,
            message=message,
            intent=intent,
            state=state,
        )
    
    @staticmethod
    def log_search(
        *,
        request,
        chat_session,
        query,
        result,
    ):
        customer = None
 
        if request.user.is_authenticated:
            customer = getattr(request.user, "customer", None)
 
        # ActionEngineV2 nests logging metadata under "log"; it isn't
        # available at the top level of `result`.
        log_data = result.get("log") or {}
 
        matched_faq = log_data.get("matched_faq")
        matched_bundle = log_data.get("matched_bundle")
        support_ticket = log_data.get("support_ticket")
        selected_product = log_data.get("selected_product")
        matched_products = log_data.get("matched_products") or []
 
        # These are serialized dicts (e.g. {"id": .., "question": ..}),
        # not model instances, so assign via the *_id field using the id.
        log = ChatbotSearchLog.objects.create(
            customer=customer,
            session=chat_session,
            query=query,
            result_type=log_data.get("result_type", "EMPTY"),
            matched_faq_id=matched_faq.get("id") if matched_faq else None,
            matched_bundle_id=matched_bundle.get("id") if matched_bundle else None,
            support_ticket_id=support_ticket.get("id") if support_ticket else None,
            selected_product_id=selected_product.get("id") if selected_product else None,
        )
 
        product_ids = [p["id"] for p in matched_products if p and p.get("id")]
 
        if product_ids:
            log.matched_products.set(product_ids)
 
        return log
    