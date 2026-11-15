from django import forms

from users.validators import validate_github_url

from .models import Project

STATUS_LABELS = [("open", "Открыт"), ("closed", "Закрыт")]


class ProjectForm(forms.ModelForm):
    status = forms.ChoiceField(label="Статус", choices=STATUS_LABELS)

    class Meta:
        model = Project
        fields = ("name", "description", "github_url", "status")

    def clean_github_url(self):
        url = self.cleaned_data["github_url"]
        if url:
            validate_github_url(url)
        return url
