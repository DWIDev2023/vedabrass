"""
Run from your Django project root:

    python manage.py shell < core/chatbot/v2/shell_flow_tests.py

This exercises chatbot v2 with your real Product/FAQ/Order database and checks
that every result can be returned by JsonResponse.
"""

import json
from dataclasses import dataclass, field

from django.core.serializers.json import DjangoJSONEncoder

from core.chatbot.v2.state_engine_v2 import StateEngineV2
from core.chatbot.v2.action_engine_v2 import ActionEngineV2
from core.chatbot.v2.recommendation_engine_v2 import RecommendationEngineV2


@dataclass
class DummyChatSession:
    current_state: str = "greeting"
    context: dict = field(default_factory=dict)
    customer: object = None

    def save(self, *args, **kwargs):
        return None


def assert_json_safe(label, result):
    try:
        json.dumps(result, cls=DjangoJSONEncoder)
    except TypeError as exc:
        raise AssertionError(f"{label} returned non-JSON-safe data: {exc}\n{result}") from exc


def assert_not_empty_products(label, result):
    assert_json_safe(label, result)
    if result.get("log", {}).get("result_type") == "EMPTY":
        print(f"WARN: {label}: EMPTY -> {result.get('reply')}")
    else:
        print(f"PASS: {label}: {len(result.get('products', []))} products")


def run_state_sequence(label, messages):
    session = DummyChatSession()
    result = None
    for message in messages:
        result = StateEngineV2.handle(session, message)
        assert_json_safe(f"{label} / {message}", result)
    return result


print("\n=== Basic state/menu tests ===")
for message in [
    "Main Menu",
    "Browse Products",
    "Recommend Products",
    "Track Order",
    "Download Invoice",
    "Shipping Help",
    "Show More Products",
]:
    result = run_state_sequence(message, [message])
    print(f"PASS: {message}: state flow JSON-safe")

support_result = ActionEngineV2.execute("SHOW_SUPPORT", message="Need support", chat_session=None)
assert_json_safe("SHOW_SUPPORT without session", support_result)
print("PASS: SHOW_SUPPORT without real session JSON-safe")

print("\n=== Browse category + budget guided tests ===")
categories = ["Brass Idols", "Home Decor", "Pooja Essentials", "Kitchen Essentials"]
budgets = [
    "Under 1000",
    "1000 to 3000",
    "3000 to 7000",
    "7000 to 10000",
    "10000 to 15000",
    "15000 to 20000",
    "20000 to 25000",
    "Above 25000",
]
for category in categories:
    for budget in budgets:
        result = run_state_sequence(
            f"Browse / {category} / {budget}",
            ["Browse Products", category, budget],
        )
        assert_not_empty_products(f"Browse / {category} / {budget}", result)

print("\n=== Gifting hierarchy guided tests ===")
gifting_paths = {
    "Festival Gifts": ["Diwali", "Onam", "Holi", "Dussehra", "Janmashtami", "Ganesh Chaturthi", "Navratri"],
    "Special Occasion Gifts": ["Happy Rakhi", "House Warming Gift", "Wedding Anniversary"],
    "Corporate Gifting": ["Gift Hamper", "Work Anniversary", "Special Combos"],
}
for subcategory, collections in gifting_paths.items():
    for collection in collections:
        for budget in budgets:
            result = run_state_sequence(
                f"Browse / Gifting / {subcategory} / {collection} / {budget}",
                ["Browse Products", "Gifting", subcategory, collection, budget],
            )
            assert_not_empty_products(
                f"Browse / Gifting / {subcategory} / {collection} / {budget}",
                result,
            )

for subcategory, collections in gifting_paths.items():
    for collection in collections:
        for budget in budgets:
            result = run_state_sequence(
                f"Recommend / Gifting / {subcategory} / {collection} / {budget}",
                ["Recommend Products", "Gifting", subcategory, collection, budget],
            )
            assert_not_empty_products(
                f"Recommend / Gifting / {subcategory} / {collection} / {budget}",
                result,
            )

print("\n=== Recommendation use-case + budget guided tests ===")
use_cases = ["Daily Worship", "Home Decor", "Festival Wedding"]
for use_case in use_cases:
    for budget in budgets:
        result = run_state_sequence(
            f"Recommend / {use_case} / {budget}",
            ["Recommend Products", use_case, budget],
        )
        assert_not_empty_products(f"Recommend / {use_case} / {budget}", result)

print("\n=== Free-text product/FAQ tests ===")
queries = [
    "ganesha idol",
    "krishna idol",
    "lakshmi murti",
    "brass diya",
    "pooja bell",
    "brass urli",
    "home decor",
    "wedding gift",
    "housewarming gift",
    "under 1000 ganesha",
    "above 25000 idol",
    "shipping policy",
    "delivery time",
    "return policy",
]
for query in queries:
    result = RecommendationEngineV2.recommend(query, limit=5)
    assert_json_safe(f"Free text / {query}", result)
    print(f"PASS: Free text / {query}: {result.get('log', {}).get('result_type')}")

print("\n=== Invalid order/invoice tests ===")
for action, message in [("TRACK_ORDER", "INVALID-ORDER-ID"), ("GET_INVOICE", "INVALID-ORDER-ID")]:
    result = ActionEngineV2.execute(action, message=message)
    assert_json_safe(f"{action} invalid", result)
    print(f"PASS: {action} invalid JSON-safe")

print("\nALL TESTS COMPLETED")
