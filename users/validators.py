from urllib.parse import urlparse

from django.core.exceptions import ValidationError


def validate_github_url(value):
    host = urlparse(value).hostname or ""
    if host != "github.com" and not host.endswith(".github.com"):
        raise ValidationError("Ссылка должна вести на GitHub")
