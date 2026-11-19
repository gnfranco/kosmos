"""Brazilian CPF/CNPJ offline format and check-digit validation.

CNPJ letters use ASCII code minus 48 (Receita Federal technical manual).
All stored IDs are uppercase and unpunctuated; no third-party lookup is made.
"""

import re

CPF_PATTERN = re.compile(r"^[0-9]{11}$")
CNPJ_PATTERN = re.compile(r"^[0-9A-Z]{12}[0-9]{2}$")
DOCUMENT_CHARS = re.compile(r"^[0-9A-Za-z./\s-]+$")


def normalize_document(value):
    """Return an unpunctuated uppercase identifier, rejecting exotic chars."""
    text = (value or "").strip()
    if text and not DOCUMENT_CHARS.fullmatch(text):
        raise ValueError("Invalid document characters.")
    cleaned = re.sub(r"[\s./-]", "", text).upper()
    if text and not cleaned:
        raise ValueError("Document identifier is empty.")
    return cleaned


def format_br_document(value, person_type, *, masked=False):
    """Add the standard CPF/CNPJ punctuation for display only.

    The model retains the canonical value without punctuation.
    Details show only the last four original characters, including for
    alphanumeric CNPJ. Unknown or malformed identifiers are never exposed
    in masked mode.
    """
    if not value:
        return ""
    if person_type == "PF" and CPF_PATTERN.fullmatch(value):
        width = 11
        segments = (3, 3, 3, 2)
        separators = (".", ".", "-")
    elif person_type == "PJ" and CNPJ_PATTERN.fullmatch(value):
        width = 14
        segments = (2, 3, 3, 4, 2)
        separators = (".", ".", "/", "-")
    else:
        return ("••••" + value[-4:]) if masked else value

    chars = ("•" * (width - 4) + value[-4:]) if masked else value
    output = []
    cursor = 0
    for index, size in enumerate(segments):
        output.append(chars[cursor : cursor + size])
        cursor += size
        if index < len(separators):
            output.append(separators[index])
    return "".join(output)


def is_valid_cpf(value):
    if not CPF_PATTERN.fullmatch(value or "") or len(set(value)) == 1:
        return False
    digits = [int(char) for char in value]
    for length in (9, 10):
        total = sum(
            digit * weight
            for digit, weight in zip(digits[:length], range(length + 1, 1, -1))
        )
        check = (total * 10) % 11
        if check == 10:
            check = 0
        if digits[length] != check:
            return False
    return True


def _cnpj_digit(prefix):
    # Works with both traditional numeric and new alphanumeric CNPJ.
    weights = (
        [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        if len(prefix) == 12
        else [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    )
    remainder = (
        sum((ord(char) - 48) * weight for char, weight in zip(prefix, weights)) % 11
    )
    return str(0 if remainder < 2 else 11 - remainder)


def is_valid_cnpj(value):
    if not CNPJ_PATTERN.fullmatch(value or "") or len(set(value)) == 1:
        return False
    return value[-2:] == _cnpj_digit(value[:12]) + _cnpj_digit(value[:13])


def normalize_br_phone(value):
    """Normalize Brazilian local or +55 numbers for Contact.phone* fields."""
    original = (value or "").strip()
    if not original:
        return original
    if not re.fullmatch(r"\+?[0-9\s().-]+", original):
        raise ValueError("Phone contains invalid characters.")
    digits = re.sub(r"\D", "", original)
    if digits.startswith("55") and len(digits) in (12, 13):
        digits = digits[2:]
    if len(digits) not in (10, 11) or digits[:2] == "00":
        raise ValueError("Enter a Brazilian phone with DDD and 8 or 9 local digits.")
    return digits
