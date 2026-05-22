import re
import json
import streamlit as st
import chromadb

from sentence_transformers import SentenceTransformer
from groq import Groq

# ==========================================
# PAGE CONFIG
# ==========================================

st.set_page_config(
    page_title="Election Affidavit RAG",
    layout="wide"
)

st.title(
    "🗳️ Election Affidavit Intelligence System"
)

st.markdown(
    """
RAG system for Tamil Nadu election affidavits using:

- SentenceTransformers
- ChromaDB
- Groq LLM Generation
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

    collection = client.get_collection(
        "candidate_affidavits"
    )

    return collection

collection = load_collection()

# ==========================================
# GROQ CLIENT
# ==========================================

groq_client = Groq(
    api_key="YOUR_GROQ_API_KEY"
)

# ==========================================
# USER QUERY
# ==========================================

query = st.text_input(
    "Ask a question"
)

# ==========================================
# QUERY EXECUTION
# ==========================================

if query:

    normalized_query = (
        query.lower()
        .replace(" ", "")
    )

    matched_candidate = None

    # ======================================
    # EXACT CANDIDATE MATCH
    # ======================================

    for candidate in candidate_names:

        normalized_candidate = (
            candidate.lower()
            .replace(" ", "")
        )

        if (
            normalized_candidate
            in normalized_query
        ):

            matched_candidate = candidate
            break

    # ======================================
    # EMBEDDING SEARCH
    # ======================================

    query_embedding = model.encode(
        query
    ).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=10
    )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]

    retrieved_docs = list(
        zip(documents, metadatas)
    )

    # ======================================
    # FILTER BY CANDIDATE
    # ======================================

    if matched_candidate:

        filtered_docs = []

        for doc, meta in retrieved_docs:

            if (
                meta["candidate"]
                == matched_candidate
            ):

                filtered_docs.append(
                    (doc, meta)
                )

    else:

        filtered_docs = retrieved_docs

    # ======================================
    # BUILD CONTEXT
    # ======================================

    context = "\n\n".join(

        [

            f"""
Candidate:
{meta.get('candidate', 'Unknown')}

Party:
{meta.get('party', 'Unknown')}

Constituency:
{meta.get('constituency', 'Unknown')}

Page:
{meta.get('page', 'Unknown')}

Content:
{doc}
"""

            for doc, meta in filtered_docs

        ]
    )

    # ======================================
    # SPECIAL FIELD EXTRACTION
    # ======================================

    lower_query = query.lower()

    # ======================================
    # PAN EXTRACTION
    # ======================================

    if "pan" in lower_query:

        pan_pattern = (
            r"[A-Z]{5}[0-9]{4}[A-Z]"
        )

        pans = re.findall(
            pan_pattern,
            context
        )

        if pans:

            st.subheader("Answer")

            st.success(
                f"""
Candidate:
{matched_candidate}

PAN ID:
{pans[0]}
"""
            )

        else:

            st.warning(
                "PAN ID not found."
            )

    # ======================================
    # INCOME EXTRACTION
    # ======================================

    elif "income" in lower_query:

        income_pattern = (
            r"₹?\s?[\d,]+"
        )

        incomes = re.findall(
            income_pattern,
            context
        )

        st.subheader("Answer")

        if incomes:

            unique_incomes = list(
                set(incomes)
            )

            st.success(
                f"""
Candidate:
{matched_candidate}

Possible Income Values:
{", ".join(unique_incomes[:10])}
"""
            )

        else:

            st.warning(
                "Income details not found."
            )

    # ======================================
    # PARTY QUERY
    # ======================================

    elif "party" in lower_query:

        if (
            matched_candidate
            and matched_candidate
            in candidate_master_data
        ):

            party = (
                candidate_master_data[
                    matched_candidate
                ]["party"]
            )

            st.subheader("Answer")

            st.success(
                f"""
{matched_candidate}
belongs to
{party}
party.
"""
            )

        else:

            st.warning(
                "Party information not found."
            )

    # ======================================
    # GENERAL RAG GENERATION
    # ======================================

    else:

        prompt = f"""
You are an election affidavit analyst.

Answer ONLY from the provided context.

If information is unavailable,
say:
'Information not found in affidavit.'

Context:
{context}

Question:
{query}

Answer clearly.
"""

        try:

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

            answer = (
                response.choices[0]
                .message.content
            )

            st.subheader("Answer")

            st.success(answer)

        except Exception as e:

            st.error(
                f"Generation failed.\n\n{e}"
            )

    # ======================================
    # SHOW RETRIEVED EVIDENCE
    # ======================================

    st.subheader(
        "Retrieved Evidence"
    )

    for doc, meta in filtered_docs:

        st.markdown("---")

        st.markdown(
            f"""
### {meta.get('candidate', 'Unknown')}
"""
        )

        st.write(
            f"Party: {meta.get('party', 'Unknown')}"
        )

        st.write(
            f"Constituency: {meta.get('constituency', 'Unknown')}"
        )

        st.write(
            f"Page: {meta.get('page', 'Unknown')}"
        )

        st.text(doc[:1500])