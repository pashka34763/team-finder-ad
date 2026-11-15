import shutil
import tempfile

from django.test import TestCase, override_settings
from django.urls import reverse

from users.models import User

from .models import Project

TEMP_MEDIA_ROOT = tempfile.mkdtemp()
PASSWORD = "Str0ng-pass-123"


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ProjectTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.owner = User.objects.create_user(
            "maria@example.com", PASSWORD, name="Мария", surname="Иванова"
        )
        self.guest_user = User.objects.create_user(
            "anna@example.com", PASSWORD, name="Анна", surname="Кузнецова"
        )
        self.project = Project.objects.create(name="Трекер привычек", owner=self.owner)
        self.project.participants.add(self.owner)

    def url(self, name):
        return reverse(f"projects:{name}", args=[self.project.pk])

    def test_root_redirects_to_project_list(self):
        response = self.client.get("/")
        self.assertRedirects(response, reverse("projects:list"))

    def test_project_list_and_detail_are_public(self):
        self.assertContains(self.client.get(reverse("projects:list")), "Трекер привычек")
        self.assertContains(self.client.get(self.url("detail")), "Трекер привычек")

    def test_guest_cannot_create_project(self):
        response = self.client.get(reverse("projects:create"))
        self.assertRedirects(response, "/users/login/?next=/projects/create-project/")

    def test_create_project_sets_owner_and_participant(self):
        self.client.force_login(self.guest_user)
        data = {"name": "Новый", "description": "", "github_url": "", "status": "open"}
        self.client.post(reverse("projects:create"), data)
        project = Project.objects.get(name="Новый")
        self.assertEqual(project.owner, self.guest_user)
        self.assertIn(self.guest_user, project.participants.all())

    def test_github_url_must_lead_to_github(self):
        self.client.force_login(self.guest_user)
        data = {"name": "Новый", "github_url": "https://google.com", "status": "open"}
        response = self.client.post(reverse("projects:create"), data)
        self.assertContains(response, "Ссылка должна вести на GitHub")
        self.assertFalse(Project.objects.filter(name="Новый").exists())

    def test_only_owner_can_edit(self):
        self.client.force_login(self.guest_user)
        self.assertEqual(self.client.get(self.url("edit")).status_code, 403)
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(self.url("edit")).status_code, 200)

    def test_owner_completes_project(self):
        self.client.force_login(self.owner)
        response = self.client.post(self.url("complete"))
        self.assertEqual(response.json(), {"status": "ok", "project_status": "closed"})
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, "closed")

    def test_stranger_cannot_complete_project(self):
        self.client.force_login(self.guest_user)
        self.assertEqual(self.client.post(self.url("complete")).status_code, 403)
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, "open")

    def test_toggle_participate(self):
        self.client.force_login(self.guest_user)
        response = self.client.post(self.url("toggle_participate"))
        self.assertEqual(response.json(), {"status": "ok", "participant": True})
        self.assertIn(self.guest_user, self.project.participants.all())
        response = self.client.post(self.url("toggle_participate"))
        self.assertEqual(response.json(), {"status": "ok", "participant": False})
        self.assertNotIn(self.guest_user, self.project.participants.all())

    def test_toggle_favorite_and_favorites_page(self):
        self.client.force_login(self.guest_user)
        response = self.client.post(self.url("toggle_favorite"))
        self.assertEqual(response.json(), {"status": "ok", "favorited": True})
        response = self.client.get(reverse("projects:favorites"))
        self.assertEqual(list(response.context["projects"]), [self.project])

    def test_guest_cannot_toggle(self):
        self.assertEqual(self.client.post(self.url("toggle_favorite")).status_code, 401)
        self.assertEqual(self.client.post(self.url("toggle_participate")).status_code, 401)
