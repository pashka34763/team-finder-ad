from django.core.paginator import Paginator
from django.shortcuts import render

from .models import Project

PROJECTS_PER_PAGE = 12


def project_list(request):
    projects = Project.objects.select_related("owner")
    page_obj = Paginator(projects, PROJECTS_PER_PAGE).get_page(request.GET.get("page"))
    context = {"projects": projects, "page_obj": page_obj}
    return render(request, "projects/project_list.html", context)
