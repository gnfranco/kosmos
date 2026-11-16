"""Opt-in Brazilian cleanup must never remove existing legal classifications."""
import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings
from django.utils import translation

from apps.intakes.models import Intake
from apps.matters.forms import MatterForm
from apps.matters.management.commands.seed_br_practice_areas import BR_AREAS
from apps.matters.models import Matter, PracticeArea

pytestmark = pytest.mark.django_db


@override_settings(LANGUAGE_CODE="pt-br")
def test_cleanup_is_idempotent_and_preserves_legacy_references():
    used = PracticeArea.objects.get(name="General")
    used.is_active = True
    used.save(update_fields=["is_active"])
    case = Matter.objects.create(
        name="Processo legado", practice_area=used, status="Open",
    )
    unused = PracticeArea.objects.get(name="Boundary")
    unused.is_active = True
    unused.save(update_fields=["is_active"])
    intake_area = PracticeArea.objects.get(name="HOA")
    intake_area.is_active = True
    intake_area.save(update_fields=["is_active"])
    intake = Intake.objects.create(name="Triagem anterior", practice_area=intake_area)
    custom = PracticeArea.objects.create(name="Minha área personalizada", is_active=True)

    call_command("seed_br_practice_areas", deactivate_unused_legacy=True)
    assert all(PracticeArea.objects.filter(name=name, is_active=True).exists() for name in BR_AREAS)
    unused.refresh_from_db()
    assert unused.is_active is False
    assert PracticeArea.objects.filter(pk=used.pk, is_active=True).exists()
    assert PracticeArea.objects.filter(pk=intake_area.pk, is_active=True).exists()
    assert PracticeArea.objects.filter(pk=custom.pk, is_active=True).exists()
    assert Matter.objects.get(pk=case.pk).practice_area_id == used.pk
    assert Intake.objects.get(pk=intake.pk).practice_area_id == intake_area.pk

    count = PracticeArea.objects.count()
    call_command("seed_br_practice_areas", deactivate_unused_legacy=True)
    assert PracticeArea.objects.count() == count
    assert unused.pk == PracticeArea.objects.get(pk=unused.pk).pk

    # New cases hide inactive areas, while existing cases keep their links.
    with translation.override("pt-br"):
        assert unused not in MatterForm().fields["practice_area"].queryset
        assert used in MatterForm(instance=case).fields["practice_area"].queryset


@override_settings(LANGUAGE_CODE="pt-br")
def test_dry_run_leaves_all_categories_unchanged():
    before = list(PracticeArea.objects.values_list("pk", "name", "is_active"))
    call_command(
        "seed_br_practice_areas", deactivate_unused_legacy=True, dry_run=True,
    )
    assert before == list(PracticeArea.objects.values_list("pk", "name", "is_active"))


@override_settings(LANGUAGE_CODE="en-us")
def test_cleanup_refuses_non_brazilian_deployment():
    with pytest.raises(CommandError):
        call_command("seed_br_practice_areas", deactivate_unused_legacy=True)


def test_client_lookup_widget_is_translated_in_pt_br():
    with translation.override("pt-br"):
        html = str(MatterForm()["client"])
    assert "Buscar contatos..." in html
    assert "Limpar seleção" in html
