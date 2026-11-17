"""Brazilian fee arrangements are contractual metadata, never invoices."""

from decimal import Decimal

import pytest
from django.utils import translation

from apps.matters.forms import MatterForm
from apps.matters.models import Matter

pytestmark = pytest.mark.django_db


def _posted_fields(**overrides):
    return {
        "name": "Ação de teste",
        "status": "Open",
        "date_start": "16/11/2026",
        "billing_type": "HOURLY",
        "fee_agreement_type": "SUCCESS",
        "fee_success_percentage": "25,50",
        "fee_success_basis": "Valores efetivamente recebidos pelo cliente",
        "fee_agreement_notes": "Cláusula contratual conferida pelo escritório.",
        **overrides,
    }


def test_success_fee_form_and_model_store_decimal_not_invoice():
    with translation.override("pt-br"):
        form = MatterForm(_posted_fields())
        assert form.is_valid(), form.errors.as_json()
        matter = form.save()

    matter.refresh_from_db()
    assert matter.fee_agreement_type == "SUCCESS"
    assert matter.fee_success_percentage == Decimal("25.50")
    assert matter.fee_success_basis.startswith("Valores efetivamente")
    assert matter.billing_type == "HOURLY"
    assert matter.flat_fee_amount is None
    assert matter.history.first().fee_success_percentage == Decimal("25.50")


def test_success_fee_requires_percentage_and_explicit_contractual_basis():
    with translation.override("pt-br"):
        missing = MatterForm(
            _posted_fields(fee_success_percentage="", fee_success_basis="")
        )
        assert not missing.is_valid()
        assert "fee_success_percentage" in missing.errors
        assert "fee_success_basis" in missing.errors
        too_high = MatterForm(_posted_fields(fee_success_percentage="105"))
        assert not too_high.is_valid()
        assert "fee_success_percentage" in too_high.errors


def test_mixed_fee_is_tracked_without_turning_into_flat_fee():
    with translation.override("pt-br"):
        form = MatterForm(
            _posted_fields(
                fee_agreement_type="MIXED",
                fee_fixed_amount="1500,00",
                fee_success_percentage="20,00",
                fee_agreement_notes="Entrada de R$ 1.500 mais êxito.",
            )
        )
        assert form.is_valid(), form.errors.as_json()
        matter = form.save()
    assert matter.fee_agreement_type == "MIXED"
    assert matter.fee_success_percentage == Decimal("20.00")
    assert matter.fee_fixed_amount == Decimal("1500.00")
    assert matter.billing_type == "HOURLY"


def test_non_success_mode_removes_stale_percent_and_basis():
    matter = Matter.objects.create(
        name="Contrato anterior",
        status="Open",
        fee_agreement_type="SUCCESS",
        fee_success_percentage=Decimal("30.00"),
        fee_success_basis="Quantia recuperada",
    )
    with translation.override("pt-br"):
        form = MatterForm(
            _posted_fields(
                fee_agreement_type="FIXED",
                fee_fixed_amount="3000,00",
                fee_success_percentage="30,00",
                fee_success_basis="Quantia recuperada",
            ),
            instance=matter,
        )
        assert form.is_valid(), form.errors.as_json()
        form.save()
    matter.refresh_from_db()
    assert matter.fee_agreement_type == "FIXED"
    assert matter.fee_fixed_amount == Decimal("3000.00")
    assert matter.fee_success_percentage is None
    assert matter.fee_success_basis == ""


def test_legacy_form_post_preserves_existing_contract():
    matter = Matter.objects.create(
        name="Caso antigo",
        status="Open",
        fee_agreement_type="SUCCESS",
        fee_success_percentage=Decimal("25.00"),
        fee_success_basis="Atrasados efetivamente recebidos",
    )
    with translation.override("pt-br"):
        payload = _posted_fields(name="Caso antigo atualizado")
        for name in MatterForm.CONTRACT_FIELDS:
            payload.pop(name, None)
        form = MatterForm(payload, instance=matter)
        assert form.is_valid(), form.errors.as_json()
        form.save()
    matter.refresh_from_db()
    assert matter.name == "Caso antigo atualizado"
    assert matter.fee_agreement_type == "SUCCESS"
    assert matter.fee_success_percentage == Decimal("25.00")
    assert matter.fee_success_basis == "Atrasados efetivamente recebidos"


def test_real_http_case_creation_stores_fee_terms(client):
    with translation.override("pt-br"):
        page = client.get("/matters/add")
        assert page.status_code == 200
        body = page.content.decode()
        assert "Honorários contratuais" in body
        assert "Honorários de êxito (percentual)" in body
        assert "Sobre o que incide o percentual?" in body
        assert "não emite cobranças nem calcula automaticamente" in body
        response = client.post("/matters/add", _posted_fields())
    assert response.status_code == 204
    matter = Matter.objects.get(name="Ação de teste")
    assert matter.fee_agreement_type == "SUCCESS"
    assert matter.fee_success_percentage == Decimal("25.50")
