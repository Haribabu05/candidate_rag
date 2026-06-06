# ==========================================
# SINGLE CANDIDATE
# ==========================================

def format_candidate(candidate):

    if not candidate:

        return "Candidate not found."

    return f"""
Name: {candidate['candidate']}

Party: {candidate['party']}

Constituency: {candidate['constituency']}

Education: {candidate['education']['degree']}

Assets: ₹{candidate['assets']['total']:,}

Liabilities: ₹{candidate['liabilities']:,}

Occupation: {candidate['occupation']}

Spouse: {candidate['spouse']}

Phones: {", ".join(candidate['phones']) if candidate['phones'] else "Not Available"}

Emails: {", ".join(candidate['emails']) if candidate['emails'] else "Not Available"}

PAN IDs: {", ".join(candidate['pan_ids']) if candidate['pan_ids'] else "Not Available"}
"""


# ==========================================
# CANDIDATE LIST
# ==========================================

def format_candidate_list(candidates):

    if not candidates:

        return "No candidates found."

    response = []

    for i, candidate in enumerate(
        candidates,
        start=1
    ):

        response.append(
            f"{i}. "
            f"{candidate['candidate']} "
            f"({candidate['party']}) - "
            f"{candidate['constituency']}"
        )

    return "\n".join(response)


# ==========================================
# COMPARE
# ==========================================

def format_comparison(c1, c2):

    if not c1 or not c2:

        return (
            "Could not compare "
            "the candidates."
        )

    return f"""
================================

{c1['candidate']} VS {c2['candidate']}

================================

Party

• {c1['candidate']}:
  {c1['party']}

• {c2['candidate']}:
  {c2['party']}

--------------------------------

Constituency

• {c1['candidate']}:
  {c1['constituency']}

• {c2['candidate']}:
  {c2['constituency']}

--------------------------------

Education

• {c1['candidate']}:
  {c1['education']['degree']}

• {c2['candidate']}:
  {c2['education']['degree']}

--------------------------------

Assets

• {c1['candidate']}:
  ₹{c1['assets']['total']:,}

• {c2['candidate']}:
  ₹{c2['assets']['total']:,}

--------------------------------

Liabilities

• {c1['candidate']}:
  ₹{c1['liabilities']:,}

• {c2['candidate']}:
  ₹{c2['liabilities']:,}

--------------------------------

Criminal Cases

• {c1['candidate']}:
  {c1['criminal_cases']['pending']}

• {c2['candidate']}:
  {c2['criminal_cases']['pending']}
"""

