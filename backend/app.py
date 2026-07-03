from flask import Flask,jsonify
import json
from groq_client import ask_gemini
from flask_cors import CORS

from semantic_search import semantic_answer

from flask import request
from groq_client import ask_gemini
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
    richest_candidates,
      find_by_gender
)

with open(
    "candidate_master_data.json",
    "r",
    encoding="utf-8"
) as f:

    candidate_data = json.load(f)

KNOWN_CANDIDATES = list(candidate_data.keys())   

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

        print("EDUCATION RESULT COUNT =", len(result))
        print("RESULT =", result[:3]) 

        return jsonify({

            "answer": format_candidate_list(result),

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


    elif intent == "male":

        result = find_by_gender("male")

        return jsonify({

            "answer":
                format_candidate_list(result),

            "source":
                "candidate_db"
        })


    elif intent == "female":

        result = find_by_gender("female")

        return jsonify({

            "answer":
                format_candidate_list(result),

            "source":
                "candidate_db"
        })

    elif intent == "compare":

        result = compare_candidates(query)

        if not result:

            return jsonify({
                "answer": "Please provide two valid candidate names.",
                "source": "candidate_db"
            })

        c1 = result["candidate1"]
        c2 = result["candidate2"]

        def value(v):
            if isinstance(v, (int, float)) and v == 0:
                return "Not Available"
            return f"₹{v:,}" if isinstance(v, (int, float)) else (v or "Not Available")

        prompt = f"""
    You are an AI assistant comparing two Tamil Nadu election candidates.

    Use ONLY the information below.

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
    • Keep the answer under 180 words.
    """

        ai_answer = ask_gemini(prompt)

        return jsonify({
            "answer": ai_answer,
            "source": "groq_compare"
        })
       
      
        # ==========================
        # SEMANTIC
        # ==========================

    elif intent == "semantic":

        result = semantic_answer(
            query=query,
            known_candidates=KNOWN_CANDIDATES,
            ask_gemini_fn=ask_gemini
        )

        return jsonify(result)

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
