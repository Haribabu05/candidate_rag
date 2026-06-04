from intent_router import detect_intent

while True:

    q = input("Query: ")

    print(
        detect_intent(q)
    )