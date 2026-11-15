import shutil
import tempfile

from django.test import TestCase, override_settings
from django.urls import reverse

from projects.models import Project

from .models import User

TEMP_MEDIA_ROOT = tempfile.mkdtemp()
PASSWORD = "Str0ng-pass-123"


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class UserTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.user = User.objects.create_user(
            "anna@example.com", PASSWORD, name="Анна", surname="Кузнецова"
        )
        self.other = User.objects.create_user(
            "petr@example.com", PASSWORD, name="Пётр", surname="Сидоров"
        )

    def profile_data(self, **changes):
        data = {
            "name": "Анна",
            "surname": "Кузнецова",
            "about": "",
            "phone": "",
            "github_url": "",
        }
        data.update(changes)
        return data

    def test_avatar_is_generated(self):
        self.assertTrue(self.user.avatar.name.startswith("avatars/"))

    def test_register_creates_user(self):
        data = {
            "name": "Мария",
            "surname": "Иванова",
            "email": "maria@example.com",
            "password": PASSWORD,
        }
        response = self.client.post(reverse("users:register"), data)
        self.assertRedirects(response, reverse("users:login"))
        self.assertTrue(User.objects.filter(email="maria@example.com").exists())

    def test_login_with_wrong_password(self):
        data = {"email": "anna@example.com", "password": "wrong"}
        response = self.client.post(reverse("users:login"), data)
        self.assertContains(response, "Неверный имейл или пароль")

    def test_login_success(self):
        data = {"email": "anna@example.com", "password": PASSWORD}
        response = self.client.post(reverse("users:login"), data)
        self.assertRedirects(response, reverse("projects:list"))

    def test_edit_profile_requires_login(self):
        response = self.client.get(reverse("users:edit_profile"))
        self.assertRedirects(response, "/users/login/?next=/users/edit-profile/")

    def test_phone_is_normalized(self):
        self.client.force_login(self.user)
        data = self.profile_data(phone="89001234567")
        self.client.post(reverse("users:edit_profile"), data)
        self.user.refresh_from_db()
        self.assertEqual(self.user.phone, "+79001234567")

    def test_duplicate_phone_is_rejected(self):
        self.other.phone = "+79001234567"
        self.other.save()
        self.client.force_login(self.user)
        data = self.profile_data(phone="89001234567")
        response = self.client.post(reverse("users:edit_profile"), data)
        self.assertContains(response, "уже используется")

    def test_wrong_phone_format_is_rejected(self):
        self.client.force_login(self.user)
        data = self.profile_data(phone="12345")
        response = self.client.post(reverse("users:edit_profile"), data)
        self.assertContains(response, "Телефон должен быть в формате")

    def test_github_url_must_lead_to_github(self):
        self.client.force_login(self.user)
        data = self.profile_data(github_url="https://google.com")
        response = self.client.post(reverse("users:edit_profile"), data)
        self.assertContains(response, "Ссылка должна вести на GitHub")

    def test_filter_owners_of_favorite_projects(self):
        project = Project.objects.create(name="Бот", owner=self.other)
        self.user.favorites.add(project)
        self.client.force_login(self.user)
        url = reverse("users:list") + "?filter=owners-of-favorite-projects"
        response = self.client.get(url)
        self.assertEqual(list(response.context["page_obj"]), [self.other])

    def test_filter_is_ignored_for_guest(self):
        url = reverse("users:list") + "?filter=owners-of-favorite-projects"
        response = self.client.get(url)
        self.assertEqual(len(response.context["page_obj"]), 2)
