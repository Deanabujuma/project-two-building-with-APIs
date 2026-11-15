from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """HTTP.tv's user model.

    It adds no fields yet, but starting with a custom user model (before the first
    migration) means the user table can be changed later without a painful migration.
    """
