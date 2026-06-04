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

    r"\bb\.?e\b",

    r"\bm\.?tech\b",
    r"\bmtech\b",

    r"\bph\.?d\b",
    r"\bphd\b",

    r"\bb\.?ed\b",
    r"\bm\.?phil\b",

    r"\biti\b",
    r"\bhsc\b",
    r"\bsslc\b"
]

SEMANTIC_KEYWORDS = [

    "summarize",
    "summary",

    "affidavit",

    "criminal",

    "background",

    "declaration",

    "disclosure",

    "explain affidavit"
]

COMPARE_WORDS = [

    "compare",
    "vs",
    "versus",

    "better",
    "best",

    "difference",

    "stronger",

    "richer"
]

CANDIDATE_QUERY_WORDS = [

    "who is",

    "tell me about",

    "describe",

    "details of",

    "profile of",

    "education of",

    "email of",

    "phone of",

    "mobile of",

    "assets of",

    "liabilities of",

    "income tax of"
]


def detect_intent(query):

    q = query.lower().strip()

    # =========================
    # COMPARE
    # =========================

    for word in COMPARE_WORDS:

        if re.search(
            rf"\b{re.escape(word)}\b",
            q
        ):
            return "compare"

    # =========================
    # PARTY
    # =========================

    for party in PARTIES:

        if re.search(
            rf"\b{re.escape(party)}\b",
            q
        ):
            return "party"

    # =========================
    # EDUCATION
    # =========================

    for pattern in EDUCATION_PATTERNS:

        if re.search(pattern, q):

            return "education"

    # =========================
    # CONSTITUENCY
    # =========================

    constituency_words = [

        "constituency",

        "region",

        "kolathur",

        "ambattur",

        "candidate in",

        "candidates in",

        "candidate from",

        "candidates from",

        "female candidates",

        "male candidates",

        "richest candidate"
    ]

    for word in constituency_words:

        if word in q:

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

    for phrase in CANDIDATE_QUERY_WORDS:

        if phrase in q:

            return "candidate"

    # Single candidate lookup
    # Examples:
    # MKStalin
    # SSharan
    # O Poornima

    words = q.split()

    if len(words) <= 3:

        return "candidate"

    # =========================
    # WEB FALLBACK
    # =========================

    return "web"