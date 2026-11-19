import re

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import (
    get_language,
    gettext_lazy as _,
)

from config.helpers import normalize_phone
from config.settings import CustomFormRendererCompact

from .br_documents import (
    is_valid_cnpj,
    is_valid_cpf,
    normalize_br_phone,
    normalize_document,
)
from .models import Contact


class ContactForm(forms.ModelForm):
    # The displayed tax ID may be masked (18 chars), while the normalized
    # model column stores exactly 11 or 14 characters.
    tax_id = forms.CharField(
        label=_("CPF or CNPJ"),
        max_length=24,
        required=False,
        widget=forms.TextInput(attrs={"class": "span2", "autocomplete": "off"}),
    )

    class Meta:
        model = Contact

        fields = (
            "folder",
            "name",
            "person_type",
            "tax_id",
            "trade_name",
            "company",
            "email",
            "email2",
            "address",
            "phone1",
            "phone1_label",
            "phone2",
            "phone2_label",
            "phone3",
            "phone3_label",
            "website",
            "notes",
        )

        PHONE_LABELS = (
            ("Mobile", "Mobile"),
            ("Home", "Home"),
            ("Work", "Work"),
            ("Fax", "Fax"),
            ("Other", "Other"),
        )

        widgets = {
            "folder": forms.Select(attrs={"class": "span2"}),
            "person_type": forms.Select(attrs={"class": "span2"}),
            "tax_id": forms.TextInput(attrs={"class": "span2", "autocomplete": "off"}),
            "trade_name": forms.TextInput(attrs={"class": "span2"}),
            "name": forms.TextInput(
                attrs={
                    "onfocus": "moveFocusToEnd(this)",
                    "class": "span2",
                }
            ),
            "company": forms.TextInput(attrs={"class": "span2"}),
            "email": forms.TextInput(attrs={"class": "span2"}),
            "email2": forms.TextInput(attrs={"class": "span2"}),
            "website": forms.URLInput(attrs={"class": "span2"}),
            "address": forms.Textarea(attrs={"class": "span2", "rows": "3"}),
            "notes": forms.Textarea(attrs={"class": "span2", "rows": "7"}),
            "phone1_label": forms.Select(choices=PHONE_LABELS),
            "phone2_label": forms.Select(choices=PHONE_LABELS),
            "phone3_label": forms.Select(choices=PHONE_LABELS),
        }

        labels = {
            "person_type": _("Person Type"),
            "tax_id": _("CPF or CNPJ"),
            "trade_name": _("Trade Name"),
            "phone1": "Phone 1",
            "phone2": "Phone 2",
            "phone3": "Phone 3",
            "phone1_label": "For",
            "phone2_label": "For",
            "phone3_label": "For",
            "email2": "Email 2",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.renderer = CustomFormRendererCompact()
        self.is_brazilian = (get_language() or "").lower().replace("_", "-") == "pt-br"
        self.BR_FIELDS = ("person_type", "tax_id", "trade_name")
        # Legacy UIs and import forms never sent these new fields. An edit
        # through such a client must not clear an already stored tax ID.
        if not self.is_brazilian or (
            self.is_bound and not any(key in self.data for key in self.BR_FIELDS)
        ):
            for key in self.BR_FIELDS:
                self.fields.pop(key, None)
        else:
            self.fields["person_type"].choices = (
                ("UNSPECIFIED", _("Not specified")),
                ("PF", _("Individual (CPF)")),
                ("PJ", _("Legal entity (CNPJ)")),
            )
            for name, label in {
                "name": _("Name or Legal Name"),
                "company": _("Company / Affiliation"),
                "phone1": _("Telephone 1"),
                "phone2": _("Telephone 2"),
                "phone3": _("Telephone 3"),
                "address": _("Address"),
            }.items():
                self.fields[name].label = label

    def clean_tax_id(self):
        text = self.cleaned_data.get("tax_id") or ""
        try:
            return normalize_document(text)
        except ValueError as error:
            raise ValidationError(_("Enter a valid CPF/CNPJ format.")) from error

    def clean(self):
        cleaned = super().clean()
        if "person_type" not in self.fields:
            return cleaned
        kind = cleaned.get("person_type") or "UNSPECIFIED"
        identifier = cleaned.get("tax_id") or ""
        if identifier:
            if kind == "PF" and not is_valid_cpf(identifier):
                self.add_error("tax_id", _("CPF has invalid check digits."))
            elif kind == "PJ" and not is_valid_cnpj(identifier):
                self.add_error("tax_id", _("CNPJ has invalid check digits."))
            elif kind not in ("PF", "PJ"):
                self.add_error(
                    "person_type", _("Select individual or legal entity for CPF/CNPJ.")
                )
        if kind != "PJ":
            cleaned["trade_name"] = ""
        return cleaned

    def _clean_phone(self, value):
        if not value:
            return value
        if self.is_brazilian:
            try:
                return normalize_br_phone(value)
            except ValueError as error:
                raise ValidationError(
                    _("Enter a Brazilian telephone with DDD (10 or 11 digits).")
                ) from error
        normalized, is_valid = normalize_phone(value)
        if not is_valid:
            raise ValidationError("Enter a valid 10-digit US phone number.")
        return normalized

    def clean_name(self):
        name = self.cleaned_data["name"]
        if len(name) < 2:
            raise ValidationError("Name must be at least 2 characters.")
        if self.is_brazilian:
            if len(name) > 100:
                raise ValidationError(
                    _("Name or legal name must be 100 characters or fewer.")
                )
        elif len(name) > 50:
            raise ValidationError("Name must be 50 characters or fewer.")
        return name

    def clean_company(self):
        company = self.cleaned_data["company"]
        if company:
            if len(company) >= 50:
                raise ValidationError("Company must be fewer than 50 characters.")
        return company

    def clean_address(self):
        address = self.cleaned_data["address"]
        if address:
            if len(address) > 250:
                raise ValidationError("Address must be 250 characters or fewer.")
        return address

    def clean_phone1(self):
        return self._clean_phone(self.cleaned_data.get("phone1"))

    def clean_phone2(self):
        return self._clean_phone(self.cleaned_data.get("phone2"))

    def clean_phone3(self):
        return self._clean_phone(self.cleaned_data.get("phone3"))

    def clean_website(self):
        website = self.cleaned_data.get("website")
        if website:
            # Ensure website has a scheme
            if not website.startswith(("http://", "https://")):
                website = "https://" + website
            # Basic URL validation
            url_pattern = re.compile(
                r"^https?://"
                r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"
                r"localhost|"
                r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
                r"(?::\d+)?"
                r"(?:/?|[/?]\S+)$",
                re.IGNORECASE,
            )
            if not url_pattern.match(website):
                raise ValidationError("Enter a valid URL.")
            if len(website) > 255:
                raise ValidationError("Website URL must be 255 characters or fewer.")
        return website

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email:
            return email.lower()
        return email

    def clean_email2(self):
        email = self.cleaned_data.get("email2")
        if email:
            return email.lower()
        return email

    def clean_notes(self):
        notes = self.cleaned_data["notes"]
        if notes:
            if len(notes) >= 250:
                raise ValidationError("Notes must be fewer than 250 characters.")
        return notes
