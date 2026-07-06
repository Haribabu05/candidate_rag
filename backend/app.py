from flask import Flask, jsonify, request
import json
import os
import uuid

from flask_cors import CORS
from groq_client import ask_gemini
from semantic_search import semantic_answer
from intent_router import detect_intent
from memory import recall_memory, retain_memory, remember_candidate, remember_party, remember_constituency, remember_compare
from answer_formatter import format_candidate, format_candidate_list, format_comparison
from query_engine import (
    find_candidate,
    find_by_party,
    find_by_education,
    find_by_constituency,
    compare_candidates,
    richest_candidates,
    find_by_gender
)

# ── Load candidate data ───────────────────────────────────────────────────────
_dir = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(_dir, "candidate_master_data.json"), "r", encoding="utf-8") as f:
    candidate_data = json.load(f)

KNOWN_CANDIDATES = list(candidate_data.keys())


# ── Follow-up question generation ─────────────────────────────────────────────
def generate_follow_ups(query, answer, context=""):
    prompt = f"""Based on this question and answer about Tamil Nadu election candidates,
generate 4 short follow-up questions a user might want to ask next.
Question: {query}
Answer: {answer}
{f"Context: {context}" if context else ""}
Return only 4 numbered questions, nothing else."""

    try:
        response = ask_gemini(prompt)
        follow_ups = []
        for line in response.splitlines():
            line = line.strip()
            if line and line[0].isdigit():
                question = line[2:].strip() if len(line) > 1 and line[1] in ".)" else line
                follow_ups.append(question)
        return follow_ups[:4]
    except Exception as e:
        print("FOLLOW-UP GENERATION ERROR:", e)
        return []


# ── Flask app ─────────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# ── Routes ────────────────────────────────────────────────────────────────────
@app.route('/')
def home():
    return {"message": "Candidate API is Running"}

@app.route('/candidates/<name>')
def get_candidate(name):
    candidate = candidate_data.get(name)
    if candidate:
        return jsonify(candidate)
    return jsonify({"error": "Candidate not found"}), 404

@app.route('/candidates')
def all_candidates():
    return jsonify(list(candidate_data.keys()))

@app.route('/party/<party>')
def get_by_party(party):
    results = [c['candidate'] for c in candidate_data.values() if c["party"].lower() == party.lower()]
    return jsonify(results)

@app.route('/region/<region>')
def get_by_region(region):
    results = [c["candidate"] for c in candidate_data.values() if c["constituency"].lower() == region.lower()]
    return jsonify(results)

@app.route('/compare')
def compare_candidates_api():
    c1 = request.args.get("c1")
    c2 = request.args.get("c2")
    candidate1 = candidate_data.get(c1)
    candidate2 = candidate_data.get(c2)
    if not candidate1 or not candidate2:
        return jsonify({"error": "One or both candidates not found"}), 404
    return jsonify({"candidate1": candidate1, "candidate2": candidate2})

@app.route('/education/<degree>')
def get_by_education(degree):
    results = [c["candidate"] for c in candidate_data.values() if c["education"]["degree"].lower() == degree.lower()]
    return jsonify(results)

@app.route('/top-assets')
def top_assets():
    results = sorted(candidate_data.values(), key=lambda x: x["assets"]["total"], reverse=True)
    return jsonify(results[:10])

# ── Main chat endpoint ────────────────────────────────────────────────────────
@app.route("/chat", methods=["POST"])
def chat():

    data = request.get_json()
    query = data["message"]

    # ── Get or create session ID ──────────────────────────────────────────────
    session_id = data.get("session_id", str(uuid.uuid4()))

    print("QUERY:", query)
    print("SESSION:", session_id)

    # ── Step 1: Recall memory from Hindsight ──────────────────────────────────
    past_memory = recall_memory(session_id, query)

    if past_memory:
        print("MEMORY RECALLED:", past_memory[:150])
    else:
        print("NO MEMORY FOUND")

    # ── Step 2: Detect intent ─────────────────────────────────────────────────
    intent = detect_intent(query)
    print("INTENT:", intent)

    # ── Helper: format memory context for prompts ─────────────────────────────
    def memory_block():
        if past_memory:
            return f"\nPrevious context from this user's session:\n{past_memory}\n"
        return ""

    # ── Step 3: Route by intent ───────────────────────────────────────────────

    # CANDIDATE LOOKUP
    if intent == "unknown":
        result = find_candidate(query)
        if result:
            answer = format_candidate(result)
            remember_candidate(session_id, result["candidate"])
            retain_memory(session_id, f"User asked about candidate {result['candidate']} from {result['party']}.")
            follow_ups = generate_follow_ups(query, answer)
            return jsonify({"answer": answer, "source": "candidate_db", "follow_ups": follow_ups})

    # PARTY
    elif intent == "party":
        result = find_by_party(query)
        answer = format_candidate_list(result)
        remember_party(session_id, query)
        retain_memory(session_id, f"User searched for candidates by party. Query: {query}")
        follow_ups = generate_follow_ups(query, answer)
        return jsonify({"answer": answer, "source": "candidate_db", "follow_ups": follow_ups})

    # EDUCATION
    elif intent == "education":
        result = find_by_education(query)
        print("EDUCATION RESULT COUNT =", len(result))
        answer = format_candidate_list(result)
        retain_memory(session_id, f"User searched for candidates by education. Query: {query}")
        follow_ups = generate_follow_ups(query, answer)
        return jsonify({"answer": answer, "source": "candidate_db", "follow_ups": follow_ups})

    # CONSTITUENCY
    elif intent == "constituency":
        result = find_by_constituency(query)
        answer = format_candidate_list(result)
        remember_constituency(session_id, query)
        retain_memory(session_id, f"User searched for candidates in constituency. Query: {query}")
        follow_ups = generate_follow_ups(query, answer)
        return jsonify({"answer": answer, "source": "candidate_db", "follow_ups": follow_ups})

    # MALE
    elif intent == "male":
        result = find_by_gender("male")
        answer = format_candidate_list(result)
        retain_memory(session_id, "User searched for male candidates.")
        follow_ups = generate_follow_ups(query, answer)
        return jsonify({"answer": answer, "source": "candidate_db", "follow_ups": follow_ups})

    # FEMALE
    elif intent == "female":
        result = find_by_gender("female")
        answer = format_candidate_list(result)
        retain_memory(session_id, "User searched for female candidates.")
        follow_ups = generate_follow_ups(query, answer)
        return jsonify({"answer": answer, "source": "candidate_db", "follow_ups": follow_ups})

    # COMPARE
    elif intent == "compare":
        result = compare_candidates(query)
        if not result:
            return jsonify({"answer": "Please provide two valid candidate names.", "source": "candidate_db"})

        c1 = result["candidate1"]
        c2 = result["candidate2"]

        def value(v):
            if isinstance(v, (int, float)) and v == 0:
                return "Not Available"
            return f"₹{v:,}" if isinstance(v, (int, float)) else (v or "Not Available")

        prompt = f"""You are an AI assistant comparing two Tamil Nadu election candidates.
Use ONLY the information below.
{memory_block()}
Candidate 1
-----------
Name: {c1['candidate']}
Party: {c1['party']}
Constituency: {c1['constituency']}
Education: {c1['education']['degree']}
Assets: {value(c1['assets']['total'])}
Liabilities: {value(c1['liabilities'])}
Pending Criminal Cases: {c1['criminal_cases']['pending']}
Convicted Criminal Cases: {c1['criminal_cases']['convicted']}
Occupation: {c1.get('occupation','Not Available') or 'Not Available'}

Candidate 2
-----------
Name: {c2['candidate']}
Party: {c2['party']}
Constituency: {c2['constituency']}
Education: {c2['education']['degree']}
Assets: {value(c2['assets']['total'])}
Liabilities: {value(c2['liabilities'])}
Pending Criminal Cases: {c2['criminal_cases']['pending']}
Convicted Criminal Cases: {c2['criminal_cases']['convicted']}
Occupation: {c2.get('occupation','Not Available') or 'Not Available'}

Instructions:
• Compare the two candidates.
• Mention the important differences first.
• Mention similarities if relevant.
• Do NOT invent facts.
• If information is unavailable, simply say it is not available.
• Write in clear natural language.
• Keep the answer under 180 words."""

        ai_answer = ask_gemini(prompt)
        remember_compare(session_id, c1["candidate"], c2["candidate"])
        retain_memory(session_id, f"User compared {c1['candidate']} with {c2['candidate']}.")
        follow_ups = generate_follow_ups(query, ai_answer)
        return jsonify({"answer": ai_answer, "source": "groq_compare", "follow_ups": follow_ups})

    # SEMANTIC RAG
    elif intent == "semantic":
        result = semantic_answer(
            query=query,
            known_candidates=KNOWN_CANDIDATES,
            ask_gemini_fn=ask_gemini,
            memory_context=past_memory
        )
        retain_memory(session_id, f"User asked: {query}. Answer summary: {result['answer'][:200]}")
        return jsonify(result)

    # GROQ FALLBACK
    try:
        prompt_with_memory = f"""{memory_block()}Question: {query}

Answer based on Tamil Nadu election candidate information if relevant, otherwise answer generally."""
        answer = ask_gemini(prompt_with_memory)
    except Exception as e:
        print("GROQ ERROR:", e)
        answer = "External AI service is currently unavailable."

    retain_memory(session_id, f"User asked: {query}. Answer: {answer[:200]}")

    follow_ups = generate_follow_ups(query, answer)
    return jsonify({"answer": answer, "source": "groq", "follow_ups": follow_ups})


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)