from core.models import ChatbotSearchLog


class ChatbotLogger:
    @staticmethod
    def log(
        *,
        query,
        customer=None,
        session=None,
        result_type,
        faq=None,
        bundle=None,
        products=None,
        support_ticket=None,
        selected_product=None,
    ):

        log = ChatbotSearchLog.objects.create(
            customer=customer,
            session=session,
            query=query,
            matched_faq=faq,
            matched_bundle=bundle,
            support_ticket=support_ticket,
            selected_product=selected_product,
            result_type=result_type,
        )

        if products:
            log.matched_products.set(products)

        return log