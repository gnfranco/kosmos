"""Regression for gettext's "_" alias in the dashboard WIP handler."""
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase
from django.utils import translation

from apps.dash.views import dash_wip_context


class DashboardWipTranslationTests(SimpleTestCase):
    def test_admin_context_does_not_shadow_gettext(self):
        request = SimpleNamespace(
            session={}, GET={},
            user=SimpleNamespace(is_admin=True, perm_reports=True),
        )
        with (
            translation.override("pt-br"),
            patch("apps.dash.views.wip_user_breakdown", return_value=([], [], {})),
            patch("apps.dash.views.wip_matter_breakdown", return_value=([], [], {})),
        ):
            context = dash_wip_context(request)
        self.assertTrue(context["wip_period_label"])
        self.assertTrue(context["wip_show_all"])
        self.assertEqual(context["user_rows"], [])
