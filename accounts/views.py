from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count
from django.shortcuts import redirect, render
from rest_framework.authtoken.models import Token

from shows.models import CollectionEntry

from .forms import DeleteAccountForm, PreferencesForm, SignUpForm, StyledPasswordChangeForm, UsernameForm


def signup(request):
    """Create an account and log the new user straight in."""
    if request.user.is_authenticated:
        return redirect("home")
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to HTTP.tv, {user.username}!")
            return redirect("home")
    else:
        form = SignUpForm()
    return render(request, "accounts/signup.html", {"form": form})


def _fresh_user(request):
    """A separate copy of the user for a form to edit, so a rejected form never changes request.user."""
    return get_user_model().objects.get(pk=request.user.pk)


def _collection_counts(user):
    counts = dict(CollectionEntry.objects.filter(user=user).values_list("status").annotate(n=Count("pk")))
    rows = [(label, counts.get(value, 0)) for value, label in CollectionEntry.Status.choices]
    return sum(counts.values()), rows


@login_required
def profile(request):
    """Profile & Settings: account details, username, password, preferences, shortcuts, Danger Zone.

    Each form posts with a hidden `form` field naming which one was submitted.
    """
    forms = {
        "username": UsernameForm(instance=_fresh_user(request), prefix="username"),
        "password": StyledPasswordChangeForm(request.user, prefix="password"),
        "preferences": PreferencesForm(instance=_fresh_user(request), prefix="preferences"),
    }
    status = 200
    if request.method == "POST":
        which = request.POST.get("form")
        if which == "username":
            form = UsernameForm(request.POST, instance=_fresh_user(request), prefix="username")
            if form.is_valid():
                form.save()
                messages.success(request, f"Your username is now {form.instance.username}.")
                return redirect("accounts:profile")
        elif which == "password":
            form = StyledPasswordChangeForm(request.user, request.POST, prefix="password")
            if form.is_valid():
                user = form.save()
                update_session_auth_hash(request, user)  # stay logged in on this device
                revoked = Token.objects.filter(user=user).delete()[0]
                note = " Your API token was revoked; get a new one for scripts." if revoked else ""
                messages.success(request, "Your password was changed." + note)
                return redirect("accounts:profile")
        elif which == "preferences":
            form = PreferencesForm(request.POST, instance=_fresh_user(request), prefix="preferences")
            if form.is_valid():
                form.save()
                messages.success(request, "Your preferences were saved.")
                return redirect("accounts:profile")
        else:
            return redirect("accounts:profile")
        forms[which] = form
        status = 400

    total, by_status = _collection_counts(request.user)
    return render(request, "accounts/profile.html", {
        **{f"{name}_form": form for name, form in forms.items()},
        "total_saved": total,
        "by_status": by_status,
        "has_token": Token.objects.filter(user=request.user).exists(),
    }, status=status)


@login_required
def delete_account(request):
    """Permanently delete the logged-in user's account, after a confirmation page.

    GET only shows the warning and the form. POST (CSRF-protected) re-checks the password
    and the word DELETE on the server, then deletes this user. The database cascades remove
    only their collection entries and API token; shared Show rows and other users stay.
    """
    if request.method == "POST":
        form = DeleteAccountForm(request.user, request.POST)
        if form.is_valid():
            user = _fresh_user(request)
            with transaction.atomic():
                user.delete()
            logout(request)
            messages.success(request, "Your account has been permanently deleted.")
            return redirect("home")
        status = 400
    else:
        form = DeleteAccountForm(request.user)
        status = 200
    total, _ = _collection_counts(request.user)
    return render(request, "accounts/delete_account.html", {"form": form, "total_saved": total}, status=status)
