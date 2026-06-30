from query_engine import find_candidate

tests = [
    "Aruldoss",
    "arul doss",
    "aruldosa",
    "mkstalin",
    "mk stalin",
    "stalin",
    "poornima",
    "modi"
]

for q in tests:
    print("=" * 50)
    print("QUERY:", q)

    result = find_candidate(q)

    if result:
        print("FOUND:", result["candidate"])
    else:
        print("NOT FOUND")