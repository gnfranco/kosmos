from django import template

register = template.Library()


@register.filter("phone_number")
def phone_number(value, person_type=None):
    """Format Brazilian typed contacts with DDD, preserving US legacy mode."""
    if not value:
        return value

    # Handle extension
    extension = ""
    if "x" in value.lower():
        idx = value.lower().index("x")
        ext_digits = "".join(c for c in value[idx:] if c.isdigit())
        if ext_digits:
            extension = " x " + ext_digits
        value = value[:idx]

    # Strip any non-digits (for legacy data)
    digits = "".join(c for c in value if c.isdigit())

    if person_type in ("PF", "PJ") and len(digits) in (10, 11):
        return f"({digits[:2]}) {digits[2:-4]}-{digits[-4:]}" + extension

    if len(digits) == 10:
        formatted = f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        return formatted + extension

    return value + extension


@register.filter("phone_tel")
def phone_tel(value, person_type=None):
    """Format telephone link for BR identity, preserving US legacy links."""
    if not value:
        return ""

    # Strip extension for tel: link (base number only)
    if "x" in value.lower():
        idx = value.lower().index("x")
        value = value[:idx]

    # Strip all non-digits
    digits = "".join(c for c in value if c.isdigit())

    if person_type in ("PF", "PJ") and len(digits) in (10, 11):
        return f"+55{digits}"

    # Handle 10-digit US numbers
    if len(digits) == 10:
        return f"+1{digits}"
    # Handle 11-digit numbers starting with 1
    elif len(digits) == 11 and digits.startswith("1"):
        return f"+{digits}"

    # Fallback: return digits only
    return digits if digits else value


@register.filter("zillow_address")
def zillow_address(address):
    """Format address for Zillow URL - replace spaces and newlines with dashes."""
    if address:
        # Replace newlines and multiple spaces with single space first
        formatted = " ".join(address.split())
        # Replace spaces with dashes
        return formatted.replace(" ", "-")
    return ""
