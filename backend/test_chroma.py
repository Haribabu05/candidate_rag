from search_chroma import semantic_search

result = semantic_search(
    query="education",
    candidate="VSBabu"
)

print(result["documents"][0][0])