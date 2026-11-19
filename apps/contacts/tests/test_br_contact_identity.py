"""Brazilian contact identity and safe legacy compatibility (L2a)."""

import pytest
from django.utils import translation

from apps.contacts.br_documents import (
    is_valid_cnpj,
    is_valid_cpf,
    normalize_br_phone,
    normalize_document,
)
from apps.contacts.forms import ContactForm
from apps.contacts.models import Contact

pytestmark = pytest.mark.django_db


def test_cpf_check_digit_and_normalization():
    assert normalize_document("529.982.247-25") == "52998224725"
    assert is_valid_cpf("52998224725")
    assert not is_valid_cpf("52998224726")
    assert not is_valid_cpf("11111111111")
    with pytest.raises(ValueError):
        normalize_document("123<456")
    with pytest.raises(ValueError):
        normalize_document("---")


def test_cnpj_numeric_and_alphanumeric_from_receita_federal():
    assert is_valid_cnpj("04252011000110")  # traditional numeric
    assert normalize_document("00.000.000/E08G-12") == "00000000E08G12"
    assert is_valid_cnpj("00000000E08G12")  # official first alpha CNPJ
    assert not is_valid_cnpj("00000000E08G13")
    assert not is_valid_cnpj("00000000E08G1X")
    assert not is_valid_cnpj("00000000000000")


def test_br_phone_with_ddd_and_optional_country_code():
    assert normalize_br_phone("(16) 99999-1234") == "16999991234"
    assert normalize_br_phone("+55 (16) 3333-4444") == "1633334444"
    with pytest.raises(ValueError):
        normalize_br_phone("(16) 123")
    with pytest.raises(ValueError):
        normalize_br_phone("https://not-a-phone.invalid")


def test_pf_form_uses_validated_cpf_and_phone(contact):
    with translation.override("pt-br"):
        form = ContactForm(
            {
                "name": "Pessoa de laboratório",
                "person_type": "PF",
                "tax_id": "529.982.247-25",
                "phone1": "(16) 99999-1234",
            }
        )
        assert form.is_valid(), form.errors.as_json()
        person = form.save()
    person.refresh_from_db()
    assert person.person_type == "PF"
    assert person.tax_id == "52998224725"
    assert person.phone1 == "16999991234"
    assert person.history.first().tax_id == "52998224725"
    assert person.tax_id_masked == "••••4725"


def test_pj_form_accepts_alphanumeric_cnpj_and_trade_name():
    with translation.override("pt-br"):
        form = ContactForm(
            {
                "name": "Empresa fictícia de laboratório Ltda",
                "person_type": "PJ",
                "tax_id": "00.000.000/E08G-12",
                "trade_name": "Laboratório",
            }
        )
        assert form.is_valid(), form.errors.as_json()
        contact = form.save()
    assert contact.tax_id == "00000000E08G12"
    assert contact.trade_name == "Laboratório"
    assert contact.person_type == "PJ"


def test_tax_id_validation_and_person_type_are_consistent():
    with translation.override("pt-br"):
        wrong = ContactForm(
            {"name": "Teste", "person_type": "PF", "tax_id": "00000000E08G12"}
        )
        assert not wrong.is_valid()
        assert "tax_id" in wrong.errors
        missing_type = ContactForm({"name": "Teste", "tax_id": "52998224725"})
        assert not missing_type.is_valid()
        assert "person_type" in missing_type.errors
        invalid = ContactForm(
            {"name": "Teste", "person_type": "PJ", "tax_id": "00000000E08G13"}
        )
        assert not invalid.is_valid()
        assert "tax_id" in invalid.errors


def test_legacy_post_does_not_delete_tax_id_or_change_person_type():
    contact = Contact.objects.create(
        name="Legado", person_type="PF", tax_id="52998224725"
    )
    with translation.override("pt-br"):
        form = ContactForm({"name": "Legado atualizado"}, instance=contact)
        assert form.is_valid(), form.errors.as_json()
        form.save()
    contact.refresh_from_db()
    assert contact.name == "Legado atualizado"
    assert contact.person_type == "PF"
    assert contact.tax_id == "52998224725"


def test_en_us_form_still_accepts_us_phone_without_editing_br_fields():
    contact = Contact.objects.create(
        name="US legacy", person_type="PJ", tax_id="04252011000110"
    )
    with translation.override("en-us"):
        form = ContactForm(
            {"name": "US legacy updated", "phone1": "(406) 363-1234"},
            instance=contact,
        )
        assert "tax_id" not in form.fields
        assert form.is_valid(), form.errors.as_json()
        form.save()
    contact.refresh_from_db()
    assert contact.tax_id == "04252011000110"
    assert contact.phone1 == "4063631234"


def test_http_roundtrip_add_edit_and_masked_details(client):
    with translation.override("pt-br"):
        page = client.get("/contacts/add")
        assert page.status_code == 200
        assert "Pessoa jurídica (CNPJ)" in page.content.decode()
        assert "CPF ou CNPJ" in page.content.decode()

        response = client.post(
            "/contacts/add",
            {
                "name": "Pessoa de exemplo",
                "person_type": "PF",
                "tax_id": "529.982.247-25",
                "phone1": "(16) 99999-1234",
            },
        )
        assert response.status_code == 302
        created = Contact.objects.get(name="Pessoa de exemplo")
        edited = client.get(f"/contacts/{created.pk}/edit")
        assert edited.status_code == 200
        assert "52998224725" in edited.content.decode()
        details = client.get(f"/contacts/{created.pk}/details")
        assert details.status_code == 200
        html = details.content.decode()
        assert "••••4725" in html
        assert "52998224725" not in html
        saved = client.post(
            f"/contacts/{created.pk}/edit",
            {
                "name": "Pessoa de exemplo atualizada",
                "person_type": "PF",
                "tax_id": "529.982.247-25",
            },
        )
        assert saved.status_code == 302
    created.refresh_from_db()
    assert created.tax_id == "52998224725"


def test_foreign_or_legacy_contact_without_br_id_is_unchanged():
    legacy = Contact.objects.create(name="Contato estrangeiro")
    assert legacy.person_type == "UNSPECIFIED"
    assert legacy.tax_id == ""
    assert legacy.trade_name == ""


def test_brazilian_phone_display_and_tel_link_for_typed_contacts():
    from apps.management.templatetags.phone_numbers import phone_number, phone_tel

    assert phone_number("16999991234", "PF") == "(16) 99999-1234"
    assert phone_number("1633334444", "PJ") == "(16) 3333-4444"
    assert phone_tel("16999991234", "PF") == "+5516999991234"
    assert phone_number("4063631234") == "(406) 363-1234"
    assert phone_tel("4063631234") == "+14063631234"


def test_long_brazilian_legal_name_uses_model_limit():
    long_name = "Empresa exemplo fictícia de serviços e consultoria de gestão" + " XYZ"
    assert 50 < len(long_name) <= 100
    with translation.override("pt-br"):
        form = ContactForm({"name": long_name, "person_type": "PJ"})
        assert form.is_valid(), form.errors.as_json()
        item = form.save()
    assert item.name == long_name


def test_invalid_tax_document_is_rejected_by_http(client):
    with translation.override("pt-br"):
        response = client.post(
            "/contacts/add",
            {
                "name": "Contato recusado",
                "person_type": "PJ",
                "tax_id": "00.000.000/E08G-13",
            },
        )
    assert response.status_code == 200
    assert not Contact.objects.filter(name="Contato recusado").exists()
    assert "O CNPJ informado possui dígitos verificadores inválidos." in (
        response.content.decode()
    )
