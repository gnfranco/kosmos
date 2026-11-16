"""Regression checks for the first Brazilian Portuguese localization slice.

English source msgids remain stable for upstream merges; translations are
selected at request/render time rather than replacing internal data keys.
"""

from datetime import date

from django.template.loader import get_template
from django.test import SimpleTestCase
from django.utils import formats, translation
from django.utils.translation import gettext

from apps.reports.wip.aggregation import WIP_PERIODS


class BrazilianPortugueseLocaleTests(SimpleTestCase):
    def test_pt_br_catalog_and_dashboard_period_labels(self):
        with translation.override("pt-br"):
            self.assertEqual(gettext("Matters"), "Casos")
            self.assertEqual(gettext("Work in Progress"), "Horas a faturar")
            self.assertEqual(gettext("Invalid verification code."), "Código de verificação inválido.")
            self.assertEqual(str(dict(WIP_PERIODS)["this_month"]), "Este mês")

    def test_date_uses_brazilian_order(self):
        with translation.override("pt-br"):
            self.assertEqual(
                formats.date_format(date(2026, 11, 16), "SHORT_DATE_FORMAT"),
                "16/11/2026",
            )

    def test_english_fallback_remains_available(self):
        with translation.override("en-us"):
            self.assertEqual(gettext("Matters"), "Matters")
            self.assertEqual(str(dict(WIP_PERIODS)["this_month"]), "This Month")

    def test_primary_templates_compile(self):
        for name in (
            "base.html",
            "base-minimal.html",
            "sidebar.html",
            "registration/base.html",
            "registration/login.html",
            "registration/verify_code.html",
            "registration/verify_authenticator.html",
            "registration/password_reset_done.html",
            "registration/password_reset_complete.html",
            "registration/password_reset_confirm.html",
            "registration/password_reset_form.html",
            "dash/content.html",
            "dash/events_section.html",
            "dash/wip_section.html",
        ):
            with self.subTest(template=name):
                self.assertIsNotNone(get_template(name))
