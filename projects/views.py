from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from .forms import ProjectForm
from .models import Project

PROJECTS_PER_PAGE = 12


def ajax_login_required(view):
    """Для запросов из JavaScript: гостю отвечаем JSON-ошибкой, а не редиректом."""

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"status": "error"}, status=401)
        return view(request, *args, **kwargs)

    return wrapper


@ensure_csrf_cookie
def project_list(request):
    projects = Project.objects.select_related("owner")
    page_obj = Paginator(projects, PROJECTS_PER_PAGE).get_page(request.GET.get("page"))
    context = {"projects": projects, "page_obj": page_obj}
    return render(request, "projects/project_list.html", context)


@login_required
@ensure_csrf_cookie
def favorite_projects(request):
    projects = request.user.favorites.select_related("owner")
    return render(request, "projects/favorite_projects.html", {"projects": projects})


@ensure_csrf_cookie
def project_detail(request, project_id):
    project = get_object_or_404(Project.objects.select_related("owner"), pk=project_id)
    return render(request, "projects/project-details.html", {"project": project})


@login_required
def create_project(request):
    form = ProjectForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        project = form.save(commit=False)
        project.owner = request.user
        project.save()
        project.participants.add(request.user)
        return redirect("projects:detail", project_id=project.pk)
    context = {"form": form, "is_edit": False}
    return render(request, "projects/create-project.html", context)


@login_required
def edit_project(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    if project.owner_id != request.user.pk:
        raise PermissionDenied
    form = ProjectForm(request.POST or None, instance=project)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("projects:detail", project_id=project.pk)
    context = {"form": form, "is_edit": True}
    return render(request, "projects/create-project.html", context)


@require_POST
@ajax_login_required
def complete_project(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    if project.owner_id != request.user.pk:
        return JsonResponse({"status": "error"}, status=403)
    if project.status != "open":
        return JsonResponse({"status": "error"}, status=400)
    project.status = "closed"
    project.save(update_fields=["status"])
    return JsonResponse({"status": "ok", "project_status": "closed"})


@require_POST
@ajax_login_required
def toggle_participate(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    is_participant = project.participants.filter(pk=request.user.pk).exists()
    if is_participant:
        project.participants.remove(request.user)
    else:
        project.participants.add(request.user)
    return JsonResponse({"status": "ok", "participant": not is_participant})


@require_POST
@ajax_login_required
def toggle_favorite(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    is_favorite = request.user.favorites.filter(pk=project.pk).exists()
    if is_favorite:
        request.user.favorites.remove(project)
    else:
        request.user.favorites.add(project)
    return JsonResponse({"status": "ok", "favorited": not is_favorite})
