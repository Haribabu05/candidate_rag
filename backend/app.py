from flask import Flask,jsonify
import json

app = Flask(__name__)

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

if __name__ == '__main__':

    app.run(debug=True)