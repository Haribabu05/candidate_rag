import streamlit as st
import chromadb

from sentence_transformers import SentenceTransformer
from openai import OpenAI

# ==========================================
# PAGE CONFIG
# ==========================================
st.set_page_config(
    page_title="Election Affidavit Intelligence System",
    layout="wide"
)

# ==========================================
# TITLE
# ==========================================
st.title("🗳️ Election Affidavit Intelligence System")

st.markdown("""
RAG system for Tamil Nadu election affidavits using:

- SentenceTransformers
- ChromaDB
- Groq LLM Generation
""")

# ==========================================
# LOAD EMBEDDING MODEL
# ==========================================
@st.cache_resource
def load_model():

    return SentenceTransformer(
        "sentence-transformers/all-MiniLM-L6-v2"
    )

model = load_model()

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
# GROQ CLIENT
# ==========================================
groq_client = OpenAI(
    api_key=st.secrets["GROQ_API_KEY"],
    base_url="https://api.groq.com/openai/v1"
)

# ==========================================
# USER INPUT
# ==========================================
query = st.text_input(
    "Ask a question",
    placeholder="Who is MK Stalin?"
)

# ==========================================
# MAIN PIPELINE
# ==========================================
if query:

    # ======================================
    # NORMALIZED QUERY
    # ======================================
    normalized_query = (
        query.lower()
        .replace(" ", "")
    )

    query_lower = query.lower()

    matched_docs = []

    # ======================================
    # LOAD ALL DOCUMENTS
    # ======================================
    all_docs = collection.get()

    # ======================================
    # DETECT QUERY TYPE
    # ======================================
    query_type = "general"

    if "income" in query_lower:

        query_type = "income"

    elif "asset" in query_lower:

        query_type = "asset"

    elif "criminal" in query_lower:

        query_type = "criminal"

    elif "party" in query_lower:

        query_type = "party"

    elif "pan" in query_lower:

        query_type = "pan"

    elif "compare" in query_lower:

        query_type = "compare"

    # ======================================
    # CANDIDATE MATCHING
    # ======================================
    candidate_matches = []

    for doc, meta in zip(
        all_docs["documents"],
        all_docs["metadatas"]
    ):

        candidate = meta.get(
            "candidate",
            ""
        )

        normalized_candidate = (
            candidate.lower()
            .replace(" ", "")
        )

        # exact + partial matching
        if (
            normalized_candidate in normalized_query
            or normalized_query in normalized_candidate
        ):

            candidate_matches.append(
                (doc, meta)
            )

    # ======================================
    # FILTER RELEVANT CHUNKS
    # ======================================
    if len(candidate_matches) > 0:

        filtered = []

        for doc, meta in candidate_matches:

            text_lower = doc.lower()

            # income
            if (
                query_type == "income"
                and "income" in text_lower
            ):

                filtered.append((doc, meta))

            # assets
            elif (
                query_type == "asset"
                and (
                    "asset" in text_lower
                    or "liabilit" in text_lower
                )
            ):

                filtered.append((doc, meta))

            # criminal
            elif (
                query_type == "criminal"
                and "criminal" in text_lower
            ):

                filtered.append((doc, meta))

            # party
            elif (
                query_type == "party"
                and "party" in text_lower
            ):

                filtered.append((doc, meta))

            # PAN
            elif (
                query_type == "pan"
                and "pan" in text_lower
            ):

                filtered.append((doc, meta))

            # compare
            elif query_type == "compare":

                filtered.append((doc, meta))

            # general
            elif query_type == "general":

                filtered.append((doc, meta))

        if len(filtered) > 0:

            matched_docs = filtered

        else:

            matched_docs = candidate_matches

    # ======================================
    # VECTOR SEARCH FALLBACK
    # ======================================
    if len(matched_docs) == 0:

        query_embedding = model.encode(
            query
        ).tolist()

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=5
        )

        documents = results["documents"][0]

        metadatas = results["metadatas"][0]

        matched_docs = list(
            zip(documents, metadatas)
        )

    # ======================================
    # NO RESULTS
    # ======================================
    if len(matched_docs) == 0:

        st.warning(
            "No matching affidavit information found."
        )

    else:

        # ==================================
        # BUILD CONTEXT
        # ==================================
        context = ""

        shown_pages = set()

        for doc, meta in matched_docs:

            page = meta.get(
                "page",
                "Unknown"
            )

            # skip duplicate pages
            if page in shown_pages:
                continue

            shown_pages.add(page)

            candidate = meta.get(
                "candidate",
                "Unknown"
            )

            party = meta.get(
                "party",
                "Unknown"
            )

            constituency = meta.get(
                "constituency",
                "Unknown"
            )

            context += f"""
Candidate: {candidate}
Party: {party}
Constituency: {constituency}
Page: {page}

Affidavit Content:
{doc}

=========================================
"""

            if len(shown_pages) >= 5:
                break

        # ==================================
        # PROMPT
        # ==================================
        prompt = f"""
You are an AI assistant analyzing
Tamil Nadu election affidavits.

Answer ONLY using the provided affidavit context.

Rules:
- Be concise
- Be factual
- Do not hallucinate
- If answer is unavailable say:
  "Information not found in affidavit."

AFFIDAVIT CONTEXT:
{context}

QUESTION:
{query}
"""

        # ==================================
        # GENERATE ANSWER
        # ==================================
        with st.spinner("Generating answer..."):

            try:

                response = groq_client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You answer questions "
                                "about Tamil Nadu election "
                                "affidavits using ONLY "
                                "provided context."
                            )
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.2
                )

                answer = (
                    response
                    .choices[0]
                    .message
                    .content
                )

            except Exception as e:

                answer = (
                    "Generation failed.\n\n"
                    f"{str(e)}"
                )

        # ==================================
        # SHOW ANSWER
        # ==================================
        st.subheader("Answer")

        st.success(answer)

        # ==================================
        # SHOW EVIDENCE
        # ==================================
        st.subheader("Retrieved Evidence")

        shown_pages = set()

        for doc, meta in matched_docs:

            page = meta.get(
                "page",
                "Unknown"
            )

            if page in shown_pages:
                continue

            shown_pages.add(page)

            candidate = meta.get(
                "candidate",
                "Unknown"
            )

            party = meta.get(
                "party",
                "Unknown"
            )

            constituency = meta.get(
                "constituency",
                "Unknown"
            )

            with st.expander(
                f"{candidate} | {party} | Page {page}"
            ):

                st.markdown(f"""
### Candidate
{candidate}

### Party
{party}

### Constituency
{constituency}

### Page
{page}
""")

                st.text(doc[:1500])

            if len(shown_pages) >= 5:
                break