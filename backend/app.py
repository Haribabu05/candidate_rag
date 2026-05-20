import streamlit as st
import chromadb

from sentence_transformers import SentenceTransformer

st.title("Election Affidavit RAG")

# Load embedding model
model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)

# Load ChromaDB
client = chromadb.PersistentClient(
    path="chroma_db"
)

collection = client.get_collection(
    "candidate_affidavits"
)

query = st.text_input(
    "Ask a question"
)

if query:

    query_embedding = model.encode(query).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=5
    )

    st.subheader("Results")

    for i, doc in enumerate(results["documents"][0]):

        meta = results["metadatas"][0][i]

        st.markdown("---")

        st.write(
            f"Candidate: {meta['candidate']}"
        )

        st.write(
            f"Party: {meta['party']}"
        )

        st.write(
            f"Constituency: {meta['constituency']}"
        )

        st.write(
            f"Page: {meta['page']}"
        )

        st.write(doc)