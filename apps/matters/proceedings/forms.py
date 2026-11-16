from django import forms
from django.utils.translation import gettext_lazy as _

from apps.matters.proceedings.cnj import normalize_cnj
from apps.matters.proceedings.models import Proceeding
from config.helpers import YESNO_CHOICES
from config.settings import CustomFormRendererCompact


class ProceedingForm(forms.ModelForm):
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
            "claim_amount_brl": _("Initial claim value (BRL)"),
            "claim_updated_brl": _("Updated claim value (BRL)"),
            "date_final_judgment": _("Final judgment date"),
            "case_url": _("Court case URL"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.renderer = CustomFormRendererCompact()
        for name in ("claim_amount_brl", "claim_updated_brl"):
            self.fields[name].localize = True
            self.fields[name].widget.is_localized = True

    def clean_case_number(self):
        value = (self.cleaned_data.get("case_number") or "").strip()
        if self.cleaned_data.get("numbering_scheme") == "CNJ":
            return normalize_cnj(value)
        return value
