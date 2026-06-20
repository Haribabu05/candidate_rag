from flask import Flask,jsonify
import json

from flask_cors import CORS

from flask import request
from gemini_client import ask_gemini
from intent_router import detect_intent

from answer_formatter import (
    format_candidate,
    format_candidate_list,
    format_comparison
)


#stats of the candidate
from query_engine import (
    find_candidate,
    find_by_party,
    find_by_education,
    find_by_constituency,
    compare_candidates,
    richest_candidates
)

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
def compare_candidates_api():

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



@app.route(
    "/chat",
    methods=["POST"]
)
def chat():

    data = request.get_json()

    query = data["message"]

    intent = detect_intent(query)

    print("QUERY:", query)
    print("INTENT:", intent)

    # ==========================
    # CANDIDATE
    # ==========================

    if intent == "unknown":

        result = find_candidate(query)

        if result:

            return jsonify({

                "answer":
                            format_candidate(
                                result
                            ),

                "source": "candidate_db"
            })

    # ==========================
    # PARTY
    # ==========================

    elif intent == "party":

        result = find_by_party(query)

        return jsonify({

            "answer":
                        format_candidate_list(
                            result
                        ),

            "source": "candidate_db"
        })

    # ==========================
    # EDUCATION
    # ==========================

    elif intent == "education":

        result = find_by_education(query)

        return jsonify({

            "answer":  format_candidate_list(
            result
        ),

            "source": "candidate_db"
        })

    # ==========================
    # CONSTITUENCY
    # ==========================

    elif intent == "constituency":

        result = find_by_constituency(query)

        return jsonify({

            "answer":  format_candidate_list(
                    result
                    ),

            "source": "candidate_db"
        })

    # ==========================
    # COMPARE
    # ==========================

    elif intent == "compare":

        result = compare_candidates(query)

        if not result:

            return jsonify({

                "answer":
                    "Please provide two valid candidate names.",

                "source":
                    "candidate_db"
            })

        return jsonify({

            "answer":
                format_comparison(

                    result["candidate1"],

                    result["candidate2"]
                ),

            "source":
                "candidate_db"
        })

    # ==========================
    # SEMANTIC
    # ==========================

    elif intent == "semantic":

        return jsonify({

            "answer":
                "ChromaDB not connected yet.",

            "source":
                "semantic"
        })

    # ==========================
    # WEB / GEMINI
    # ==========================

    # ==========================
    # WEB / GEMINI
    # ==========================

    try:

        answer = ask_gemini(query)

    except Exception as e:

        print("GEMINI ERROR:", e)

        answer = (
            "External AI service is currently unavailable."
        )

    return jsonify({

            "answer": answer,

            "source": "gemini"
        })

if __name__ == '__main__':

    app.run(
        debug=True,
        use_reloader=False
        )  
    

#commit on 8/06/2024
#commit on 9/06/2024
