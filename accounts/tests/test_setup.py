"""Phase 1 checks: secure settings and the custom user model."""

import os
import subprocess
import sys
from pathlib import Path

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser

REPO_ROOT = Path(__file__).resolve().parents[2]


def run_django_setup(extra_env):
    """Start Django with config.settings in a fresh process and return the result."""
    env = {k: v for k, v in os.environ.items() if k != "DJANGO_SECRET_KEY"}
    env.update({"DJANGO_SETTINGS_MODULE": "config.settings", **extra_env})
    return subprocess.run(
        [sys.executable, "-c", "import django; django.setup(); print('started')"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


def test_settings_refuse_to_start_without_secret_key():
    result = run_django_setup({})
    assert result.returncode != 0
    assert "DJANGO_SECRET_KEY is not set" in result.stderr


def test_settings_refuse_blank_secret_key():
    result = run_django_setup({"DJANGO_SECRET_KEY": "   "})
    assert result.returncode != 0
    assert "DJANGO_SECRET_KEY is not set" in result.stderr


def test_settings_start_when_secret_key_is_set():
    result = run_django_setup({"DJANGO_SECRET_KEY": "a-test-key-for-this-check-only"})
    assert result.returncode == 0, result.stderr
    assert "started" in result.stdout


def test_custom_user_model_is_active():
    User = get_user_model()
    assert User._meta.label == "accounts.User"
    assert issubclass(User, AbstractUser)


def test_custom_user_can_be_created(db):
    user = get_user_model().objects.create_user(username="demo_user", password="a-strong-pass-123")
    assert user.check_password("a-strong-pass-123")


def test_no_migration_references_builtin_auth_user():
    for migration in REPO_ROOT.glob("*/migrations/0*.py"):
        assert "auth.User" not in migration.read_text(encoding="utf-8"), migration
