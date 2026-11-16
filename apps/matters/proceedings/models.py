from django.db import models
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords

from apps.matters.models import Matter
from utils.models import AuditMixin


class Proceeding(AuditMixin, models.Model):
    # `status` is a plain CharField; the form's choices come from here.
    STATUSES = ("Ongoing", "Concluded", "Stayed", "Dismissed")
    STATUS_CHOICES = tuple((status, _(status)) for status in STATUSES)
    NUMBERING_SCHEMES = (
        ("OTHER", _("Other / legacy number")),
        ("CNJ", _("CNJ (Brazil)")),
    )

    user = models.ForeignKey(
        "accounts.CustomUser", on_delete=models.SET_NULL, null=True, blank=True
    )
    matter = models.ForeignKey(Matter, on_delete=models.CASCADE, null=True)
    date_filed = models.DateField(null=True)
    forum = models.CharField(max_length=150, null=True)
    case_number = models.CharField(max_length=50, null=True, blank=True)
    numbering_scheme = models.CharField(
        max_length=8, choices=NUMBERING_SCHEMES, default="OTHER"
    )
    case_class = models.CharField(max_length=160, blank=True)
    court_division = models.CharField(max_length=160, blank=True)
    claim_amount_brl = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True
    )
    claim_updated_brl = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True
    )
    date_final_judgment = models.DateField(blank=True, null=True)
    case_url = models.URLField(max_length=500, blank=True)
    nickname = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(max_length=50, null=True)
    primary = models.BooleanField(default=False)
    history = HistoricalRecords()

    @property
    def status_label(self):
        return dict(self.STATUS_CHOICES).get(self.status, self.status)

    def __str__(self):
        return f"{self.case_number}"

    @property
    def display_name(self):
        """Return nickname if set, otherwise forum."""
        return self.nickname if self.nickname else self.forum

    class Meta:
        db_table = "app_proceeding"

    def save(self, *args, **kwargs):
        # If this is the primary proceeding, set all other proceedings to not primary
        if self.primary:
            Proceeding.objects.filter(matter=self.matter).exclude(pk=self.pk).update(
                primary=False
            )

        super().save(*args, **kwargs)
