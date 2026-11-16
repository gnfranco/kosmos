from django import forms
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from apps.calendar.widgets import CheckSelect
from apps.contacts.models import Contact
from config.helpers import YESNO_CHOICES
from config.settings import CustomFormRendererCompact

from .models import Group, Matter, PracticeArea


class ContactComboboxWidget(forms.Widget):
    """Search/selection widget; keeps the canonical client id in a hidden input."""

    template_name = "matters/widgets/contact_combobox.html"

    def id_for_label(self, id_):
        return "assign-search-input"

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        selected_name = ""
        if value not in (None, ""):
            contact = Contact.objects.filter(pk=value).first()
            selected_name = contact.name if contact else ""
        context["widget"]["selected_name"] = selected_name
        return context


class MatterForm(forms.ModelForm):
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
        )

        STATUSES = Matter.STATUS_CHOICES

        widgets = {
            "name": forms.TextInput(attrs={
                "onfocus": "moveFocusToEnd(this)", "class": "span2",
            }),
            "description": forms.TextInput(attrs={"class": "span3"}),
            "work_status": forms.TextInput(attrs={"class": "span2"}),
            "status": forms.Select(choices=STATUSES),
            "client": ContactComboboxWidget(),
            "billing_contacts": CheckSelect(
                empty_label=_("None"), many_label=_("copied"),
            ),
            # A native date picker takes its visible order from the device/
            # browser (it showed MM/DD/YYYY on Android even with lang=pt-br).
            # Use explicit DD/MM/YYYY for this Lex case form while accepting
            # ISO dates from existing integrations on POST.
            "date_start": forms.DateInput(
                format="%d/%m/%Y",
                attrs={
                    "type": "text",
                    "placeholder": "DD/MM/AAAA",
                    "inputmode": "numeric",
                    "maxlength": "10",
                    "autocomplete": "off",
                },
            ),
            "jurisdiction": forms.TextInput(),
            "billable": forms.Select(
                choices=((True, _("Yes")), (False, _("No (Administrative)"))),
            ),
            "billing_type": forms.Select(
                attrs={"onchange": "toggleFlatFeeAmount()"},
            ),
            "flat_fee_amount": forms.NumberInput(attrs={"step": "0.01"}),
            "deferred_fees": forms.Select(choices=YESNO_CHOICES),
        }

        labels = {
            "client": _("Client"),
            "name": _("Matter Name"),
            "status": _("Status"),
            "date_start": _("Open Date"),
            "description": _("Description"),
            "work_status": _("Work status"),
            "jurisdiction": _("Jurisdiction"),
            "practice_area": _("Practice Area"),
            "billing_contacts": _("Additional Billing Contacts"),
            "billable": _("Billable"),
            "billing_type": _("Billing Type"),
            "flat_fee_amount": _("Flat Fee Amount"),
            "deferred_fees": _("Deferred Fee Arrangement"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.renderer = CustomFormRendererCompact()

        # Keep the stored status and billing_type codes in English for
        # compatibility with business logic, filtering and upstream merges.
        self.fields["status"].widget.choices = [
            (code, _(code)) for code in Matter.STATUSES
        ]
        self.fields["billing_type"].choices = [
            ("HOURLY", _("Hourly")),
            ("FLAT_FEE", _("Flat Fee")),
        ]
        self.fields["date_start"].input_formats = ("%d/%m/%Y", "%Y-%m-%d")
        self.fields["date_start"].help_text = _("Use DD/MM/YYYY (day/month/year).")

        # Client is nullable but not blank in the model; administrative cases
        # without a client must remain valid.
        self.fields["client"].required = False
        self.fields["client"].queryset = Contact.objects.all()

        # Billing contacts come from the matter's Client group, keeping any
        # previously selected contacts to avoid dropping them on unrelated edits.
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

        # Server-side validation lets the UI show actual error messages.
        self.use_required_attribute = False

        # Keep inactive practice areas visible on existing cases, so an edit
        # does not accidentally erase a previously valid classification.
        areas = PracticeArea.objects.filter(is_active=True)
        if matter and matter.practice_area_id:
            areas = PracticeArea.objects.filter(
                Q(is_active=True) | Q(pk=matter.practice_area_id)
            )
        self.fields["practice_area"].queryset = areas.order_by("name")
