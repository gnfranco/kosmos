from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from apps.intakes.models import Intake
from apps.matters.models import PracticeArea
from apps.settings.matters.forms import PracticeAreaForm


@login_required
def matters_index(request):
    if not request.user.is_admin:
        return HttpResponseForbidden()

    practice_area_filter = request.session.get(
        "settings_practice_area_filter", "active"
    )

    practice_areas = PracticeArea.objects.all().order_by("name")
    if practice_area_filter == "active":
        practice_areas = practice_areas.filter(is_active=True)
    elif practice_area_filter == "inactive":
        practice_areas = practice_areas.filter(is_active=False)

    context = {
        "subapp": "matters",
        "practice_areas": practice_areas,
        "practice_area_filter": practice_area_filter,
    }

    return render(request, "settings/matters/index.html", context)


@login_required
def practice_area_list(request):
    if not request.user.is_admin:
        return HttpResponseForbidden()

    practice_area_filter = request.session.get(
        "settings_practice_area_filter", "active"
    )

    practice_areas = PracticeArea.objects.all().order_by("name")
    if practice_area_filter == "active":
        practice_areas = practice_areas.filter(is_active=True)
    elif practice_area_filter == "inactive":
        practice_areas = practice_areas.filter(is_active=False)

    context = {
        "practice_areas": practice_areas,
        "practice_area_filter": practice_area_filter,
    }

    return render(request, "settings/matters/practice-area-table.html", context)


@login_required
def practice_area_filter(request, status):
    if not request.user.is_admin:
        return HttpResponseForbidden()

    request.session["settings_practice_area_filter"] = status
    return HttpResponse(status=204, headers={"HX-Trigger": "practiceAreaListReload"})


@login_required
def add_practice_area(request):
    if not request.user.is_admin:
        return HttpResponseForbidden()

    if request.method == "POST":
        form = PracticeAreaForm(request.POST)

        if form.is_valid():
            form.save()

            return HttpResponse(
                status=204, headers={"HX-Trigger": "practiceAreaListReload"}
            )
    else:
        form = PracticeAreaForm()

    context = {
        "form": form,
    }

    return render(request, "settings/matters/practice-area-form.html", context)


@login_required
def edit_practice_area(request, practice_area_id):
    if not request.user.is_admin:
        return HttpResponseForbidden()

    practice_area = PracticeArea.objects.get(id=practice_area_id)

    if request.method == "POST":
        form = PracticeAreaForm(request.POST, instance=practice_area)

        if form.is_valid():
            form.save()

            return HttpResponse(
                status=204, headers={"HX-Trigger": "practiceAreaListReload"}
            )
    else:
        form = PracticeAreaForm(instance=practice_area)

    context = {
        "form": form,
        "practice_area": practice_area,
    }

    return render(request, "settings/matters/practice-area-form.html", context)


@login_required
@require_POST
def delete_practice_area(request, practice_area_id):
    if not request.user.is_admin:
        return HttpResponseForbidden()

    practice_area = get_object_or_404(PracticeArea, pk=practice_area_id)
    if (
        practice_area.matters.exists()
        or Intake.objects.filter(practice_area=practice_area).exists()
    ):
        # Do not silently clear FKs from existing cases or intakes.
        return HttpResponse(status=409)
    practice_area.delete()
    return HttpResponse(status=204, headers={"HX-Trigger": "practiceAreaListReload"})
