"""Proceeding form with an optional CNJ validator and BRL-only claim fields."""
import re
from decimal import Decimal, InvalidOperation

from django import forms
from django.utils import translation
from django.utils.translation import gettext_lazy as _

from apps.matters.proceedings.cnj import normalize_cnj
from apps.matters.proceedings.models import Proceeding
from config.helpers import YESNO_CHOICES
from config.settings import CustomFormRendererCompact


_BR_AMOUNT = re.compile(
    r"^(?:[0-9]+|[0-9]{1,3}(?:\.[0-9]{3})+)(?:,[0-9]{1,2})?$"
)
_BR_GROUPED_INTEGER = re.compile(r"^[0-9]{1,3}(?:\.[0-9]{3})+$")
_CANONICAL_DECIMAL = re.compile(r"^[0-9]+\.[0-9]{1,2}$")


class BRLAmountField(forms.DecimalField):
    """Parse pt-BR currency unambiguously, preserving amounts and cents."""

    def to_python(self, value):
        if not isinstance(value, str) or not (
            translation.get_language() or ""
        ).lower().startswith("pt"):
            return super().to_python(value)

        value = value.strip()
        if not value:
            return super().to_python(value)
        if "," in value:
            if not _BR_AMOUNT.fullmatch(value):
                raise forms.ValidationError(_("Enter a valid amount in BRL."))
            value = value.replace(".", "").replace(",", ".")
        elif _BR_GROUPED_INTEGER.fullmatch(value):
            value = value.replace(".", "")
        elif not (value.isascii() and value.isdigit()) and not _CANONICAL_DECIMAL.fullmatch(value):
            raise forms.ValidationError(_("Enter a valid amount in BRL."))
        try:
            # A Decimal bypasses Django's locale separator sanitizer, which
            # would otherwise interpret the single dot in 12.500 as decimal.
            return super().to_python(Decimal(value))
        except InvalidOperation:
            raise forms.ValidationError(_("Enter a valid amount in BRL."))


class ProceedingForm(forms.ModelForm):
    claim_amount_brl = BRLAmountField(
        required=False, min_value=0, max_digits=15, decimal_places=2,
        localize=True, label=_("Initial claim value (BRL)"),
        widget=forms.TextInput(attrs={"inputmode": "decimal"}),
    )
    claim_updated_brl = BRLAmountField(
        required=False, min_value=0, max_digits=15, decimal_places=2,
        localize=True, label=_("Updated claim value (BRL)"),
        widget=forms.TextInput(attrs={"inputmode": "decimal"}),
    )

    class Meta:
        model = Proceeding
        fields = (
            "numbering_scheme",
            "case_number",
            "date_filed",
            "case_class",
            "forum",
            "court_division",
            "nickname",
            "status",
            "primary",
            "claim_amount_brl",
            "claim_updated_brl",
            "date_final_judgment",
            "case_url",
        )

        STATUSES = Proceeding.STATUS_CHOICES

        widgets = {
            "forum": forms.TextInput(attrs={"onfocus": "moveFocusToEnd(this)"}),
            "nickname": forms.TextInput(
                attrs={"placeholder": _("Main, appeal, enforcement, etc.")}
            ),
            "status": forms.Select(choices=STATUSES),
            "date_filed": forms.DateInput(attrs={"type": "date"}),
            "date_final_judgment": forms.DateInput(attrs={"type": "date"}),
            "primary": forms.Select(choices=YESNO_CHOICES),
            "case_number": forms.TextInput(
                attrs={"placeholder": _("NNNNNNN-DD.AAAA.J.TR.OOOO")}
            ),
        }

        labels = {
            "numbering_scheme": _("Numbering scheme"),
            "case_number": _("Case number"),
            "date_filed": _("Date filed / distribution"),
            "case_class": _("Procedural class"),
            "forum": _("Court / tribunal"),
            "court_division": _("Judicial division (vara)"),
            "nickname": _("Short name"),
            "status": _("Status"),
            "primary": _("Primary proceeding"),
            "date_final_judgment": _("Final judgment date"),
            "case_url": _("Court case URL"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.renderer = CustomFormRendererCompact()
        # Older clients and automation scripts may still submit the pre-BR
        # proceeding form. Preserve the instance's numbering scheme and
        # Brazilian metadata when these fields are absent, not when the user
        # deliberately clears them in the new form.
        if self.is_bound and "numbering_scheme" not in self.data:
            data = self.data.copy()
            data["numbering_scheme"] = (
                self.instance.numbering_scheme or "OTHER"
            )
            if self.instance.pk:
                for field_name in (
                    "case_class", "court_division", "claim_amount_brl",
                    "claim_updated_brl", "date_final_judgment", "case_url",
                ):
                    if field_name not in data:
                        value = getattr(self.instance, field_name)
                        if value is not None:
                            data[field_name] = (
                                value.isoformat() if hasattr(value, "isoformat")
                                else str(value)
                            )
            self.data = data

    def clean_case_number(self):
        value = (self.cleaned_data.get("case_number") or "").strip()
        if self.cleaned_data.get("numbering_scheme") == "CNJ":
            if not value:
                raise forms.ValidationError(_("A CNJ number is required."))
            return normalize_cnj(value)
        return value
