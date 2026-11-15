import re

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.forms import PasswordChangeForm

from .models import User
from .validators import validate_github_url


class RegisterForm(forms.ModelForm):
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ("name", "surname", "email", "password")

    def clean_password(self):
        password = self.cleaned_data["password"]
        validate_password(password)
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    email = forms.EmailField(label="Email")
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        self.user = None

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")
        if email and password:
            self.user = authenticate(self.request, email=email, password=password)
            if self.user is None:
                raise forms.ValidationError("Неверный имейл или пароль")
        return cleaned_data


PHONE_PATTERN = re.compile(r"^(\+7|8)\d{10}$")


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("name", "surname", "avatar", "about", "phone", "github_url")
        widgets = {
            "avatar": forms.FileInput,
            "about": forms.Textarea(attrs={"rows": 4}),
        }

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip()
        if not phone:
            return phone
        if not PHONE_PATTERN.match(phone):
            raise forms.ValidationError(
                "Телефон должен быть в формате 8XXXXXXXXXX или +7XXXXXXXXXX"
            )
        if phone.startswith("8"):
            phone = "+7" + phone[1:]
        if User.objects.filter(phone=phone).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Этот номер телефона уже используется")
        return phone

    def clean_github_url(self):
        url = self.cleaned_data["github_url"]
        if url:
            validate_github_url(url)
        return url


class ChangePasswordForm(PasswordChangeForm):
    pass
