import os

from hindsight_client import Hindsight


# ---------------------------------------
# Initialize Hindsight
# ---------------------------------------

client = Hindsight(
    base_url="https://api.hindsight.vectorize.io",
    api_key=os.getenv("HINDSIGHT_API_KEY")
)

BANK_ID = "candidate-rag"


# ---------------------------------------
# Store Memory
# ---------------------------------------

def retain_memory(session_id: str, memory: str):
    """
    Stores a memory in Hindsight.
    """

    try:

        client.retain(

            bank_id=BANK_ID,

            content=f"""
Session:
{session_id}

Memory:
{memory}
""",

            metadata={
                "session_id": session_id
            }
        )

    except Exception as e:

        print("Hindsight retain error:", e)


# ---------------------------------------
# Recall Memory
# ---------------------------------------

def recall_memory(session_id: str, query: str):

    """
    Recall memories related to this session.
    """

    try:

        result = client.recall(

            bank_id=BANK_ID,

            query=f"""
Session:
{session_id}

Question:
{query}
"""
        )

        if not result.results:

            return ""

        memories = []

        for memory in result.results:

            memories.append(memory.text)

        return "\n".join(memories)

    except Exception as e:

        print("Hindsight recall error:", e)

        return ""


# ---------------------------------------
# Helper functions
# ---------------------------------------

def remember_candidate(session_id, candidate):

    retain_memory(

        session_id,

        f"User is interested in candidate {candidate}."
    )


def remember_party(session_id, party):

    retain_memory(

        session_id,

        f"User is interested in {party} party."
    )


def remember_constituency(session_id, constituency):

    retain_memory(

        session_id,

        f"User is exploring constituency {constituency}."
    )


def remember_topic(session_id, topic):

    retain_memory(

        session_id,

        f"User prefers information about {topic}."
    )


def remember_compare(session_id, c1, c2):

    retain_memory(

        session_id,

        f"User compared {c1} with {c2}."
    )