import chromadb

client = chromadb.PersistentClient(
    path="chroma_db"
)

collection = client.get_collection(
    "affidavits"
)


def semantic_search(query, candidate=None, party=None, constituency=None, n_results=5):

    where = {}

    if candidate:
        where["candidate"] = candidate

    if party:
        where["party"] = party

    if constituency:
        where["constituency"] = constituency

    # If any metadata filter exists
    if where:

        result = collection.query(
            query_texts=[query],
            where=where,
            n_results=n_results
        )

    # Otherwise search entire collection
    else:

        result = collection.query(
            query_texts=[query],
            n_results=n_results
        )

    return result