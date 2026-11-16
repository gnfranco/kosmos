"""Brazilian unified case-number (CNJ) helpers.

Resolução CNJ 65/2008, art. 1º and Anexo VIII (ISO 7064 MOD 97-10).
These helpers validate identifiers, not court jurisdiction or case existence.
"""
import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

CNJ_PATTERN = re.compile(r"^[0-9][0-9.\-\s]*$")


def normalize_cnj(value: str) -> str:
    """Validate and format NNNNNNN-DD.AAAA.J.TR.OOOO.

    Digit verification follows the official sequence:
    98 - (NNNNNNNAAA AJTROOOO00 mod 97), with groups concatenated.
    """
    original = (value or "").strip()
    if not original:
        return ""
    if not CNJ_PATTERN.fullmatch(original):
        raise ValidationError(_("Enter a valid CNJ number with 20 digits."))

    digits = re.sub(r"[^0-9]", "", original)
    if len(digits) != 20:
        raise ValidationError(_("Enter a valid CNJ number with 20 digits."))

    sequence, check, year, jurisdiction, tribunal, origin = (
        digits[:7], digits[7:9], digits[9:13], digits[13:14],
        digits[14:16], digits[16:20]
    )
    if jurisdiction == "0":
        raise ValidationError(_("CNJ judicial segment must be between 1 and 9."))

    base = sequence + year + jurisdiction + tribunal + origin + "00"
    expected = 98 - (int(base) % 97)
    if int(check) != expected:
        raise ValidationError(_("Invalid CNJ check digits."))

    return (
        f"{sequence}-{check}.{year}.{jurisdiction}.{tribunal}.{origin}"
    )
