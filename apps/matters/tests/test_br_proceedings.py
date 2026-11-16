"""Brazilian proceeding extension: check digits, amounts, auth, compatibility."""
from decimal import Decimal

from django.http import Http404
from django.template.loader import get_template
from django.test import RequestFactory, SimpleTestCase, TestCase
from django.utils import translation
from django.core.exceptions import ValidationError

from apps.accounts.models import CustomUser
from apps.matters.models import Matter
from apps.matters.proceedings import views
from apps.matters.proceedings.cnj import normalize_cnj
from apps.matters.proceedings.forms import ProceedingForm
from apps.matters.proceedings.models import Proceeding


VALID_CNJ = "5000094-40.2025.4.03.6312"


class CnjValidationTests(SimpleTestCase):
    def test_verified_number_is_normalized(self):
        self.assertEqual(normalize_cnj(VALID_CNJ), VALID_CNJ)
        self.assertEqual(normalize_cnj("50000944020254036312"), VALID_CNJ)

    def test_bad_digit_is_rejected(self):
        with self.assertRaises(ValidationError):
            normalize_cnj("5000094-41.2025.4.03.6312")

    def test_invalid_format_and_segment_rejected(self):
        for value in ("123", "5000094-40.2025.X.03.6312",
                      "5000094-40.2025.0.03.6312"):
            with self.subTest(value=value):
                with self.assertRaises(ValidationError):
                    normalize_cnj(value)

    def test_other_case_number_keeps_original(self):
        form = ProceedingForm(data={
            "numbering_scheme": "OTHER",
            "case_number": "20CV141360",
            "primary": "False",
        })
        self.assertTrue(form.is_valid(), form.errors.as_text())
        self.assertEqual(form.cleaned_data["case_number"], "20CV141360")

    def test_cnj_scheme_requires_valid_check_digits(self):
        form = ProceedingForm(data={
            "numbering_scheme": "CNJ",
            "case_number": "5000094-41.2025.4.03.6312",
            "primary": "False",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("case_number", form.errors)

    def test_form_uses_portuguese_labels_and_date_format(self):
        with translation.override("pt-br"):
            form = ProceedingForm()
            self.assertEqual(str(form.fields["case_class"].label), "Classe processual")
            self.assertEqual(str(form.fields["numbering_scheme"].label), "Tipo de numeração")
            self.assertIsNotNone(get_template("matters/proceedings/list.html"))
            self.assertIsNotNone(get_template("matters/proceedings/form.html"))


class BrazilianProceedingPersistenceTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="lexbrtest", email="lexbrtest@example.com",
            password="not-used", role="ADMIN",
        )
        self.matter_a = Matter.objects.create(
            name="Caso A", user=self.user, status="Open"
        )
        self.matter_b = Matter.objects.create(
            name="Caso B", user=self.user, status="Open"
        )
        self.request_factory = RequestFactory()

    def request(self, method, url):
        request = getattr(self.request_factory, method)(url)
        request.user = self.user
        return request

    def test_creation_persists_fields_and_history(self):
        form = ProceedingForm(data={
            "numbering_scheme": "CNJ",
            "case_number": "50000944020254036312",
            "case_class": "Reclamação Trabalhista",
            "court_division": "1ª Vara do Trabalho",
            "forum": "TRT da 3ª Região",
            "claim_amount_brl": "12500.50",
            "claim_updated_brl": "13000.75",
            "date_filed": "2025-03-01",
            "date_final_judgment": "2026-02-01",
            "case_url": "https://www.trt3.jus.br/",
            "status": "Ongoing",
            "primary": "True",
        })
        self.assertTrue(form.is_valid(), form.errors.as_text())
        obj = form.save(commit=False)
        obj.matter = self.matter_a
        obj.user = self.user
        obj.save()
        obj.refresh_from_db()
        self.assertEqual(obj.case_number, VALID_CNJ)
        self.assertEqual(obj.claim_amount_brl, Decimal("12500.50"))
        self.assertEqual(obj.claim_updated_brl, Decimal("13000.75"))
        self.assertEqual(obj.date_final_judgment.isoformat(), "2026-02-01")
        self.assertEqual(obj.history.first().case_class, "Reclamação Trabalhista")

    def test_one_case_can_have_several_judicial_proceedings(self):
        for num in ("20CV141360", "20CV141361"):
            Proceeding.objects.create(
                matter=self.matter_a, user=self.user,
                numbering_scheme="OTHER", case_number=num
            )
        self.assertEqual(self.matter_a.proceeding_set.count(), 2)

    def test_cross_matter_edit_and_delete_do_not_touch_proceeding(self):
        alien = Proceeding.objects.create(
            matter=self.matter_b, user=self.user,
            case_number="OTHER-123", numbering_scheme="OTHER",
        )
        url = f"/matters/{self.matter_a.pk}/proceedings/{alien.pk}/edit"
        with self.assertRaises(Http404):
            views.edit(self.request("get", url),
                       id=self.matter_a.pk, proceeding_id=alien.pk)
        with self.assertRaises(Http404):
            views.edit(self.request("post", url),
                       id=self.matter_a.pk, proceeding_id=alien.pk)
        url = f"/matters/{self.matter_a.pk}/proceedings/{alien.pk}/delete"
        with self.assertRaises(Http404):
            views.delete(self.request("delete", url),
                         matter_id=self.matter_a.pk, proceeding_id=alien.pk)
        self.assertTrue(Proceeding.objects.filter(pk=alien.pk).exists())

    def test_delete_refuses_get(self):
        obj = Proceeding.objects.create(
            matter=self.matter_a, user=self.user, case_number="LEGACY"
        )
        url = f"/matters/{self.matter_a.pk}/proceedings/{obj.pk}/delete"
        response = views.delete(self.request("get", url),
                                matter_id=self.matter_a.pk, proceeding_id=obj.pk)
        self.assertEqual(response.status_code, 405)
        self.assertTrue(Proceeding.objects.filter(pk=obj.pk).exists())
