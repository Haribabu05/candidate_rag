# ==========================================
# FILE: backend/app.py
# ==========================================

import re
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
# EMBEDDING MODEL
# ==========================================

@st.cache_resource
def load_embedding_model():

    return SentenceTransformer(
        "sentence-transformers/all-MiniLM-L6-v2"
    )

model = load_embedding_model()

# ==========================================
# CHROMADB
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

groq_client = Groq(
    api_key="YOUR_GROQ_API_KEY"
)

# ==========================================
# HELPER FUNCTIONS
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

        if normalize(candidate) in normalized_query:

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
# COMPARISON ENGINE
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
# ANALYTICS
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
# VECTOR RAG
# ==========================================

def rag_search(query):

    query_embedding = model.encode(
        query
    ).tolist()

    results = collection.query(

        query_embeddings=[
            query_embedding
        ],

        n_results=5
    )

    docs = results["documents"][0]

    metas = results["metadatas"][0]

    return list(zip(docs, metas))

# ==========================================
# RAG GENERATION
# ==========================================

def generate_answer(query, context):

    prompt = f"""
You are an election affidavit analyst.

Answer ONLY from the provided context.

Context:
{context}

Question:
{query}

Answer clearly.
"""

    response = (
        groq_client.chat.completions.create(

            model="llama-3.3-70b-versatile",

            messages=[

                {
                    "role": "system",
                    "content":
                    "You answer based only on affidavit evidence."
                },

                {
                    "role": "user",
                    "content": prompt
                }
            ],

            temperature=0.2
        )
    )

    return (
        response
        .choices[0]
        .message.content
    )

# ==========================================
# USER QUERY
# ==========================================

query = st.text_input(
    "Ask a question"
)

# ==========================================
# MAIN QUERY ENGINE
# ==========================================

if query:

    query_lower = query.lower()

    matched_candidate = find_candidate(query)

    # ======================================
    # PAN QUERY
    # ======================================

    if "pan" in query_lower:

        if matched_candidate:

            pans = get_pan(
                matched_candidate
            )

            st.subheader("PAN Details")

            if pans:

                st.success(

                    f"""
Candidate:
{matched_candidate}

PAN IDs:
{", ".join(pans)}
"""
                )

            else:

                st.warning(
                    "PAN not found."
                )

    # ======================================
    # INCOME QUERY
    # ======================================

    elif "income" in query_lower:

        if matched_candidate:

            incomes = get_income(
                matched_candidate
            )

            st.subheader(
                "Income Details"
            )

            if incomes:

                st.success(

                    f"""
Candidate:
{matched_candidate}

Income Values:
{", ".join(incomes)}
"""
                )

            else:

                st.warning(
                    "Income not found."
                )

    # ======================================
    # EMAIL QUERY
    # ======================================

    elif "email" in query_lower:

        if matched_candidate:

            emails = get_emails(
                matched_candidate
            )

            st.subheader(
                "Email Details"
            )

            st.success(
                ", ".join(emails)
            )

    # ======================================
    # PHONE QUERY
    # ======================================

    elif "phone" in query_lower:

        if matched_candidate:

            phones = get_phones(
                matched_candidate
            )

            st.subheader(
                "Phone Details"
            )

            st.success(
                ", ".join(phones)
            )

    # ======================================
    # PARTY QUERY
    # ======================================

    elif "party" in query_lower:

        if matched_candidate:

            party = get_party(
                matched_candidate
            )

            st.subheader(
                "Party Details"
            )

            st.success(

                f"""
{matched_candidate}
belongs to
{party}
party.
"""
            )

    # ======================================
    # COMPARISON ENGINE
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

            c1 = found[0]
            c2 = found[1]

            comparison = compare_candidates(
                c1,
                c2
            )

            st.subheader(
                "Candidate Comparison"
            )

            st.table(comparison)

        else:

            st.warning(
                "Need two candidates."
            )

    # ======================================
    # PARTY COUNT
    # ======================================

    elif (
        "how many" in query_lower
        and
        "candidate" in query_lower
    ):

        for party in [

            "DMK",
            "AIADMK",
            "TVK",
            "BJP",
            "INC"
        ]:

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

    elif "richest" in query_lower:

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
    # VECTOR RAG
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
                f"Generation failed:\n{e}"
            )

        # ==================================
        # SHOW EVIDENCE
        # ==================================

        st.subheader(
            "Retrieved Evidence"
        )

        for doc, meta in retrieved:

            st.markdown("---")

            st.markdown(

                f"""
### {meta['candidate']}
"""
            )

            st.write(
                f"Party: {meta['party']}"
            )

            st.write(
                f"Page: {meta['page']}"
            )

            st.text(doc[:1200])