from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm


class DarkFormMixin:
    """Give every widget Bootstrap's form-control class so it matches the dark theme."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")


class SignUpForm(DarkFormMixin, UserCreationForm):
    """Sign-up form for HTTP.tv's custom user model."""

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ("username",)


class LoginForm(DarkFormMixin, AuthenticationForm):
    """Django's login form, styled for the dark theme."""
