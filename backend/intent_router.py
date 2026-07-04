import json
import re

import re
import json

import os
_dir = os.path.dirname(os.path.abspath(__file__))

with open(
    os.path.join(_dir, "candidate_master_data.json"),
    "r",
    encoding="utf-8"
) as f:
    candidate_data = json.load(f)

CONSTITUENCIES = set()

for candidate in candidate_data.values():

    CONSTITUENCIES.add(
        candidate["constituency"].lower()
    )

print("TOTAL CONSTITUENCIES =", len(CONSTITUENCIES))





# CONSTITUENCIES INDEX

CONSTITUENCIES = set()

for candidate in candidate_data.values():

    CONSTITUENCIES.add(
        candidate["constituency"].lower()
    )

print("TOTAL CONSTITUENCIES =", len(CONSTITUENCIES))
print(CONSTITUENCIES)


# EDUCATION INDEX

EDUCATIONS = set()

for candidate in candidate_data.values():

    EDUCATIONS.add(
        candidate["education"]["degree"].lower()
    )

print("TOTAL EDUCATIONS =", len(EDUCATIONS))
print(EDUCATIONS)


PARTIES = [
    "dmk",
    "aiadmk",
    "bjp",
    "tvk",
    "ntk",
    "indep",
    "independent"
]



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

    "richest candidate"
]
EDUCATION_PATTERNS = [

    # School
    r"\bsslc\b",
    r"\bhsc\b",

    # ITI
    r"\biti\b",

    # Diploma
    r"\bdiploma\b",

    # Undergraduate
    r"\bbca\b",
    r"\bb\.?ca\b",

    r"\bbsc\b",
    r"\bb\.?sc\b",

    r"\bbcom\b",
    r"\bb\.?com\b",

    r"\bba\b",
    r"\bb\.?a\b",

    r"\bbe\b",
    r"\bb\.?e\b",

    r"\bbtech\b",
    r"\bb\.?tech\b",

    r"\bbed\b",
    r"\bb\.?ed\b",

    # Postgraduate
    r"\bmca\b",
    r"\bm\.?ca\b",

    r"\bmba\b",
    r"\bm\.?ba\b",

    r"\bma\b",
    r"\bm\.?a\b",

    r"\bmcom\b",
    r"\bm\.?com\b",

    r"\bmtech\b",
    r"\bm\.?tech\b",

    r"\bmphil\b",
    r"\bm\.?phil\b",

    # Doctorate
    r"\bphd\b",
    r"\bph\.?d\b",
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

CONSTITUENCIES = [
    "kolathur",
    "ambattur"
]



def detect_intent(query):

    q = query.lower().strip()

    # =====================
    # COMPARE
    # =====================

    for word in COMPARE_WORDS:

        if re.search(
            rf"\b{re.escape(word)}\b",
            q
        ):
            return "compare"

    # =====================
    # PARTY
    # =====================

    for party in PARTIES:

        if re.search(
            rf"\b{re.escape(party)}\b",
            q
        ):
            return "party"

    # =====================
    # EDUCATION
    # =====================

    for pattern in EDUCATION_PATTERNS:

        if re.search(pattern, q):

            return "education"

    # =====================
    # GENDER
    # =====================

    if "male candidate" in q or "male candidates" in q:
        return "male"

    if "female candidate" in q or "female candidates" in q:
        return "female"

    # =====================
    # RICHEST
    # =====================

    richest_words = [

        "richest candidate",
        "richest candidates",

        "top assets",
        "highest assets",

        "wealthiest candidate",
        "wealthiest candidates"
    ] 

    for word in richest_words:

        if word in q:

            return "richest"

    # =====================
    # CONSTITUENCY
    # =====================

    for constituency in CONSTITUENCIES:

        if constituency in q:

            print("FOUND CONSTITUENCY =", constituency)

            return "constituency"

    # =====================
    # SEMANTIC
    # =====================

    for word in SEMANTIC_KEYWORDS:

        if word in q:

            return "semantic"

    # =====================
    # CANDIDATE LOOKUP
    # =====================

    candidate_words = [

        "who is",
        "tell me about",
        "describe",
        "explain",
        "details of",
        "profile of",

        "education of",
        "assets of",
        "liabilities of",

        "phone of",
        "email of",
        "mobile of"
    ]

    for word in candidate_words:

        if word in q:

            return "unknown"

    # =====================
    # DEFAULT
    # =====================

    return "unknown"