from search_chroma import semantic_search

result = semantic_search(
    query="assets",
    candidate="ERaamadasan"
)
print(result["documents"][0][0])