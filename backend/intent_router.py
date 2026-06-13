import re

PARTIES = [
    "dmk",
    "aiadmk",
    "bjp",
    "tvk",
    "ntk",
    "indep",
    "independent"
]

EDUCATION_PATTERNS = [
    r"\bbca\b",
    r"\bmba\b",
    r"\bmca\b",
    r"\bb\.?com\b",
    r"\bbcom\b",
    r"\bb\.?e\b",
    r"\bbe\b",
    r"\bm\.?tech\b",
    r"\bmtech\b",
    r"\bph\.?d\b",
    r"\bphd\b",
    r"\bb\.?ed\b",
    r"\bbed\b",
    r"\bm\.?phil\b",
    r"\bmphil\b",
    r"\biti\b",
    r"\bhsc\b",
    r"\bsslc\b"
]

SEMANTIC_KEYWORDS = [
    "summarize",
    "summary",
    "affidavit",
    "criminal",
    "declaration",
    "disclosure"
]

COMPARE_WORDS = [
    "compare",
    "vs",
    "versus",
    "better",
    "difference",
    "stronger",
    "richer"
]


def detect_intent(query):

    q = query.lower().strip()

    # compare

    for word in COMPARE_WORDS:

        if re.search(
            rf"\b{re.escape(word)}\b",
            q
        ):
            return "compare"

    # party

    for party in PARTIES:

        if re.search(
            rf"\b{re.escape(party)}\b",
            q
        ):
            return "party"

    # education

    for pattern in EDUCATION_PATTERNS:

        if re.search(pattern, q):

            return "education"

    # constituency

    constituency_words = [

        "constituency",
        "region",

        "candidate in",
        "candidates in",

        "candidate from",
        "candidates from",

        "female candidates",
        "male candidates",

        "richest candidate",
        "richest candidates",

        "top assets"
    ]

    for word in constituency_words:

        if word in q:

            return "constituency"

    # semantic

    for word in SEMANTIC_KEYWORDS:

        if word in q:

            return "semantic"

    return "unknown"