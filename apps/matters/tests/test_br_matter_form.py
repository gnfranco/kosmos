"""Brazilian form localization must not change stored matter codes or FKs."""

from datetime import date

import pytest
from django.utils import translation

from apps.matters.forms import MatterForm
from apps.matters.models import Matter, PracticeArea

pytestmark = pytest.mark.django_db


def test_brazilian_practice_area_seed_keeps_legacy_rows():
    assert PracticeArea.objects.filter(name="Direito Trabalhista").exists()
    assert PracticeArea.objects.filter(name="Direito Previdenciário").exists()
    assert PracticeArea.objects.filter(name="Outras áreas").exists()
    assert PracticeArea.objects.filter(name="General").exists()


def test_brazilian_labels_and_iso_compatible_date_input(practice_area):
    with translation.override("pt-br"):
        form = MatterForm(initial={"date_start": date(2026, 11, 16)})
        assert str(form.fields["name"].label) == "Nome do caso"
        assert str(form.fields["client"].label) == "Cliente"
        assert str(form.fields["status"].label) == "Situação"
        assert str(form.fields["work_status"].label) == "Situação do trabalho"
        assert 'value="16/11/2026"' in str(form["date_start"])
        assert 'placeholder="DD/MM/AAAA"' in str(form["date_start"])
        assert "Pendente" in str(form["status"])

        base_data = {
            "name": "Atendimento de teste",
            "status": "Pending",
            "practice_area": str(practice_area.pk),
            "billing_type": "HOURLY",
            "billable": "True",
            "deferred_fees": "False",
        }
        for text_date in ("16/11/2026", "2026-11-16"):
            posted = MatterForm({**base_data, "date_start": text_date})
            assert posted.is_valid(), posted.errors
            assert posted.cleaned_data["date_start"] == date(2026, 11, 16)
            matter = posted.save()
            assert matter.status == "Pending"
            assert matter.date_start == date(2026, 11, 16)


def test_inactive_legacy_category_remains_selectable_on_edit(practice_area):
    matter = Matter.objects.create(
        name="Caso legado", status="Open", practice_area=practice_area
    )
    practice_area.is_active = False
    practice_area.save()

    with translation.override("pt-br"):
        new_form = MatterForm()
        edit_form = MatterForm(instance=matter)
        assert practice_area not in new_form.fields["practice_area"].queryset
        assert practice_area in edit_form.fields["practice_area"].queryset


def test_brazilian_modal_renders_localized_fields_and_actions(client, folder):
    with translation.override("pt-br"):
        response = client.get("/matters/add")
    assert response.status_code == 200
    body = response.content.decode()
    assert "Adicionar caso" in body
    assert "Nome do caso" in body
    assert "Data de abertura" in body
    assert "DD/MM/AAAA" in body
    assert "Salvar" in body
    assert 'class="modal-dialog modal-lg matter-modal"' in body
