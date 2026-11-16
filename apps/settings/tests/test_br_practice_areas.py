"""Only administrators manage practice areas; historical links cannot be lost."""

import pytest
from django.urls import reverse
from django.utils import translation

from apps.intakes.models import Intake
from apps.matters.models import Matter, PracticeArea

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "route,method",
    [
        ("settings:matters-index", "get"),
        ("settings:practice-area-list", "get"),
        ("settings:add-practice-area", "get"),
        ("settings:add-practice-area", "post"),
    ],
)
def test_non_admin_cannot_manage_practice_areas(client, route, method):
    response = getattr(client, method)(reverse(route))
    assert response.status_code == 403


def test_admin_can_create_disable_and_view_brazilian_area(admin_client):
    add_url = reverse("settings:add-practice-area")
    with translation.override("pt-br"):
        result = admin_client.get(add_url)
        assert "Adicionar área de atuação" in result.content.decode()
        result = admin_client.post(
            add_url, {"name": "Direito Digital", "is_active": "on"}
        )
    assert result.status_code == 204
    area = PracticeArea.objects.get(name="Direito Digital")
    assert area.is_active

    edit_url = reverse("settings:edit-practice-area", args=[area.pk])
    response = admin_client.post(edit_url, {"name": area.name})
    assert response.status_code == 204
    area.refresh_from_db()
    assert not area.is_active
    assert area.pk is not None


@pytest.mark.parametrize("relation", ["matter", "intake"])
def test_cannot_delete_practice_area_in_use(admin_client, relation):
    area = PracticeArea.objects.create(name="Referenciada")
    if relation == "matter":
        Matter.objects.create(name="Caso relacionado", practice_area=area)
    else:
        Intake.objects.create(name="Atendimento relacionado", practice_area=area)

    response = admin_client.post(
        reverse("settings:delete-practice-area", args=[area.pk])
    )
    assert response.status_code == 409
    assert PracticeArea.objects.filter(pk=area.pk).exists()
