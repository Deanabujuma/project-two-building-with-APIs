from django.contrib.auth.decorators import login_required
from django.shortcuts import render


def home(request):
    """Public home page: a welcome hero for visitors, the personal home for users."""
    return render(request, "home.html")


@login_required
def discover(request):
    """Search TVmaze (built in Phase 3)."""
    return render(request, "shows/discover.html")


@login_required
def collection(request):
    """The user's collection (full filters, sorting and pagination come in Phase 7)."""
    return render(request, "shows/collection.html")
