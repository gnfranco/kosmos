import re
from decimal import Decimal

from django import forms
from django.db.models import Q
from django.utils.translation import (
    get_language,
    gettext_lazy as _,
)

from apps.calendar.widgets import CheckSelect
from apps.contacts.models import Contact
from config.helpers import YESNO_CHOICES
from config.settings import CustomFormRendererCompact

from .models import Group, Matter, PracticeArea


class ContactComboboxWidget(forms.Widget):
    """Typeahead combobox for choosing a contact. Renders a search input plus a
    hidden value input that carries the field's value on submit. Reuses
    static/js/combobox.js and the contact-search results partial
    (templates/matters/contacts/results.html, served by matters:client-search)."""

    template_name = "matters/widgets/contact_combobox.html"

    def id_for_label(self, id_):
        # The label points at the visible search input (the id combobox.js binds
        # to), not the hidden value input.
        return "assign-search-input"

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        selected_name = ""
        if value not in (None, ""):
            contact = Contact.objects.filter(pk=value).first()
            selected_name = contact.name if contact else ""
        context["widget"]["selected_name"] = selected_name
        return context


class BrazilianCurrencyField(forms.DecimalField):
    """Accept pt-BR grouped amounts without changing the stored Decimal.

    The default Django localized field accepts 2000,00; this also accepts
    2.000,00 while rejecting irregular thousands separators.
    """

    _grouped_brl = re.compile(r"^[+-]?\d{1,3}(?:\.\d{3})+,\d{1,2}$")

    def to_python(self, value):
        if (
            isinstance(value, str)
            and (get_language() or "").lower().replace("_", "-") == "pt-br"
            and self._grouped_brl.fullmatch(value.strip())
        ):
            value = value.replace(".", "")
        return super().to_python(value)


class MatterForm(forms.ModelForm):
    # Accept 25,50 in pt-BR without converting the stored Decimal to a
    # floating-point number. The value represents a contractual percentage.
    fee_success_percentage = forms.DecimalField(
        label=_("Success Fee Percentage (%)"),
        required=False,
        localize=True,
        max_digits=5,
        decimal_places=2,
        min_value=Decimal("0.01"),
        max_value=Decimal("100.00"),
        widget=forms.TextInput(attrs={"inputmode": "decimal"}),
    )

    fee_fixed_amount = BrazilianCurrencyField(
        label=_("Contractual Fixed Fee (BRL)"),
        required=False,
        localize=True,
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.01"),
        widget=forms.TextInput(attrs={"inputmode": "decimal"}),
    )
    fee_hourly_rate = BrazilianCurrencyField(
        label=_("Contractual Hourly Rate (BRL)"),
        required=False,
        localize=True,
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.01"),
        widget=forms.TextInput(attrs={"inputmode": "decimal"}),
    )

    CONTRACT_FIELDS = (
        "fee_agreement_type",
        "fee_fixed_amount",
        "fee_hourly_rate",
        "fee_success_percentage",
        "fee_success_basis",
        "fee_agreement_notes",
    )

    class Meta:
        model = Matter

        fields = (
            "client",
            "billing_contacts",
            "status",
            "date_start",
            "name",
            "practice_area",
            "description",
            "work_status",
            "jurisdiction",
            "billable",
            "billing_type",
            "deferred_fees",
            "flat_fee_amount",
            "fee_agreement_type",
            "fee_fixed_amount",
            "fee_hourly_rate",
            "fee_success_percentage",
            "fee_success_basis",
            "fee_agreement_notes",
        )

        STATUSES = Matter.STATUS_CHOICES

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "onfocus": "moveFocusToEnd(this)",
                    "class": "span2",
                }
            ),
            "description": forms.TextInput(
                attrs={
                    "class": "span3",
                }
            ),
            "work_status": forms.TextInput(
                attrs={
                    "class": "span2",
                }
            ),
            "status": forms.Select(
                choices=STATUSES,
            ),
            "client": ContactComboboxWidget(),
            # Ticked in a dropdown of check rows; the button reads the one
            # name, or how many are ticked
            "billing_contacts": CheckSelect(
                empty_label=_("None"), many_label=_("copied")
            ),
            "date_start": forms.DateInput(attrs={"type": "date"}),
            "jurisdiction": forms.TextInput(),
            "billable": forms.Select(
                choices=((True, _("Yes")), (False, _("No (Administrative)"))),
            ),
            "billing_type": forms.Select(
                attrs={"onchange": "toggleFlatFeeAmount()"},
            ),
            "flat_fee_amount": forms.NumberInput(
                attrs={"step": "0.01"},
            ),
            "deferred_fees": forms.Select(choices=YESNO_CHOICES),
            "fee_agreement_type": forms.Select(),
            "fee_success_basis": forms.TextInput(
                attrs={"class": "span3", "maxlength": 255}
            ),
            "fee_agreement_notes": forms.Textarea(attrs={"class": "span3", "rows": 2}),
        }

        labels = {
            "client": _("Client"),
            "status": _("Status"),
            "name": _("Matter Name"),
            "date_start": _("Open Date"),
            "description": _("Description"),
            "work_status": _("Work Status"),
            "jurisdiction": _("Jurisdiction"),
            "billable": _("Billable"),
            "clio_matter_id": _("Clio Matter"),
            "client_reference_id": _("Client Reference"),
            "practice_area": _("Practice Area"),
            "billing_contacts": _("Additional Billing Contacts"),
            "billing_type": _("Internal Billing Method"),
            "flat_fee_amount": _("Flat Fee Amount"),
            "deferred_fees": _("Deferred Fee Arrangement"),
            "fee_agreement_type": _("Contractual Fee Arrangement"),
            "fee_fixed_amount": _("Contractual Fixed Fee (BRL)"),
            "fee_hourly_rate": _("Contractual Hourly Rate (BRL)"),
            "fee_success_percentage": _("Success Fee Percentage (%)"),
            "fee_success_basis": _("What is the percentage applied to?"),
            "fee_agreement_notes": _("Payment Terms"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.renderer = CustomFormRendererCompact()

        # client is nullable on the model but not blank, so the form would force
        # it; relax it here so administrative matters with no client can save.
        # (name/description/work_status get their optionality from the model.)
        self.fields["client"].required = False

        # Any contact can be a matter's client (the typeahead searches all
        # contacts), so validate the submitted pk against the full set.
        self.fields["client"].queryset = Contact.objects.all()

        # The billing contacts (copied on the matter's invoices and payment
        # requests) are ticked from the matter's own Client group: the
        # people on the client's side with an email, other than the client,
        # who is already the To. Anyone already ticked stays on the list even
        # if they have since lost their email or moved group, so an unrelated
        # edit never unticks them. A new matter has no contacts yet, and a
        # matter with no one to choose has nothing to show, so the field
        # appears only once there is someone to pick.
        matter = self.instance if self.instance.pk else None
        candidates = Contact.objects.none()
        if matter:
            client_group = Group.objects.client_group()
            candidates = (
                Contact.objects.filter(
                    Q(relationship__matter=matter, relationship__group=client_group)
                    & ~Q(email__isnull=True)
                    & ~Q(email="")
                    | Q(billing_matters=matter)
                )
                .exclude(pk=matter.client_id)
                .distinct()
                .order_by("name")
            )
        if candidates.exists():
            self.fields["billing_contacts"].queryset = candidates
        else:
            del self.fields["billing_contacts"]

        # Validate server-side (as the add view already does) rather than via
        # the HTML5 `required` attribute. Otherwise the browser silently refuses
        # to submit the edit modal when a required field is empty or not
        # focusable, with no error shown to the user.
        self.use_required_attribute = False

        # Older clients may POST the historic form without these optional
        # fields. Never overwrite a contract in that situation.
        if self.is_bound and not any(
            name in self.data for name in self.CONTRACT_FIELDS
        ):
            for name in self.CONTRACT_FIELDS:
                self.fields.pop(name)

        # In the Brazilian form there is one contractual-fees editor.
        # Legacy US invoicing controls are intentionally not presented; their
        # existing persisted values remain untouched on every POST.
        self.is_brazilian = (get_language() or "").lower().replace("_", "-") == "pt-br"
        self.show_legacy_fee_notice = bool(
            self.is_brazilian
            and self.instance.pk
            and self.instance.flat_fee_amount is not None
        )
        old_basis = (self.instance.fee_success_basis or "").strip()
        self.needs_fee_basis_review = bool(
            self.is_brazilian
            and self.instance.pk
            and old_basis
            and old_basis.replace(" ", "").replace(",", "").replace(".", "").isdigit()
        )
        if self.is_brazilian:
            for name in (
                "billable",
                "billing_type",
                "deferred_fees",
                "flat_fee_amount",
            ):
                self.fields.pop(name, None)

        # Existing cases must remain editable when their historical category
        # was deactivated. New cases only offer active categories.
        current_area_id = self.instance.practice_area_id
        self.fields["practice_area"].queryset = PracticeArea.objects.filter(
            Q(is_active=True) | Q(pk=current_area_id)
        ).distinct()

        # The canonical status values stay on Matter; localize widget labels
        # rather than duplicating the allowed lifecycle in Form.Meta.
        status_labels = {
            "Pending": _("Pending"),
            "Open": _("Open"),
            "Complete": _("Complete"),
            "Closed": _("Closed"),
        }
        self.fields["status"].widget.choices = [
            (value, status_labels.get(value, label))
            for value, label in Matter.STATUS_CHOICES
        ]

        if "fee_agreement_type" in self.fields:
            self.fields["fee_agreement_type"].widget.attrs["onchange"] = (
                "toggleContractFeeFields()"
            )
            self.fields["fee_success_basis"].help_text = _(
                "Describe the contractual basis (e.g. amounts actually received), not just the claim value."
            )
            self.fields["fee_agreement_notes"].help_text = _(
                "Specify due dates, installments and other conditions in the signed contract."
            )
            if self.is_brazilian:
                self.fields["fee_success_percentage"].widget.attrs["placeholder"] = (
                    "25,00"
                )
                self.fields["fee_fixed_amount"].widget.attrs["placeholder"] = "2.000,00"
                self.fields["fee_hourly_rate"].widget.attrs["placeholder"] = "250,00"
                self.fields["fee_success_basis"].widget.attrs["placeholder"] = (
                    "Ex.: valores efetivamente recebidos pelo cliente"
                )

        # The US billing widgets remain available in non-Brazilian locales.
        if "billing_type" in self.fields:
            billing_labels = {"HOURLY": _("Hourly"), "FLAT_FEE": _("Flat Fee")}
            self.fields["billing_type"].choices = [
                (code, billing_labels.get(code, label))
                for code, label in self.fields["billing_type"].choices
            ]

        # A native type=date input displays in the browser's locale (often
        # MM/DD/YYYY on Android despite Django's pt-BR setting). Use an
        # explicit Brazilian text format for this form only, while accepting
        # ISO values from older clients and keeping a real DateField in DB.
        if (get_language() or "").lower().replace("_", "-") == "pt-br":
            date_field = self.fields["date_start"]
            date_field.widget = forms.DateInput(
                format="%d/%m/%Y",
                attrs={
                    "type": "text",
                    "inputmode": "numeric",
                    "placeholder": "DD/MM/AAAA",
                    "autocomplete": "off",
                },
            )
            date_field.input_formats = ["%d/%m/%Y", "%Y-%m-%d"]

    def clean(self):
        cleaned = super().clean()
        if "fee_agreement_type" not in self.fields:
            return cleaned

        arrangement = cleaned.get("fee_agreement_type", "UNSPECIFIED")
        if arrangement in ("SUCCESS", "MIXED"):
            if (
                cleaned.get("fee_success_percentage") is None
                and "fee_success_percentage" not in self.errors
            ):
                self.add_error(
                    "fee_success_percentage",
                    _("Enter the success fee percentage agreed in the contract."),
                )
            if not (cleaned.get("fee_success_basis") or "").strip():
                self.add_error(
                    "fee_success_basis",
                    _("Describe precisely the contractual basis for the percentage."),
                )
        else:
            # Clear values no longer applicable to the selected agreement.
            cleaned["fee_success_percentage"] = None
            cleaned["fee_success_basis"] = ""

        if "fee_fixed_amount" in self.fields:
            if arrangement in ("FIXED", "MIXED"):
                historical_empty = (
                    self.instance.pk
                    and self.instance.fee_agreement_type == arrangement
                    and self.instance.fee_fixed_amount is None
                )
                if (
                    cleaned.get("fee_fixed_amount") is None
                    and not historical_empty
                    and "fee_fixed_amount" not in self.errors
                ):
                    self.add_error(
                        "fee_fixed_amount",
                        _("Enter the fixed amount agreed in the contract."),
                    )
            else:
                cleaned["fee_fixed_amount"] = None

        if "fee_hourly_rate" in self.fields:
            if arrangement == "HOURLY":
                historical_empty = (
                    self.instance.pk
                    and self.instance.fee_agreement_type == arrangement
                    and self.instance.fee_hourly_rate is None
                )
                if (
                    cleaned.get("fee_hourly_rate") is None
                    and not historical_empty
                    and "fee_hourly_rate" not in self.errors
                ):
                    self.add_error(
                        "fee_hourly_rate",
                        _("Enter the contractual hourly rate."),
                    )
            else:
                cleaned["fee_hourly_rate"] = None

        return cleaned
