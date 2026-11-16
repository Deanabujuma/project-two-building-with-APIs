from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, UserCreationForm


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


class UsernameForm(DarkFormMixin, forms.ModelForm):
    """Change the username. Uniqueness ignores capitals, like sign-up does."""

    class Meta:
        model = get_user_model()
        fields = ("username",)

    def clean_username(self):
        username = self.cleaned_data["username"]
        taken = get_user_model().objects.filter(username__iexact=username).exclude(pk=self.instance.pk)
        if taken.exists():
            raise forms.ValidationError("That username is already taken.")
        return username


class PreferencesForm(forms.ModelForm):
    """Schedule country and default collection order."""

    class Meta:
        model = get_user_model()
        fields = ("schedule_country", "default_collection_sort")
        widgets = {
            "schedule_country": forms.Select(attrs={"class": "form-select"}),
            "default_collection_sort": forms.Select(attrs={"class": "form-select"}),
        }


class StyledPasswordChangeForm(DarkFormMixin, PasswordChangeForm):
    """Django's password change form (checks the old password and the password validators)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Django autofocuses this field; on the settings page that would jump past the other panels.
        self.fields["old_password"].widget.attrs.pop("autofocus", None)


DELETE_WORD = "DELETE"


class DeleteAccountForm(DarkFormMixin, forms.Form):
    """Confirm account deletion: the current password and the word DELETE, both checked on the server."""

    password = forms.CharField(label="Current password", strip=False,
                               widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}))
    confirm = forms.CharField(label=f"Type {DELETE_WORD} to confirm",
                              widget=forms.TextInput(attrs={"autocomplete": "off", "spellcheck": "false"}))

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_password(self):
        password = self.cleaned_data["password"]
        if not self.user.check_password(password):
            raise forms.ValidationError("That password is incorrect.")
        return password

    def clean_confirm(self):
        confirm = self.cleaned_data["confirm"]
        if confirm != DELETE_WORD:
            raise forms.ValidationError(f"Type {DELETE_WORD} exactly, in capital letters.")
        return confirm
