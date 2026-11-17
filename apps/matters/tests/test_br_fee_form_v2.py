"""Brazilian contractual fees, distinct from Kosmos' US billing engine."""

from decimal import Decimal

import pytest
from django.utils import translation

from apps.matters.forms import MatterForm
from apps.matters.models import Matter

pytestmark = pytest.mark.django_db


def posted(**overrides):
    return {
        "name": "Caso ilustrativo",
        "status": "Open",
        "date_start": "17/11/2026",
        "fee_agreement_type": "MIXED",
        "fee_fixed_amount": "2.000,00",
        "fee_success_percentage": "30,00",
        "fee_success_basis": "Valores efetivamente recebidos pelo cliente",
        "fee_agreement_notes": "Parcela fixa na contratação e êxito no recebimento.",
        **overrides,
    }


def test_br_contract_has_single_visible_fee_editor_and_creates_decimals():
    with translation.override("pt-br"):
        form = MatterForm(posted())
        assert "billing_type" not in form.fields
        assert "flat_fee_amount" not in form.fields
        assert "deferred_fees" not in form.fields
        assert "billable" not in form.fields
        assert form.is_valid(), form.errors.as_json()
        matter = form.save()
    assert matter.fee_fixed_amount == Decimal("2000.00")
    assert matter.fee_success_percentage == Decimal("30.00")
    assert matter.fee_agreement_type == "MIXED"
    assert matter.fee_success_basis == "Valores efetivamente recebidos pelo cliente"
    assert matter.flat_fee_amount is None
    assert matter.billing_type == "HOURLY"  # unchanged internal default
    assert matter.history.first().fee_fixed_amount == Decimal("2000.00")


def test_existing_legacy_billing_values_preserved_and_shown_as_review_only(client):
    matter = Matter.objects.create(
        name="Contrato em revisão",
        status="Open",
        billing_type="FLAT_FEE",
        flat_fee_amount=Decimal("2000.00"),
        billable=False,
        deferred_fees=True,
        fee_agreement_type="MIXED",
        fee_success_percentage=Decimal("30.00"),
        fee_success_basis="1800000",  # entered before the clearer UI existed
    )
    with translation.override("pt-br"):
        form = MatterForm(instance=matter)
        assert form.show_legacy_fee_notice
        assert form.needs_fee_basis_review
        assert form.fields["fee_fixed_amount"].initial is None
        updated = MatterForm(posted(name="Contrato em revisão"), instance=matter)
        assert updated.is_valid(), updated.errors.as_json()
        updated.save()
    matter.refresh_from_db()
    assert matter.billing_type == "FLAT_FEE"
    assert matter.flat_fee_amount == Decimal("2000.00")
    assert matter.deferred_fees is True
    assert matter.billable is False
    assert matter.fee_fixed_amount == Decimal("2000.00")
    assert matter.fee_success_basis == "Valores efetivamente recebidos pelo cliente"


def test_separate_fixed_hourly_and_success_validation():
    with translation.override("pt-br"):
        for mode in ("FIXED", "MIXED"):
            form = MatterForm(posted(fee_agreement_type=mode, fee_fixed_amount=""))
            assert not form.is_valid()
            assert "fee_fixed_amount" in form.errors
        hourly = MatterForm(
            posted(fee_agreement_type="HOURLY", fee_hourly_rate="250,50")
        )
        assert hourly.is_valid(), hourly.errors.as_json()
        item = hourly.save()
    assert item.fee_hourly_rate == Decimal("250.50")
    assert item.fee_fixed_amount is None
    assert item.fee_success_percentage is None
    assert item.fee_success_basis == ""


def test_empty_or_invalid_hourly_rate_is_rejected():
    with translation.override("pt-br"):
        for value in ("", "-1", "0"):
            f = MatterForm(posted(fee_agreement_type="HOURLY", fee_hourly_rate=value))
            assert not f.is_valid()
            assert "fee_hourly_rate" in f.errors


def test_changing_to_success_clears_fixed_but_keeps_legacy_billing():
    matter = Matter.objects.create(
        name="Anterior",
        status="Open",
        fee_agreement_type="MIXED",
        fee_fixed_amount=Decimal("4000"),
        fee_success_percentage=Decimal("30"),
        fee_success_basis="Pagamento do cliente",
        flat_fee_amount=Decimal("9000"),
    )
    with translation.override("pt-br"):
        form = MatterForm(
            posted(fee_agreement_type="SUCCESS", fee_fixed_amount="4000"),
            instance=matter,
        )
        assert form.is_valid(), form.errors.as_json()
        form.save()
    matter.refresh_from_db()
    assert matter.fee_fixed_amount is None
    assert matter.flat_fee_amount == Decimal("9000")
    assert matter.fee_success_percentage == Decimal("30.00")


def test_legacy_post_without_contract_fields_does_not_erase_fixed_fee():
    matter = Matter.objects.create(
        name="Casos antigos",
        status="Open",
        fee_agreement_type="MIXED",
        fee_fixed_amount=Decimal("3500"),
        fee_success_percentage=Decimal("20"),
        fee_success_basis="Verbas pagas",
    )
    payload = posted(name="Casos antigos editados")
    for field in MatterForm.CONTRACT_FIELDS:
        payload.pop(field, None)
    with translation.override("pt-br"):
        form = MatterForm(payload, instance=matter)
        assert form.is_valid(), form.errors.as_json()
        form.save()
    matter.refresh_from_db()
    assert matter.fee_fixed_amount == Decimal("3500")
    assert matter.fee_success_percentage == Decimal("20")
    assert matter.name == "Casos antigos editados"


def test_ptbr_modal_describes_terms_and_legacy_notice(client):
    matter = Matter.objects.create(
        name="Caso com legado",
        status="Open",
        flat_fee_amount=Decimal("2000"),
        fee_agreement_type="MIXED",
        fee_success_percentage=Decimal("30"),
        fee_success_basis="1800000",
    )
    with translation.override("pt-br"):
        page = client.get("/matters/add")
        assert page.status_code == 200
        body = page.content.decode()
        assert "Parcela fixa contratada" in body
        assert "Sobre o que incide o percentual?" in body
        assert "Condições de pagamento" in body
        assert "Valor dos honorários fixos" not in body
        assert "Faturamento interno (modelo atual)" not in body
        assert "id_fee_fixed_amount" in body
        assert "id_fee_hourly_rate" in body
        form = MatterForm(instance=matter)
        assert form.needs_fee_basis_review
        assert form.show_legacy_fee_notice


def test_en_us_preserves_existing_invoicing_fields():
    with translation.override("en-us"):
        form = MatterForm()
        assert "billing_type" in form.fields
        assert "flat_fee_amount" in form.fields
        assert "deferred_fees" in form.fields
        assert "billable" in form.fields


def test_http_create_edit_and_reopen_contract_on_desktop(client):
    """The actual Django modal round-trip must mirror the pilot workflow."""
    with translation.override("pt-br"):
        created = client.post("/matters/add", posted())
        assert created.status_code == 204
        matter = Matter.objects.get(name="Caso ilustrativo")

        reopened = client.get(f"/matters/{matter.pk}/edit")
        assert reopened.status_code == 200
        content = reopened.content.decode()
        assert "Parcela fixa contratada" in content
        assert 'id="id_fee_fixed_amount"' in content
        assert 'name="billing_type"' not in content
        assert 'name="flat_fee_amount"' not in content

        update = client.post(
            f"/matters/{matter.pk}/edit",
            posted(
                name="Caso ilustrativo atualizado",
                fee_fixed_amount="3.500,00",
                fee_success_percentage="25,50",
            ),
        )
        assert update.status_code == 204
        reopened_again = client.get(f"/matters/{matter.pk}/edit")
        assert reopened_again.status_code == 200

    matter.refresh_from_db()
    assert matter.fee_fixed_amount == Decimal("3500.00")
    assert matter.fee_success_percentage == Decimal("25.50")
    assert matter.name == "Caso ilustrativo atualizado"
    assert matter.flat_fee_amount is None


def test_malformed_grouping_is_not_silently_reinterpreted():
    with translation.override("pt-br"):
        malformed = MatterForm(posted(fee_fixed_amount="2.00,00"))
        assert not malformed.is_valid()
        assert "fee_fixed_amount" in malformed.errors


def test_editing_unchanged_historical_mixed_case_without_fixed_contract_is_allowed():
    matter = Matter.objects.create(
        name="Antigo sem parcela contratual",
        status="Open",
        fee_agreement_type="MIXED",
        flat_fee_amount=Decimal("2000"),
        fee_success_percentage=Decimal("30"),
        fee_success_basis="1800000",
    )
    with translation.override("pt-br"):
        unchanged = MatterForm(
            posted(
                name="Antigo atualizado",
                fee_fixed_amount="",
                fee_success_basis="1800000",
            ),
            instance=matter,
        )
        assert unchanged.is_valid(), unchanged.errors.as_json()
        unchanged.save()
        assert matter.fee_fixed_amount is None

        fresh = MatterForm(posted(fee_fixed_amount="", fee_success_basis="1800000"))
        assert not fresh.is_valid()
        assert "fee_fixed_amount" in fresh.errors
