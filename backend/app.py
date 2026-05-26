# ==========================================
# FILE: backend/app.py
# ==========================================

import json
import streamlit as st
import chromadb

from sentence_transformers import (
    SentenceTransformer
)

from groq import Groq

# ==========================================
# PAGE CONFIG
# ==========================================

st.set_page_config(
    page_title="Election Intelligence System",
    layout="wide"
)

st.title(
    "🗳️ Election Intelligence System"
)

st.markdown(
    """
Hybrid Election Intelligence Platform using:

- Structured Candidate Database
- ChromaDB Vector Search
- Groq LLM Summarization
"""
)

# ==========================================
# LOAD STRUCTURED DATA
# ==========================================

with open(
    "candidate_master_data.json",
    "r",
    encoding="utf-8"
) as f:

    candidate_master_data = json.load(f)

candidate_names = list(
    candidate_master_data.keys()
)

# ==========================================
# LOAD EMBEDDING MODEL
# ==========================================

@st.cache_resource
def load_embedding_model():

    return SentenceTransformer(
        "sentence-transformers/all-MiniLM-L6-v2"
    )

model = load_embedding_model()

# ==========================================
# LOAD CHROMADB
# ==========================================

@st.cache_resource
def load_collection():

    client = chromadb.PersistentClient(
        path="chroma_db"
    )

    return client.get_collection(
        "candidate_affidavits"
    )

collection = load_collection()

# ==========================================
# GROQ
# ==========================================

GROQ_API_KEY = "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"

groq_client = Groq(
    api_key="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"
)

# ==========================================
# NORMALIZE
# ==========================================

def normalize(text):

    return (
        text.lower()
        .replace(" ", "")
    )

# ==========================================
# FIND CANDIDATE
# ==========================================

def find_candidate(query):

    normalized_query = normalize(query)

    for candidate in candidate_names:

        if (
            normalize(candidate)
            in normalized_query
        ):

            return candidate

    return None

# ==========================================
# GET PAN
# ==========================================

def get_pan(candidate):

    return candidate_master_data[
        candidate
    ].get("pan_ids", [])

# ==========================================
# GET INCOME
# ==========================================

def get_income(candidate):

    values = candidate_master_data[
        candidate
    ].get("income_values", [])

    cleaned = []

    for value in values:

        digits = value.replace(",", "")

        if digits.isdigit():

            if len(digits) >= 5:

                cleaned.append(value)

    cleaned = list(set(cleaned))

    cleaned.sort()

    return cleaned[:20]

# ==========================================
# GET EMAILS
# ==========================================

def get_emails(candidate):

    return candidate_master_data[
        candidate
    ].get("emails", [])

# ==========================================
# GET PHONES
# ==========================================

def get_phones(candidate):

    return candidate_master_data[
        candidate
    ].get("phones", [])

# ==========================================
# GET PARTY
# ==========================================

def get_party(candidate):

    return candidate_master_data[
        candidate
    ].get("party", "Unknown")

# ==========================================
# GET CONSTITUENCY
# ==========================================

def get_constituency(candidate):

    return candidate_master_data[
        candidate
    ].get("constituency", "Unknown")

# ==========================================
# PROFILE GENERATOR
# ==========================================

def get_candidate_profile(candidate):

    data = candidate_master_data[
        candidate
    ]

    profile = f"""
Candidate: {candidate}

Party: {data['party']}

Constituency: {data['constituency']}

PAN IDs:
{", ".join(data['pan_ids'][:5])}

Phone Numbers:
{", ".join(data['phones'][:5])}

Emails:
{", ".join(data['emails'][:5])}

Known Income Values:
{", ".join(get_income(candidate)[:10])}
"""

    return profile

# ==========================================
# COMPARE CANDIDATES
# ==========================================

def compare_candidates(c1, c2):

    data1 = candidate_master_data[c1]
    data2 = candidate_master_data[c2]

    comparison = {

        "Field": [

            "Party",
            "Constituency",
            "PAN IDs",
            "Phones",
            "Emails",
            "Income Values"
        ],

        c1: [

            data1["party"],
            data1["constituency"],
            ", ".join(data1["pan_ids"][:3]),
            ", ".join(data1["phones"][:3]),
            ", ".join(data1["emails"][:3]),
            ", ".join(
                get_income(c1)[:5]
            )
        ],

        c2: [

            data2["party"],
            data2["constituency"],
            ", ".join(data2["pan_ids"][:3]),
            ", ".join(data2["phones"][:3]),
            ", ".join(data2["emails"][:3]),
            ", ".join(
                get_income(c2)[:5]
            )
        ]
    }

    return comparison

# ==========================================
# COUNT PARTY CANDIDATES
# ==========================================

def count_party_candidates(party):

    count = 0

    for candidate in candidate_master_data:

        if (
            candidate_master_data[
                candidate
            ]["party"].lower()
            ==
            party.lower()
        ):

            count += 1

    return count

# ==========================================
# TOP RICHEST
# ==========================================

def top_richest():

    candidates = []

    for candidate in candidate_master_data:

        incomes = get_income(candidate)

        numeric = []

        for income in incomes:

            try:

                numeric.append(

                    int(
                        income.replace(",", "")
                    )
                )

            except:
                pass

        if numeric:

            candidates.append(

                (
                    candidate,
                    max(numeric)
                )
            )

    candidates.sort(
        key=lambda x: x[1],
        reverse=True
    )

    return candidates[:10]

# ==========================================
# LIST CANDIDATES
# ==========================================

def list_candidates_by_constituency(
    constituency
):

    results = []

    for candidate, data in (
        candidate_master_data.items()
    ):

        if (
            data["constituency"]
            .lower()
            ==
            constituency.lower()
        ):

            results.append(

                {
                    "Candidate": candidate,
                    "Party": data["party"]
                }
            )

    return results

# ==========================================
# HIGHEST INCOME CANDIDATE
# ==========================================

def highest_income_candidate(
    constituency
):

    best_candidate = None

    best_income = 0

    for candidate, data in (
        candidate_master_data.items()
    ):

        if (
            data["constituency"]
            .lower()
            !=
            constituency.lower()
        ):

            continue

        incomes = get_income(candidate)

        numeric = []

        for income in incomes:

            try:

                numeric.append(

                    int(
                        income.replace(",", "")
                    )
                )

            except:
                pass

        if numeric:

            max_income = max(numeric)

            if max_income > best_income:

                best_income = max_income

                best_candidate = candidate

    return (
        best_candidate,
        best_income
    )

# ==========================================
# VECTOR SEARCH
# ==========================================

def rag_search(query):

    query_embedding = model.encode(
        query
    ).tolist()

    results = collection.query(

        query_embeddings=[
            query_embedding
        ],

        n_results=10
    )

    docs = results["documents"][0]

    metas = results["metadatas"][0]

    return list(zip(docs, metas))

# ==========================================
# GENERATE ANSWER
# ==========================================

def generate_answer(query, context):

    prompt = f"""
You are an election affidavit analyst.

Answer ONLY using the context below.

Context:
{context}

Question:
{query}

Give a professional answer.
"""

    response = (
        groq_client.chat.completions.create(

            model="llama-3.3-70b-versatile",

            messages=[

                {
                    "role": "system",
                    "content":
                    "You explain election affidavits professionally."
                },

                {
                    "role": "user",
                    "content": prompt
                }
            ],

            temperature=0.3
        )
    )

    return (
        response
        .choices[0]
        .message.content
    )

# ==========================================
# USER INPUT
# ==========================================

query = st.text_input(
    "Ask a question"
)

# ==========================================
# MAIN ENGINE
# ==========================================

if query:

    query_lower = query.lower()

    matched_candidate = find_candidate(
        query
    )

    # ======================================
    # WHO IS
    # ======================================

    if (
        "who is" in query_lower
        or
        "tell me about" in query_lower
    ):

        if matched_candidate:

            st.subheader(
                "Candidate Profile"
            )

            st.success(

                get_candidate_profile(
                    matched_candidate
                )
            )

    # ======================================
    # EXPLAIN
    # ======================================

    elif (

        "explain" in query_lower
        or
        "describe" in query_lower
        or
        "summarize" in query_lower

    ):

        if matched_candidate:

            retrieved = rag_search(
                matched_candidate
            )

            context = "\n\n".join(

                [

                    doc

                    for doc, meta
                    in retrieved

                    if (
                        meta["candidate"]
                        ==
                        matched_candidate
                    )
                ]
            )

            try:

                answer = generate_answer(
                    query,
                    context
                )

                st.subheader(
                    "Candidate Explanation"
                )

                st.success(answer)

            except Exception as e:

                st.error(
                    f"Generation failed: {e}"
                )

    # ======================================
    # PAN
    # ======================================

    elif "pan" in query_lower:

        if matched_candidate:

            st.subheader(
                "PAN Details"
            )

            st.success(

                ", ".join(
                    get_pan(
                        matched_candidate
                    )
                )
            )

    # ======================================
    # INCOME
    # ======================================

    elif "income" in query_lower:

        if matched_candidate:

            st.subheader(
                "Income Details"
            )

            st.success(

                ", ".join(
                    get_income(
                        matched_candidate
                    )
                )
            )

    # ======================================
    # EMAIL
    # ======================================

    elif "email" in query_lower:

        if matched_candidate:

            st.subheader(
                "Email Details"
            )

            st.success(

                ", ".join(
                    get_emails(
                        matched_candidate
                    )
                )
            )

    # ======================================
    # PHONE
    # ======================================

    elif (
        "phone" in query_lower
        or
        "mobile" in query_lower
    ):

        if matched_candidate:

            st.subheader(
                "Phone Details"
            )

            st.success(

                ", ".join(
                    get_phones(
                        matched_candidate
                    )
                )
            )

    # ======================================
    # PARTY
    # ======================================

    elif "party" in query_lower:

        if matched_candidate:

            st.subheader(
                "Party Details"
            )

            st.success(

                f"""
{matched_candidate}
belongs to
{get_party(matched_candidate)}
party.
"""
            )

    # ======================================
    # COMPARE
    # ======================================

    elif "compare" in query_lower:

        found = []

        for candidate in candidate_names:

            if (
                normalize(candidate)
                in normalize(query)
            ):

                found.append(candidate)

        if len(found) >= 2:

            st.subheader(
                "Candidate Comparison"
            )

            st.table(

                compare_candidates(
                    found[0],
                    found[1]
                )
            )

    # ======================================
    # LIST ALL CANDIDATES
    # ======================================

    elif (

        "list" in query_lower
        and
        "candidate" in query_lower

    ):

        if "kolathur" in query_lower:

            results = (
                list_candidates_by_constituency(
                    "KOLATHUR"
                )
            )

            st.subheader(
                "Kolathur Candidates"
            )

            st.table(results)

    # ======================================
    # HIGHEST INCOME
    # ======================================

    elif (

        "highest income" in query_lower
        or
        "richest candidate" in query_lower

    ):

        if "kolathur" in query_lower:

            candidate, income = (
                highest_income_candidate(
                    "KOLATHUR"
                )
            )

            st.subheader(
                "Highest Income Candidate"
            )

            st.success(

                f"""
Candidate:
{candidate}

Highest Known Income:
₹{income:,}
"""
            )

    # ======================================
    # PARTY ANALYTICS
    # ======================================

    elif (
        "how many" in query_lower
        and
        "candidate" in query_lower
    ):

        parties = [

            "DMK",
            "AIADMK",
            "TVK",
            "BJP",
            "INC"
        ]

        for party in parties:

            if party.lower() in query_lower:

                count = (
                    count_party_candidates(
                        party
                    )
                )

                st.subheader(
                    "Party Analytics"
                )

                st.success(

                    f"""
{party}
has
{count}
candidates.
"""
                )

    # ======================================
    # TOP RICHEST
    # ======================================

    elif "top richest" in query_lower:

        richest = top_richest()

        st.subheader(
            "Top Richest Candidates"
        )

        st.table({

            "Candidate": [

                x[0]
                for x in richest
            ],

            "Highest Income": [

                x[1]
                for x in richest
            ]
        })

    # ======================================
# DIRECT CANDIDATE QUERY
# ======================================

    elif matched_candidate:

        st.subheader(
            "Candidate Profile"
        )

        st.success(

            get_candidate_profile(
                matched_candidate
            )
        )

    # ======================================
    # GENERAL RAG
    # ======================================

    else:

        retrieved = rag_search(query)

        context = "\n\n".join(

            [

                f"""
Candidate:
{meta['candidate']}

Party:
{meta['party']}

Page:
{meta['page']}

Content:
{doc}
"""

                for doc, meta
                in retrieved
            ]
        )

        try:

            answer = generate_answer(
                query,
                context
            )

            st.subheader(
                "AI Generated Answer"
            )

            st.success(answer)

        except Exception as e:

            st.error(
                f"Generation failed: {e}"
            )

        # ==================================
        # EVIDENCE
        # ==================================

        st.subheader(
            "Retrieved Evidence"
        )

        for doc, meta in retrieved:

            st.markdown("---")

            st.markdown(
                f"### {meta['candidate']}"
            )

            st.write(
                f"Party: {meta['party']}"
            )

            st.write(
                f"Page: {meta['page']}"
            )

            st.text(doc[:1200])