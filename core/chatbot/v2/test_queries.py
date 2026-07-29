from core.chatbot.v2.recommendation_engine_v2 import (
    RecommendationEngineV2
)

queries = [

    "radha krishna idol",
    "krishna idol under 10000",
    "vishnu lakshmi",

    "gomatha wax casting",
    "lord balaji stone idols",

    "urli under 10000",
    "elephant urli under 10000",

    "pooja stool",
    "cooking serve pot",

    "horse decor",
    "lion decor",

    "divine symbols collection",
    "sacred heritage collection",
]

for query in queries:

    print()
    print("=" * 60)
    print(query)

    result = (
        RecommendationEngineV2.recommend(
            query
        )
    )

    print(result)