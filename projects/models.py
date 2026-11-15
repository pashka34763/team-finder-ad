from django.conf import settings
from django.db import models


class Project(models.Model):
    STATUS_CHOICES = [("open", "Open"), ("closed", "Closed")]

    name = models.CharField("Название", max_length=200)
    description = models.TextField("Описание", blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_projects",
        verbose_name="Автор",
    )
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    github_url = models.URLField("GitHub", blank=True)
    status = models.CharField("Статус", max_length=6, choices=STATUS_CHOICES, default="open")
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="participated_projects",
        blank=True,
        verbose_name="Участники",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "проект"
        verbose_name_plural = "проекты"

    def __str__(self):
        return self.name
