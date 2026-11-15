"""Settings used by pytest: the real settings plus a throwaway secret key.

This lets a fresh clone run `uv run pytest` without creating `.env`. The key below
is only for tests and must never be used to run the site.
"""

import os

os.environ.setdefault("DJANGO_SECRET_KEY", "test-only-insecure-key-do-not-use-for-the-site")

from config.settings import *  # noqa: E402,F401,F403

# Faster password hashing keeps tests quick.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
