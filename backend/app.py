from flask import Flask,jsonify
import json

from flask_cors import CORS

from flask import request
from gemini_client import ask_gemini
from intent_router import detect_intent

with open(
    "candidate_master_data.json",
    "r",
    encoding="utf-8"
) as f:

    candidate_data = json.load(f)

app = Flask(__name__)

CORS(app)

with open(
    "candidate_master_data.json",
    "r",
    encoding="utf-8"
) as f:

    candidate_data = json.load(f)

@app.route('/')
def home():
    return {
        "message" : "Candidate API is Running"
    }


@app.route('/candidates/<name>')
def get_candidate(name):

    candidate = candidate_data.get(name)
    if candidate:
        return jsonify(candidate)
    return jsonify({
        "error":"Candidate not found"
    }),404

@app.route('/candidates')
def all_candidates():

    return jsonify(
        list(candidate_data.keys())
    )

@app.route('/party/<party>')
def get_by_party(party):
    
    results = []

    for candidate in candidate_data.values():

        if(
            candidate["party"].lower() == party.lower()
        ):
            results.append(candidate['candidate'])

    return jsonify(results)


@app.route('/region/<region>')
def get_by_region(region):
    
    results= []

    for candidate in candidate_data.values():

        if(
            candidate["constituency"].lower() == region.lower()
        ):
            results.append(candidate["candidate"])
        
    return jsonify(results)


#=========================
#compare two candidates
#=========================

@app.route('/compare')
def compare_candidates():

    from flask import request

    c1 = request.args.get("c1")
    c2 = request.args.get("c2")

    candidate1 = candidate_data.get(c1)
    candidate2 = candidate_data.get(c2)

    if not candidate1 or not candidate2:
        return jsonify({
            "error":"One or both candidates not found"
        }),404

    return jsonify({
        "candidate1": candidate1,
        "candidate2": candidate2
    })


#search by education


@app.route('/education/<degree>')
def get_by_education(degree):

    results = []

    for candidate in candidate_data.values():

        education = (
            candidate["education"]["degree"]
        )

        if education.lower() == degree.lower():

            results.append(
                candidate["candidate"]
            )

    return jsonify(results)

  #assests endpoint

@app.route('/top-assets')
def top_assets():

    results = sorted(

        candidate_data.values(),
         key=lambda x:
            x["assets"]["total"],
        reverse=True
    )

    return jsonify(
        results[:10]
    )

#stats of the candidate

@app.route('/stats')
def stats():
    return jsonify({

        "total_candidates":
            len(candidate_data),

        "parties":
            len(
                set(
                    c["party"]
                    for c in candidate_data.values()
                )
            )
    })


#chat endpoint for gemini

@app.route(
    "/chat",
    methods=["POST"]
)
def chat():

    data = request.json

    query = data["message"]

    intent = detect_intent(
        query
    )

    context = ""

    # Candidate lookup
    for candidate in candidate_data.values():

        if (
            candidate["candidate"].lower()
            in query.lower()
        ):

            context = json.dumps(
                candidate,
                indent=2
            )

            break

    prompt = f"""
You are an Election Candidate Assistant.

Candidate Context:

{context}

Question:

{query}

Answer using the context.
"""

    answer = ask_gemini(
        prompt
    )

    return jsonify({

        "answer": answer,

        "intent": intent
    })

if __name__ == '__main__':

    app.run(debug=True)