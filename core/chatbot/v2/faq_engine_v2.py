from difflib import SequenceMatcher
from core.models import FAQ


class FAQEngineV2:

    STOP_WORDS = {
        "a", "an", "the", "is", "are", "was", "were",
        "can", "could", "do", "does", "did",
        "how", "what", "when", "where", "which",
        "i", "me", "my", "you", "your",
        "to", "for", "of", "in", "on", "at",
        "and", "or", "with", "from", "please"
    }

    @staticmethod
    def tokenize(text):

        return {
            word.strip()
            for word in str(text).lower().split()
            if word.strip() and word not in FAQEngineV2.STOP_WORDS
        }

    @staticmethod
    def score(message, faq):

        message = str(message).lower().strip()

        score = 0

        question = (faq.question or "").lower()
        keywords = (faq.keywords or "").lower()

        message_tokens = FAQEngineV2.tokenize(message)
        question_tokens = FAQEngineV2.tokenize(question)

        # -------------------------------
        # Exact keyword match (Highest)
        # -------------------------------

        for keyword in keywords.split(","):

            keyword = keyword.strip().lower()

            if not keyword:
                continue

            if keyword == message:
                score += 5

            elif keyword in message:
                score += 3

        # -------------------------------
        # Question token overlap
        # -------------------------------

        overlap = len(
            message_tokens.intersection(
                question_tokens
            )
        )

        score += overlap * 1.2

        # -------------------------------
        # Small fuzzy boost only
        # -------------------------------

        score += (
            SequenceMatcher(
                None,
                message,
                question
            ).ratio()
            * 0.5
        )

        return score

    @staticmethod
    def search(message):

        faqs = (
            FAQ.objects.filter(
                is_active=True
            ).select_related(
                "product",
                "bundle",
            )
        )

        best_faq = None
        best_score = 0

        for faq in faqs:

            score = FAQEngineV2.score(
                message,
                faq
            )

            if score > best_score:

                best_score = score
                best_faq = faq

        # Require meaningful confidence
        if best_faq and best_score >= 2.5:

            return {
                "found": True,
                "faq": best_faq,
                "answer": best_faq.answer,
                "product": best_faq.product,
                "bundle": best_faq.bundle,
            }

        return {
            "found": False
        }