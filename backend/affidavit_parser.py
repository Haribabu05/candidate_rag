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

def extract_education(
    pages
):

    education_keywords = [

        "sslc",
        "hsc",
        "graduate",
        "post graduate",
        "mba",
        "b.e",
        "b.tech",
        "m.e",
        "m.tech",
        "b.sc",
        "m.sc",
        "b.a",
        "m.a",
        "phd",
        "doctor",
        "diploma",
        "llb",
        "law"
    ]

    # ======================================
    # SEARCH PAGE BY PAGE
    # ======================================

    for page in pages:

        text = page["text"]

        lower = text.lower()

        # ==================================
        # LOOK FOR EDUCATION SECTION
        # ==================================

        if (

            "educational qualification"
            in lower

            or

            "qualification"
            in lower

            or

            "education"
            in lower
        ):

            lines = text.splitlines()

            for line in lines:

                clean = line.lower()

                for keyword in education_keywords:

                    if keyword in clean:

                        return keyword.upper()

    # ======================================
    # GLOBAL FALLBACK SEARCH
    # ======================================

    combined = ""

    for page in pages:

        combined += (
            "\n"
            + page["text"]
        )

    combined = combined.lower()

    for keyword in education_keywords:

        if keyword in combined:

            return keyword.upper()

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

    income_tax = extract_income_tax(
        income_section
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

        "income_tax": income_tax,

        "criminal_cases": criminal_cases,

        "movable_assets": movable_assets,

        "immovable_assets": immovable_assets,

        "liabilities": liabilities,

        "education": education
    }

    return candidate_data