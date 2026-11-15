from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ChangePasswordForm, LoginForm, ProfileForm, RegisterForm
from .models import User

USERS_PER_PAGE = 12

USER_FILTERS = {
    "owners-of-favorite-projects": "owned_projects__interested_users",
    "owners-of-participating-projects": "owned_projects__participants",
    "interested-in-my-projects": "favorites__owner",
    "participants-of-my-projects": "participated_projects__owner",
}


def register(request):
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("users:login")
    return render(request, "users/register.html", {"form": form})


def login_view(request):
    form = LoginForm(request.POST or None, request=request)
    if request.method == "POST" and form.is_valid():
        login(request, form.user)
        return redirect("projects:list")
    return render(request, "users/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("projects:list")


def user_list(request):
    users = User.objects.all()
    active_filter = ""
    query_prefix = ""
    if request.user.is_authenticated:
        lookup = USER_FILTERS.get(request.GET.get("filter"))
        if lookup:
            active_filter = request.GET["filter"]
            query_prefix = f"filter={active_filter}&"
            users = (
                users.filter(**{lookup: request.user})
                .exclude(pk=request.user.pk)
                .distinct()
            )
    page_obj = Paginator(users, USERS_PER_PAGE).get_page(request.GET.get("page"))
    context = {
        "participants": users,
        "page_obj": page_obj,
        "active_filter": active_filter,
        "query_prefix": query_prefix,
    }
    return render(request, "users/participants.html", context)


def user_detail(request, user_id):
    profile_user = get_object_or_404(User, pk=user_id)
    return render(request, "users/user-details.html", {"user": profile_user})


@login_required
def edit_profile(request):
    form = ProfileForm(
        request.POST or None, request.FILES or None, instance=request.user
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("users:detail", user_id=request.user.pk)
    return render(request, "users/edit_profile.html", {"form": form})


@login_required
def change_password(request):
    form = ChangePasswordForm(request.user, request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        return redirect("users:detail", user_id=user.pk)
    return render(request, "users/change_password.html", {"form": form})
