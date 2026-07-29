from difflib import SequenceMatcher
from core.models import FAQ


class FAQEngine:
    @staticmethod
    def score_text(message, faq):
        message = str(message or "").lower().strip()

        question = str(faq.question or "").lower()
        keywords = str(faq.keywords or "").lower()
        answer = str(faq.answer or "").lower()

        score = SequenceMatcher(None, message, question).ratio()

        for keyword in keywords.split(","):
            keyword = keyword.strip()

            if keyword and keyword in message:
                score += 0.45

        if message in question:
            score += 0.25

        if message in answer:
            score += 0.15

        return score

    @staticmethod
    def find_answer(message, category=None, product=None):
        faqs = FAQ.objects.filter(is_active=True).select_related("product", "bundle",)

        if category:
            faqs = faqs.filter(category=category)

        if product:
            faqs = faqs.filter(product=product)

        best_faq = None
        best_score = 0

        for faq in faqs:
            score = FAQEngine.score_text(message, faq)

            if score > best_score:
                best_score = score
                best_faq = faq

        if best_faq and best_score >= 0.45:
            return {
                "found": True,
                "answer": best_faq.answer,
                "faq": best_faq,
                "product": best_faq.product,
                "bundle": best_faq.bundle,
                "score": round(best_score, 2)
            }

        return {
            "found": False,
            "answer": None,
            "faq": None,
            "product": None,
            "bundle": None,
            "score": round(best_score, 2)
        }