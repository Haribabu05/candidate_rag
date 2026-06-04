import re

STRUCTURED_KEYWORDS = [

    "candidate",
    "candidates",

    "party",

    "constituency",
    "region",

    "education",
    "graduate",
    "graduates",

    "bca",
    "b.com",
    "b.e",
    "be",
    "mba",
    "mca",
    "m.tech",
    "mtech",
    "phd",
    "iti",
    "hsc",
    "sslc",

    "asset",
    "assets",

    "liability",
    "liabilities",

    "income tax",

    "compare"
]


SEMANTIC_KEYWORDS = [

    "summarize",
    "summary",

    "affidavit",

    "criminal",

    "background",

    "explain",

    "details",

    "declaration"
]


def detect_intent(query):

    q = query.lower()

    # =========================
    # COMPARE
    # =========================

    if "compare" in q:

        return "compare"

    # =========================
    # EDUCATION
    # =========================

    education_terms = [

        "bca",
        "mba",
        "mca",
        "b.com",
        "be",
        "b.e",
        "m.tech",
        "iti",
        "phd",
        "hsc",
        "sslc"
    ]

    for term in education_terms:

        if term in q:

            return "education"

    # =========================
    # PARTY
    # =========================

    if "party" in q:

        return "party"

    # =========================
    # CONSTITUENCY
    # =========================

    if (
        "constituency" in q
        or
        "region" in q
        or
        "kolathur" in q
        or
        "ambattur" in q
    ):

        return "constituency"

    # =========================
    # SEMANTIC
    # =========================

    for word in SEMANTIC_KEYWORDS:

        if word in q:

            return "semantic"

    # =========================
    # CANDIDATE
    # =========================

    if (
        q.startswith("who is")
        or
        q.startswith("tell me about")
    ):

        return "candidate"

    # =========================
    # WEB
    # =========================

    return "web"