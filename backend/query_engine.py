import json
import re
from rapidfuzz import process

DEGREE_KEYWORDS = {

    "bca": [
        "bca"
    ],

    "mba": [
        "mba"
    ],

    "mca": [
        "mca"
    ],

    "bcom": [
        "b.com",
        "bcom"
    ],

    "be": [
        "be",
        "b.e"
    ],

    "mtech": [
        "m.tech",
        "mtech"
    ],

    "phd": [
        "phd",
        "ph.d"
    ],

    "iti": [
        "iti"
    ],

    "hsc": [
        "hsc"
    ],

    "sslc": [
        "sslc"
    ]
}

with open(
    r"C:\Users\bockb\YCDI\pdf_app\candidate_master_data.json",
    "r",
    encoding="utf-8"
) as f:

    candidate_data = json.load(f)


# ==========================================
# FIND CANDIDATE
# ==========================================

from rapidfuzz import process
import re
import json


with open(
    "candidate_master_data.json",
    "r",
    encoding="utf-8"
) as f:

    candidate_data = json.load(f)


# ====================================
# CLEAN QUERY
# ====================================

def clean_query(query):

    q = query.lower()

    remove_phrases = [

        "who is",
        "tell me about",
        "describe",
        "details of",
        "profile of",

        "assets of",
        "asset of",

        "liabilities of",

        "education of",

        "email of",
        "phone of",
        "mobile of",

        "candidate"
    ]

    for phrase in remove_phrases:

        q = q.replace(
            phrase,
            ""
        )

    q = re.sub(
        r"[^a-z0-9 ]",
        " ",
        q
    )

    q = " ".join(
        q.split()
    )

    return q
 

# ====================================
# FIND CANDIDATE
# ====================================

from rapidfuzz import process
import re

def normalize(text):

    return re.sub(
        r"[^a-z0-9]",
        "",
        text.lower()
    )


def find_candidate(query):

    cleaned_query = normalize(
        clean_query(query)
    )

    candidate_lookup = {}

    for candidate in candidate_data.values():

        original_name = candidate["candidate"]

        normalized_name = normalize(
            original_name
        )

        candidate_lookup[
            normalized_name
        ] = candidate

    match = process.extractOne(

        cleaned_query,

        candidate_lookup.keys(),

        score_cutoff=60
    )

    print("QUERY =", cleaned_query)
    print("MATCH =", match)

    if not match:

        return None

    return candidate_lookup[
        match[0]
    ]

# ==========================================
# FIND BY PARTY
# ==========================================

def find_by_party(query):

    q = query.lower()

    results = []

    for candidate in candidate_data.values():

        if (

            candidate["party"]
            .lower()

            in q

        ):

            results.append(
                candidate
            )

    return results


# ==========================================
# FIND BY EDUCATION
# ==========================================

def find_by_education(query):

    q = query.lower()

    target_degree = None

    for degree, keywords in DEGREE_KEYWORDS.items():

        for keyword in keywords:

            if keyword in q:

                target_degree = degree

                break

    if not target_degree:

        return []

    results = []

    for candidate in candidate_data.values():

        degree = candidate[
            "education"
        ][
            "degree"
        ].lower()

        if target_degree in degree:

            results.append(
                candidate
            )

    return results


# ==========================================
# FIND BY CONSTITUENCY
# ==========================================

def find_by_constituency(query):

    q = query.lower()

    results = []

    for candidate in candidate_data.values():

        constituency = candidate[
            "constituency"
        ].lower()

        if constituency in q:

            results.append(
                candidate
            )

    return results


# ==========================================
# COMPARE CANDIDATES
# ==========================================

import re

def compare_candidates(query):

    print("NEW COMPARE FUNCTION LOADED")

    parts = re.split(
        r"\b(?:compare|vs|versus|and)\b",
        query.lower()
    )

    parts = [
        p.strip()
        for p in parts
        if p.strip()
    ]

    print("PARTS =", parts)

    if len(parts) != 2:

        return None

    candidate1 = find_candidate(parts[0])
    candidate2 = find_candidate(parts[1])

    print("CANDIDATE 1 =", candidate1)
    print("CANDIDATE 2 =", candidate2)

    if not candidate1 or not candidate2:

        return None

    return {
        "candidate1": candidate1,
        "candidate2": candidate2
    }

# ==========================================
# TOP ASSETS
# ==========================================

def richest_candidates(limit=10):

    candidates = sorted(

        candidate_data.values(),

        key=lambda x:

            x["assets"][
                "total"
            ],

        reverse=True
    )

    return candidates[:limit]


# ==========================================
# MALE / FEMALE
# ==========================================

def find_by_gender(gender):

    results = []

    for candidate in candidate_data.values():

        if (

            candidate.get(
                "gender",
                ""
            ).lower()

            ==

            gender.lower()

        ):

            results.append(
                candidate
            )

    return results