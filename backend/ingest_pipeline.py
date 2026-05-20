import json
import chromadb

from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
# Load extracted pages
with open("extracted_pages.json", "r", encoding="utf-8") as f:
    pages = json.load(f)

# Embedding model
model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)

# ChromaDB persistent client
client = chromadb.PersistentClient(
    path="chroma_db"
)

collection = client.get_or_create_collection(
    "candidate_affidavits"
)

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50
)

doc_id = 0

for page in pages:

    chunks = splitter.split_text(page["text"])

    for chunk in chunks:

        embedding = model.encode(chunk).tolist()

        collection.add(
            documents=[chunk],
            embeddings=[embedding],
            metadatas=[page["metadata"]],
            ids=[f"doc_{doc_id}"]
        )

        doc_id += 1

print(f"Stored {doc_id} chunks in ChromaDB")