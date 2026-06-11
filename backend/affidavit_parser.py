# ==========================================
# FILE: backend/affidavit_parser.py
# ==========================================

import re

# ==========================================
# REGEX
# ==========================================

PAN_REGEX = r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"

PHONE_REGEX = r"\b[6-9]\d{9}\b"

EMAIL_REGEX = (
    r"[a-zA-Z0-9_.+-]+"
    r"@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
)

MONEY_REGEX = (
    r"\d{1,3}(?:,\d{2,3})+"
)

# ==========================================
# CLEAN MONEY
# ==========================================

def clean_money(value):

    try:

        return int(
            value.replace(",", "")
        )

    except:

        return 0

# ==========================================
# SECTION FINDER
# ==========================================

def get_section(
    pages,
    keywords
):

    section_text = ""

    for page in pages:

        text = page["text"]

        lower = text.lower()


        for keyword in keywords:

            if keyword.lower() in lower:

                section_text += (
                    "\n"
                    + text
                )

                break

    return section_text

# ==========================================
# PAN IDS
# ==========================================

def extract_pan_ids(text):

    pans = re.findall(
        PAN_REGEX,
        text
    )

    return list(set(pans))

# ==========================================
# PHONES
# ==========================================

def extract_phones(text):

    phones = re.findall(
        PHONE_REGEX,
        text
    )

    return list(set(phones))

# ==========================================
# EMAILS
# ==========================================

def extract_emails(text):

    emails = re.findall(
        EMAIL_REGEX,
        text
    )

    return list(set(emails))

# ==========================================
# EDUCATION EXTRACTION
# ==========================================

EDUCATION_PATTERNS = {

    # School
    "sslc": "SSLC",
    "10th": "SSLC",

    "hsc": "HSC",
    "12th": "HSC",

    # ITI / Diploma
    "iti": "ITI",
    "diploma": "Diploma",

    # Undergraduate
    "b.a": "B.A",
    "bcom": "B.Com",
    "b.com": "B.Com",

    "bsc": "B.Sc",
    "b.sc": "B.Sc",

    "bca": "BCA",
    "bba": "BBA",

    "b.e": "B.E",
    "be ": "B.E",

    "b.tech": "B.Tech",
    "btech": "B.Tech",

    "llb": "LL.B",

    # Postgraduate
    "m.a": "M.A",
    "mcom": "M.Com",
    "m.com": "M.Com",

    "msc": "M.Sc",
    "m.sc": "M.Sc",

    "mba": "MBA",
    "mca": "MCA",

    "m.e": "M.E",

    "mtech": "M.Tech",
    "m.tech": "M.Tech",

    "m.phil": "M.Phil",
    "mphil": "M.Phil",

    "ph.d": "Ph.D",
    "phd": "Ph.D"
}

def extract_education(pages):

    combined = ""

    for page in pages:

        combined += (
            "\n"
            + page["text"]
        )

    lower = combined.lower()

    # Tamil special cases

    if "அரசியல்அறிவியல்" in combined:
        return "B.A. Political Science"

    if (
        "இளங்கலை" in combined
        or
        "இளங்கைல" in combined
    ):
        return "Bachelor Degree"

    if "முதுகலை" in combined:
        return "Master Degree"

    if "முனைவர்" in combined:
        return "Ph.D"

    # English patterns

    for pattern, degree in EDUCATION_PATTERNS.items():

        if pattern in lower:

            return degree

    return "Unknown"

# ==========================================
# CRIMINAL CASES
# ==========================================

def extract_criminal_cases(
    criminal_section
):

    lower = criminal_section.lower()

    if (
        "no criminal case" in lower
        or
        "nil" in lower
        or
        "not convicted" in lower
    ):

        return 0

    return 0

# ==========================================
# INCOME TAX
# ==========================================

def extract_income_tax(
    income_section
):

    income_data = {}

    lines = income_section.splitlines()

    for i in range(len(lines)):

        line = lines[i]

        year_match = re.search(
            r"(20\d{2})",
            line
        )

        if year_match:

            year = year_match.group()

            combined = line

            if i + 1 < len(lines):

                combined += (
                    " "
                    + lines[i + 1]
                )

            money_matches = re.findall(
                MONEY_REGEX,
                combined
            )

            cleaned = []

            for value in money_matches:

                amount = clean_money(
                    value
                )

                if amount > 1000:

                    cleaned.append(amount)

            if cleaned:

                income_data[
                    year
                ] = max(cleaned)

    return income_data

# ==========================================
# MOVABLE ASSETS
# ==========================================

def extract_movable_assets(
    movable_section
):

    money_matches = re.findall(
        MONEY_REGEX,
        movable_section
    )

    cleaned = []

    for value in money_matches:

        amount = clean_money(value)

        if amount > 1000:

            cleaned.append(amount)

    if cleaned:

        return max(cleaned)

    return 0

# ==========================================
# IMMOVABLE ASSETS
# ==========================================

def extract_immovable_assets(
    immovable_section
):

    money_matches = re.findall(
        MONEY_REGEX,
        immovable_section
    )

    cleaned = []

    for value in money_matches:

        amount = clean_money(value)

        if amount > 1000:

            cleaned.append(amount)

    if cleaned:

        return max(cleaned)

    return 0

# ==========================================
# LIABILITIES
# ==========================================

def extract_liabilities(
    liabilities_section
):

    money_matches = re.findall(
        MONEY_REGEX,
        liabilities_section
    )

    cleaned = []

    for value in money_matches:

        amount = clean_money(value)

        if amount > 1000:

            cleaned.append(amount)

    if cleaned:

        return max(cleaned)

    return 0


# ==========================================
# MAIN PARSER
# ==========================================

def extract_age(text):

    age_match = re.search(
        r'Age[:\s]+(\d{2})',
        text,
        re.I
    )

    if age_match:
        return int(age_match.group(1))

    return None


def extract_gender(text):

    lower = text.lower()

    if "male" in lower:
        return "Male"

    if "female" in lower:
        return "Female"

    return None


def extract_occupation(text):

    return ""


def extract_spouse(text):

    return ""

def parse_candidate_pages(
    candidate_name,
    pages
):

    full_text = ""

    for page in pages:

        full_text += (
            "\n"
            + page["text"]
        )

    metadata = pages[0]["metadata"]

    party = metadata["party"]

    constituency = (
        metadata["constituency"]
    )

    # DEBUGGING

    if candidate_name == "SSharan":

        with open(
            "debug_SSharan.txt",
            "w",
            encoding="utf-8"
        ) as f:

            f.write(full_text)

    print("Processing:", candidate_name)

    if "Aathithya" in candidate_name:

        print("DEBUG HIT:", candidate_name)

        with open(
            "debug_aathithya.txt",
            "w",
            encoding="utf-8"
        ) as f:

            f.write(full_text)

        print("File written")
    # ======================================
    # BASIC INFO
    # ======================================

    age = extract_age(
        full_text
    )

    gender = extract_gender(
        full_text
    )

    occupation = extract_occupation(
        full_text
    )

    spouse = extract_spouse(
        full_text
    )   

    # ======================================
    # CONTACT
    # ======================================

    pan_ids = extract_pan_ids(
        full_text
    )

    phones = extract_phones(
        full_text
    )

    emails = extract_emails(
        full_text
    )

    # ======================================
    # SECTIONS
    # ======================================

    income_section = get_section(

        pages,

        [
            "income tax",
            "income return",
            "income shown",
            "வருமான"
        ]
    )

    criminal_section = get_section(

        pages,

        [
            "criminal cases",
            "criminal case",
            "convicted",
            "குற்றவியல்"
        ]
    )

    movable_section = get_section(

        pages,

        [
            "movable assets",
            "அசையும்"
        ]
    )

    immovable_section = get_section(

        pages,

        [
            "immovable assets",
            "அசையாச்"
        ]
    )

    liabilities_section = get_section(

        pages,

        [
            "liabilities",
            "dues",
            "கடன்"
        ]
    )

    # ======================================
    # EXTRACTION
    # ======================================

    # Use full_text instead of income_section
    # because OCR often misses the section heading

    income_tax = extract_income_tax(
        full_text
    )

    criminal_cases = (
        extract_criminal_cases(
            criminal_section
        )
    )

    movable_assets = (
        extract_movable_assets(
            movable_section
        )
    )

    immovable_assets = (
        extract_immovable_assets(
            immovable_section
        )
    )

    liabilities = (
        extract_liabilities(
            liabilities_section
        )
    )

    education = extract_education(
        pages
    )

    # ======================================
    # FINAL JSON
    # ======================================

    candidate_data = {

         "candidate": candidate_name,

        "party": party,

        "constituency": constituency,

        "phones": phones,

        "emails": emails,

        "pan_ids": pan_ids,

        "education": {
            "degree": education
        },

        "criminal_cases": {
            "pending": criminal_cases,
            "convicted": 0
        },

        "income_tax": income_tax,

        "assets": {
            "movable": movable_assets,
            "immovable": immovable_assets,
            "total": (
                movable_assets
                +
                immovable_assets
            )
        },

        "liabilities": liabilities,

        "occupation": "",

        "spouse": "",

        "dependents": 0,

        "source_pdf": metadata.get(
            "pdf_file",
            ""
    )
    }

    return candidate_data

    #commit on 11/06/2024