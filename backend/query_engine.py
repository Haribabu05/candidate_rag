import json
import re


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

from rapidfuzz import fuzz

def find_candidate(query):

    q = query.lower()

    best_candidate = None
    best_score = 0

    for candidate in candidate_data.values():

        name = candidate["candidate"].lower()

        score = fuzz.partial_ratio(
            name,
            q
        )

        if score > best_score:

            best_score = score
            best_candidate = candidate

    if best_score >= 80:

        return best_candidate

    return None


# ==========================================
# FIND BY PARTY
# ==========================================

def find_by_party(query):

    q = query.lower()

    results = []

    for candidate in candidate_data.values():

        party = candidate[
            "party"
        ].lower()

        if party in q:

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

def compare_candidates(query):

    q = query.lower()

    matched = []

    for candidate in candidate_data.values():

        name = candidate[
            "candidate"
        ].lower()

        if name in q:

            matched.append(
                candidate
            )

    if len(matched) < 2:

        return None

    return {

        "candidate1":
            matched[0],

        "candidate2":
            matched[1]
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