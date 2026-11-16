"""Brazilian Lex case forms and configurable practice areas."""
from datetime import date

import pytest
from django.core.management import call_command
from django.test import override_settings
from django.urls import reverse
from django.utils import translation

from apps.matters.forms import MatterForm
from apps.matters.models import Matter, PracticeArea
from apps.matters.management.commands.seed_br_practice_areas import BR_AREAS

pytestmark = pytest.mark.django_db


@override_settings(LANGUAGE_CODE="pt-br")
def test_seed_is_idempotent_and_legacy_data_is_retained():
    legacy = PracticeArea.objects.filter(name="General").first()
    if not legacy:
        legacy = PracticeArea.objects.create(name="General", is_active=True)
    legacy.is_active = True
    legacy.save(update_fields=["is_active"])
    case = Matter.objects.create(
        name="Teste legado", status="Open", practice_area=legacy,
    )
    unused = PracticeArea.objects.filter(name="Boundary").first()
    if not unused:
        unused = PracticeArea.objects.create(name="Boundary", is_active=True)
    unused.is_active = True
    unused.save(update_fields=["is_active"])
    custom = PracticeArea.objects.create(name="Especialidade própria", is_active=True)

    call_command("seed_br_practice_areas", deactivate_unused_legacy=True)
    assert all(PracticeArea.objects.filter(name=name, is_active=True).exists() for name in BR_AREAS)
    assert PracticeArea.objects.filter(name="General", is_active=True).exists()
    unused.refresh_from_db()
    assert unused.is_active is False
    assert PracticeArea.objects.filter(pk=custom.pk, is_active=True).exists()
    assert Matter.objects.get(pk=case.pk).practice_area_id == legacy.pk

    count = PracticeArea.objects.count()
    call_command("seed_br_practice_areas", deactivate_unused_legacy=True)
    assert PracticeArea.objects.count() == count


@override_settings(LANGUAGE_CODE="pt-br")
def test_seed_dry_run_does_not_change_data():
    before = {name: tuple(PracticeArea.objects.filter(name=name).values_list("id", flat=True))
              for name in BR_AREAS}
    call_command("seed_br_practice_areas", deactivate_unused_legacy=True, dry_run=True)
    after = {name: tuple(PracticeArea.objects.filter(name=name).values_list("id", flat=True))
             for name in BR_AREAS}
    assert before == after


def test_case_fields_and_status_render_in_portuguese():
    with translation.override("pt-br"):
        form = MatterForm()
        assert str(form.fields["name"].label) == "Nome do caso"
        assert str(form.fields["status"].label) == "Situação"
        assert str(form.fields["date_start"].label) == "Data de abertura"
        assert str(form.fields["practice_area"].label) == "Área de atuação"
        choices = list(form.fields["status"].widget.choices)
        assert ("Pending", "Pendente") in [(val, str(text)) for val, text in choices]
        html = str(form["date_start"])
        assert 'type="text"' in html
        assert 'placeholder="DD/MM/AAAA"' in html
        assert form.fields["date_start"].clean("16/11/2026") == date(2026, 11, 16)
        assert form.fields["date_start"].clean("2026-11-16") == date(2026, 11, 16)


def test_case_date_edits_render_day_first():
    with translation.override("pt-br"):
        instance = Matter(name="Caso", date_start=date(2026, 11, 16))
        form = MatterForm(instance=instance)
        assert 'value="16/11/2026"' in str(form["date_start"])


def test_inactive_area_remains_eligible_when_editing_existing_case():
    area = PracticeArea.objects.create(name="Classificação arquivada", is_active=False)
    matter = Matter.objects.create(name="Caso anterior", practice_area=area)
    assert area in MatterForm(instance=matter).fields["practice_area"].queryset
    assert area not in MatterForm().fields["practice_area"].queryset


def test_settings_can_edit_area_without_deleting_referenced_case(admin_client):
    area = PracticeArea.objects.create(name="Direito Trabalhista QA")
    matter = Matter.objects.create(name="Reclamação teste", practice_area=area)
    url = reverse("settings:delete-practice-area", args=[area.pk])
    response = admin_client.post(url)
    assert response.status_code == 409
    assert Matter.objects.get(pk=matter.pk).practice_area_id == area.pk
    assert PracticeArea.objects.filter(pk=area.pk).exists()
    edit_url = reverse("settings:edit-practice-area", args=[area.pk])
    response = admin_client.post(edit_url, data={"name": area.name, "is_active": ""})
    assert response.status_code == 204
    area.refresh_from_db()
    assert not area.is_active


def test_non_admin_cannot_change_practice_areas(client):
    area = PracticeArea.objects.create(name="Confidencial")
    assert client.post(reverse("settings:delete-practice-area", args=[area.pk])).status_code == 403
    assert client.post(reverse("settings:edit-practice-area", args=[area.pk]), data={"name": "Alterado"}).status_code == 403
    assert client.post(reverse("settings:add-practice-area"), data={"name": "Inadequado"}).status_code == 403
    assert PracticeArea.objects.get(pk=area.pk).name == "Confidencial"
