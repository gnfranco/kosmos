from django import forms
from django.utils.translation import gettext_lazy as _

from apps.matters.models import PracticeArea
from config.settings import CustomFormRendererCompact


class PracticeAreaForm(forms.ModelForm):
    class Meta:
        model = PracticeArea
        fields = ["name", "is_active"]
        labels = {"name": _("Name"), "is_active": _("Active")}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.renderer = CustomFormRendererCompact()
