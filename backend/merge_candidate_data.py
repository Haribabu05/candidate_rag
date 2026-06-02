import json

# ==========================
# LOAD ENGLISH DATA
# ==========================

with open(
    "candidate_master_data.json",
    "r",
    encoding="utf-8"
) as f:

    english_data = json.load(f)

# ==========================
# LOAD TAMIL DATA
# ==========================

with open(
    "candidate_master_data_tamil.json",
    "r",
    encoding="utf-8"
) as f:

    tamil_data = json.load(f)

# ==========================
# MERGE
# ==========================

merged = {}

all_candidates = set(
    list(english_data.keys())
    +
    list(tamil_data.keys())
)

for candidate in all_candidates:

    eng = english_data.get(
        candidate,
        {}
    )

    tam = tamil_data.get(
        candidate,
        {}
    )

    merged[candidate] = {

        # ENGLISH OCR
        "candidate": eng.get(
            "candidate",
            candidate
        ),

        "party": eng.get(
            "party",
            ""
        ),

        "constituency": eng.get(
            "constituency",
            ""
        ),

        "phones": eng.get(
            "phones",
            []
        ),

        "emails": eng.get(
            "emails",
            []
        ),

        "pan_ids": eng.get(
            "pan_ids",
            []
        ),

        "income_tax": eng.get(
            "income_tax",
            {}
        ),

        # TAMIL OCR
        "education": tam.get(
            "education",
            "Unknown"
        ),

        "criminal_cases": tam.get(
            "criminal_cases",
            0
        ),

        "movable_assets": tam.get(
            "movable_assets",
            0
        ),

        "immovable_assets": tam.get(
            "immovable_assets",
            0
        ),

        "liabilities": tam.get(
            "liabilities",
            0
        )
    }

# ==========================
# SAVE
# ==========================

with open(
    "candidate_master_data_merged.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        merged,
        f,
        indent=2,
        ensure_ascii=False
    )

print(
    f"Merged {len(merged)} candidates"
)